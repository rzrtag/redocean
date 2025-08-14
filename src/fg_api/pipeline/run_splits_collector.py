#!/usr/bin/env python3
"""
Fangraphs Splits Collection Pipeline

Run the advanced splits collector with player-based organization.
"""

import sys
import time
import argparse
from pathlib import Path
import json

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from fg_api.collectors.splits_collector import FGSplitsCollector


def run_splits_collection(force_update=False, max_workers=1):
    """Run Fangraphs splits collection with player-based approach."""
    start_time = time.time()

    print(f"📊 Fangraphs Splits Collection - {'FORCED' if force_update else 'SMART'}")
    print("🔒 Using player-based organization to handle traded players correctly...")

    try:
        # Initialize splits collector
        collector = FGSplitsCollector(
            performance_profile='stealth',
            max_workers=max_workers
        )

        # Run player-based collection
        summary = collector.collect_all_players_splits(force_update=force_update)

        elapsed = time.time() - start_time

        if summary:
            print(f"\n✅ Splits collection completed in {elapsed:.1f}s")
            print(f"📈 Results: {summary.get('players_with_splits', 0)} players with splits")
            print(f"📊 Total splits collected: {summary.get('total_splits', 0)}")
            print(f"👥 Total players processed: {summary.get('total_players', 0)}")
        else:
            print(f"\n❌ Splits collection failed")

        return summary

    except Exception as e:
        print(f"❌ Splits collection failed: {e}")
        return None


def show_status():
    """Show current collection status."""
    try:
        collector = FGSplitsCollector()

        # Check for player-based data
        data_dir = collector.data_dir
        player_files = list(data_dir.glob("player_*_splits.json"))
        summary_file = data_dir / "splits_collection_summary.json"

        print("📊 Fangraphs Splits Collection Status")
        print("=" * 50)
        print(f"Collection Method: Player-based (MLB ID)")
        print(f"Data Directory: {data_dir}")
        print(f"Individual Player Files: {len(player_files)}")

        if summary_file.exists():
            try:
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
                print(f"Total Players: {summary.get('total_players', 0)}")
                print(f"Players with Splits: {summary.get('players_with_splits', 0)}")
                print(f"Total Splits: {summary.get('total_splits', 0)}")
                print(f"Last Updated: {summary.get('collection_timestamp', 'Unknown')}")
            except Exception as e:
                print(f"Error reading summary: {e}")
        else:
            print("No collection summary found")

    except Exception as e:
        print(f"❌ Failed to get status: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Fangraphs Splits Collection Pipeline")
    parser.add_argument('--force', action='store_true',
                       help='Force update all players (ignore existing data)')
    parser.add_argument('--workers', type=int, default=1,
                       help='Number of concurrent workers (default: 1 for stealth)')
    parser.add_argument('--status', action='store_true',
                       help='Show current collection status')

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    # Run splits collection
    run_splits_collection(
        force_update=args.force,
        max_workers=args.workers
    )


if __name__ == "__main__":
    main()
