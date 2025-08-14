#!/usr/bin/env python3
"""
Win Calc Pipeline Runner

Builds site-specific adj tables (batters/pitchers) from SaberSim atoms
build_optimization outputs and exports upload CSVs (DFS ID, Name, My Proj).

This script auto-detects the latest slate for each site and runs end-to-end:
- Build adj_* JSONs via in-process calls to adj builder
- Export CSVs matching SaberSim override format
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
import argparse

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from win_calc.adj_builder import build_adj_from_build_optimization, write_json, load_json  # noqa: E402
from win_calc.rolling_adjuster import adjust_records  # noqa: E402


DATA_ROOT = Path("/mnt/storage_fast/workspaces/red_ocean/_data/sabersim_2025")
CSV_ROOT = Path("/mnt/storage_fast/workspaces/red_ocean/dfs_1/entries")


def find_latest_slate(site: str) -> Path | None:
    site_dir = DATA_ROOT / site
    if not site_dir.exists():
        return None
    latest: Path | None = None
    for child in site_dir.iterdir():
        if child.is_dir():
            if latest is None or child.stat().st_mtime > latest.stat().st_mtime:
                latest = child
    return latest


def export_upload_csv(batters_json: Path, pitchers_json: Path, out_csv: Path) -> None:
    batters_obj = load_json(str(batters_json))
    pitchers_obj = load_json(str(pitchers_json))
    rows = []
    for key in ("batters", "pitchers"):
        for p in (batters_obj.get(key, []) if key == "batters" else pitchers_obj.get(key, [])):
            dfs_id = p.get("dfs_id")
            name = p.get("name")
            my_proj = p.get("my_proj")
            if dfs_id is None or name is None or my_proj is None:
                continue
            rows.append([dfs_id, name, my_proj])

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    import csv
    with open(out_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["DFS ID", "Name", "My Proj"])
        writer.writerows(rows)


def process_site(site: str, args: argparse.Namespace | None = None) -> dict:
    start = time.time()
    latest = find_latest_slate(site)
    if latest is None:
        return {"site": site, "status": "no_data"}

    build_json = latest / "atoms_output/atoms/build_optimization.json"
    if not build_json.exists():
        return {"site": site, "status": "missing_build_optimization", "path": str(build_json)}

    # Build adj
    raw = load_json(str(build_json))
    batters, pitchers = build_adj_from_build_optimization(raw, site=site)
    # Apply rolling-window adjustments
    if args is not None:
        batters, pitchers = adjust_records(
            site,
            batters,
            pitchers,
            w50=args.w50,
            w100=args.w100,
            w250=args.w250,
            k=args.k,
            cap=args.cap,
            league_xwoba_hitter=args.league_xwoba_hitter,
            league_xwoba_pitcher=args.league_xwoba_pitcher,
        )
    else:
        batters, pitchers = adjust_records(site, batters, pitchers)

    # Write adj JSONs
    site_prefix = "fd" if site == "fanduel" else "dk"
    out_dir = latest / "win_calc"
    out_dir.mkdir(parents=True, exist_ok=True)
    adj_batters = out_dir / f"adj_{site_prefix}_batters.json"
    adj_pitchers = out_dir / f"adj_{site_prefix}_pitchers.json"

    # Add metadata wrapper
    date = raw.get("metadata", {}).get("request_data", {}).get("date")
    write_json(str(adj_batters), {"site": site, "date": date, "slate": latest.name, "batters": batters})
    write_json(str(adj_pitchers), {"site": site, "date": date, "slate": latest.name, "pitchers": pitchers})

    # Export CSV
    out_csv = CSV_ROOT / ("fd_upload.csv" if site == "fanduel" else "dk_upload.csv")
    export_upload_csv(adj_batters, adj_pitchers, out_csv)

    elapsed = time.time() - start
    return {
        "site": site,
        "status": "ok",
        "slate": latest.name,
        "adj_batters": str(adj_batters),
        "adj_pitchers": str(adj_pitchers),
        "csv": str(out_csv),
        "elapsed_sec": round(elapsed, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Win Calc Pipeline Runner")
    # Tunables for rolling adjustments
    parser.add_argument("--w50", type=float, help="Weight for 50-event window")
    parser.add_argument("--w100", type=float, help="Weight for 100-event window")
    parser.add_argument("--w250", type=float, help="Weight for 250-event window")
    parser.add_argument("--k", type=float, help="Aggressiveness multiplier")
    parser.add_argument("--cap", type=float, help="Max absolute adjustment (fraction, e.g., 0.2 for 20%)")
    parser.add_argument("--league-xwoba-hitter", dest="league_xwoba_hitter", type=float, help="League-average xwOBA for hitters")
    parser.add_argument("--league-xwoba-pitcher", dest="league_xwoba_pitcher", type=float, help="League-average xwOBA allowed for pitchers")
    args = parser.parse_args()

    print("\n🧮 Win Calc Pipeline")
    print("=" * 50)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []
    for site in ("fanduel", "draftkings"):
        print(f"\n➡️  Processing site: {site}")
        res = process_site(site, args)
        results.append(res)
        if res.get("status") == "ok":
            print(f"✅ {site} adj + CSV done for slate {res['slate']} → {res['csv']}")
        else:
            print(f"⚠️ {site} skipped: {res}")

    print("\n📊 Win Calc Summary")
    print("=" * 50)
    for r in results:
        print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
