#!/usr/bin/env python3
"""
Active Players Collector

Collects and manages active MLB player data.
"""

from typing import Dict, Any, List, Optional
from .rosters_collector import ActiveRostersCollector
from unidecode import unidecode


class ActivePlayersCollector:
    """Collects and manages active MLB player data."""

    def __init__(self, max_workers: int = 5, request_delay: float = 0.05):
        """Initialize the active players collector."""
        self.collector = ActiveRostersCollector(
            max_workers=max_workers,
            request_delay=request_delay
        )

    def get_active_players(self) -> List[Dict[str, Any]]:
        """Get all active MLB players."""
        roster_data = self.collector._collect_all_rosters()

        active_players = []
        for team_abbr, team_data in roster_data.get('rosters', {}).items():
            for player in team_data.get('roster', []):
                # Ensure ascii name fields exist for downstream matching
                if 'fullName_ascii' not in player and 'fullName' in player:
                    player['fullName_ascii'] = unidecode(player['fullName'])
                if 'firstName_ascii' not in player and 'firstName' in player:
                    player['firstName_ascii'] = unidecode(player['firstName'])
                if 'lastName_ascii' not in player and 'lastName' in player:
                    player['lastName_ascii'] = unidecode(player['lastName'])
                player['team_abbr'] = team_abbr
                active_players.append(player)

        return active_players

    def get_players_by_position(self, position: str) -> List[Dict[str, Any]]:
        """Get active players by position."""
        players = self.get_active_players()
        return [p for p in players if p['primaryPosition']['abbreviation'] == position]

    def get_players_by_team(self, team_abbr: str) -> List[Dict[str, Any]]:
        """Get active players by team abbreviation."""
        roster_data = self.collector._collect_all_rosters()
        team_data = roster_data.get('rosters', {}).get(team_abbr)

        if team_data:
            return team_data.get('roster', [])
        return []
