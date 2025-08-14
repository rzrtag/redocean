#!/usr/bin/env python3
"""
Production Statcast Advanced Box Score Collector Runner

Runs Statcast advanced box score collection with smart incremental updates.
Daily collections with intelligent date-based updates.

Usage:
    python run_statcast_collector.py                 # Smart incremental update
    python run_statcast_collector.py --status        # Check what needs updating
    python run_statcast_collector.py --force         # Force full update
    python run_statcast_collector.py --workers 10    # Use 10 concurrent workers
    python run_statcast_collector.py --days 7        # Collect last 7 days
"""

import sys
import argparse
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from mlb_api.statcast_adv_box.statcast_collector import StatcastAdvancedCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_status():
    """Check Statcast collection status by examining existing date files."""
    print("🔍 Statcast Advanced Status Check...")

    # Check what dates we have vs what we need
    data_dir = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/statcast_adv_box/data/date")

    if not data_dir.exists():
        print("❓ No Statcast data directory found")
        return True

    # Get existing date files
    existing_files = list(data_dir.glob("advanced_statcast_*.json"))
    existing_dates = set()

    for file in existing_files:
        # Extract date from filename like "advanced_statcast_20250813.json"
        try:
            date_str = file.stem.split('_')[-1]  # Gets "20250813"
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            existing_dates.add(date_obj.date())
        except ValueError:
            continue

    if existing_dates:
        latest_date = max(existing_dates)
        days_behind = (datetime.now().date() - latest_date).days

        print(f"📅 Latest Data: {latest_date}")
        print(f"📊 Total Dates: {len(existing_dates)}")
        print(f"⏰ Days Behind: {days_behind}")

        if days_behind <= 1:
            print("✅ Statcast data is current (≤ 1 day behind)")
            return False
        else:
            print("⚠️ Statcast data needs refresh (> 1 day behind)")
            return True
    else:
        print("❓ No Statcast date files found")
        return True


def run_collection(force_update=False, max_workers=16, days_back=3):
    """Run Statcast collection with simple date-based updates."""
    start_time = time.time()

    print(f"🚀 Statcast Collection - {'FORCED' if force_update else 'SIMPLE'}")
    print(f"📅 Days Back: {days_back}")

    try:
        # Initialize collector with ultra-aggressive profile
        collector = StatcastAdvancedCollector(
            performance_profile='ultra_aggressive',
            max_workers=max_workers  # Pipeline argument overrides profile default
        )

        # Simple approach: collect recent dates directly
        if days_back and days_back > 0:
            end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

            print(f"📅 Collecting dates: {start_date} to {end_date}")
            results = collector.collect_date_range(start_date, end_date)

            # Calculate summary from results
            total_at_bats = sum(results.values())
            dates_collected = len([v for v in results.values() if v > 0])

            execution_time = time.time() - start_time

            print(f"✅ Collection completed in {execution_time:.1f}s")
            print(f"📊 Results:")
            print(f"   📅 Dates collected: {dates_collected}")
            print(f"   ⚾ Total at-bats: {total_at_bats}")

            # Show recent dates with actual data
            print("🗓️ Recent Dates:")
            for date_str, at_bats in sorted(results.items(), reverse=True)[:5]:
                if at_bats > 0:
                    print(f"   {date_str}: {at_bats} at-bats")

            return True

        else:
            print("⏭️ No dates specified for collection")
            return False

    except KeyboardInterrupt:
        print("\n⏹️ Collection cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Collection failed: {e}")
        logger.exception("Statcast collection error")
        return False

    except KeyboardInterrupt:
        print("\n⏹️ Collection cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Collection failed: {e}")
        logger.exception("Statcast collection error")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Statcast Advanced Collector')
    parser.add_argument('--status', action='store_true',
                       help='Check status without running collection')
    parser.add_argument('--force', action='store_true',
                       help='Force full update regardless of hash')
    parser.add_argument('--workers', type=int, default=12,
                       help='Number of concurrent workers (default: 12)')
    parser.add_argument('--days', type=int, default=3,
                       help='Number of days back to collect (default: 3)')

    args = parser.parse_args()

    if args.status:
        needs_update = check_status()
        sys.exit(1 if needs_update else 0)
    else:
        success = run_collection(
            force_update=args.force,
            max_workers=args.workers,
            days_back=args.days
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
