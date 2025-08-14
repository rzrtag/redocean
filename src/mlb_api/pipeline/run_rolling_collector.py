#!/usr/bin/env python3
"""
Production Rolling Windows Collector Runner

Runs rolling windows data collection with the new Baseball Savant JSON endpoints.

Usage:
    python run_rolling_collector.py              # Collect all active players
    python run_rolling_collector.py --status     # Check collection status
    python run_rolling_collector.py --force      # Force full update
    python run_rolling_collector.py --workers 16 # Use 16 concurrent workers
"""

import sys
import argparse
import time
import logging
import json
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from mlb_api.rolling_windows.core.collector import EnhancedRollingCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_active_players():
    """Get list of active players from rosters (includes recently activated players)."""
    try:
        rosters_file = Path("_data/mlb_api_2025/active_rosters/data/active_rosters.json")
        if not rosters_file.exists():
            logger.warning("No active rosters found, using sample players")
            return [("670242", "hitter"), ("677951", "hitter"), ("624413", "hitter")]

        with open(rosters_file, 'r') as f:
            data = json.load(f)

        players = []
        for team_data in data.get('rosters', {}).values():
            team_roster = team_data.get('roster', [])
            for player in team_roster:
                player_id = str(player.get('id'))
                position = player.get('primaryPosition', {})
                position_type = position.get('type', 'Unknown')

                # Determine player type
                if position_type == 'Pitcher':
                    player_type = 'pitcher'
                else:
                    player_type = 'hitter'

                players.append((player_id, player_type))

        logger.info(f"Found {len(players)} active roster players (including recently activated)")
        return players

    except Exception as e:
        logger.error(f"Error loading Statcast BBE players: {e}")
        # Fallback to active rosters if Statcast data not available
        try:
            rosters_file = Path("_data/mlb_api_2025/active_rosters/data/active_rosters.json")
            if rosters_file.exists():
                with open(rosters_file, 'r') as f:
                    data = json.load(f)

                players = []
                for team_data in data.get('rosters', {}).values():
                    team_roster = team_data.get('roster', [])
                    for player in team_roster:
                        player_id = str(player.get('id'))
                        position = player.get('primaryPosition', {})
                        position_type = position.get('type', 'Unknown')

                        if position_type == 'Pitcher':
                            player_type = 'pitcher'
                        else:
                            player_type = 'hitter'

                        players.append((player_id, player_type))

                logger.info(f"Fallback: Found {len(players)} active roster players")
                return players
        except Exception as e2:
            logger.error(f"Fallback also failed: {e2}")

        return [("670242", "hitter"), ("677951", "hitter"), ("624413", "hitter")]


def cleanup_empty_files():
    """Remove rolling windows files with no actual data."""
    data_dir = Path("_data/mlb_api_2025/rolling_windows")
    hitters_dir = data_dir / "data" / "hitters"
    pitchers_dir = data_dir / "data" / "pitchers"

    removed = 0
    kept = 0

    # Clean hitters
    if hitters_dir.exists():
        for file_path in hitters_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Check if player has actual rolling windows data
                has_data = False
                for window_size in ['50', '100', '250']:
                    if len(data.get('rolling_windows', {}).get(window_size, {}).get('series', [])) > 0:
                        has_data = True
                        break

                if not has_data:
                    file_path.unlink()
                    removed += 1
                else:
                    kept += 1

            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")

    # Clean pitchers
    if pitchers_dir.exists():
        for file_path in pitchers_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Check if player has actual rolling windows data
                has_data = False
                for window_size in ['50', '100', '250']:
                    if len(data.get('rolling_windows', {}).get(window_size, {}).get('series', [])) > 0:
                        has_data = True
                        break

                if not has_data:
                    file_path.unlink()
                    removed += 1
                else:
                    kept += 1

            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")

    return {"removed": removed, "kept": kept}


def check_status():
    """Check rolling windows collection status."""
    print("🔍 Rolling Windows Status Check...")

    data_dir = Path("_data/mlb_api_2025/rolling_windows")
    hitters_dir = data_dir / "data" / "hitters"
    pitchers_dir = data_dir / "data" / "pitchers"

    hitters_count = len(list(hitters_dir.glob("*.json"))) if hitters_dir.exists() else 0
    pitchers_count = len(list(pitchers_dir.glob("*.json"))) if pitchers_dir.exists() else 0
    total_files = hitters_count + pitchers_count

    print(f"📊 Current Data:")
    print(f"   Hitters: {hitters_count} files")
    print(f"   Pitchers: {pitchers_count} files")
    print(f"   Total: {total_files} files")

    # Get active players count for comparison
    active_players = get_active_players()
    print(f"🎯 Active Players: {len(active_players)}")

    if total_files == 0:
        print("❌ No data collected yet - full collection needed")
        return True
    elif total_files < len(active_players) * 0.8:  # Less than 80% coverage
        print("⚠️ Incomplete data - collection needed")
        return True
    else:
        print("✅ Data appears complete")
        return False


def run_collection(force_update=False, max_workers=16):
    """Run rolling windows collection."""
    start_time = time.time()

    print(f"🚀 Rolling Windows Collection - {'FORCED' if force_update else 'STANDARD'}")
    print(f"⚡ Super Aggressive Mode: {max_workers} workers")

    try:
        # Initialize collector with super aggressive profile
        collector = EnhancedRollingCollector(
            data_dir="_data/mlb_api_2025/rolling_windows",
            performance_profile='super_aggressive'
        )

        # Get active players
        active_players = get_active_players()
        player_ids = [p[0] for p in active_players]
        player_types = list(set([p[1] for p in active_players]))

        print(f"📊 Collecting data for {len(player_ids)} players...")
        print(f"🎯 Player types: {player_types}")

        # Run collection
        results = collector.collect_all_players(player_ids, player_types)

        execution_time = time.time() - start_time

        # Display results
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

        # Clean up empty files (players with no recent data)
        print("🧹 Cleaning up empty files...")
        cleanup_results = cleanup_empty_files()
        print(f"   📁 Removed {cleanup_results['removed']} empty files")
        print(f"   📊 Kept {cleanup_results['kept']} files with data")

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
