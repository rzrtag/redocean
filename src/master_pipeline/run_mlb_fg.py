#!/usr/bin/env python3
"""
Master Pipeline for Red Ocean Data Collection

Runs the core data collectors in the correct order:
1. MLB Rosters (active players)
2. Fangraphs Rosters (for verification)
3. MLB Statcast (comprehensive event data)
4. MLB Rolling Windows (aggregated stats)
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def run_mlb_rosters(force_update=False):
    """Run MLB API roster collection."""
    print("\n" + "="*60)
    print("🏟️  STEP 1: MLB ROSTERS COLLECTION")
    print("="*60)

    try:
        from mlb_api.rosters.rosters_collector import ActiveRostersCollector

        collector = ActiveRostersCollector()
        summary = collector.collect_all_teams(force_update=force_update)

        print(f"✅ MLB Rosters completed: {summary.get('total_players', 0)} players")
        return True

    except Exception as e:
        print(f"❌ MLB Rosters failed: {e}")
        return False

def run_fg_rosters(force_update=False):
    """Run Fangraphs roster collection."""
    print("\n" + "="*60)
    print("📊 STEP 2: FANGGRAPHS ROSTERS COLLECTION")
    print("="*60)

    try:
        from fg_api.pipeline.run_roster_collector import run_roster_collection

        summary = run_roster_collection(force_update=force_update)

        print(f"✅ Fangraphs Rosters completed: {summary.get('total_players', 0)} players")
        return True

    except Exception as e:
        print(f"❌ Fangraphs Rosters failed: {e}")
        return False

def run_mlb_statcast(force_update=False):
    """Run MLB Statcast collection."""
    print("\n" + "="*60)
    print("⚾ STEP 3: MLB STATCAST COLLECTION")
    print("="*60)

    try:
        from mlb_api.statcast_adv_box.statcast_collector import StatcastCollector

        collector = StatcastCollector()
        summary = collector.collect_all_data(force_update=force_update)

        print(f"✅ MLB Statcast completed: {summary.get('total_events', 0)} events")
        return True

    except Exception as e:
        print(f"❌ MLB Statcast failed: {e}")
        return False

def run_mlb_rolling_windows(force_update=False):
    """Run MLB Rolling Windows collection."""
    print("\n" + "="*60)
    print("📈 STEP 4: MLB ROLLING WINDOWS COLLECTION")
    print("="*60)

    try:
        from mlb_api.rolling_windows.main import run_rolling_windows_collection

        summary = run_rolling_windows_collection(force_update=force_update)

        print(f"✅ MLB Rolling Windows completed: {summary.get('total_players', 0)} players")
        return True

    except Exception as e:
        print(f"❌ MLB Rolling Windows failed: {e}")
        return False

def run_master_pipeline(force_update=False, steps=None):
    """Run the complete master pipeline."""
    start_time = time.time()

    print("🚀 RED OCEAN MASTER PIPELINE")
    print("="*60)
    print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔄 Force Update: {'Yes' if force_update else 'No'}")
    print(f"📋 Steps: {steps if steps else 'All'}")
    print("="*60)

    # Define pipeline steps
    pipeline_steps = [
        ("MLB Rosters", run_mlb_rosters),
        ("Fangraphs Rosters", run_fg_rosters),
        ("MLB Statcast", run_mlb_statcast),
        ("MLB Rolling Windows", run_mlb_rolling_windows)
    ]

    # Filter steps if specified
    if steps:
        pipeline_steps = [step for step in pipeline_steps if step[0] in steps]

    # Run pipeline
    results = {}
    for step_name, step_func in pipeline_steps:
        print(f"\n🔄 Running {step_name}...")
        step_start = time.time()

        success = step_func(force_update=force_update)
        results[step_name] = success

        step_time = time.time() - step_start
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status} - {step_name} completed in {step_time:.1f}s")

    # Summary
    total_time = time.time() - start_time
    successful_steps = sum(results.values())
    total_steps = len(results)

    print("\n" + "="*60)
    print("📊 MASTER PIPELINE SUMMARY")
    print("="*60)
    print(f"✅ Successful: {successful_steps}/{total_steps}")
    print(f"⏱️  Total Time: {total_time:.1f}s")
    print(f"🕒 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for step_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {step_name}")

    print("="*60)

    return results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Red Ocean Master Pipeline")
    parser.add_argument("--force", action="store_true", help="Force update all data")
    parser.add_argument("--steps", nargs="+", choices=["MLB Rosters", "Fangraphs Rosters", "MLB Statcast", "MLB Rolling Windows"],
                       help="Specific steps to run")

    args = parser.parse_args()

    try:
        results = run_master_pipeline(force_update=args.force, steps=args.steps)

        # Exit with error code if any step failed
        if not all(results.values()):
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
