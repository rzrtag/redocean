import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple


# Defaults (tunable)
WEIGHTS = {"50": 0.5, "100": 0.3, "250": 0.2}
AGGRESSIVENESS_K = 0.15
MAX_ABS_TILT = 0.20
LEAGUE_XWOBA_HITTER = 0.320
LEAGUE_XWOBA_PITCHER_ALLOWED = 0.320

ROLLING_ROOT = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/rolling_windows/data"
ROSTERS_PATH = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/active_rosters/data/active_rosters.json"


def _normalize_name(name: str) -> str:
	name = name.lower().strip()
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
			full = p.get("fullName") or ""
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


def _compute_signal(role: str, rolling: Dict[str, Any], weights: Dict[str, float], league_h: float, league_p: float) -> Optional[float]:
	# Build weighted deviation from league average
	acc = 0.0
	weight_sum = 0.0
	for w_key, w in weights.items():
		x = _latest_xwoba(rolling, w_key)
		if x is None:
			continue
		league = league_h if role == "batter" else league_p
		# Relative difference
		d = (x - league) / league if league else 0.0
		# For pitchers, lower xwOBA allowed is better → invert sign
		if role == "pitcher":
			d = -d
		acc += w * d
		weight_sum += w
	if weight_sum == 0.0:
		return None
	return acc / weight_sum


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
			team = str(r.get("team") or "").upper()
			mlb_id = name_index.get((name, team))
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
