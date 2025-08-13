#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any, Optional


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
        if isinstance(v, list) and v and isinstance(v[0], dict) and (
            'players' in v[0] or 'roster' in v[0] or 'slots' in v[0]
        ):
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


def _player_name(p: dict) -> Optional[str]:
    for key in ('name', 'displayName', 'fullName', 'playerName'):
        v = p.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    if 'player' in p and isinstance(p['player'], dict):
        for key in ('name', 'displayName', 'fullName'):
            v = p['player'].get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
    if 'metadata' in p and isinstance(p['metadata'], dict):
        v = p['metadata'].get('name')
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def compute_ownership_from_atom(atom_file: Path) -> Dict[str, Any]:
    atom = _load_json(atom_file)
    data = atom.get('response_data') or atom.get('data') or {}
    lineups = _extract_lineups(data)
    total = len(lineups)
    counts: Counter = Counter()
    for lu in lineups:
        players = _extract_players(lu)
        for p in players:
            name = _player_name(p)
            if name:
                counts[name] += 1
    players_out = [
        {
            'name': name,
            'count': cnt,
            'own_pct': round(100.0 * cnt / total, 3) if total else 0.0,
        }
        for name, cnt in counts.most_common()
    ]
    return {
        'total_lineups': total,
        'unique_players': len(counts),
        'players': players_out,
    }


def write_bucket_ownership(site: str, date_mmdd: str, slate: str, bucket: str) -> Optional[Path]:
    atoms_dir = Path('_data') / 'sabersim_2025' / site / f"{date_mmdd}_{slate}" / 'atoms_output' / 'by_contest' / bucket / 'atoms'
    atom_file = atoms_dir / f'field_lineups_{bucket}.json'
    if not atom_file.exists():
        return None
    own = compute_ownership_from_atom(atom_file)
    out_dir = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'tables' / 'batters'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f'own_{bucket}.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump({'bucket': bucket, **own}, f, indent=2)
    return out_file
