#!/usr/bin/env python3
"""
Enhanced Statcast BBE Collector Runner

Runs Statcast BBE collection with super aggressive parallel collection.
Collects all players at once, then splits into hitter/pitcher after collection.

Usage:
    python run_enhanced_statcast_collector.py              # Collect all active players
    python run_enhanced_statcast_collector.py --status     # Check collection status
    python run_enhanced_statcast_collector.py --force      # Force full update
    python run_enhanced_statcast_collector.py --workers 16 # Use 16 concurrent workers
"""

import sys
import argparse
import time
import logging
import json
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

from mlb_api.statcast_adv_box.enhanced_statcast_collector import EnhancedStatcastCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_active_players():
    """Get list of active players from rosters."""
    try:
        rosters_file = Path("_data/mlb_api_2025/active_rosters/data/active_rosters.json")
        if not rosters_file.exists():
            logger.warning("No active rosters found, using sample players")
            return ["455117", "456781", "670242"]
        
        with open(rosters_file, 'r') as f:
            data = json.load(f)
        
        players = []
        for team_data in data.get('rosters', {}).values():
            team_roster = team_data.get('roster', [])
            for player in team_roster:
                player_id = str(player.get('id'))
                players.append(player_id)
        
        logger.info(f"Found {len(players)} active players")
        return players
        
    except Exception as e:
        logger.error(f"Error loading active players: {e}")
        return ["455117", "456781", "670242"]


def check_status():
    """Check Statcast collection status."""
    print("🔍 Enhanced Statcast Status Check...")
    
    data_dir = Path("_data/mlb_api_2025/statcast_adv_box")
    raw_dir = data_dir / "data" / "raw"
    batter_dir = data_dir / "data" / "batter"
    pitcher_dir = data_dir / "data" / "pitcher"
    
    raw_count = len(list(raw_dir.glob("*.json"))) if raw_dir.exists() else 0
    batter_count = len(list(batter_dir.glob("*.json"))) if batter_dir.exists() else 0
    pitcher_count = len(list(pitcher_dir.glob("*.json"))) if pitcher_dir.exists() else 0
    total_files = raw_count + batter_count + pitcher_count
    
    print(f"📊 Current Data:")
    print(f"   Raw files: {raw_count}")
    print(f"   Batter files: {batter_count}")
    print(f"   Pitcher files: {pitcher_count}")
    print(f"   Total: {total_files} files")
    
    active_players = get_active_players()
    print(f"🎯 Active Players: {len(active_players)}")
    
    if total_files == 0:
        print("❌ No data collected yet - full collection needed")
        return True
    elif total_files < len(active_players) * 0.8:
        print("⚠️ Incomplete data - collection needed")
        return True
    else:
        print("✅ Data appears complete")
        return False


def run_collection(force_update=False, max_workers=16):
    """Run enhanced Statcast collection."""
    start_time = time.time()

    print(f"🚀 Enhanced Statcast Collection - {'FORCED' if force_update else 'STANDARD'}")
    print(f"⚡ Super Aggressive Mode: {max_workers} workers")

    try:
        collector = EnhancedStatcastCollector(
            data_dir="_data/mlb_api_2025/statcast_adv_box",
            performance_profile='super_aggressive'
        )

        active_players = get_active_players()
        
        print(f"📊 Collecting data for {len(active_players)} players...")
        print(f"🎯 Collection method: Parallel player collection")

        # Step 1: Collect all players in parallel
        results = collector.collect_all_players(active_players)

        # Step 2: Split data into batter/pitcher directories
        print("🔄 Splitting data into batter/pitcher directories...")
        collector.split_data_by_type()

        execution_time = time.time() - start_time

        successful = len(results['success'])
        failed = len(results['failed'])
        skipped = len(results['skipped'])

        print(f"✅ Collection completed in {execution_time:.1f}s")
        print(f"📊 Results:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   ⏭️ Skipped: {skipped}")

        if failed > 0:
            print(f"❌ Failed players (first 5):")
            for failure in results['failed'][:5]:
                print(f"   {failure}")

        return True

    except KeyboardInterrupt:
        print("\n⏹️ Collection cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Collection failed: {e}")
        logger.exception("Enhanced Statcast collection error")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Enhanced Statcast Collector')
    parser.add_argument('--status', action='store_true',
                       help='Check status without running collection')
    parser.add_argument('--force', action='store_true',
                       help='Force full update regardless of existing data')
    parser.add_argument('--workers', type=int, default=16,
                       help='Number of concurrent workers (default: 16)')

    args = parser.parse_args()

    if args.status:
        needs_update = check_status()
        sys.exit(1 if needs_update else 0)
    else:
        success = run_collection(force_update=args.force, max_workers=args.workers)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
