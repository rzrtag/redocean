import json
from typing import Any, Dict, List, Tuple


def _infer_role(player: Dict[str, Any]) -> str:
	"""Return 'pitcher' or 'batter' based on position fields."""
	pos = player.get("position") or player.get("pos_str")
	if isinstance(pos, list):
		is_pitcher = any(p in {"P", "SP", "RP"} for p in pos)
	else:
		is_pitcher = str(pos).upper() in {"P", "SP", "RP"}
	return "pitcher" if is_pitcher else "batter"


def _site_prefix_fields(site: str) -> Tuple[str, str]:
	"""Return primary projection/std key prefixes for a site."""
	site = site.lower()
	if site == "fanduel":
		return "fd", "fd"
	if site == "draftkings":
		return "dk", "dk"
	# Default to site-agnostic 'fd' like structure if unknown
	return "fd", "fd"


def _select_common_fields(player: Dict[str, Any]) -> Dict[str, Any]:
	"""Fields that are site-agnostic and useful for projection analysis."""
	keep = {
		"pid": player.get("pid"),
		"dfs_id": player.get("dfs_id"),
		"name": player.get("name"),
		"team": player.get("team"),
		"team_id": player.get("team_id"),
		"opp": player.get("opp"),
		"position": player.get("position"),
		"positions": player.get("pos") or player.get("pos_str"),
		"price": player.get("price"),
		"value": player.get("value"),
		"ownership": player.get("ownership"),
		"origOwnership": player.get("origOwnership"),
		"adjustedOwnership": player.get("adjustedOwnership"),
		"gid": player.get("gid"),
		"confirmed": player.get("confirmed"),
		"status": player.get("status"),
	}
	return {k: v for k, v in keep.items() if v is not None}


def _select_site_fields(player: Dict[str, Any], site: str) -> Dict[str, Any]:
	"""Only include fields for the given site (percentiles, points, std, projection)."""
	prefix, _ = _site_prefix_fields(site)
	fields = {}
	fields[f"{prefix}_points"] = player.get(f"{prefix}_points")
	fields[f"{prefix}_std"] = player.get(f"{prefix}_std")
	fields[f"{prefix}Projection"] = player.get(f"{prefix}Projection")
	# Default custom projection equals site's projection initially
	proj_val = player.get(f"{prefix}Projection")
	if proj_val is not None:
		fields["my_proj"] = proj_val
	# Include typical percentiles for the site
	for pct in ("25_percentile", "50_percentile", "75_percentile", "85_percentile", "95_percentile", "99_percentile"):
		key = f"{prefix}_{pct}"
		if key in player:
			fields[key] = player[key]
	return {k: v for k, v in fields.items() if v is not None}


def _select_batter_fields(player: Dict[str, Any]) -> Dict[str, Any]:
	"""Batter-specific means/rates that are directly useful for projections/histograms."""
	keep = {
		"bat_ord": player.get("bat_ord"),
		"pa": player.get("pa"),
		"hits": player.get("hits"),
		"singles": player.get("singles"),
		"doubles": player.get("doubles"),
		"triples": player.get("triples"),
		"home_runs": player.get("home_runs"),
		"r": player.get("r"),
		"rbi": player.get("rbi"),
		"sb": player.get("sb"),
		"so": player.get("so"),
		"walks": player.get("walks"),
		"saberTeam": player.get("saberTeam"),
		"saberTotal": player.get("saberTotal"),
	}
	return {k: v for k, v in keep.items() if v is not None}


def _select_pitcher_fields(player: Dict[str, Any]) -> Dict[str, Any]:
	"""Pitcher-specific means/rates that are directly useful for projections/histograms."""
	keep = {
		"ip": player.get("ip"),
		"pitches": player.get("pitches"),
		"so": player.get("so"),
		"er": player.get("er"),
		"wins": player.get("wins"),
		"saves": player.get("saves"),
		"qs": player.get("qs"),
		"cg": player.get("cg"),
		"cgso": player.get("cgso"),
		"walks": player.get("walks"),
		# Include batter-like allowed stats for pitchers
		"hits": player.get("hits"),
		"singles": player.get("singles"),
		"doubles": player.get("doubles"),
		"triples": player.get("triples"),
		"home_runs": player.get("home_runs"),
		"r": player.get("r"),
		"rbi": player.get("rbi"),
		"sb": player.get("sb"),
		"saberTeam": player.get("saberTeam"),
		"saberTotal": player.get("saberTotal"),
	}
	return {k: v for k, v in keep.items() if v is not None}


