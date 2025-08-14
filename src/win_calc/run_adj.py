#!/usr/bin/env python3
"""
ADJ Projection System CLI

MVP: Load SaberSim starters, apply rolling window adjustments, export CSVs.
"""

import argparse
import sys

from .starters import load_all_starters
from .exporter import export_csv


def run_adj_mvp(site: str, date_mmdd: str, slate: str, export: bool = False):
    """Run MVP adjustment process."""
    print(f"🎯 Running ADJ MVP for {site} {date_mmdd} {slate}")
    
    # Load starters
    print("📊 Loading starters...")
    pitcher_names, batter_data = load_all_starters(site, date_mmdd, slate)
    
    print(f"   Pitchers: {len(pitcher_names)}")
    print(f"   Batters: {len(batter_data)}")
    
    # Initialize rolling adjuster (for future use)
    # adjuster = RollingAdjuster()
    
    # Process pitchers (for MVP, we'll use placeholder adjustments)
    print("⚾ Processing pitchers...")
    pitcher_rows = []
    for name in pitcher_names[:5]:  # Limit to 5 for MVP
        # For MVP, use simple placeholder adjustment
        adjustment = 0.02  # +2% for MVP demo
        pitcher_rows.append({
            "site": site,
            "slate": slate,
            "player_id": f"P_{name.replace(' ', '_')}",
            "player_name": name,
            "team": "TBD",  # Would come from SaberSim data
            "pos": "P",
            "salary": 0,  # Would come from SaberSim data
            "projection_adj": adjustment
        })
    
    # Process batters
    print("🏃 Processing batters...")
    batter_rows = []
    for batter in batter_data[:10]:  # Limit to 10 for MVP
        name = batter.get("name", "Unknown")
        # For MVP, use simple placeholder adjustment
        adjustment = -0.01  # -1% for MVP demo
        batter_rows.append({
            "site": site,
            "slate": slate,
            "player_id": f"B_{name.replace(' ', '_')}",
            "player_name": name,
            "team": batter.get("team", "TBD"),
            "pos": batter.get("position", "UTIL"),
            "salary": 0,  # Would come from SaberSim data
            "projection_adj": adjustment
        })
    
    # Combine all rows
    all_rows = pitcher_rows + batter_rows
    
    print(f"✅ Processed {len(all_rows)} players")
    
    # Export if requested
    if export:
        print("📤 Exporting CSV...")
        csv_path = export_csv(site, date_mmdd, slate, all_rows)
        print(f"   Exported to: {csv_path}")
    
    return all_rows


def main():
    parser = argparse.ArgumentParser(description="ADJ Projection System")
    parser.add_argument("--site", required=True, 
                       choices=["draftkings", "fanduel"],
                       help="Site to process")
    parser.add_argument("--date", required=True, help="Date in MMDD format")
    parser.add_argument("--slate", required=True, help="Slate name")
    parser.add_argument("--export", action="store_true", help="Export CSV")
    
    args = parser.parse_args()
    
    try:
        rows = run_adj_mvp(args.site, args.date, args.slate, args.export)
        print(f"🎉 MVP completed successfully! Processed {len(rows)} players")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
