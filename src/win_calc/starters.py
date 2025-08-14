from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple, Any
import json

BASE_DATA = Path("/mnt/storage_fast/workspaces/red_ocean/_data")
SS_BASE = BASE_DATA / "sabersim_2025"


def _load_json(path: Path) -> Any:
    with open(path, "r") as f:
        return json.load(f)


def slate_paths(site: str, date_mmdd: str, slate: str) -> Dict[str, Path]:
    root = SS_BASE / site / f"{date_mmdd}_{slate}" / "atoms_output" / "tables"
    return {
        "players": root / "players.json",
        "starters": root / "starters.json",
        "games": root / "games.json",
    }


def load_pitcher_starters(site: str, date_mmdd: str, slate: str) -> List[str]:
    p = slate_paths(site, date_mmdd, slate)["starters"]
    if p.exists():
        names = _load_json(p)
        if isinstance(names, list):
            return [str(x) for x in names]
    # Fallback: infer from games.json
    g = slate_paths(site, date_mmdd, slate)["games"]
    starters: List[str] = []
    if g.exists():
        data = _load_json(g)
        for game in data.get("games", []):
            for key in ("home_starter", "away_starter"):
                name = game.get(key)
                if name:
                    starters.append(str(name))
    # Deduplicate while preserving order
    seen = set()
    out: List[str] = []
    for n in starters:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def load_batter_starters(site: str, date_mmdd: str, slate: str) -> List[Dict[str, Any]]:
    """Return batter starter rows (players with bat_order_visible > 0)."""
    p = slate_paths(site, date_mmdd, slate)["players"]
    if not p.exists():
        return []
    data = _load_json(p)
    players = data.get("players") or []
    starters: List[Dict[str, Any]] = []
    for pl in players:
        try:
            order = pl.get("bat_order_visible")
            if isinstance(order, int) and order > 0:
                starters.append(pl)
        except Exception:
            continue
    return starters


def load_all_starters(site: str, date_mmdd: str, slate: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    return load_pitcher_starters(site, date_mmdd, slate), load_batter_starters(site, date_mmdd, slate)
