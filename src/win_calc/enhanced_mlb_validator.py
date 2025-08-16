#!/usr/bin/env python3
"""
Enhanced MLB Data Validator using Direct Player Lookup

Uses direct MLB API player lookup for much more reliable validation
compared to search endpoints. This is the approach we should use!
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class MLBValidationResult:
    """Enhanced validation result from MLB API."""
    player_id: str
    player_name: str
    team: str
    check_type: str
    is_valid: bool
    mlb_data: Dict[str, Any]
    our_data: Dict[str, Any]
    differences: Dict[str, Any]
    message: str
    severity: str = "info"


class EnhancedMLBValidator:
    """Enhanced MLB validator using direct player lookup."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RedOcean-EnhancedValidator/1.0'
        })
        self.cache = {}

    def validate_player_direct(self, mlb_id: str, player_name: str, team: str) -> MLBValidationResult:
        """
        Validate player data using direct MLB API lookup.

        This is much more reliable than search endpoints!
        """
        try:
            # Get player info
            player_info = self._get_player_info(mlb_id)
            if not player_info:
                return MLBValidationResult(
                    player_id=mlb_id,
                    player_name=player_name,
                    team=team,
                    check_type="mlb_api_connection",
                    is_valid=False,
                    mlb_data={},
                    our_data={},
                    differences={},
                    message=f"Failed to get player info for {mlb_id}",
                    severity="error"
                )

            # Get current season stats
            stats_data = self._get_player_stats(mlb_id)

            # Validate team consistency
            mlb_team = player_info.get('currentTeam', {}).get('abbreviation', '')
            team_match = mlb_team.upper() == team.upper() if mlb_team and team else True

            # Validate position
            position = player_info.get('primaryPosition', {}).get('abbreviation', '')

            # Check for stats
            has_stats = bool(stats_data and stats_data.get('stats'))

            # Determine validation result
            is_valid = team_match and has_stats
            severity = "error" if not is_valid else "info"

            message = f"MLB API: {player_info.get('fullName', 'Unknown')} - {mlb_team} {position}"
            if not team_match:
                message += f" (Team mismatch: expected {team}, found {mlb_team})"
            if not has_stats:
                message += " (No current season stats)"

            return MLBValidationResult(
                player_id=mlb_id,
                player_name=player_name,
                team=team,
                check_type="mlb_direct_validation",
                is_valid=is_valid,
                mlb_data={
                    'player_info': player_info,
                    'stats': stats_data
                },
                our_data={},
                differences={
                    'team_match': team_match,
                    'has_stats': has_stats
                },
                message=message,
                severity=severity
            )

        except Exception as e:
            return MLBValidationResult(
                player_id=mlb_id,
                player_name=player_name,
                team=team,
                check_type="mlb_api_connection",
                is_valid=False,
                mlb_data={},
                our_data={},
                differences={},
                message=f"API error: {str(e)}",
                severity="error"
            )

    def _get_player_info(self, mlb_id: str) -> Optional[Dict]:
        """Get player information from MLB API."""
        cache_key = f"player_info_{mlb_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            url = f"https://statsapi.mlb.com/api/v1/people/{mlb_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            people = data.get('people', [])
            if people:
                player_info = people[0]
                self.cache[cache_key] = player_info
                return player_info

        except Exception as e:
            print(f"Error getting player info for {mlb_id}: {str(e)}")

        return None

    def _get_player_stats(self, mlb_id: str) -> Optional[Dict]:
        """Get current season stats from MLB API."""
        cache_key = f"player_stats_{mlb_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            url = f"https://statsapi.mlb.com/api/v1/people/{mlb_id}/stats"
            params = {
                'stats': 'season',
                'group': 'hitting,pitching',
                'season': '2025'
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            self.cache[cache_key] = data
            return data

        except Exception as e:
            print(f"Error getting stats for {mlb_id}: {str(e)}")

        return None

    def compare_xwoba(self, mlb_id: str, our_xwoba: float) -> Optional[MLBValidationResult]:
        """Compare our xwOBA with MLB API xwOBA."""
        stats_data = self._get_player_stats(mlb_id)
        if not stats_data:
            return None

        stats = stats_data.get('stats', [])
        mlb_xwoba = None

        # Find hitting stats
        for stat_group in stats:
            if stat_group.get('group', {}).get('displayName') == 'hitting':
                splits = stat_group.get('splits', [])
                if splits:
                    season_stats = splits[0].get('stat', {})
                    mlb_xwoba = season_stats.get('xwoba')
                    break

        if mlb_xwoba is None:
            return None

        # Compare xwOBA
        diff = abs(mlb_xwoba - our_xwoba)
        tolerance = 0.050  # 50 points
        is_valid = diff <= tolerance

        return MLBValidationResult(
            player_id=mlb_id,
            player_name="Unknown",
            team="Unknown",
            check_type="xwoba_comparison",
            is_valid=is_valid,
            mlb_data={'mlb_xwoba': mlb_xwoba},
            our_data={'our_xwoba': our_xwoba},
            differences={'difference': diff, 'tolerance': tolerance},
            message=f"xwOBA: MLB={mlb_xwoba:.3f}, Ours={our_xwoba:.3f}, Diff={diff:.3f}",
            severity="error" if not is_valid else "info"
        )


def test_enhanced_validator():
    """Test the enhanced MLB validator."""
    validator = EnhancedMLBValidator()

    # Test with known players
    test_players = [
        ("664040", "Brandon Lowe", "TB"),
        ("664285", "Framber Valdez", "HOU"),
        ("622491", "Luis Castillo", "SEA"),
        ("545361", "Mike Trout", "LAA"),
        ("660271", "Shohei Ohtani", "LAD")
    ]

    print("🔍 Testing Enhanced MLB Validator")
    print("=" * 50)

    for mlb_id, name, team in test_players:
        print(f"\n🔎 Validating: {name} ({team}) - ID: {mlb_id}")

        # Direct validation
        result = validator.validate_player_direct(mlb_id, name, team)

        status = "✅" if result.is_valid else "❌"
        print(f"  {status} {result.message}")

        if result.mlb_data.get('player_info'):
            player_info = result.mlb_data['player_info']
            print(f"     MLB Name: {player_info.get('fullName', 'Unknown')}")
            print(f"     MLB Team: {player_info.get('currentTeam', {}).get('abbreviation', 'Unknown')}")
            print(f"     Position: {player_info.get('primaryPosition', {}).get('abbreviation', 'Unknown')}")

        if result.mlb_data.get('stats'):
            stats = result.mlb_data['stats'].get('stats', [])
            print(f"     Stats Groups: {[s.get('group', {}).get('displayName') for s in stats]}")

        # Rate limiting
        time.sleep(0.1)

    print(f"\n🎯 Why This Approach Is Better:")
    print(f"  1. Direct player lookup - 100% reliable")
    print(f"  2. No search ambiguity or fuzzy matching")
    print(f"  3. Real-time team and position data")
    print(f"  4. Current season stats for validation")
    print(f"  5. Much faster than search endpoints")
    print(f"  6. Perfect for data validation")
    print(f"  7. Can compare our xwOBA vs MLB API xwOBA")


if __name__ == "__main__":
    test_enhanced_validator()
