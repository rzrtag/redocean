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
    print("🔍 Active Rosters Status Check...")

    collector = ActiveRostersCollector()

    # Check hash information
    hash_info = collector.updater.get_hash_info()

    if hash_info:
        # Handle both timestamp formats
        current_hash = hash_info.get('current_hash', {})
        timestamp = current_hash.get('timestamp') or hash_info.get('last_update')
        data_size = current_hash.get('data_size', 0)

        if timestamp:
            last_update = datetime.fromisoformat(timestamp.replace('Z', '+00:00') if timestamp.endswith('Z') else timestamp)
            hours_since = (datetime.now() - last_update).total_seconds() / 3600

            print(f"📅 Last Update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏰ Hours Since: {hours_since:.1f}h")
            print(f"📊 Data Size: {hash_info.get('data_size', 0):,} bytes")

            # Rosters change less frequently - 24 hour threshold
            if hours_since < 24:
                print("✅ Rosters are current (< 24 hours)")
                return False
            else:
                print("⚠️ Rosters need refresh (> 24 hours)")
                return True
        else:
            print("❓ No timestamp found")
            return True
    else:
        print("❓ No hash data found - full collection needed")
        return True


def run_collection(force_update=False, max_workers=12):
    """Run active rosters collection with smart incremental updates."""
    start_time = time.time()

    print(f"🚀 Active Rosters Collection - {'FORCED' if force_update else 'SMART'}")

    try:
        # Initialize collector with ultra-aggressive settings
        collector = ActiveRostersCollector(
            max_workers=max_workers,
            request_delay=0.01  # Ultra-aggressive delay
        )

        # Run collection with incremental logic
        was_updated, data, reason = collector.run_collection(force_update=force_update)

        execution_time = time.time() - start_time

        if was_updated:
            rosters = data.get('rosters', {})
            total_teams = len(rosters)
            total_players = sum(len(team_data.get('roster', [])) for team_data in rosters.values())

            print(f"✅ Collection completed in {execution_time:.1f}s")
            print(f"⚾ Teams: {total_teams}")
            print(f"👥 Total Players: {total_players}")
            print(f"💡 Reason: {reason}")

            # Show some team details
            if rosters:
                print("📋 Sample Teams:")
                for i, (team_abbr, team_data) in enumerate(list(rosters.items())[:5]):
                    roster_size = len(team_data.get('roster', []))
                    print(f"   {team_abbr}: {roster_size} players")

                if total_teams > 5:
                    print(f"   ... and {total_teams - 5} more teams")

        else:
            print(f"⏭️ No updates needed ({execution_time:.1f}s)")
            print(f"💡 Reason: {reason}")

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
