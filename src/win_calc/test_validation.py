#!/usr/bin/env python3
"""
Test script for data validation tool.
"""

import json
from pathlib import Path
from win_calc.data_validator import MLBDataValidator, ValidationResult


def test_validation_workflow():
    """Test the validation workflow with sample data."""

    print("🧪 Testing Data Validation Workflow")
    print("=" * 50)

    # Test with sample players
    test_players = [
        ("664040", "Brandon Lowe", "TB", "batter"),
        ("664285", "Framber Valdez", "HOU", "pitcher"),
    ]

    validator = MLBDataValidator()

    for player_id, name, team, role in test_players:
        print(f"\n🔍 Validating {name} ({team}) - {role}")
        print("-" * 40)

        # Test MLB stats validation
        mlb_results = validator.validate_player_stats(player_id, name, team)
        print(f"MLB Stats validation: {len(mlb_results)} checks")
        for result in mlb_results:
            status = "✅" if result.is_valid else "❌"
            print(f"  {status} {result.check_type}: {result.message}")

        # Test Statcast validation
        statcast_results = validator.validate_statcast_data(player_id, name, team)
        print(f"Statcast validation: {len(statcast_results)} checks")
        for result in statcast_results:
            status = "✅" if result.is_valid else "❌"
            print(f"  {status} {result.check_type}: {result.message}")

    print(f"\n✅ Validation workflow test complete!")


def test_enhanced_adjuster_validation():
    """Test validation specifically for enhanced adjuster data."""

    print("\n🔧 Testing Enhanced Adjuster Data Validation")
    print("=" * 50)

    # Load test data from win calc pipeline
    test_data_path = Path("_data/sabersim_2025/fanduel/0815_main_slate/win_calc/adj_fd_batters.json")

    if not test_data_path.exists():
        print("❌ No test data found. Run win calc pipeline first.")
        return

    with open(test_data_path, 'r') as f:
        batters_data = json.load(f)

    batters = batters_data.get('batters', [])
    print(f"Found {len(batters)} batters in test data")

    # Check data quality
    enhanced_adjustments = 0
    total_adjustments = 0

    for batter in batters:
        base_proj = batter.get('my_proj', 0)
        adj_proj = batter.get('my_proj_adj')

        if adj_proj and adj_proj != base_proj:
            total_adjustments += 1
            if 'enhanced_signal' in batter:
                enhanced_adjustments += 1

    print(f"Total adjustments: {total_adjustments}")
    print(f"Enhanced adjustments: {enhanced_adjustments}")
    print(f"Enhanced coverage: {enhanced_adjustments/total_adjustments*100:.1f}%" if total_adjustments > 0 else "No adjustments found")

    # Validate a few specific players
    validator = MLBDataValidator()

    for i, batter in enumerate(batters[:3]):  # Test first 3 batters
        name = batter.get('name', 'Unknown')
        team = batter.get('team', 'Unknown')

        print(f"\n🔍 Validating {name} ({team})")

        # Find MLB ID (this would need roster lookup in real implementation)
        # For now, just show the adjustment data
        base_proj = batter.get('my_proj', 0)
        adj_proj = batter.get('my_proj_adj')
        enhanced_signal = batter.get('enhanced_signal')

        if adj_proj and adj_proj != base_proj:
            delta = adj_proj - base_proj
            print(f"  Base projection: {base_proj:.2f}")
            print(f"  Adjusted projection: {adj_proj:.2f}")
            print(f"  Adjustment: {delta:+.2f}")
            if enhanced_signal:
                print(f"  Enhanced signal: {enhanced_signal:.3f}")
        else:
            print(f"  No adjustment applied")


if __name__ == "__main__":
    test_validation_workflow()
    test_enhanced_adjuster_validation()
