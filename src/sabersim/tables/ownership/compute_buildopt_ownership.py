#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _load_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _extract_name(meta: Dict[str, Any]) -> Optional[str]:
    for k in ('name', 'displayName', 'fullName', 'playerName'):
        v = meta.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _extract_team(meta: Dict[str, Any]) -> Optional[str]:
    for key in ('team_abbr', 'teamAbbr', 'team_abbreviation', 'teamAbbreviation', 'mlbTeamAbbrev', 'team_code', 'teamCode', 'team'):
        v = meta.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip().upper()
    tv = meta.get('team')
    if isinstance(tv, dict):
        for k in ('abbr', 'abbreviation', 'code', 'triCode', 'shortName', 'name'):
            v = tv.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip().upper()
    return None


def _extract_pos(meta: Dict[str, Any]) -> Optional[str]:
    pos = meta.get('position')
    if isinstance(pos, dict):
        for k in ('abbreviation', 'name', 'type'):
            v = pos.get(k)
            if isinstance(v, str) and v:
                return v
    if isinstance(pos, str) and pos:
        return pos
    if isinstance(meta.get('pos_str'), str):
        return meta['pos_str']
    if isinstance(meta.get('pos'), str):
        return meta['pos']
    return None


def _extract_projection(meta: Dict[str, Any]) -> Optional[float]:
    # Try common projection keys, in order
    for key in ('projection', 'proj', 'fpts', 'points', 'dkProjection', 'fdProjection', 'value'):
        if key in meta:
            try:
                return float(meta[key])
            except (TypeError, ValueError):
                continue
    return None


def _collect_buildopt_players(atom_path: Path) -> Dict[str, Dict[str, Any]]:
    """Return pid -> meta with ownership fields from build/portfolio atoms."""
    result: Dict[str, Dict[str, Any]] = {}
    if not atom_path.exists():
        return result
    atom = _load_json(atom_path)
    data = atom  # scan whole object
    stack: List[Any] = [data]
    while stack:
        x = stack.pop()
        if isinstance(x, dict):
            pid = x.get('pid') or x.get('playerId') or x.get('id')
            if pid:
                own = x.get('ownership')
                adj = x.get('adjustedOwnership')
                orig = x.get('origOwnership')
                if own is not None or adj is not None or orig is not None:
                    meta = result.setdefault(str(pid), {})
                    meta.update(x)
            for v in x.values():
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(x, list):
            for v in x:
                if isinstance(v, (dict, list)):
                    stack.append(v)
    return result


def build_player_ownership(site: str, date_mmdd: str, slate: str) -> Tuple[Optional[Path], Optional[Path], Optional[Path]]:
    """Build per-player ownership from build/portfolio optimization.

    Searches same site across slates (requested -> main_slate -> night_slate) to ensure
    we populate even if one slate folder lacks the file.
    """
    def atoms_dir_for(sl: str) -> Path:
        return Path('_data') / 'star_cannon' / site / date_mmdd / sl / 'atoms_output' / 'atoms'

    players: Dict[str, Dict[str, Any]] = {}
    for sl in [slate, 'main_slate', 'night_slate']:
        d = atoms_dir_for(sl)
        if not d.exists():
            continue
        build_path = d / 'build_optimization.json'
        portfolio_path = d / 'portfolio_optimization_latest.json'
        players = _collect_buildopt_players(build_path)
        if not players:
            players = _collect_buildopt_players(portfolio_path)
        if players:
            break

    out_dir = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'tables' / 'players'
    out_dir.mkdir(parents=True, exist_ok=True)

    def site_prefix(s: str) -> str:
        return 'dk_' + s if site == 'draftkings' else 'fd_' + s

    def write_metric(metric_key: str, filename_stub: str) -> Optional[Path]:
        out_file = out_dir / f"{site_prefix(filename_stub)}.json"
        records: List[Dict[str, Any]] = []
        for pid, meta in players.items():
            val = meta.get(metric_key)
            if val is None:
                continue
            name = _extract_name(meta) or pid
            team = _extract_team(meta)
            pos = _extract_pos(meta)
            proj_val = _extract_projection(meta)
            try:
                val_num = float(val)
            except (TypeError, ValueError):
                continue
            rec = {
                'pid': pid,
                'name': name,
                'team': team,
                'pos': pos,
                metric_key: val_num,
            }
            if proj_val is not None:
                rec['projection'] = proj_val
            records.append(rec)
        records.sort(key=lambda r: (-r.get(metric_key, 0.0), r.get('name') or ''))
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump({'total_players': len(records), 'players': records}, f, indent=2)
        return out_file

    own_out = write_metric('ownership', 'build_optm_own')
    adj_out = write_metric('adjustedOwnership', 'build_optm_adj_own')
    orig_out = write_metric('origOwnership', 'build_opt_orig_own')
    # Also write role-split files into batters/ and pitchers/
    def is_pitcher(meta: Dict[str, Any]) -> bool:
        pos = meta.get('position')
        pos_strs: List[str] = []
        if isinstance(pos, dict):
            for k in ('abbreviation', 'name', 'type'):
                v = pos.get(k)
                if isinstance(v, str):
                    pos_strs.append(v)
        elif isinstance(pos, str):
            pos_strs.append(pos)
        for k in ('pos', 'pos_str'):
            v = meta.get(k)
            if isinstance(v, str):
                pos_strs.append(v)
        for s in pos_strs:
            u = s.upper()
            if any(x in u for x in ('P', 'SP', 'RP', 'PITCH')):
                return True
        return False

    def write_role(metric_key: str, subdir: str, filename_stub: str) -> Optional[Path]:
        out_dir_role = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'tables' / subdir
        out_dir_role.mkdir(parents=True, exist_ok=True)
        out_file = out_dir_role / f"{site_prefix(filename_stub)}.json"
        records: List[Dict[str, Any]] = []
        for pid, meta in players.items():
            val = meta.get(metric_key)
            if val is None:
                continue
            name = _extract_name(meta) or pid
            team = _extract_team(meta)
            pos = _extract_pos(meta)
            proj_val = _extract_projection(meta)
            role_dir = 'pitchers' if is_pitcher(meta) else 'batters'
            if role_dir != subdir:
                continue
            try:
                val_num = float(val)
            except (TypeError, ValueError):
                continue
            rec = {
                'pid': pid,
                'name': name,
                'team': team,
                'pos': pos,
                metric_key: val_num,
            }
            if proj_val is not None:
                rec['projection'] = proj_val
            records.append(rec)
        records.sort(key=lambda r: (-r.get(metric_key, 0.0), r.get('name') or ''))
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump({'total_players': len(records), 'players': records}, f, indent=2)
        return out_file

    for key, stub in (
        ('ownership', 'build_optm_own'),
        ('adjustedOwnership', 'build_optm_adj_own'),
        ('origOwnership', 'build_opt_orig_own'),
    ):
        write_role(key, 'batters', stub)
        write_role(key, 'pitchers', stub)

    return own_out, adj_out, orig_out
