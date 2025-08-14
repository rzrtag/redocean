#!/usr/bin/env python3
"""
Test Baseball Savant Histogram API
"""

import requests
import time
import csv
from io import StringIO

def test_histogram_api():
    """Test the Baseball Savant histogram API endpoints."""
    
    base_url = "https://baseballsavant.mlb.com/statcast_search/csv"
    player_id = "677951"  # Bobby Witt Jr.
    
    print(f"🧪 Testing Baseball Savant histogram API for player {player_id}")
    
    # Test exit velocity histogram
    print("\n1. Testing Exit Velocity Histogram...")
    params_ev = {
        'all': 'true',
        'hfPT': '',
        'hfAB': '',
        'hfBBT': '',
        'hfPR': '',
        'hfZ': '',
        'stadium': '',
        'hfBBL': '',
        'hfNewZones': '',
        'hfGT': 'R%7C',
        'hfC': '',
        'hfSea': '2025%7C',
        'hfSit': '',
        'player_type': 'batter',
        'hfOuts': '',
        'opponent': '',
        'pitcher_throws': '',
        'batter_stands': '',
        'hfSA': '',
        'game_date_gt': '2025-03-01',
        'game_date_lt': '2025-12-01',
        'hfInfield': '',
        'team': '',
        'position': '',
        'hfOutfield': '',
        'hfRO': '',
        'home_road': '',
        'batters_lookup[]': player_id,
        'type': 'details',
        'rolling_window': '50',
        'hfEV': 'true'  # Exit velocity filter
    }
    
    try:
        response = requests.get(base_url, params=params_ev, timeout=30)
        response.raise_for_status()
        print(f"✅ Exit Velocity API Response: {len(response.text)} characters")
        print(f"   First 200 chars: {response.text[:200]}")
        
        # Parse CSV
        if response.text.strip():
            csv_reader = csv.DictReader(StringIO(response.text))
            rows = list(csv_reader)
            print(f"   CSV rows: {len(rows)}")
            if rows:
                print(f"   Headers: {list(rows[0].keys())}")
                print(f"   Sample row: {dict(list(rows[0].items())[:5])}")
        else:
            print("   ❌ Empty response")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    time.sleep(1)
    
    # Test launch angle histogram
    print("\n2. Testing Launch Angle Histogram...")
    params_la = params_ev.copy()
    params_la['hfLA'] = 'true'  # Launch angle filter
    params_la.pop('hfEV', None)
    
    try:
        response = requests.get(base_url, params=params_la, timeout=30)
        response.raise_for_status()
        print(f"✅ Launch Angle API Response: {len(response.text)} characters")
        print(f"   First 200 chars: {response.text[:200]}")
        
        if response.text.strip():
            csv_reader = csv.DictReader(StringIO(response.text))
            rows = list(csv_reader)
            print(f"   CSV rows: {len(rows)}")
            if rows:
                print(f"   Headers: {list(rows[0].keys())}")
                print(f"   Sample row: {dict(list(rows[0].items())[:5])}")
        else:
            print("   ❌ Empty response")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    time.sleep(1)
    
    # Test pitch speed histogram
    print("\n3. Testing Pitch Speed Histogram...")
    params_ps = params_ev.copy()
    params_ps['hfSP'] = 'true'  # Pitch speed filter
    params_ps.pop('hfEV', None)
    
    try:
        response = requests.get(base_url, params=params_ps, timeout=30)
        response.raise_for_status()
        print(f"✅ Pitch Speed API Response: {len(response.text)} characters")
        print(f"   First 200 chars: {response.text[:200]}")
        
        if response.text.strip():
            csv_reader = csv.DictReader(StringIO(response.text))
            rows = list(csv_reader)
            print(f"   CSV rows: {len(rows)}")
            if rows:
                print(f"   Headers: {list(rows[0].keys())}")
                print(f"   Sample row: {dict(list(rows[0].items())[:5])}")
        else:
            print("   ❌ Empty response")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_histogram_api()
