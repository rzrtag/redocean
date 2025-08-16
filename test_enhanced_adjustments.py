#!/usr/bin/env python3
"""
Test script to compare old vs enhanced adjustment methods.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from win_calc.rolling_adjuster import adjust_records
from win_calc.enhanced_rolling_adjuster import adjust_records_enhanced
import json

def load_test_data():
    """Load sample data for testing."""
    # Load recent win calc data
    batters_path = Path("_data/sabersim_2025/fanduel/0815_main_slate/win_calc/adj_fd_batters.json")
    pitchers_path = Path("_data/sabersim_2025/fanduel/0815_main_slate/win_calc/adj_fd_pitchers.json")

    if not batters_path.exists() or not pitchers_path.exists():
        print("❌ No test data found. Run win calc pipeline first.")
        return None, None

    with open(batters_path, 'r') as f:
        batters_data = json.load(f)

    with open(pitchers_path, 'r') as f:
        pitchers_data = json.load(f)

    return batters_data.get('batters', []), pitchers_data.get('pitchers', [])

def compare_adjustments():
    """Compare old vs enhanced adjustment methods."""
    print("🔍 Loading test data...")
    batters, pitchers = load_test_data()

    if not batters or not pitchers:
        print("❌ No test data available")
        return

    print(f"📊 Testing with {len(batters)} batters and {len(pitchers)} pitchers")

    # Test old method
    print("\n🔄 Testing OLD adjustment method...")
    old_batters, old_pitchers = adjust_records(
        site="fanduel",
        batters=batters.copy(),
        pitchers=pitchers.copy()
    )

    # Test enhanced method
    print("🚀 Testing ENHANCED adjustment method...")
    enhanced_batters, enhanced_pitchers = adjust_records_enhanced(
        site="fanduel",
        batters=batters.copy(),
        pitchers=pitchers.copy()
    )

    # Compare results
    print("\n📈 COMPARISON RESULTS:")
    print("=" * 80)

    # Analyze batters
    print("\n🏏 BATTERS:")
    print(f"{'Name':<20} {'Base':<8} {'Old Adj':<8} {'Old Delta':<8} {'Enhanced Adj':<12} {'Enhanced Delta':<12} {'Improvement':<12}")
    print("-" * 80)

    old_adjusted_count = 0
    enhanced_adjusted_count = 0
    total_old_delta = 0
    total_enhanced_delta = 0

    for i, (old_b, enhanced_b) in enumerate(zip(old_batters, enhanced_batters)):
        base_proj = old_b.get('my_proj', 0)

        # Old adjustment
        old_adj = old_b.get('my_proj_adj')
        old_delta = old_adj - base_proj if old_adj else 0
        if old_adj:
            old_adjusted_count += 1
            total_old_delta += abs(old_delta)

        # Enhanced adjustment
        enhanced_adj = enhanced_b.get('my_proj_adj')
        enhanced_delta = enhanced_adj - base_proj if enhanced_adj else 0
        if enhanced_adj:
            enhanced_adjusted_count += 1
            total_enhanced_delta += abs(enhanced_delta)

        # Show top 10 by enhanced delta
        if i < 10:
            name = old_b.get('name', 'Unknown')[:19]
            old_adj_display = old_adj if old_adj is not None else 0
            enhanced_adj_display = enhanced_adj if enhanced_adj is not None else 0
            improvement = enhanced_delta - old_delta if old_adj and enhanced_adj else 0
            print(f"{name:<20} {base_proj:<8.2f} {old_adj_display:<8.2f} {old_delta:<8.2f} {enhanced_adj_display:<12.2f} {enhanced_delta:<12.2f} {improvement:<12.2f}")

    # Analyze pitchers
    print("\n⚾ PITCHERS:")
    print(f"{'Name':<20} {'Base':<8} {'Old Adj':<8} {'Old Delta':<8} {'Enhanced Adj':<12} {'Enhanced Delta':<12} {'Improvement':<12}")
    print("-" * 80)

    for i, (old_p, enhanced_p) in enumerate(zip(old_pitchers, enhanced_pitchers)):
        base_proj = old_p.get('my_proj', 0)

        # Old adjustment
        old_adj = old_p.get('my_proj_adj')
        old_delta = old_adj - base_proj if old_adj else 0
        if old_adj:
            old_adjusted_count += 1
            total_old_delta += abs(old_delta)

        # Enhanced adjustment
        enhanced_adj = enhanced_p.get('my_proj_adj')
        enhanced_delta = enhanced_adj - base_proj if enhanced_adj else 0
        if enhanced_adj:
            enhanced_adjusted_count += 1
            total_enhanced_delta += abs(enhanced_delta)

        # Show top 10 by enhanced delta
        if i < 10:
            name = old_p.get('name', 'Unknown')[:19]
            old_adj_display = old_adj if old_adj is not None else 0
            enhanced_adj_display = enhanced_adj if enhanced_adj is not None else 0
            improvement = enhanced_delta - old_delta if old_adj and enhanced_adj else 0
            print(f"{name:<20} {base_proj:<8.2f} {old_adj_display:<8.2f} {old_delta:<8.2f} {enhanced_adj_display:<12.2f} {enhanced_delta:<12.2f} {improvement:<12.2f}")

    # Summary statistics
    print("\n📊 SUMMARY STATISTICS:")
    print("=" * 50)
    print(f"Players adjusted (old): {old_adjusted_count}")
    print(f"Players adjusted (enhanced): {enhanced_adjusted_count}")
    print(f"Average adjustment magnitude (old): {total_old_delta / old_adjusted_count:.2f} points")
    print(f"Average adjustment magnitude (enhanced): {total_enhanced_delta / enhanced_adjusted_count:.2f} points")
    if total_old_delta > 0:
        print(f"Magnitude improvement: {(total_enhanced_delta / enhanced_adjusted_count) / (total_old_delta / old_adjusted_count):.1f}x")
    else:
        print(f"Magnitude improvement: ∞x (old method had no adjustments)")

    # Find max adjustments
    max_old_delta = 0
    max_enhanced_delta = 0

    for old_b, enhanced_b in zip(old_batters, enhanced_batters):
        base_proj = old_b.get('my_proj', 0)
        old_adj = old_b.get('my_proj_adj')
        enhanced_adj = enhanced_b.get('my_proj_adj')

        if old_adj:
            old_delta = abs(old_adj - base_proj)
            max_old_delta = max(max_old_delta, old_delta)

        if enhanced_adj:
            enhanced_delta = abs(enhanced_adj - base_proj)
            max_enhanced_delta = max(max_enhanced_delta, enhanced_delta)

    for old_p, enhanced_p in zip(old_pitchers, enhanced_pitchers):
        base_proj = old_p.get('my_proj', 0)
        old_adj = old_p.get('my_proj_adj')
        enhanced_adj = enhanced_p.get('my_proj_adj')

        if old_adj:
            old_delta = abs(old_adj - base_proj)
            max_old_delta = max(max_old_delta, old_delta)

        if enhanced_adj:
            enhanced_delta = abs(enhanced_adj - base_proj)
            max_enhanced_delta = max(max_enhanced_delta, enhanced_delta)

    print(f"Maximum adjustment (old): {max_old_delta:.2f} points")
    print(f"Maximum adjustment (enhanced): {max_enhanced_delta:.2f} points")
    if max_old_delta > 0:
        print(f"Max improvement: {max_enhanced_delta / max_old_delta:.1f}x")
    else:
        print(f"Max improvement: ∞x (old method had no adjustments)")

if __name__ == "__main__":
    compare_adjustments()
