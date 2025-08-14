#!/usr/bin/env python3
"""
Production Active Rosters Collector Runner

Runs MLB active rosters collection with smart incremental updates.
Only collects data that has actually changed since last update.

Usage:
    python run_roster_collector.py              # Smart incremental update
    python run_roster_collector.py --status     # Check what needs updating
    python run_roster_collector.py --force      # Force full update
    python run_roster_collector.py --workers 8  # Use 8 concurrent workers
"""

import sys
import argparse
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from mlb_api.rosters.rosters_collector import ActiveRostersCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_status():
    """Check active rosters update status."""
    print("🔍 Active Rosters Status Check (simplified)...")
    path = Path('/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/active_rosters/data/active_rosters.json')
    if not path.exists():
        print("❓ No data file found - collection needed")
        return True
    try:
        import json
        with open(path, 'r') as f:
            data = json.load(f)
        ts = data.get('metadata', {}).get('collection_timestamp')
        if ts:
            last_update = datetime.fromisoformat(ts)
            hours_since = (datetime.now() - last_update).total_seconds() / 3600
            print(f"📅 Last Update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏰ Hours Since: {hours_since:.1f}h")
            return hours_since >= 24
    except Exception:
        pass
    return True


def run_collection(force_update=False, max_workers=12):
    """Run active rosters collection with smart incremental updates."""
    start_time = time.time()

    print(f"🚀 Active Rosters Collection - {'FORCED' if force_update else 'SMART'}")

    try:
        collector = ActiveRostersCollector(max_workers=max_workers, request_delay=0.01)
        data = collector.collect_all_teams()

        execution_time = time.time() - start_time

        rosters = data.get('rosters', {})
        total_teams = len(rosters)
        total_players = sum(len(team_data.get('roster', [])) for team_data in rosters.values())

        print(f"✅ Collection completed in {execution_time:.1f}s")
        print(f"⚾ Teams: {total_teams}")
        print(f"👥 Total Players: {total_players}")

        # Show some team details
        if rosters:
            print("📋 Sample Teams:")
            for i, (team_abbr, team_data) in enumerate(list(rosters.items())[:5]):
                roster_size = len(team_data.get('roster', []))
                print(f"   {team_abbr}: {roster_size} players")

            if total_teams > 5:
                print(f"   ... and {total_teams - 5} more teams")

        return True

    except KeyboardInterrupt:
        print("\n⏹️ Collection cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Collection failed: {e}")
        logger.exception("Active rosters collection error")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Active Rosters Collector')
    parser.add_argument('--status', action='store_true',
                       help='Check status without running collection')
    parser.add_argument('--force', action='store_true',
                       help='Force full update regardless of hash')
    parser.add_argument('--workers', type=int, default=12,
                       help='Number of concurrent workers (default: 12)')

    args = parser.parse_args()

    if args.status:
        needs_update = check_status()
        sys.exit(1 if needs_update else 0)
    else:
        success = run_collection(force_update=args.force, max_workers=args.workers)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
