#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Optional


def _load_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _extract_lineups(response_data: Any) -> List[dict]:
    if isinstance(response_data, list):
        return response_data
    if not isinstance(response_data, dict):
        return []
    for key in ('lineups', 'field_lineups', 'contest_lineups', 'entries'):
        val = response_data.get(key)
        if isinstance(val, list):
            return val
    for v in response_data.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v
    return []


def _extract_players(lineup: dict) -> List[dict]:
    if 'players' in lineup and isinstance(lineup['players'], list):
        return lineup['players']
    if 'roster' in lineup:
        roster = lineup['roster']
        if isinstance(roster, list):
            return roster
        if isinstance(roster, dict):
            return [v for v in roster.values() if isinstance(v, dict)]
    if 'slots' in lineup and isinstance(lineup['slots'], list):
        return [s.get('player') or s for s in lineup['slots']]
    return []


def _is_pitcher(p: dict) -> bool:
    # Try common fields
    pos_val = p.get('position')
    pos = ''
    if isinstance(pos_val, dict):
        pos = (pos_val.get('abbreviation') or pos_val.get('name') or pos_val.get('type') or '').upper()
    elif isinstance(pos_val, str):
        pos = pos_val.upper()
    else:
        pos = (p.get('pos') or p.get('positionAbbreviation') or '').upper()
    if any(x in pos for x in ('P', 'SP', 'RP', 'PITCH')):
        return True
    if 'player' in p and isinstance(p['player'], dict):
        return _is_pitcher(p['player'])
    return False


def _player_team(p: dict) -> Optional[str]:
    # Common simple string fields
    for key in (
        'team_abbr', 'teamAbbr', 'team_abbreviation', 'teamAbbreviation',
        'mlbTeamAbbrev', 'team_code', 'teamCode', 'team'
    ):
        v = p.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip().upper()
    # Nested team object
    tv = p.get('team')
    if isinstance(tv, dict):
        for k in ('abbr', 'abbreviation', 'code', 'triCode', 'shortName', 'name'):
            v = tv.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip().upper()
    # Nested player field
    if 'player' in p and isinstance(p['player'], dict):
        t = _player_team(p['player'])
        if t:
            return t
    # Metadata fallback
    if 'metadata' in p and isinstance(p['metadata'], dict):
        for k in ('team', 'teamAbbreviation', 'team_abbr'):
            v = p['metadata'].get(k)
            if isinstance(v, str) and v.strip():
                return v.strip().upper()
    return None


def _pid_team_map(site: str, date_mmdd: str, slate: str) -> Dict[str, str]:
    """Build a PID->TEAM map.

    Order of preference:
    1) portfolio_optimization_latest.json (contains explicit pid and team)
    2) lineup_data.json (derive team from nested fields)
    3) Fallback to the other site's portfolio for same date/slate
    """
    def scan_file(path: Path) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        if not path.exists():
            return mapping
        try:
            atom = _load_json(path)
            # Scan the entire root object to catch cases where useful fields
            # are outside of response_data (e.g., portfolio configs/players)
            data = atom
            # Iterative traversal to avoid recursion depth limits
            stack: List[Any] = [data]
            while stack:
                x = stack.pop()
                if isinstance(x, dict):
                    pid = x.get('pid') or x.get('playerId') or x.get('id')
                    team = _player_team(x)
                    if pid and team and isinstance(pid, (str, int)):
                        mapping[str(pid)] = team
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

    # Build a list of candidate files to scan, ordered by preference
    def atoms_dir_for(s: str, sl: str) -> Path:
        # Updated to sabersim_2025 directory layout: <base>/<site>/<mmdd>_<slate>/atoms_output/atoms
        return Path('_data') / 'sabersim_2025' / s / f"{date_mmdd}_{sl}" / 'atoms_output' / 'atoms'

    other_site = 'draftkings' if site == 'fanduel' else 'fanduel'
    all_slates = [slate, 'main_slate', 'night_slate']

    candidates: List[Path] = []
    seen_dirs = set()
    # Prefer same site, requested slate, then other slates
    for sl in all_slates:
        d = atoms_dir_for(site, sl)
        if d.exists() and str(d) not in seen_dirs:
            seen_dirs.add(str(d))
            candidates.extend([
                d / 'portfolio_optimization_latest.json',
                d / 'build_optimization.json',
                d / 'lineup_data.json',
            ])
    # Then other site, same slate first, then other slates
    for sl in all_slates:
        d = atoms_dir_for(other_site, sl)
        if d.exists() and str(d) not in seen_dirs:
            seen_dirs.add(str(d))
            candidates.extend([
                d / 'portfolio_optimization_latest.json',
                d / 'build_optimization.json',
                d / 'lineup_data.json',
            ])

    # Scan in order until we find any mappings
    for p in candidates:
        mapping = scan_file(p)
        if mapping:
            return mapping

    return {}


