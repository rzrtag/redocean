#!/usr/bin/env python3
"""
Test Hash System

Verify that our hash-based incremental update system is working correctly.
"""

import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from fg_api.shared.hash_manager import FGHashManager
from fg_api.shared.config import fg_config


def test_hash_system():
    """Test the hash system with existing data."""
    print("🧪 Testing Hash System")
    print("=" * 40)
    
    # Initialize hash manager
    hash_manager = FGHashManager("roster")
    
    # Test with existing team data
    test_team = "TEX"
    test_level = "MLB"
    
    # Load existing data
    data_file = fg_config.get_collector_dir("roster") / fg_config.generate_filename(test_team, test_level)
    
    if not data_file.exists():
        print(f"❌ No data file found for {test_team} {test_level}")
        return False
    
    print(f"📁 Found data file: {data_file}")
    
    # Load the data
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    print(f"📊 Data loaded: {len(data.get('players', []))} players")
    
    # Test hash calculation
    data_hash = hash_manager.calculate_data_hash(data)
    print(f"🔐 Calculated hash: {data_hash}")
    
    # Test hash loading
    existing_hash_data = hash_manager.load_hash(test_team, test_level)
    if existing_hash_data:
        existing_hash = existing_hash_data.get('data_hash')
        print(f"📋 Existing hash: {existing_hash}")
        
        # Test hash comparison
        if data_hash == existing_hash:
            print("✅ Hash comparison: MATCH (data unchanged)")
            return True
        else:
            print("⚠️ Hash comparison: MISMATCH (data changed)")
            return False
    else:
        print("❌ No existing hash found")
        return False


def test_hash_stability():
    """Test that hash calculation is stable (same data = same hash)."""
    print("\n🧪 Testing Hash Stability")
    print("=" * 40)
    
    hash_manager = FGHashManager("roster")
    
    # Create test data
    test_data = {
        'team_abbr': 'TEST',
        'level': 'MLB',
        'players': [
            {'name': 'Player 1', 'position': 'P', 'stats': {'era': 3.50}},
            {'name': 'Player 2', 'position': 'C', 'stats': {'avg': 0.280}}
        ]
    }
    
    # Calculate hash multiple times
    hash1 = hash_manager.calculate_data_hash(test_data)
    hash2 = hash_manager.calculate_data_hash(test_data)
    hash3 = hash_manager.calculate_data_hash(test_data)
    
    print(f"🔐 Hash 1: {hash1}")
    print(f"🔐 Hash 2: {hash2}")
    print(f"🔐 Hash 3: {hash3}")
    
    if hash1 == hash2 == hash3:
        print("✅ Hash stability: PASSED (consistent hashing)")
        return True
    else:
        print("❌ Hash stability: FAILED (inconsistent hashing)")
        return False


def main():
    """Run all hash system tests."""
    print("🚀 Fangraphs Hash System Test Suite")
    print("=" * 50)
    
    # Test 1: Hash system with existing data
    test1_passed = test_hash_system()
    
    # Test 2: Hash stability
    test2_passed = test_hash_stability()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    print(f"Hash System Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Hash Stability Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Hash system is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Hash system needs attention.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
