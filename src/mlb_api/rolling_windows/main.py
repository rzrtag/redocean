#!/usr/bin/env python3
"""
Rolling Windows System - Main Entry Point

Provides a unified interface for the rolling windows analysis system.
"""

import argparse
import logging
import sys
from pathlib import Path
import json

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from .core.collector import EnhancedRollingCollector
from .analysis.rolling_analyzer import RollingWindowsAnalyzer
from .analysis.enhanced_analyzer import EnhancedRollingAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def collect_data(args):
    """Collect rolling windows data."""
    print("🚀 Starting Enhanced Rolling Windows Collection...")

    collector = EnhancedRollingCollector(args.output_dir)

    if args.single_player:
        # Collect single player
        success = collector.collect_player(args.player_id, args.player_type)
        if success:
            print(f"✅ Successfully collected data for {args.player_type} {args.player_id}")
        else:
            print(f"❌ Failed to collect data for {args.player_type} {args.player_id}")
            sys.exit(1)
    else:
        # Collect all active players
        results = collector.collect_active_players(args.max_workers)
        print(f"\n📊 Collection Results:")
        print(f"✅ Success: {results['success']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"📊 Total API calls: {collector.stats['total_api_calls']}")
        print(f"🎯 Window sizes collected: {collector.stats['window_sizes_collected']}")


def analyze_data(args):
    """Analyze rolling windows data."""
    print("🔍 Starting Rolling Windows Analysis...")

    if args.analyzer_type == "basic":
        analyzer = RollingWindowsAnalyzer(args.data_dir)
    else:
        analyzer = EnhancedRollingAnalyzer(args.data_dir)

    if args.single_player:
        # Analyze single player
        analysis = analyzer.get_comprehensive_player_analysis(args.player_id, args.player_type)
        if analysis:
            print(f"📊 Analysis for {args.player_type} {args.player_id}:")
            print(json.dumps(analysis, indent=2, default=str))
        else:
            print(f"❌ No data found for {args.player_type} {args.player_id}")
            sys.exit(1)
    else:
        # Get data statistics
        stats = analyzer.get_data_statistics()
        print(f"📊 Data Statistics:")
        print(f"Total Hitters: {stats['total_hitters']}")
        print(f"Total Pitchers: {stats['total_pitchers']}")
        if 'data_quality_summary' in stats:
            print(f"Data Quality Summary:")
            for player_type, quality in stats['data_quality_summary'].items():
                print(f"  {player_type.capitalize()}: {quality['avg_completeness']:.2f} completeness")


def compare_players(args):
    """Compare multiple players."""
    print("⚖️  Starting Player Comparison...")

    analyzer = EnhancedRollingAnalyzer(args.data_dir)

    # Parse player IDs
    player_ids = [pid.strip() for pid in args.player_ids.split(',')]

    comparison = analyzer.compare_players(player_ids, args.player_type)

    print(f"📊 Comparison Results:")
    print(f"Players compared: {len(player_ids)}")

    if 'rankings' in comparison and 'xwoba' in comparison['rankings']:
        print(f"\n🏆 xwOBA Rankings:")
        for rank in comparison['rankings']['xwoba']:
            print(f"  {rank['rank']}. Player {rank['player_id']}: {rank['xwoba']:.3f}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Rolling Windows Analysis System')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect rolling windows data')
    collect_parser.add_argument('--output-dir', default='_data/rolling', help='Output directory')
    collect_parser.add_argument('--max-workers', type=int, default=5, help='Maximum concurrent workers')
    collect_parser.add_argument('--single-player', action='store_true', help='Collect single player only')
    collect_parser.add_argument('--player-id', help='Player ID for single player collection')
    collect_parser.add_argument('--player-type', choices=['hitter', 'pitcher'], default='hitter', help='Player type')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze rolling windows data')
    analyze_parser.add_argument('--data-dir', default='_data/rolling', help='Data directory')
    analyze_parser.add_argument('--analyzer-type', choices=['basic', 'enhanced'], default='enhanced', help='Analyzer type')
    analyze_parser.add_argument('--single-player', action='store_true', help='Analyze single player only')
    analyze_parser.add_argument('--player-id', help='Player ID for single player analysis')
    analyze_parser.add_argument('--player-type', choices=['hitter', 'pitcher'], default='hitter', help='Player type')

    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple players')
    compare_parser.add_argument('--data-dir', default='_data/rolling', help='Data directory')
    compare_parser.add_argument('--player-ids', required=True, help='Comma-separated list of player IDs')
    compare_parser.add_argument('--player-type', choices=['hitter', 'pitcher'], default='hitter', help='Player type')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'collect':
            collect_data(args)
        elif args.command == 'analyze':
            analyze_data(args)
        elif args.command == 'compare':
            compare_players(args)
    except Exception as e:
        logger.error(f"Error executing {args.command}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()