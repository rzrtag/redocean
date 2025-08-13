#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional


def _load_json(p: Path) -> dict:
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def _players_proj_path(site: str, date_mmdd: str, slate: str) -> Optional[Path]:
    # Use build optimization adjusted ownership/projection file set as proxy for projections
    p = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'tables' / 'players'
    # Prefer adjusted ownership file that includes names/teams and we can attach projection later if available
    # In absence of a projections table, this module will compute leverage only using ownership (placeholder)
    return p / (('dk_' if site == 'draftkings' else 'fd_') + 'build_optm_adj_own.json')


def _read_ownership(site: str, date_mmdd: str, slate: str, role: str, bucket: str) -> dict:
    sub = 'batters' if role == 'batter' else 'pitchers'
    p = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'tables' / sub / f'own_{bucket}.json'
    return _load_json(p) if p.exists() else {}


def compute_leverage(site: str, date_mmdd: str, slate: str, bucket: str, role: str) -> Optional[Path]:
    own = _read_ownership(site, date_mmdd, slate, role, bucket)
    if not own:
        return None
    proj_path = _players_proj_path(site, date_mmdd, slate)
    proj = _load_json(proj_path) if proj_path.exists() else {'players': []}
    # Build name->ownership and name->proj maps (PID preferred when available)
    own_map: Dict[str, float] = {}
    pid_map: Dict[str, float] = {}
    for rec in own.get('players', []):
        if not isinstance(rec, dict):
            continue
        name = rec.get('name')
        pct = rec.get('own_pct')
        pid = rec.get('pid')
        if isinstance(name, str) and isinstance(pct, (int, float)):
            own_map[name] = float(pct)
        if isinstance(pid, str) and isinstance(pct, (int, float)):
            pid_map[pid] = float(pct)
    proj_map: Dict[str, float] = {}
    pid_proj: Dict[str, float] = {}
    for rec in proj.get('players', []):
        if not isinstance(rec, dict):
            continue
        name = rec.get('name')
        pid = rec.get('pid')
        # choose projection numeric source if exists; else 0
        pv = rec.get('projection') or rec.get('proj') or rec.get('dkProjection') or rec.get('fdProjection')
        try:
            pv_f = float(pv)
        except (TypeError, ValueError):
            pv_f = 0.0
        if isinstance(name, str):
            proj_map[name] = pv_f
        if isinstance(pid, str):
            pid_proj[pid] = pv_f

    # Compose leverage table (prefer PID-based join when available)
    rows = []
    for rec in own.get('players', []):
        if not isinstance(rec, dict):
            continue
        name = rec.get('name')
        own_pct = rec.get('own_pct')
        pid = rec.get('pid') if isinstance(rec.get('pid'), str) else None
        if not isinstance(name, str) or not isinstance(own_pct, (int, float)):
            continue
        proj_val = 0.0
        if pid and pid in pid_proj:
            proj_val = pid_proj[pid]
        else:
            proj_val = proj_map.get(name, 0.0)
        rows.append({
            'pid': pid,
            'name': name,
            'own_pct': float(own_pct),
            'proj': proj_val,
            'lev_proj_minus_own': round(proj_val - float(own_pct), 3),
        })

    out_dir = Path('_data') / 'star_cannon' / site / date_mmdd / slate / 'tables' / 'analysis'
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f'leverage_{role}_{bucket}.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'bucket': bucket, 'role': role, 'rows': rows}, f, indent=2)
    return out
