#!/usr/bin/env python3
"""
CLI interface for data validation tool.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from win_calc.data_validator import run_validation_report, MLBDataValidator


def main():
    parser = argparse.ArgumentParser(description="Validate MLB data against official sources")
    parser.add_argument(
        "--players",
        nargs="+",
        help="Specific player IDs to validate (default: sample players)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all players in active rosters"
    )
    parser.add_argument(
        "--output",
        default="diagnostics/reports/output/win_calc/validation_report.json",
        help="Output path for validation report"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick validation (sample players only)"
    )

    args = parser.parse_args()

    if args.quick:
        # Quick validation with sample players
        sample_players = [
            "664040",  # Brandon Lowe
            "664285",  # Framber Valdez
            "622491",  # Luis Castillo
        ]
        player_ids = sample_players
    elif args.players:
        player_ids = args.players
    elif args.all:
        player_ids = None  # Will validate all players
    else:
        # Default to sample players
        sample_players = [
            "664040",  # Brandon Lowe
            "664285",  # Framber Valdez
            "622491",  # Luis Castillo
        ]
        player_ids = sample_players

    print("🔍 Starting MLB data validation...")
    print(f"   Players: {len(player_ids) if player_ids else 'All active players'}")
    print(f"   Output: {args.output}")
    print()

    try:
        report = run_validation_report(
            player_ids=player_ids,
            output_path=args.output
        )

        print(f"\n✅ Validation complete! Report saved to: {args.output}")

        # Exit with error code if there are critical errors
        if report["summary"]["error_count"] > 0:
            print(f"\n⚠️  Found {report['summary']['error_count']} errors - please review!")
            sys.exit(1)
        else:
            print(f"\n🎉 All validations passed!")
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ Validation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
