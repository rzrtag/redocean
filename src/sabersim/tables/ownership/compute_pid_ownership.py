#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


def _load_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _is_pitcher_from_meta(meta: Dict[str, Any]) -> bool:
    pos_val = meta.get('position')
    pos_strs: List[str] = []
    if isinstance(pos_val, dict):
        for k in ('abbreviation', 'name', 'type'):
            v = pos_val.get(k)
            if isinstance(v, str):
                pos_strs.append(v)
    elif isinstance(pos_val, str):
        pos_strs.append(pos_val)
    if 'pos' in meta and isinstance(meta['pos'], str):
        pos_strs.append(meta['pos'])
    if isinstance(meta.get('pos'), list):
        pos_strs.extend([str(x) for x in meta['pos']])
    if isinstance(meta.get('pos'), tuple):
        pos_strs.extend([str(x) for x in list(meta['pos'])])
    # Some payloads use ['P'] list under 'pos'
    if isinstance(meta.get('pos'), list):
        for v in meta['pos']:
            if isinstance(v, str):
                pos_strs.append(v)
    for s in pos_strs:
        u = s.upper()
        if any(x in u for x in ('P', 'SP', 'RP', 'PITCH')):
            return True
    return False


def _extract_name_team(meta: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    name = None
    for key in ('name', 'displayName', 'fullName', 'playerName'):
        v = meta.get(key)
        if isinstance(v, str) and v.strip():
            name = v.strip()
            break
    team = None
    for key in ('team_abbr', 'teamAbbr', 'team_abbreviation', 'teamAbbreviation', 'mlbTeamAbbrev', 'team_code', 'teamCode', 'team'):
        v = meta.get(key)
        if isinstance(v, str) and v.strip():
            team = v.strip().upper()
            break
    if not team and isinstance(meta.get('team'), dict):
        for k in ('abbr', 'abbreviation', 'code', 'triCode', 'shortName', 'name'):
            v = meta['team'].get(k)
            if isinstance(v, str) and v.strip():
                team = v.strip().upper()
                break
    return name, team


def _pid_meta_map(site: str, date_mmdd: str, slate: str) -> Dict[str, Dict[str, Any]]:
    """Build a PID -> meta index (name, team, position, bat_ord, etc).

    Scans multiple atom files across sites/slates for robustness.
    """
    def scan_file(path: Path) -> Dict[str, Dict[str, Any]]:
        mapping: Dict[str, Dict[str, Any]] = {}
        if not path.exists():
            return mapping
        try:
            atom = _load_json(path)
            data = atom  # scan entire root to pick up players under non-standard roots
            stack: List[Any] = [data]
            while stack:
                x = stack.pop()
                if isinstance(x, dict):
                    pid = x.get('pid') or x.get('playerId') or x.get('id')
                    if pid:
                        if isinstance(pid, (str, int)):
                            pid_str = str(pid)
                            new_meta = dict(x)
                            old_meta = mapping.get(pid_str, {})
                            # Prefer richer records (with name/team/position), but merge fields
                            def richness(m: Dict[str, Any]) -> int:
                                score = 0
                                if any(isinstance(m.get(k), str) and m.get(k) for k in ('name','displayName','fullName','playerName')):
                                    score += 2
                                if any(isinstance(m.get(k), str) and m.get(k) for k in ('team','teamAbbr','team_abbr','teamAbbreviation','mlbTeamAbbrev')):
                                    score += 1
                                posv = m.get('position') or m.get('pos') or m.get('pos_str')
                                if isinstance(posv, (str, dict, list)):
                                    score += 1
                                return score
                            if old_meta:
                                if richness(new_meta) >= richness(old_meta):
                                    merged = dict(old_meta)
                                    merged.update(new_meta)
                                    mapping[pid_str] = merged
                                else:
                                    merged = dict(new_meta)
                                    merged.update(old_meta)
                                    mapping[pid_str] = merged
                            else:
                                mapping[pid_str] = new_meta
                    for v in x.values():
                        if isinstance(v, (dict, list)):
                            stack.append(v)
                elif isinstance(x, list):
                    for v in x:
                        if isinstance(v, (dict, list)):
                            stack.append(v)
        except Exception:
            return {}
        return mapping

    def atoms_dir_for(s: str, sl: str) -> Path:
        # Updated to sabersim_2025 directory layout
        return Path('_data') / 'sabersim_2025' / s / f"{date_mmdd}_{sl}" / 'atoms_output' / 'atoms'

    other_site = 'draftkings' if site == 'fanduel' else 'fanduel'
    all_slates = [slate, 'main_slate', 'night_slate']

    candidates: List[Path] = []
    seen_dirs = set()
    for sl in all_slates:
        d = atoms_dir_for(site, sl)
        if d.exists() and str(d) not in seen_dirs:
            seen_dirs.add(str(d))
            candidates.extend([
                d / 'portfolio_optimization_latest.json',
                d / 'build_optimization.json',
                d / 'lineup_data.json',
            ])
    for sl in all_slates:
        d = atoms_dir_for(other_site, sl)
        if d.exists() and str(d) not in seen_dirs:
            seen_dirs.add(str(d))
            candidates.extend([
                d / 'portfolio_optimization_latest.json',
                d / 'build_optimization.json',
                d / 'lineup_data.json',
            ])

    combined: Dict[str, Dict[str, Any]] = {}
    for p in candidates:
        m = scan_file(p)
        if m:
            combined.update(m)
    return combined


def compute_pid_ownership(atom_file: Path, role: str, pid_meta: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    atom = _load_json(atom_file)
    data = atom.get('response_data') or atom.get('data') or {}
    lineups = []
    if isinstance(data, dict):
        lineups = data.get('lineups') or data.get('field_lineups') or data.get('contest_lineups') or []
    elif isinstance(data, list):
        lineups = data
    total = len(lineups)
    counts: Dict[str, int] = {}
    extras: Dict[str, Dict[str, Any]] = {}
    for lu in lineups:
        pids = lu.get('pids') if isinstance(lu, dict) else None
        if not isinstance(pids, list):
            continue
        for pid in pids:
            meta = pid_meta.get(str(pid)) or {}
            if not meta:
                continue
            is_pitcher = _is_pitcher_from_meta(meta)
            if role == 'pitcher' and not is_pitcher:
                continue
            if role == 'batter' and is_pitcher:
                continue
            name, team = _extract_name_team(meta)
            if not name:
                continue
            counts[name] = counts.get(name, 0) + 1
            if name not in extras:
                extras[name] = {
                    'team': team,
                    'pos': meta.get('position') or meta.get('pos') or meta.get('pos_str'),
                }
    # Build reverse map name->pid best-effort (names not unique but acceptable for leverage aggregation)
    name_to_pid: Dict[str, str] = {}
    for pid, meta in pid_meta.items():
        n, _ = _extract_name_team(meta)
        if n and n not in name_to_pid:
            name_to_pid[n] = pid
    players_out = []
    for name, cnt in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        rec = {
            'pid': name_to_pid.get(name),
            'name': name,
            'count': cnt,
            'own_pct': round(100.0 * cnt / total, 3) if total else 0.0,
        }
        rec.update({k: v for k, v in extras.get(name, {}).items() if v is not None})
        players_out.append(rec)
    return {
        'total_lineups': total,
        'unique_players': len(counts),
        'players': players_out,
    }


def write_bucket_pid_ownership(site: str, date_mmdd: str, slate: str, bucket: str) -> Tuple[Optional[Path], Optional[Path]]:
    atoms_dir = Path('_data') / 'sabersim_2025' / site / f"{date_mmdd}_{slate}" / 'atoms_output' / 'by_contest' / bucket / 'atoms'
    atom_file = atoms_dir / f'field_lineups_{bucket}.json'
    if not atom_file.exists():
        return None, None
    pid_meta = _pid_meta_map(site, date_mmdd, slate)
    batters = compute_pid_ownership(atom_file, 'batter', pid_meta)
    pitchers = compute_pid_ownership(atom_file, 'pitcher', pid_meta)
    bat_dir = Path('_data') / 'sabersim_2025' / site / f"{date_mmdd}_{slate}" / 'tables' / 'batters'
    pit_dir = Path('_data') / 'sabersim_2025' / site / f"{date_mmdd}_{slate}" / 'tables' / 'pitchers'
    bat_dir.mkdir(parents=True, exist_ok=True)
    pit_dir.mkdir(parents=True, exist_ok=True)
    bat_out = bat_dir / f'own_{bucket}.json'
    pit_out = pit_dir / f'own_{bucket}.json'
    with open(bat_out, 'w', encoding='utf-8') as f:
        json.dump({'bucket': bucket, **batters}, f, indent=2)
    with open(pit_out, 'w', encoding='utf-8') as f:
        json.dump({'bucket': bucket, **pitchers}, f, indent=2)
    return bat_out, pit_out
