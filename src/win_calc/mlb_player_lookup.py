#!/usr/bin/env python3
"""
MLB Player Lookup using MLB API Search Endpoint

A much simpler and more reliable way to find player IDs compared to
maintaining roster files. Uses the official MLB API search endpoint.
"""

import requests
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PlayerInfo:
    """Player information from MLB API."""
    mlb_id: str
    full_name: str
    team: str
    position: str
    confidence: float  # How confident we are in the match


class MLBPlayerLookup:
    """Simple player lookup using MLB API search endpoint."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RedOcean-PlayerLookup/1.0'
        })
        self.cache = {}  # Simple cache to avoid repeated API calls

    def search_player(self, name: str, team: Optional[str] = None) -> Optional[PlayerInfo]:
        """
        Search for a player by name using MLB API.

        Args:
            name: Player name to search for
            team: Optional team abbreviation to help disambiguate

        Returns:
            PlayerInfo if found, None otherwise
        """
        # Check cache first
        cache_key = f"{name}_{team or 'any'}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Search MLB API
            url = "https://statsapi.mlb.com/api/v1/people/search"
            params = {'q': name}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            people = data.get('people', [])

            if not people:
                return None

            # Find the best match
            best_match = self._find_best_match(people, name, team)

            # Cache the result
            self.cache[cache_key] = best_match

            return best_match

        except Exception as e:
            print(f"Error searching for {name}: {str(e)}")
            return None

    def _find_best_match(self, people: List[Dict], search_name: str, team: Optional[str] = None) -> Optional[PlayerInfo]:
        """Find the best matching player from search results."""

        # Normalize search name
        search_name_lower = search_name.lower().strip()

        best_match = None
        best_score = 0

        for person in people:
            full_name = person.get('fullName', '')
            mlb_id = person.get('id')
            current_team = person.get('currentTeam', {}).get('abbreviation', '')
            position = person.get('primaryPosition', {}).get('abbreviation', '')

            if not full_name or not mlb_id:
                continue

            # Calculate match score
            score = self._calculate_match_score(
                search_name_lower,
                full_name.lower(),
                team,
                current_team
            )

            if score > best_score:
                best_score = score
                best_match = PlayerInfo(
                    mlb_id=str(mlb_id),
                    full_name=full_name,
                    team=current_team,
                    position=position,
                    confidence=score
                )

        return best_match

    def _calculate_match_score(self, search_name: str, full_name: str,
                              search_team: Optional[str], current_team: str) -> float:
        """Calculate how well a player matches our search criteria."""
        score = 0.0

        # Exact name match gets highest score
        if search_name == full_name:
            score += 100.0
        elif search_name in full_name or full_name in search_name:
            score += 80.0
        else:
            # Partial match
            search_words = set(search_name.split())
            full_words = set(full_name.split())
            common_words = search_words.intersection(full_words)
            if common_words:
                score += len(common_words) * 20.0

        # Team match bonus
        if search_team and current_team and search_team.upper() == current_team.upper():
            score += 50.0

        # Active player bonus (has current team)
        if current_team:
            score += 10.0

        return score

    def get_player_stats(self, mlb_id: str) -> Optional[Dict]:
        """Get current season stats for a player."""
        try:
            url = f"https://statsapi.mlb.com/api/v1/people/{mlb_id}/stats"
            params = {
                'stats': 'season',
                'group': 'hitting,pitching',
                'season': '2025'
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting stats for {mlb_id}: {str(e)}")
            return None

    def validate_player_data(self, name: str, team: Optional[str] = None) -> Dict:
        """
        Validate player data by searching MLB API and comparing with our data.

        Returns validation results including:
        - Player found in MLB API
        - Current team and position
        - Stats availability
        - Data consistency
        """
        result = {
            'player_found': False,
            'mlb_id': None,
            'current_team': None,
            'position': None,
            'stats_available': False,
            'validation_errors': [],
            'warnings': []
        }

        # Search for player
        player_info = self.search_player(name, team)

        if not player_info:
            result['validation_errors'].append(f"Player '{name}' not found in MLB API")
            return result

        result['player_found'] = True
        result['mlb_id'] = player_info.mlb_id
        result['current_team'] = player_info.team
        result['position'] = player_info.position

        # Check if team matches (if provided)
        if team and player_info.team and team.upper() != player_info.team.upper():
            result['warnings'].append(
                f"Team mismatch: Expected {team}, found {player_info.team}"
            )

        # Get stats
        stats_data = self.get_player_stats(player_info.mlb_id)
        if stats_data:
            result['stats_available'] = True
            stats = stats_data.get('stats', [])
            result['stat_groups'] = [s.get('group', {}).get('displayName') for s in stats]

        return result


def test_player_lookup():
    """Test the player lookup system."""
    lookup = MLBPlayerLookup()

    test_cases = [
        ("Brandon Lowe", "TB"),
        ("Framber Valdez", "HOU"),
        ("Luis Castillo", "SEA"),
        ("Mike Trout", "LAA"),
        ("Shohei Ohtani", "LAD")
    ]

    print("🔍 Testing MLB Player Lookup System")
    print("=" * 50)

    for name, team in test_cases:
        print(f"\n🔎 Looking up: {name} ({team})")

        # Search for player
        player_info = lookup.search_player(name, team)

        if player_info:
            print(f"  ✅ Found: {player_info.full_name}")
            print(f"     MLB ID: {player_info.mlb_id}")
            print(f"     Team: {player_info.team}")
            print(f"     Position: {player_info.position}")
            print(f"     Confidence: {player_info.confidence:.1f}")

            # Validate data
            validation = lookup.validate_player_data(name, team)
            if validation['warnings']:
                print(f"     ⚠️  Warnings: {validation['warnings']}")
            if validation['stats_available']:
                print(f"     📊 Stats: {validation['stat_groups']}")
        else:
            print(f"  ❌ Not found")

        # Rate limiting
        time.sleep(0.1)

    print(f"\n🎯 Benefits of This Approach:")
    print(f"  1. No roster file maintenance required")
    print(f"  2. Always up-to-date with current teams")
    print(f"  3. Handles player trades automatically")
    print(f"  4. Fuzzy matching for name variations")
    print(f"  5. Single API call gets everything")
    print(f"  6. Much simpler than our current approach")


if __name__ == "__main__":
    test_player_lookup()