def project_adj_records(players: List[Dict[str, Any]], site: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
	"""Return (batters, pitchers) lists of simplified player records for given site.

	- Filters out obviously irrelevant UI/admin fields implicitly by not selecting them
	- Removes other-site percentile/projection fields
	- Keeps means/percentiles relevant for projection analysis
	"""
	batter_records: List[Dict[str, Any]] = []
	pitcher_records: List[Dict[str, Any]] = []
	for p in players:
		role = _infer_role(p)
		base = _select_common_fields(p)
		site_fields = _select_site_fields(p, site)
		if role == "pitcher":
			extra = _select_pitcher_fields(p)
			record = {**base, **site_fields, **extra}
			pitcher_records.append(record)
		else:
			extra = _select_batter_fields(p)
			record = {**base, **site_fields, **extra}
			batter_records.append(record)
	return batter_records, pitcher_records


def build_adj_from_build_optimization(build_json: Dict[str, Any], site: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
	"""Given loaded build_optimization json and site, return (batters, pitchers).

	Filters:
	- Batters: keep only starters where bat_ord_visible > 0
	- Pitchers: keep only starters as per games: home_starter/away_starter
	"""

	def _find_players_rec(obj: Any) -> List[Dict[str, Any]]:
		# Depth-first search for a 'players' key containing a list of dicts with projection-like fields
		if isinstance(obj, dict):
			if "players" in obj and isinstance(obj["players"], list) and obj["players"]:
				if isinstance(obj["players"][0], dict):
					return obj["players"]
			for v in obj.values():
				found = _find_players_rec(v)
				if found:
					return found
		elif isinstance(obj, list):
			for item in obj:
				found = _find_players_rec(item)
				if found:
					return found
		return []

	def _find_games_rec(obj: Any) -> List[Dict[str, Any]]:
		if isinstance(obj, dict):
			if "games" in obj and isinstance(obj["games"], list) and obj["games"]:
				first = obj["games"][0]
				if isinstance(first, dict) and {
					"gid",
					"home_team",
					"away_team",
					"home_starter",
					"away_starter",
				}.issubset(first.keys()):
					return obj["games"]
			for v in obj.values():
				found = _find_games_rec(v)
				if found:
					return found
		elif isinstance(obj, list):
			for item in obj:
				found = _find_games_rec(item)
				if found:
					return found
		return []

	players = _find_players_rec(build_json)
	if not players:
		raise ValueError("Could not locate 'players' array in build_optimization payload")

	games = _find_games_rec(build_json)
	game_by_gid: Dict[str, Dict[str, Any]] = {}
	for g in games:
		gid = g.get("gid")
		if gid:
			game_by_gid[str(gid)] = g

	def _is_home_for_player(p: Dict[str, Any]) -> Any:
		gid = str(p.get("gid")) if p.get("gid") is not None else None
		if not gid or gid not in game_by_gid:
			return None
		g = game_by_gid[gid]
		team = str(p.get("team") or "").strip().upper()
		home_team = str(g.get("home_team") or "").strip().upper()
		away_team = str(g.get("away_team") or "").strip().upper()
		if team == home_team:
			return True
		if team == away_team:
			return False
		return None

	def _is_starting_batter(p: Dict[str, Any]) -> bool:
		visible = p.get("bat_ord_visible")
		try:
			return (isinstance(visible, (int, float)) and visible > 0) or (
				isinstance(visible, str) and visible.isdigit() and int(visible) > 0
			)
		except Exception:
			return False

	def _is_starting_pitcher(p: Dict[str, Any]) -> bool:
		gid = str(p.get("gid")) if p.get("gid") is not None else None
		if not gid or gid not in game_by_gid:
			return False
		g = game_by_gid[gid]
		name = str(p.get("name") or "").strip()
		team = str(p.get("team") or "").strip().upper()
		home_team = str(g.get("home_team") or "").strip().upper()
		away_team = str(g.get("away_team") or "").strip().upper()
		home_starter = str(g.get("home_starter") or "").strip()
		away_starter = str(g.get("away_starter") or "").strip()
		if not name or not team:
			return False
		if team == home_team and name == home_starter:
			return True
		if team == away_team and name == away_starter:
			return True
		return False

	# Build filtered lists
	batter_records: List[Dict[str, Any]] = []
	pitcher_records: List[Dict[str, Any]] = []
	for p in players:
		role = _infer_role(p)
		if role == "pitcher":
			if not _is_starting_pitcher(p):
				continue
			base = _select_common_fields(p)
			is_home = _is_home_for_player(p)
			site_fields = _select_site_fields(p, site)
			extra = _select_pitcher_fields(p)
			record = {**base, **site_fields, **extra, "is_starter": True}
			if is_home is not None:
				record["is_home"] = is_home
				record["is_away"] = not is_home
			pitcher_records.append(record)
		else:
			if not _is_starting_batter(p):
				continue
			base = _select_common_fields(p)
			is_home = _is_home_for_player(p)
			site_fields = _select_site_fields(p, site)
			extra = _select_batter_fields(p)
			record = {**base, **site_fields, **extra, "is_starter": True}
			if is_home is not None:
				record["is_home"] = is_home
				record["is_away"] = not is_home
			batter_records.append(record)

	return batter_records, pitcher_records


def load_json(path: str) -> Dict[str, Any]:
	with open(path, "r") as f:
		return json.load(f)


def write_json(path: str, data: Any) -> None:
	path_dir_end = path.rfind("/")
	if path_dir_end > 0:
		# Ensure parent directory exists
		import os
		os.makedirs(path[:path_dir_end], exist_ok=True)
	with open(path, "w") as f:
		json.dump(data, f, indent=2)
