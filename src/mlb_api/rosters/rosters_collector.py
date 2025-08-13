#!/usr/bin/env python3
"""
MLB Active Rosters Collector

Collects current MLB team rosters and player data from the MLB API.
Uses shared components for incremental updates, hashing, and configuration.
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Union, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from shared.incremental_updater import MLBAPICollector
from shared.config import MLBConfig


class ActiveRostersCollector(MLBAPICollector):
    """Collects active MLB rosters with incremental update support using shared components."""

    def __init__(self, max_workers: int = 5, request_delay: float = 0.05):
        """Initialize the collector with shared configuration."""
        # Initialize shared configuration
        self.config = MLBConfig.from_env()

        # Initialize the parent MLBAPICollector
        super().__init__("active_rosters", str(self.config.base_data_path))

        # Set performance settings
        self.set_performance_settings(max_workers, request_delay)

        # API endpoints using shared configuration
        self.teams_endpoint = f"{self.config.mlb_api_base_url}/teams"
        self.roster_endpoint = f"{self.config.mlb_api_base_url}/teams/{{team_id}}/roster"

        # Ensure directories exist using shared configuration
        self.config.ensure_directories()

    def collect_data(self) -> Union[Dict, List]:
        """Implement the required collect_data method for MLBAPICollector."""
        print("📡 Collecting roster data...")

        # Start collection
        start_time = time.time()

        # Collect roster data
        roster_data = self._collect_all_rosters()

        # Add metadata
        collection_time = time.time() - start_time
        roster_data['metadata'] = {
            'collection_timestamp': datetime.now().isoformat(),
            'season': 2025,
            'total_teams': len(roster_data.get('teams', [])),
            'total_players': sum(len(team.get('roster', [])) for team in roster_data.get('rosters', {}).values()),
            'collector_version': '1.0.0',
            'collector_name': 'active_rosters',
            'performance': {
                'max_workers': self.max_workers,
                'request_delay': self.request_delay,
                'collection_time_seconds': collection_time
            }
        }

        return roster_data

    def _collect_all_rosters(self) -> Dict[str, Any]:
        """Collect rosters for all MLB teams."""
        print("🏟️  Collecting team information...")
        teams = self._collect_teams()

        print(f"👥 Collecting rosters for {len(teams)} teams...")
        rosters = self._collect_team_rosters(teams)

        # Build complete dataset
        data = {
            'teams': teams,
            'rosters': rosters,
            'summary': self._build_summary(teams, rosters)
        }

        return data

    def _collect_teams(self) -> List[Dict[str, Any]]:
        """Collect basic team information using shared API configuration."""
        try:
            response = requests.get(
                self.teams_endpoint,
                params={'sportId': 1},  # MLB sport ID
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            teams = data.get('teams', [])

            # Filter for active teams and add league/division info
            active_teams = []
            for team in teams:
                if team.get('active'):
                    team_info = {
                        'id': team['id'],
                        'name': team['name'],
                        'abbreviation': team['abbreviation'],
                        'league': {
                            'id': team['league']['id'],
                            'name': team['league']['name']
                        },
                        'division': {
                            'id': team['division']['id'],
                            'name': team['division']['name']
                        }
                    }
                    active_teams.append(team_info)

            return active_teams

        except Exception as e:
            print(f"❌ Error collecting teams: {e}")
            return []

    def _collect_team_rosters(self, teams: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect rosters for all teams using concurrent processing and shared rate limiting."""
        rosters = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all roster collection tasks
            future_to_team = {
                executor.submit(self._collect_single_roster, team): team
                for team in teams
            }

            # Process completed tasks
            for future in as_completed(future_to_team):
                team = future_to_team[future]
                try:
                    team_roster = future.result()
                    if team_roster:
                        rosters[team['abbreviation']] = team_roster
                        print(f"✅ {team['abbreviation']}: {len(team_roster.get('roster', []))} players")

                    # Respect rate limiting using shared configuration
                    time.sleep(self.request_delay)

                except Exception as e:
                    print(f"❌ Error collecting roster for {team['abbreviation']}: {e}")

        return rosters

    def _collect_single_roster(self, team: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Collect roster for a single team using shared API configuration."""
        try:
            team_id = team['id']
            response = requests.get(
                self.roster_endpoint.format(team_id=team_id),
                params={'rosterType': 'active'},  # Active roster only
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            roster_data = data.get('roster', [])

            # Process player data
            players = []
            for player in roster_data:
                # Handle different position data structures
                position_data = player.get('position', {})
                if not position_data:
                    # Try alternative position field
                    position_data = player.get('person', {}).get('position', {})

                # Extract position information safely
                position_code = position_data.get('code', '')
                position_name = position_data.get('name', '')
                position_type = position_data.get('type', '')
                position_abbr = position_data.get('abbreviation', '')

                # If position data is missing, try to infer from other fields
                if not position_code and 'position' in player:
                    # Handle case where position might be a string
                    pos_str = str(player.get('position', ''))
                    if pos_str:
                        position_abbr = pos_str
                        position_name = pos_str

                player_info = {
                    'id': player['person']['id'],
                    'fullName': player['person']['fullName'],
                    'firstName': player['person'].get('firstName', ''),
                    'lastName': player['person'].get('lastName', ''),
                    'primaryNumber': player.get('jerseyNumber', ''),
                    'birthDate': player['person'].get('birthDate', ''),
                    'height': player['person'].get('height', ''),
                    'weight': player['person'].get('weight', 0),
                    'primaryPosition': {
                        'code': position_code,
                        'name': position_name,
                        'type': position_type,
                        'abbreviation': position_abbr
                    },
                    'mlbDebutDate': player['person'].get('mlbDebutDate', ''),
                    'team_id': team['id'],
                    'team_name': team['name'],
                    'team_abbr': team['abbreviation'],
                    'league': team['league']['name'],
                    'division': team['division']['name']
                }
                players.append(player_info)

            return {
                'team_info': team,
                'roster': players
            }

        except Exception as e:
            print(f"❌ Error collecting roster for team {team['id']}: {e}")
            return None

    def _build_summary(self, teams: List[Dict[str, Any]], rosters: Dict[str, Any]) -> Dict[str, Any]:
        """Build summary statistics using shared data structures."""
        # Count players by position
        position_counts = {}
        team_counts = {}

        for team_abbr, team_data in rosters.items():
            team_counts[team_abbr] = len(team_data.get('roster', []))

            for player in team_data.get('roster', []):
                pos = player['primaryPosition']['abbreviation']
                position_counts[pos] = position_counts.get(pos, 0) + 1

        # Build league/division summaries
        leagues = {}
        divisions = {}

        for team in teams:
            league_name = team['league']['name']
            division_name = team['division']['name']

            if league_name not in leagues:
                leagues[league_name] = []
            leagues[league_name].append({
                'id': team['id'],
                'name': team['name'],
                'abbreviation': team['abbreviation']
            })

            if division_name not in divisions:
                divisions[division_name] = []
            divisions[division_name].append({
                'id': team['id'],
                'name': team['name'],
                'abbreviation': team['abbreviation']
            })

        return {
            'leagues': leagues,
            'divisions': divisions,
            'players_by_position': position_counts,
            'players_by_team': team_counts
        }

    def run_collection(self, force_update: bool = False) -> Tuple[bool, Union[Dict, List], str]:
        """Run the roster collection process using shared incremental update logic."""
        try:
            # Use the parent class's run_collection method
            was_updated, data, reason = super().run_collection(force_update)

            if was_updated:
                print(f"✅ Data updated: {reason}")
                print(f"📊 Collected {data['metadata']['total_players']} players from {data['metadata']['total_teams']} teams")

                # Show performance info
                performance = data['metadata'].get('performance', {})
                if performance:
                    print(f"⚡ Collection time: {performance.get('collection_time_seconds', 'N/A'):.2f} seconds")
                    print(f"⚡ Workers used: {performance.get('max_workers', 'N/A')}")
                    print(f"⚡ Request delay: {performance.get('request_delay', 'N/A')}s")
            else:
                print(f"ℹ️  No update needed: {reason}")

            return was_updated, data, reason

        except Exception as e:
            error_msg = f"Collection failed: {str(e)}"
            print(f"❌ {error_msg}")
            return False, None, error_msg

    def get_roster_summary(self) -> Dict[str, Any]:
        """Get a summary of the collected roster data using shared components."""
        try:
            # Get status using shared incremental updater
            status = self.get_status()

            # Try to load latest data file
            data_files = status.get('data_files', [])
            if not data_files:
                return {'error': 'No data files available'}

            # Load the most recent data file
            latest_file = Path(sorted(data_files)[-1])
            with open(latest_file, 'r') as f:
                data = json.load(f)

            metadata = data.get('metadata', {})

            return {
                'total_teams': metadata.get('total_teams'),
                'total_players': metadata.get('total_players'),
                'season': metadata.get('season'),
                'last_update': metadata.get('collection_timestamp'),
                'performance': metadata.get('performance', {})
            }

        except Exception as e:
            return {'error': str(e)}

    def force_update(self) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Force an update regardless of hash status using shared components."""
        return self.run_collection(force_update=True)
