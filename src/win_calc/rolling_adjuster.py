import json
import os
import re
import requests
from unidecode import unidecode
from typing import Any, Dict, List, Optional, Tuple


# Defaults (tunable)
WEIGHTS = {"50": 0.5, "100": 0.3, "250": 0.2}

# Ratchet up adjustment effect slightly
AGGRESSIVENESS_K = 0.22
MAX_ABS_TILT = 0.28

LEAGUE_XWOBA_HITTER = 0.320
LEAGUE_XWOBA_PITCHER_ALLOWED = 0.320

# League baselines for histogram-derived quality metrics (tunable)
LEAGUE_HARD_HIT_RATE = 0.38  # share of BBE ≥95 mph
LEAGUE_MEAN_EV = 88.5        # mph
LEAGUE_LINE_DRIVE_RATE = 0.22  # share of BBE with 0–15° launch angle

# Intra-signal weights for quality metrics and blend with xwOBA (tunable)
QUALITY_WEIGHTS = {"hard_hit_rate": 0.5, "mean_ev": 0.3, "line_drive_rate": 0.2}
SIGNAL_BLEND = {"xwoba": 0.7, "quality": 0.3}

ROLLING_ROOT = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/rolling_windows/data"
ROSTERS_PATH = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/active_rosters/data/active_rosters.json"


def _normalize_name(name: str) -> str:
	# Use ASCII fold to handle accents/diacritics
	name = unidecode(name or "").lower().strip()
	name = re.sub(r"[\.'`’]", "", name)
	name = re.sub(r"\s+jr$", "", name)
	name = re.sub(r"\s+sr$", "", name)
	name = re.sub(r"\s+ii$|\s+iii$|\s+iv$", "", name)
	name = re.sub(r"\s+", " ", name)
	return name


def _load_active_rosters() -> Dict[str, Any]:
	try:
		with open(ROSTERS_PATH, "r") as f:
			return json.load(f)
	except Exception:
		return {}


def _build_name_index(rosters: Dict[str, Any]) -> Dict[Tuple[str, str], str]:
	index: Dict[Tuple[str, str], str] = {}
	for team_abbr, team_data in rosters.get("rosters", {}).items():
		for p in team_data.get("roster", []):
			full = p.get("fullName_ascii") or p.get("fullName") or ""
			pid = p.get("id")
			if not full or pid is None:
				continue
			index[(_normalize_name(full), team_abbr.upper())] = str(pid)
	return index


def _load_rolling_file(player_id: str, role: str) -> Optional[Dict[str, Any]]:
	path = os.path.join(ROLLING_ROOT, "hitters" if role == "batter" else "pitchers", f"{player_id}.json")
	if not os.path.exists(path):
		return None
	try:
		with open(path, "r") as f:
			return json.load(f)
	except Exception:
		return None


def _latest_xwoba(rolling: Dict[str, Any], window: str) -> Optional[float]:
	series = (rolling.get("rolling_windows", {}).get(window, {}) or {}).get("series", [])
	if not series:
		return None
	# Assume first entry is most recent
	val = series[0].get("xwoba")
	return float(val) if isinstance(val, (int, float)) else None


def _to_float(value: Any) -> Optional[float]:
	try:
		return float(value)
	except Exception:
		return None


def _safe_int(value: Any) -> int:
	try:
		# pitch_count values are often numeric strings
		return int(float(value))
	except Exception:
		return 0


