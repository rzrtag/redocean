#!/usr/bin/env python3
"""
Compute consolidated contest/site summary tables from extracted atoms.

Reads from the standardized atoms_output and writes analysis tables under
<base>/<site>/<date_slate>/tables_analysis.
"""
from __future__ import annotations

from pathlib import Path
import json
from typing import Dict, Any, Optional, List

from sabersim.tables.manifest import SaberSimLayout, load_json


def build_summary(layout: SaberSimLayout) -> Dict[str, Any]:
    tables_dir = layout.tables_dir
    out: Dict[str, Any] = {
        "site": layout.site,
        "date_slate": layout.date_slate,
        "paths": {
            "contest_summary": str(tables_dir / "contest_summary.json"),
            "lineup_summary": str(tables_dir / "lineup_summary.json"),
            "portfolio_data": str(tables_dir / "portfolio_data.json"),
            "portfolio_summary": str(tables_dir / "portfolio_summary.json"),
            "progress_data": str(tables_dir / "progress_data.json"),
            "master_summary": str(tables_dir / "master_summary.json"),
        },
        "stats": {}
    }

    # Load quick stats if present
    contest = load_json(tables_dir / "contest_summary.json")
    lineups = load_json(tables_dir / "lineup_summary.json")
    out["stats"]["num_contests"] = len(contest) if isinstance(contest, list) else 0
    out["stats"]["num_lineups"] = len(lineups) if isinstance(lineups, list) else 0
    return out


def write_summary(layout: SaberSimLayout) -> Path:
    layout.analysis_dir.mkdir(parents=True, exist_ok=True)
    out_path = layout.analysis_dir / "contest_site_summary.json"
    payload = build_summary(layout)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return out_path

## Legacy helpers removed to prevent import-order conflicts
