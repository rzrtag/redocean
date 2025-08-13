#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from star_cannon.core.tables.ownership.compute_pid_ownership import _pid_meta_map, _is_pitcher_from_meta, _extract_name_team


def _load_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _field_lineups_atom(site: str, date_mmdd: str, slate: str, bucket: str) -> Optional[Path]:
    p = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'atoms_output' / 'by_contest' / bucket / 'atoms' / f'field_lineups_{bucket}.json'
    return p if p.exists() else None


def _collect_lineups(atom_path: Path) -> List[Tuple[List[str], float]]:
    j = _load_json(atom_path)
    data = j.get('response_data') or j.get('data') or {}
    lineups = data.get('lineups') or []
    out: List[Tuple[List[str], float]] = []
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
            out.append(([str(x) for x in pids], score))
    return out


def compute_top_inclusion(site: str, date_mmdd: str, slate: str, bucket: str, percents: List[int] = [1, 5, 10]) -> Dict[str, Any]:
    atom = _field_lineups_atom(site, date_mmdd, slate, bucket)
    if not atom:
        return {}
    lineups = _collect_lineups(atom)
    total = len(lineups)
    if total == 0:
        return {'total_lineups': 0, 'players': {}}
    # Sort by projected score descending
    lineups.sort(key=lambda x: x[1], reverse=True)
    pid_meta = _pid_meta_map(site, date_mmdd, slate)

    # Determine top-cut indices
    cuts: Dict[int, int] = {}
    for p in percents:
        n = max(1, int(round(total * (p / 100.0))))
        cuts[p] = n

    # Count appearances in top-k for each pid
    from collections import defaultdict
    appears_in: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for pct, n in cuts.items():
        for pids, _ in lineups[:n]:
            for pid in pids:
                appears_in[pid][pct] += 1

    # Build output records split by role
    batters: List[Dict[str, Any]] = []
    pitchers: List[Dict[str, Any]] = []
    for pid, counts in appears_in.items():
        meta = pid_meta.get(pid, {})
        name, team = _extract_name_team(meta)
        role_pitcher = _is_pitcher_from_meta(meta)
        record = {
            'pid': pid,
            'name': name or pid,
            'team': team,
        }
        for pct, n in cuts.items():
            c = int(counts.get(pct, 0))
            record[f'top_{pct}_count'] = c
            record[f'top_{pct}_pct'] = round(100.0 * c / n, 3) if n else 0.0
        if role_pitcher:
            pitchers.append(record)
        else:
            batters.append(record)

    def sort_key(r: Dict[str, Any]) -> Tuple:
        # Primary sort by top_1 then top_5 then name
        return (
            -float(r.get('top_1_count', 0)),
            -float(r.get('top_5_count', 0)),
            r.get('name') or ''
        )

    batters.sort(key=sort_key)
    pitchers.sort(key=sort_key)

    return {
        'bucket': bucket,
        'total_lineups': total,
        'cuts': {str(k): v for k, v in cuts.items()},
        'batters': batters,
        'pitchers': pitchers,
    }


def write_top_inclusion(site: str, date_mmdd: str, slate: str, bucket: str) -> Optional[Path]:
    res = compute_top_inclusion(site, date_mmdd, slate, bucket)
    if not res:
        return None
    out_dir = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'tables' / 'analysis'
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f'top_inclusion_{bucket}.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(res, f, indent=2)
    return out
