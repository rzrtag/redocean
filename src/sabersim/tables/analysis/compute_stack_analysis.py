#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Optional, Tuple

from star_cannon.core.tables.stacks.compute_stack_ownership import _pid_team_map
from star_cannon.core.tables.stacks.compute_stack_ownership import _load_json as _load_json_base


def _load_json(path: Path) -> dict:
    return _load_json_base(path)


def _field_lineups_atom(site: str, date_mmdd: str, slate: str, bucket: str) -> Optional[Path]:
    p = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'atoms_output' / 'by_contest' / bucket / 'atoms' / f'field_lineups_{bucket}.json'
    return p if p.exists() else None


def _site_stack_config(site: str) -> Tuple[int, List[int]]:
    if site == 'draftkings':
        return 5, [5, 4, 3, 2]
    return 4, [4, 3, 2]


def _is_pitcher_pos(meta: Dict[str, Any]) -> bool:
    pos_val = meta.get('position')
    pos_strs: List[str] = []
    if isinstance(pos_val, dict):
        for k in ('abbreviation', 'name', 'type'):
            v = pos_val.get(k)
            if isinstance(v, str):
                pos_strs.append(v)
    elif isinstance(pos_val, str):
        pos_strs.append(pos_val)
    v = meta.get('pos')
    if isinstance(v, str):
        pos_strs.append(v)
    if isinstance(v, list):
        pos_strs.extend([str(x) for x in v])
    for s in pos_strs:
        u = s.upper()
        if any(x in u for x in ('P', 'SP', 'RP', 'PITCH')):
            return True
    return False


def _collect_lineups(atom_path: Path) -> List[Dict[str, Any]]:
    j = _load_json(atom_path)
    data = j.get('response_data') or j.get('data') or {}
    lineups = data.get('lineups') or []
    out: List[Dict[str, Any]] = []
    for lu in lineups:
        if not isinstance(lu, dict):
            continue
        pids = lu.get('pids')
        proj = lu.get('proj') or lu.get('projection') or 0.0
        if isinstance(pids, list):
            try:
                score = float(proj)
            except (TypeError, ValueError):
                score = 0.0
            out.append({'pids': [str(x) for x in pids], 'proj': score})
    return out


def _lineup_team_stack_counts(pids: List[str], pid_team: Dict[str, str], max_stack: int) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    for pid in pids:
        team = pid_team.get(str(pid))
        if team:
            counts[team] += 1
    # clamp sizes
    for t in list(counts.keys()):
        if counts[t] > max_stack:
            counts[t] = max_stack
    return dict(counts)


def _lineup_pitchers(site: str, pids: List[str], pid_meta: Dict[str, Dict[str, Any]]) -> List[str]:
    names: List[str] = []
    for pid in pids:
        meta = pid_meta.get(pid) or {}
        if _is_pitcher_pos(meta):
            name = None
            for k in ('name', 'displayName', 'fullName', 'playerName'):
                v = meta.get(k)
                if isinstance(v, str) and v.strip():
                    name = v.strip()
                    break
            if name:
                names.append(name)
    # For DK keep up to 2; for FD up to 1
    if site == 'draftkings':
        names = sorted(names)[:2]
    else:
        names = sorted(names)[:1]
    return names


def _read_stack_ownership(site: str, date_mmdd: str, slate: str, bucket: str) -> Dict[str, Any]:
    p = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'tables' / 'stacks' / f'own_{bucket}.json'
    return _load_json(p) if p.exists() else {}


def compute_stack_top_inclusion_and_leverage(site: str, date_mmdd: str, slate: str, bucket: str,
                                             percents: List[int] = [1, 5, 10], with_pitcher: bool = False) -> Dict[str, Any]:
    atom = _field_lineups_atom(site, date_mmdd, slate, bucket)
    if not atom:
        return {}
    max_stack, allowed_sizes = _site_stack_config(site)
    pid_team = _pid_team_map(site, date_mmdd, slate)
    pid_meta = {}  # lazy build only if with_pitcher
    if with_pitcher:
        # reuse pid meta building from ownership module by scanning atoms dirs broadly
        from star_cannon.core.tables.ownership.compute_pid_ownership import _pid_meta_map
        pid_meta = _pid_meta_map(site, date_mmdd, slate)
    lineups = _collect_lineups(atom)
    total = len(lineups)
    if total == 0:
        return {'total_lineups': 0}
    # sort by projection descending
    lineups.sort(key=lambda x: x['proj'], reverse=True)
    # Build keys per lineup
    lineup_keys: List[Tuple[List[str], float]] = []
    for lu in lineups:
        pids = lu['pids']
        team_counts = _lineup_team_stack_counts(pids, pid_team, max_stack)
        keys: List[str] = []
        if with_pitcher:
            pitchers = _lineup_pitchers(site, pids, pid_meta)
        else:
            pitchers = []
        for team, size in team_counts.items():
            if size in allowed_sizes:
                if pitchers:
                    key = f"{team}|{size}|{'&'.join(pitchers)}"
                else:
                    key = f"{team}|{size}"
                keys.append(key)
        lineup_keys.append((keys, lu['proj']))
    # Cuts
    cuts: Dict[int, int] = {}
    for p in percents:
        n = max(1, int(round(total * (p / 100.0))))
        cuts[p] = n
    # Count inclusion
    appears_in: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for pct, n in cuts.items():
        for keys, _ in lineup_keys[:n]:
            for k in keys:
                appears_in[k][pct] += 1
    # Ownership map for leverage (team-size only)
    own = _read_stack_ownership(site, date_mmdd, slate, bucket)
    team_size_own_pct: Dict[str, float] = {}
    by_team = own.get('by_team') or {}
    for team, rec in by_team.items():
        size_pct = rec.get('size_pct') or {}
        for sz_str, pct in size_pct.items():
            try:
                sz = int(sz_str)
            except Exception:
                continue
            if sz in allowed_sizes:
                team_size_own_pct[f"{team}|{sz}"] = float(pct)
    # Build rows
    rows: List[Dict[str, Any]] = []
    for key, counts in appears_in.items():
        base_key = key.split('|')[:2]
        base = '|'.join(base_key)
        row = {'key': key, 'team': base_key[0], 'size': int(base_key[1])}
        for pct, n in cuts.items():
            c = int(counts.get(pct, 0))
            row[f'top_{pct}_count'] = c
            row[f'top_{pct}_pct'] = round(100.0 * c / n, 3) if n else 0.0
        own_pct = team_size_own_pct.get(base)
        if own_pct is not None:
            row['own_pct'] = own_pct
            # Simple leverage: top_10 minus own
            row['lev_top10_minus_own'] = round(row.get('top_10_pct', 0.0) - own_pct, 3)
        rows.append(row)
    # Sort by top_1 then top_5
    rows.sort(key=lambda r: (-r.get('top_1_count', 0), -r.get('top_5_count', 0), r.get('team', '')))
    return {
        'bucket': bucket,
        'with_pitcher': with_pitcher,
        'total_lineups': total,
        'cuts': {str(k): v for k, v in cuts.items()},
        'rows': rows,
    }


def write_stack_analysis(site: str, date_mmdd: str, slate: str, bucket: str, with_pitcher: bool = False) -> Optional[Path]:
    res = compute_stack_top_inclusion_and_leverage(site, date_mmdd, slate, bucket, with_pitcher=with_pitcher)
    if not res:
        return None
    out_dir = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'tables' / 'analysis'
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = 'stack_with_pitcher' if with_pitcher else 'stack'
    out = out_dir / f'{suffix}_analysis_{bucket}.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=2)
    return out
