#!/usr/bin/env python3
"""
Production Rolling Windows Collector Runner

Runs rolling windows data collection with smart incremental updates.
Only collects data that has actually changed since last update.

Usage:
    python run_rolling_collector.py              # Smart incremental update
    python run_rolling_collector.py --status     # Check what needs updating
    python run_rolling_collector.py --force      # Force full update
    python run_rolling_collector.py --workers 8  # Use 8 concurrent workers
"""

import sys
import argparse
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from mlb_api.rolling_windows.core.collector import EnhancedRollingCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_status():
    """Check rolling windows update status."""
    print("🔍 Rolling Windows Status Check...")

    collector = EnhancedRollingCollector(performance_profile='balanced')

    # Check hash information
    hash_info = collector.updater.get_hash_info()

    if hash_info:
        # Get timestamp from current hash data or last_update field
        current_hash = hash_info.get('current_hash', {})
        timestamp = current_hash.get('timestamp') or hash_info.get('last_update')
        data_size = current_hash.get('data_size', 0)

        if timestamp:
            if isinstance(timestamp, str):
                last_update = datetime.fromisoformat(timestamp.replace('Z', '+00:00') if timestamp.endswith('Z') else timestamp)
            else:
                last_update = timestamp
            hours_since = (datetime.now() - last_update).total_seconds() / 3600

            print(f"📅 Last Update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏰ Hours Since: {hours_since:.1f}h")
            print(f"📊 Data Size: {data_size:,} bytes")

            if hours_since < 6:
                print("✅ Data is current (< 6 hours)")
                return False
            else:
                print("⚠️ Data needs refresh (> 6 hours)")
                return True
        else:
            print("❓ No timestamp found")
            return True
    else:
        print("❓ No hash data found - full collection needed")
        return True


def run_collection(force_update=False, max_workers=4):
    """Run rolling windows collection with smart incremental updates."""
    start_time = time.time()

    print(f"🚀 Rolling Windows Collection - {'FORCED' if force_update else 'SMART'}")

    try:
        # Initialize collector with ultra-aggressive profile
        collector = EnhancedRollingCollector(
            performance_profile='ultra_aggressive',
            max_workers=max_workers  # Pipeline argument overrides profile default
        )

        # Run collection with incremental logic
        was_updated, data, reason = collector.run_collection(force_update=force_update)

        execution_time = time.time() - start_time

        if was_updated:
            metadata = data.get('metadata', {})
            total_players = metadata.get('total_players', 0)
            successful = metadata.get('successful_collections', 0)
            failed = metadata.get('failed_collections', 0)

            print(f"✅ Collection completed in {execution_time:.1f}s")
            print(f"📊 Total Players: {total_players}")
            print(f"🎯 Successful: {successful}, Failed: {failed}")
            print(f"💡 Reason: {reason}")

            # Show efficiency metrics if available
            if hasattr(collector, '_last_collection_stats'):
                stats = collector._last_collection_stats
                updated = stats.get('updated_players', 0)
                skipped = stats.get('skipped_players', 0)
                print(f"⚡ Efficiency: {updated} updated, {skipped} skipped")

        else:
            print(f"⏭️ No updates needed ({execution_time:.1f}s)")
            print(f"💡 Reason: {reason}")

        return True

    except KeyboardInterrupt:
        print("\n⏹️ Collection cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Collection failed: {e}")
        logger.exception("Rolling windows collection error")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Rolling Windows Collector')
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
