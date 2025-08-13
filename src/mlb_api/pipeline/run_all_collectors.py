#!/usr/bin/env python3
"""
Production MLB API Data Pipeline Runner

Orchestrates all MLB data collection with smart incremental updates.
Runs rosters, rolling windows, and Statcast collections efficiently.

Usage:
    python run_all_mlb_api_collectors.py              # Smart incremental updates
    python run_all_mlb_api_collectors.py --status     # Check all collectors status
    python run_all_mlb_api_collectors.py --force      # Force all updates
    python run_all_mlb_api_collectors.py --skip-rolling  # Skip rolling windows
    python run_all_mlb_api_collectors.py --only rosters  # Run only rosters
"""

import sys
import argparse
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

def run_collector(script_name, args=None, description=""):
    """Run a collector script and return success status."""
    script_path = Path(__file__).parent / script_name
    # Force use of python3 instead of sys.executable to avoid Cursor issues
    cmd = ["python3", str(script_path)]

    if args:
        cmd.extend(args)

    print(f"\n🚀 {description}")
    print(f"📄 Running: {' '.join(cmd)}")

    start_time = time.time()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout

        execution_time = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ {description} completed in {execution_time:.1f}s")
            if result.stdout.strip():
                print("📋 Output:")
                for line in result.stdout.strip().split('\n'):
                    print(f"   {line}")
            return True
        else:
            print(f"❌ {description} failed after {execution_time:.1f}s")
            if result.stderr.strip():
                print("🔴 Error:")
                for line in result.stderr.strip().split('\n'):
                    print(f"   {line}")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out after 30 minutes")
        return False
    except Exception as e:
        print(f"💥 {description} crashed: {e}")
        return False


def check_all_status():
    """Check status of all collectors."""
    print("🔍 MLB API Pipeline Status Check")
    print("=" * 50)

    collectors = [
        ("run_roster_collector.py", "Active Rosters"),
        ("run_rolling_collector.py", "Rolling Windows"),
        ("run_statcast_collector.py", "Statcast Advanced")
    ]

    needs_updates = []

    for script, name in collectors:
        print(f"\n📊 {name}:")
        success = run_collector(script, ["--status"], f"{name} Status")
        if not success:  # Exit code 1 means needs update
            needs_updates.append(name)

    print(f"\n📋 Summary:")
    if needs_updates:
        print(f"⚠️ Need Updates: {', '.join(needs_updates)}")
        return True
    else:
        print("✅ All collectors are current")
        return False


def run_all_collections(force_update=False, skip_collectors=None, only_collector=None):
    """Run all MLB data collections."""
    start_time = time.time()

    print("🚀 MLB API Complete Data Pipeline")
    print("=" * 50)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔄 Mode: {'FORCED UPDATE' if force_update else 'SMART INCREMENTAL'}")

    # Define collection order and settings
    collections = [
        {
            "script": "run_roster_collector.py",
            "name": "Active Rosters",
            "key": "rosters",
            "args": ["--workers", "5"] + (["--force"] if force_update else []),
            "description": "MLB team rosters and player info"
        },
        {
            "script": "run_rolling_collector.py",
            "name": "Rolling Windows",
            "key": "rolling",
            "args": ["--workers", "6"] + (["--force"] if force_update else []),
            "description": "Player rolling window statistics"
        },
        {
            "script": "run_statcast_collector.py",
            "name": "Statcast Advanced",
            "key": "statcast",
            "args": ["--workers", "8", "--days", "3"] + (["--force"] if force_update else []),
            "description": "Advanced Statcast box scores"
        }
    ]

    # Filter collections based on arguments
    if only_collector:
        collections = [c for c in collections if c["key"] == only_collector]
    elif skip_collectors:
        collections = [c for c in collections if c["key"] not in skip_collectors]

    # Run collections
    results = {}

    for collection in collections:
        success = run_collector(
            collection["script"],
            collection["args"],
            collection["name"]
        )
        results[collection["name"]] = success

    # Summary
    total_time = time.time() - start_time
    successful = sum(results.values())
    total = len(results)

    print(f"\n📊 Pipeline Summary")
    print("=" * 50)
    print(f"⏱️ Total Time: {total_time:.1f}s")
    print(f"✅ Successful: {successful}/{total}")

    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {name}")

    if successful == total:
        print(f"\n🎉 All collections completed successfully!")
        return True
    else:
        print(f"\n⚠️ {total - successful} collections failed")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='MLB API Complete Data Pipeline')
    parser.add_argument('--status', action='store_true',
                       help='Check status of all collectors')
    parser.add_argument('--force', action='store_true',
                       help='Force all updates regardless of hash')
    parser.add_argument('--skip-rosters', action='store_true',
                       help='Skip rosters collection')
    parser.add_argument('--skip-rolling', action='store_true',
                       help='Skip rolling windows collection')
    parser.add_argument('--skip-statcast', action='store_true',
                       help='Skip Statcast collection')
    parser.add_argument('--only', choices=['rosters', 'rolling', 'statcast'],
                       help='Run only the specified collector')

    args = parser.parse_args()

    if args.status:
        needs_update = check_all_status()
        sys.exit(1 if needs_update else 0)
    else:
        # Build skip list
        skip_collectors = []
        if args.skip_rosters:
            skip_collectors.append('rosters')
        if args.skip_rolling:
            skip_collectors.append('rolling')
        if args.skip_statcast:
            skip_collectors.append('statcast')

        success = run_all_collections(
            force_update=args.force,
            skip_collectors=skip_collectors,
            only_collector=args.only
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
