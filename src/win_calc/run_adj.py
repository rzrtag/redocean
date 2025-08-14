#!/usr/bin/env python3
"""
win_calc: Adjust SaberSim median projections using MLB rolling/Statcast signals.

MVP stub: sets up CLI and file paths. Implementation to follow as we finalize methodology.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

BASE_DATA = Path("/mnt/storage_fast/workspaces/red_ocean/_data")
SABERSIM_BASE = BASE_DATA / "sabersim_2025"
WIN_BASE = BASE_DATA / "win_calc"


def build_paths(site: str, date_mmdd: str, slate: str) -> dict:
    base = {}
    base["ss_tables"] = SABERSIM_BASE / site / f"{date_mmdd}_{slate}" / "atoms_output" / "tables"
    base["out_dir"] = WIN_BASE / "output" / site / f"{date_mmdd}_{slate}"
    base["export_dir"] = WIN_BASE / "export" / site / f"{date_mmdd}_{slate}"
    base["adj_json"] = base["out_dir"] / "projections_adj.json"
    base["upload_csv"] = base["export_dir"] / f"{('dk' if site=='draftkings' else 'fd')}_upload.csv"
    return base


def ensure_dirs(paths: dict) -> None:
    paths["out_dir"].mkdir(parents=True, exist_ok=True)
    paths["export_dir"].mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="win_calc: adjusted projections generator")
    parser.add_argument("--site", choices=["draftkings", "fanduel"], required=True)
    parser.add_argument("--date", dest="date_mmdd", required=True, help="MMDD slate date")
    parser.add_argument("--slate", default="main_slate", help="slate name, e.g., main_slate")
    parser.add_argument("--export", action="store_true", help="write upload CSV")
    parser.add_argument("--cap", type=float, default=0.2, help="max absolute adj fraction (e.g., 0.2=±20%)")
    parser.add_argument("--k", type=float, default=0.15, help="aggressiveness multiplier")
    args = parser.parse_args()

    started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("🚀 win_calc: Adjust Projections")
    print("=" * 60)
    print(f"🕐 Started: {started}")
    print(f"🧭 Site: {args.site}  Date: {args.date_mmdd}  Slate: {args.slate}")

    paths = build_paths(args.site, args.date_mmdd, args.slate)
    ensure_dirs(paths)

    # Validate inputs exist (SaberSim tables)
    if not paths["ss_tables"].exists():
        print(f"❌ Missing SaberSim tables: {paths['ss_tables']}")
        sys.exit(1)

    # Stub: write empty adjusted projections skeleton
    from json import dump
    adj_payload = {
        "meta": {
            "site": args.site,
            "date": args.date_mmdd,
            "slate": args.slate,
            "created_at": started,
            "cap": args.cap,
            "k": args.k,
        },
        "players": []
    }
    with open(paths["adj_json"], "w") as f:
        dump(adj_payload, f, indent=2)
    print(f"✅ Wrote: {paths['adj_json']}")

    if args.export:
        # Stub CSV export
        import csv
        headers = ["site", "slate", "player_id", "player_name", "team", "pos", "salary", "projection_adj"]
        with open(paths["upload_csv"], "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(headers)
        print(f"✅ Exported CSV: {paths['upload_csv']}")

    print("🎉 win_calc stub complete (MVP scaffolding). Implementation next.")


if __name__ == "__main__":
    main()