def _hist_list(rolling: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
	return (rolling.get("histogram_data") or {}).get(key, []) or []


def _compute_hard_hit_rate(role: str, rolling: Dict[str, Any]) -> Optional[float]:
	"""Share of BBE with exit velocity ≥95 mph.

	For pitchers, this is contact quality allowed; lower is better, so we invert sign later.
	"""
	ev_bins = _hist_list(rolling, "exit_velocity")
	if not ev_bins:
		return None
	den = 0
	num = 0
	for b in ev_bins:
		count = _safe_int(b.get("pitch_count"))
		den += count
		# Prefer precise EV value, else fallback to histogram_value bin label
		v = _to_float(b.get("ev"))
		if v is None:
			v = _to_float(b.get("histogram_value"))
		if v is not None and v >= 95.0:
			num += count
	if den == 0:
		return None
	return num / den


def _compute_mean_ev(role: str, rolling: Dict[str, Any]) -> Optional[float]:
	"""Weighted mean exit velocity in mph."""
	ev_bins = _hist_list(rolling, "exit_velocity")
	if not ev_bins:
		return None
	den = 0
	weighted = 0.0
	for b in ev_bins:
		count = _safe_int(b.get("pitch_count"))
		if count <= 0:
			continue
		v = _to_float(b.get("ev"))
		if v is None:
			v = _to_float(b.get("histogram_value"))
		if v is None:
			continue
		weighted += v * count
		den += count
	if den == 0:
		return None
	return weighted / den


def _compute_line_drive_rate(role: str, rolling: Dict[str, Any]) -> Optional[float]:
	"""Share of BBE with launch angle in 0–15° (line drives proxy)."""
	la_bins = _hist_list(rolling, "launch_angle")
	if not la_bins:
		return None
	den = 0
	num = 0
	for b in la_bins:
		count = _safe_int(b.get("pitch_count"))
		den += count
		ang = _to_float(b.get("la"))
		if ang is None:
			ang = _to_float(b.get("histogram_value"))
		if ang is not None and 0.0 <= ang <= 15.0:
			num += count
	if den == 0:
		return None
	return num / den


def _compute_quality_signal(role: str, rolling: Dict[str, Any]) -> Optional[float]:
	"""Compute a composite contact-quality signal from histograms.

	Uses relative differences versus league baselines and blends:
	- hard-hit rate (≥95 mph)
	- mean exit velocity
	- line-drive rate (0–15°)
	"""
	# Collect metrics
	hh = _compute_hard_hit_rate(role, rolling)
	mev = _compute_mean_ev(role, rolling)
	ldr = _compute_line_drive_rate(role, rolling)

	acc = 0.0
	wsum = 0.0
	def add(metric_val: Optional[float], league_val: float, weight: float) -> None:
		nonlocal acc, wsum
		if metric_val is None:
			return
		# Relative difference to allow blending heterogeneous metrics
		d = (metric_val - league_val) / league_val if league_val else 0.0
		# For pitchers, lower contact quality allowed is better → invert sign
		if role == "pitcher":
			d = -d
		acc += weight * d
		wsum += weight

	add(hh, LEAGUE_HARD_HIT_RATE, QUALITY_WEIGHTS["hard_hit_rate"])
	add(mev, LEAGUE_MEAN_EV, QUALITY_WEIGHTS["mean_ev"])
	add(ldr, LEAGUE_LINE_DRIVE_RATE, QUALITY_WEIGHTS["line_drive_rate"])

	if wsum == 0.0:
		return None
	return acc / wsum


def _normalize_team_abbr(abbr: str) -> str:
	"""Map SaberSim/DFS team codes to roster team_abbr codes.

	Examples:
	- 'ARI' -> 'AZ'
	- 'OAK' -> 'ATH'
	- pass-through for most others
	"""
	mapping = {
		"ARI": "AZ",
		"OAK": "ATH",
		"SDP": "SD",
		"SFG": "SF",
		"KCR": "KC",
		"TBR": "TB",
		"WSN": "WSH",
	}
	return mapping.get(abbr.upper(), abbr.upper())


_SEARCH_CACHE: Dict[Tuple[str, str], str] = {}


def _search_mlb_id_by_name(name_query: str, team_abbr: str) -> Optional[str]:
	"""Fallback: query MLB Stats API people search to resolve an MLB ID by name.

	Uses the raw name query string for searching, but normalizes for comparison
	and cache key purposes. Helps with cases like 'D. Crews' vs 'Dylan Crews'.
	"""
	name_norm = _normalize_name(name_query)
	key = (name_norm, team_abbr)
	if key in _SEARCH_CACHE:
		return _SEARCH_CACHE[key]
	try:
		resp = requests.get(
			"https://statsapi.mlb.com/api/v1/people",
			params={"search": name_query},
			timeout=10,
		)
		resp.raise_for_status()
		payload = resp.json() or {}
		people = payload.get("people", [])
		match_id: Optional[str] = None
		for person in people:
			full = str(person.get("fullName") or "")
			if _normalize_name(full) != name_norm:
				continue
			team = (person.get("currentTeam") or {}).get("abbreviation")
			if team and _normalize_team_abbr(str(team)) == team_abbr:
				match_id = str(person.get("id"))
				break
		# If no team-filtered match, take first exact-name match
		if match_id is None:
			for person in people:
				full = str(person.get("fullName") or "")
				if _normalize_name(full) == name_norm:
					match_id = str(person.get("id"))
					break
		if match_id:
			_SEARCH_CACHE[key] = match_id
		return match_id
	except Exception:
		return None


def _compute_signal(role: str, rolling: Dict[str, Any], weights: Dict[str, float], league_h: float, league_p: float) -> Optional[float]:
	"""Composite signal blending xwOBA windows with histogram quality metrics."""
	# xwOBA-based component (event windows 50/100/250)
	x_acc = 0.0
	x_wsum = 0.0
	for w_key, w in weights.items():
		x = _latest_xwoba(rolling, w_key)
		if x is None:
			continue
		league = league_h if role == "batter" else league_p
		d = (x - league) / league if league else 0.0
		if role == "pitcher":
			d = -d
		x_acc += w * d
		x_wsum += w
	x_component: Optional[float] = None if x_wsum == 0.0 else x_acc / x_wsum

	# Histogram-derived contact quality component
	q_component = _compute_quality_signal(role, rolling)

	# Blend available components
	parts = []
	weights_blend = []
	if x_component is not None:
		parts.append(x_component)
		weights_blend.append(SIGNAL_BLEND["xwoba"])
	if q_component is not None:
		parts.append(q_component)
		weights_blend.append(SIGNAL_BLEND["quality"])
	if not parts:
		return None
	# Weighted average of parts
	blend_sum = 0.0
	blend_wsum = 0.0
	for val, w in zip(parts, weights_blend):
		blend_sum += val * w
		blend_wsum += w
	return blend_sum / blend_wsum if blend_wsum > 0 else None


def _apply_adjustment(base_proj: Optional[float], signal: float, k: float, cap: float) -> Optional[float]:
	if base_proj is None:
		return None
	# Capped multiplier
	factor = k * signal
	if factor > cap:
		factor = cap
	elif factor < -cap:
		factor = -cap
	return base_proj * (1.0 + factor)


def adjust_records(
	site: str,
	batters: List[Dict[str, Any]],
	pitchers: List[Dict[str, Any]],
	w50: Optional[float] = None,
	w100: Optional[float] = None,
	w250: Optional[float] = None,
	k: Optional[float] = None,
	cap: Optional[float] = None,
	league_xwoba_hitter: Optional[float] = None,
	league_xwoba_pitcher: Optional[float] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
	"""Return new lists with my_proj adjusted based on rolling windows.

	Adds fields per record:
	- rolling_signal: weighted deviation metric used
	- my_proj_adj: adjusted projection
	- my_proj: overwritten with adjusted value for CSV export convenience
	"""
	# Use provided overrides or defaults
	weights = {
		"50": WEIGHTS.get("50") if w50 is None else float(w50),
		"100": WEIGHTS.get("100") if w100 is None else float(w100),
		"250": WEIGHTS.get("250") if w250 is None else float(w250),
	}
	use_k = AGGRESSIVENESS_K if k is None else float(k)
	use_cap = MAX_ABS_TILT if cap is None else float(cap)
	league_h = LEAGUE_XWOBA_HITTER if league_xwoba_hitter is None else float(league_xwoba_hitter)
	league_p = LEAGUE_XWOBA_PITCHER_ALLOWED if league_xwoba_pitcher is None else float(league_xwoba_pitcher)

	rosters = _load_active_rosters()
	name_index = _build_name_index(rosters)

	def _adjust_list(records: List[Dict[str, Any]], role: str) -> List[Dict[str, Any]]:
		adjusted: List[Dict[str, Any]] = []
		for r in records:
			name = _normalize_name(str(r.get("name") or ""))
			team = _normalize_team_abbr(str(r.get("team") or "").upper())
			mlb_id = name_index.get((name, team))
			if not mlb_id:
				# fallback: try any team for this normalized name
				candidates = [pid for (n, _t), pid in name_index.items() if n == name]
				if candidates:
					mlb_id = candidates[0]
				else:
					# final fallback: query MLB Stats search
					mlb_id = _search_mlb_id_by_name(name, team)
					if not mlb_id:
						adjusted.append(r)
						continue
			rolling = _load_rolling_file(mlb_id, role)
			if not rolling:
				adjusted.append(r)
				continue
			signal = _compute_signal(role, rolling, weights, league_h, league_p)
			if signal is None:
				adjusted.append(r)
				continue
			base_proj = r.get("my_proj")
			adj = _apply_adjustment(base_proj, signal, use_k, use_cap)
			if adj is None:
				adjusted.append(r)
				continue
			new_r = dict(r)
			new_r["rolling_signal"] = signal
			new_r["my_proj_adj"] = adj
			new_r["my_proj"] = adj
			adjusted.append(new_r)
		return adjusted

	return _adjust_list(batters, "batter"), _adjust_list(pitchers, "pitcher")