def _pid_team_index_from_tables(site: str, date_mmdd: str, slate: str) -> Dict[str, str]:
    idx_path = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'tables' / 'metadata' / 'pid_team_index.json'
    if not idx_path.exists():
        return {}
    try:
        with open(idx_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {str(k): v for k, v in data.items() if isinstance(v, str)}
    except Exception:
        return {}
    return {}

def _lineup_team_stack_counts(lineup: dict, max_stack: int, pid_team: Dict[str, str]) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    # If lineup includes an explicit team stack summary, use it directly
    stack = lineup.get('stack')
    if isinstance(stack, dict) and stack:
        for team, sz in stack.items():
            if isinstance(team, str) and isinstance(sz, int):
                t = team.strip().upper()
                size = min(max(sz, 0), max_stack)
                if size > 0:
                    counts[t] += size
        for t in list(counts.keys()):
            if counts[t] > max_stack:
                counts[t] = max_stack
        return dict(counts)
    # Fast path: pid-only lineups
    pids = lineup.get('pids')
    if isinstance(pids, list) and pids:
        for pid in pids:
            team = pid_team.get(str(pid))
            if team:
                counts[team] += 1
        for t in list(counts.keys()):
            if counts[t] > max_stack:
                counts[t] = max_stack
        return dict(counts)
    for pl in _extract_players(lineup):
        if _is_pitcher(pl):
            continue
        team = _player_team(pl)
        if not team:
            pid = pl.get('pid') or pl.get('playerId') or pl.get('id')
            if isinstance(pid, (str, int)):
                team = pid_team.get(str(pid))
        if team:
            counts[team] += 1
    for t in list(counts.keys()):
        if counts[t] > max_stack:
            counts[t] = max_stack
    return dict(counts)


def compute_stack_ownership_from_atom(atom_file: Path, site: str, date_mmdd: str, slate: str) -> Dict[str, Any]:
    atom = _load_json(atom_file)
    data = atom.get('response_data') or atom.get('data') or {}
    lineups = _extract_lineups(data)
    total = len(lineups)
    # Prefer prebuilt index if available, else fallback to lineup_data scan
    pid_team = _pid_team_index_from_tables(site, date_mmdd, slate)
    if not pid_team:
        pid_team = _pid_team_map(site, date_mmdd, slate)
    if site == 'draftkings':
        max_stack = 5
        primary_sizes = {5, 4}
        secondary_sizes = {3, 2}
        tertiary_sizes: set[int] = set()
        all_sizes = {5, 4, 3, 2}
    else:
        max_stack = 4
        primary_sizes = {4}
        secondary_sizes = {3}
        tertiary_sizes = {2}
        all_sizes = {4, 3, 2}

    per_team_counts: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))

    for lu in lineups:
        counts = _lineup_team_stack_counts(lu, max_stack, pid_team)
        for team, size in counts.items():
            if size in all_sizes:
                per_team_counts[team][size] += 1

    by_team: Dict[str, Any] = {}
    for team, size_map in per_team_counts.items():
        size_counts = {str(k): int(v) for k, v in size_map.items()}
        primary_count = sum(v for k, v in size_map.items() if k in primary_sizes)
        secondary_count = sum(v for k, v in size_map.items() if k in secondary_sizes)
        all_count = sum(v for k, v in size_map.items() if k in all_sizes)
        size_pct = {str(k): round(100.0 * v / total, 3) if total else 0.0 for k, v in size_map.items()}
        team_row = {
            'size_counts': size_counts,
            'primary_count': primary_count,
            'secondary_count': secondary_count,
            'all_count': all_count,
            'size_pct': size_pct,
            'primary_pct': round(100.0 * primary_count / total, 3) if total else 0.0,
            'secondary_pct': round(100.0 * secondary_count / total, 3) if total else 0.0,
            'all_pct': round(100.0 * all_count / total, 3) if total else 0.0,
        }
        if tertiary_sizes:
            tertiary_count = sum(v for k, v in size_map.items() if k in tertiary_sizes)
            team_row['tertiary_count'] = tertiary_count
            team_row['tertiary_pct'] = round(100.0 * tertiary_count / total, 3) if total else 0.0
        by_team[team] = team_row

    totals = defaultdict(int)
    for size_map in per_team_counts.values():
        for k, v in size_map.items():
            if k in all_sizes:
                totals[f'size_{k}'] += v
        totals['primary'] += sum(v for k, v in size_map.items() if k in primary_sizes)
        totals['secondary'] += sum(v for k, v in size_map.items() if k in secondary_sizes)
        if tertiary_sizes:
            totals['tertiary'] += sum(v for k, v in size_map.items() if k in tertiary_sizes)
        totals['all'] += sum(v for k, v in size_map.items() if k in all_sizes)

    totals_pct = {k + '_pct': (round(100.0 * v / total, 3) if total else 0.0) for k, v in totals.items()}

    return {
        'total_lineups': total,
        'by_team': by_team,
        'totals': dict(totals),
        'totals_pct': totals_pct,
        'config': {
            'site': site,
            'max_stack': max_stack,
            'primary_sizes': sorted(list(primary_sizes)),
            'secondary_sizes': sorted(list(secondary_sizes)),
            'tertiary_sizes': sorted(list(tertiary_sizes)),
            'all_sizes': sorted(list(all_sizes)),
        }
    }


def write_stack_ownership(site: str, date_mmdd: str, slate: str, bucket: str) -> Optional[Path]:
    atoms_dir = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'atoms_output' / 'by_contest' / bucket / 'atoms'
    atom_file = atoms_dir / f'field_lineups_{bucket}.json'
    if not atom_file.exists():
        return None
    own = compute_stack_ownership_from_atom(atom_file, site, date_mmdd, slate)
    out_dir = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'tables' / 'stacks'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f'own_{bucket}.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(own, f, indent=2)
    return out_file
