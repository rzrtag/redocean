#!/usr/bin/env python3
"""
Display a summary of the latest validation test results.
"""

import json
import glob
from pathlib import Path
from datetime import datetime


def get_latest_results():
    """Get the most recent validation results file."""
    test_dir = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/tests")
    result_files = list(test_dir.glob("validation_results_*.json"))
    
    if not result_files:
        return None
    
    # Get the most recent file
    latest_file = max(result_files, key=lambda f: f.stat().st_mtime)
    return latest_file


def display_summary():
    """Display a formatted summary of the test results."""
    results_file = get_latest_results()
    
    if not results_file:
        print("❌ No validation results found")
        return
    
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    print("📊 MLB API Data Validation Summary")
    print("=" * 50)
    print(f"📅 Test Date: {data['timestamp']}")
    print(f"⏱️  Execution Time: {data['total_execution_time']:.1f}s")
    print()
    
    # Overall summary
    summary = data['test_summary']
    issues = data['issues_summary']
    
    print("🎯 Overall Results:")
    print(f"   ✅ Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
    print(f"   📈 Success Rate: {summary['success_rate']:.1f}%")
    print(f"   ❌ Errors: {issues['total_errors']}")
    print(f"   ⚠️  Warnings: {issues['total_warnings']}")
    print()
    
    # Detailed results
    print("🔍 Detailed Test Results:")
    print("-" * 30)
    
    for result in data['detailed_results']:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status} {result['test_name']}")
        print(f"   ⏱️  Time: {result['execution_time']:.3f}s")
        
        if result['errors']:
            print(f"   ❌ Errors: {len(result['errors'])}")
            for error in result['errors']:
                print(f"      - {error}")
        
        if result['warnings']:
            print(f"   ⚠️  Warnings: {len(result['warnings'])}")
            for warning in result['warnings']:
                print(f"      - {warning}")
        
        # Show key details
        details = result['details']
        if 'teams_count' in details:
            print(f"   📊 Teams: {details['teams_count']}")
        if 'total_players' in details:
            print(f"   👥 Players: {details['total_players']}")
        if 'date_files_count' in details:
            print(f"   📅 Date Files: {details['date_files_count']}")
        if 'total_player_files' in details:
            print(f"   📁 Player Files: {details['total_player_files']}")
        if 'overlap_percentage' in details:
            print(f"   🔗 Player Overlap: {details['overlap_percentage']:.1f}%")
        
        print()
    
    # Data quality assessment
    print("📋 Data Quality Assessment:")
    print("-" * 30)
    
    roster_result = next((r for r in data['detailed_results'] if r['test_name'] == 'roster_data_validation'), None)
    rolling_result = next((r for r in data['detailed_results'] if r['test_name'] == 'rolling_data_validation'), None)
    cross_result = next((r for r in data['detailed_results'] if r['test_name'] == 'cross_references'), None)
    
    if roster_result and rolling_result and cross_result:
        roster_players = roster_result['details'].get('total_players', 0)
        rolling_players = rolling_result['details'].get('total_player_files', 0)
        overlap = cross_result['details'].get('overlap_percentage', 0)
        
        print(f"   🏟️  MLB Teams: {roster_result['details'].get('teams_count', 0)}/30")
        print(f"   👥 Active Players: {roster_players}")
        print(f"   📊 Rolling Data Files: {rolling_players}")
        print(f"   🔗 Data Consistency: {overlap:.1f}% overlap")
        
        if overlap >= 95:
            print("   🎉 Excellent data consistency!")
        elif overlap >= 80:
            print("   ✅ Good data consistency")
        else:
            print("   ⚠️  Data consistency needs attention")
    
    print(f"\n📁 Results saved to: {results_file}")


if __name__ == "__main__":
    display_summary()
