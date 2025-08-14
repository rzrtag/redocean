#!/usr/bin/env python3
"""
Fangraphs Roster Collection Pipeline

Run the advanced roster collector with comprehensive Cloudflare bypass.
"""

import sys
import time
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from fg_api.collectors.roster_collector import FGRosterCollector


def run_roster_collection(force_update=False, max_workers=1, teams=None, levels=None):
    """Run Fangraphs roster collection with advanced bypass techniques."""
    start_time = time.time()

    print(f"📊 Fangraphs Roster Collection - {'FORCED' if force_update else 'SMART'}")
    print("🔒 Using advanced Cloudflare bypass techniques...")

    try:
        # Initialize roster collector
        collector = FGRosterCollector(
            performance_profile='stealth',
            max_workers=max_workers
        )

        # Get collection status
        status = collector.get_collection_status()
        print(f"📊 Current Status: {status['total_teams']} teams, {status['total_players']} players")

        if status['last_updated']:
            print(f"🕒 Last Updated: {status['last_updated']}")

        # Run collection
        if force_update:
            print("🔄 Force update mode - collecting all teams")

        # Collect data efficiently
        summary = collector.collect_all_teams_efficient(
            teams=teams,
            levels=levels or ['MLB'],
            force_update=force_update
        )

        elapsed = time.time() - start_time

        print(f"\n✅ Roster collection completed in {elapsed:.1f}s")
        print(f"📈 Results: {summary['summary']['updated']} updated, "
              f"{summary['summary']['skipped']} skipped, "
              f"{summary['summary']['failed']} failed")
        print(f"👥 Total Players: {summary['summary']['total_players']}")

        return summary

    except Exception as e:
        print(f"❌ Stealth collection failed: {e}")
        return None


def show_status():
    """Show current collection status."""
    try:
        collector = FGRosterCollector()
        status = collector.get_collection_status()

        print("📊 Fangraphs Roster Collection Status")
        print("=" * 50)
        print(f"Collector: {status['collector_name']}")
        print(f"Total Teams: {status['total_teams']}")
        print(f"Total Players: {status['total_players']}")
        print(f"MLB Players: {status['mlb_players']}")

        if status['teams_by_level']:
            print("\nTeams by Level:")
            for level, count in status['teams_by_level'].items():
                print(f"  {level}: {count}")

        if status['last_updated']:
            print(f"\nLast Updated: {status['last_updated']}")
        else:
            print("\nNo data collected yet")

    except Exception as e:
        print(f"❌ Failed to get status: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Fangraphs Roster Collection Pipeline")
    parser.add_argument('--force', action='store_true',
                       help='Force update all teams (ignore hash checks)')
    parser.add_argument('--workers', type=int, default=1,
                       help='Number of concurrent workers (default: 1 for stealth)')
    parser.add_argument('--teams', nargs='+',
                       help='Specific teams to collect (e.g., TEX SEA)')
    parser.add_argument('--levels', nargs='+', default=['MLB'],
                       help='Levels to collect (default: MLB)')
    parser.add_argument('--status', action='store_true',
                       help='Show current collection status')

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    # Run roster collection
    run_roster_collection(
        force_update=args.force,
        max_workers=args.workers,
        teams=args.teams,
        levels=args.levels
    )


if __name__ == "__main__":
    main()
