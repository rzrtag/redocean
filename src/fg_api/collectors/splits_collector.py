#!/usr/bin/env python3
"""
Fangraphs Player Splits Collector

Collects detailed player splits data for active players from Fangraphs roster.
Uses player-based organization (MLB ID) to handle traded players correctly.
"""

import json
import time
import random
import requests
import urllib3
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Disable SSL warnings for Cloudflare bypass
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from ..shared.incremental_updater import FGIncrementalUpdater
from ..shared.config import fg_config


class FGSplitsCollector(FGIncrementalUpdater):
    """Collector for Fangraphs player splits data using player-based organization."""

    def __init__(self, performance_profile: str = 'stealth', max_workers: int = None):
        """Initialize splits collector."""
        super().__init__('splits', performance_profile, max_workers)

        # Base URL for splits API
        self.base_url = "https://www.fangraphs.com/_next/data/foRilIlBm_hTorbyeu3KF/players"

        # Initialize session for stealth
        self.session = requests.Session()
        self.session.verify = False
        self.session.trust_env = False

        # Set up stealth cookies
        self.session.cookies.update({
            '__qca': 'P1-c6b07ce3-6756-437b-b705-cef1b10bb0c3',
            'aym_t_S2S': 'on',
            'fg_uuid': '9b5d68ce-aba2-4568-8296-f996fcd5518a',
            '_ga': 'GA1.1.288863766.1755124920',
            '_ga_757YGY2LKP': 'GS2.1.s1755128591$o2$g1$t1755128832$j60$l0$h0'
        })

        # Set stealth headers
        self.session.headers.update({
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })

    def _get_stealth_headers(self, player_name: str) -> Dict[str, str]:
        """Get stealth headers for player splits request."""
        user_agents = [
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        ]

        headers = {
            'User-Agent': random.choice(user_agents),
            'Referer': f'https://www.fangraphs.com/players/{player_name}/splits-tool',
            'Priority': 'u=1, i',
            'If-None-Match': f'"{random.randint(1000000000000, 9999999999999)}"'
        }

        return headers

    def _stealth_delay(self):
        """Add random delay to mimic human behavior."""
        delay = random.uniform(0.01, 0.05)  # Much faster
        time.sleep(delay)

    def _is_pitcher(self, position: str) -> bool:
        """Check if player is a pitcher based on position."""
        if not position:
            return False

        # Common pitcher position codes
        pitcher_positions = ['P', 'SP', 'RP', 'CL', 'LHP', 'RHP']
        return any(pos in position.upper() for pos in pitcher_positions)

    def _sanitize_player_name_for_url(self, player_name: str) -> str:
        """Convert player name to URL-friendly format."""
        # Remove periods, replace spaces with hyphens, and convert to lowercase
        # Fangraphs playerNameRoute sometimes has periods that need to be removed
        clean_name = player_name.replace('.', '')  # Remove periods
        return clean_name.replace(' ', '-').lower()

    def _pre_request_setup(self, player_name: str):
        """Advanced pre-request setup to bypass Cloudflare."""
        try:
            # First, access the player page to establish session
            player_url = f'https://www.fangraphs.com/players/{player_name}/splits-tool'
            self.session.get(player_url, timeout=10, allow_redirects=True)
            time.sleep(random.uniform(0.1, 0.3))  # Much faster
        except Exception:
            pass  # Continue even if this fails

    def _check_player_needs_update(self, player_id: str, player_name_route: str, position: str) -> Tuple[bool, str]:
        """Check if a player's splits data needs updating based on hash."""
        from datetime import datetime

        # Create a unique identifier for this player's splits (just use MLB ID)
        player_key = f"{player_id}"

        # Check if we have existing splits file
        splits_file = self.data_dir / f"{player_id}.json"

        if not splits_file.exists():
            return True, "No existing splits file"

        # Check if hash file exists
        hash_file = self.hash_manager.get_hash_file_path(player_key, "splits")

        if not hash_file.exists():
            return True, "No hash file exists"

        # Check file age - if older than 24 hours, mark for update
        file_age_hours = (time.time() - splits_file.stat().st_mtime) / 3600
        if file_age_hours > 24:
            return True, f"File older than 24 hours ({file_age_hours:.1f}h)"

        return False, "Data is current"

    def _save_player_splits_with_hash(self, player_id: str, player_name_route: str, position: str, splits_data: Dict[str, Any]) -> None:
        """Save player splits data and update hash."""
        from datetime import datetime

        # Create splits data structure
        player_splits = {
            'player_id': player_id,
            'player_name_route': player_name_route,
            'position': position,
            'collection_timestamp': datetime.now().isoformat(),
            'splits': splits_data,
            'metadata': {
                'total_splits': len(splits_data),
                'split_types': [split.get('Split', '') for split in splits_data],
                'collection_method': 'player_based'
            }
        }

        # Save splits file
        splits_file = self.data_dir / f"{player_id}.json"
        with open(splits_file, 'w') as f:
            json.dump(player_splits, f, indent=2)

        # Calculate hash and save hash file
        player_key = f"{player_id}"
        data_hash = self.hash_manager.calculate_data_hash(player_splits)
        self.hash_manager.save_hash(player_key, "splits", data_hash, player_splits, str(splits_file))

    def collect_player_splits(self, player_id: str, player_name_route: str, position: str = '') -> Optional[Dict[str, Any]]:
        """Collect splits data for a single player with hash management."""
        try:
            # Check if we need to update this player's splits
            needs_update, reason = self._check_player_needs_update(player_id, player_name_route, position)

            if not needs_update:
                print(f"⏭️ Skipping {player_name_route} - {reason}")
                return {'skipped': True, 'reason': reason}

            # Advanced pre-request setup
            self._pre_request_setup(player_name_route)

            # Add stealth delay
            self._stealth_delay()

            # Build URL with Next.js dynamic route structure
            # Fangraphs uses Next.js with dynamic build IDs
            url = f"https://www.fangraphs.com/_next/data/foRilIlBm_hTorbyeu3KF/players/{player_name_route}/{player_id}/splits.json"

            # Build parameters
            params = {
                'position': position,
                'playerNameRoute': player_name_route,
                'playerId': player_id
            }

            # Get stealth headers
            headers = self._get_stealth_headers(player_name_route)

            # Retry mechanism with minimal retries
            max_retries = 2  # Only 2 attempts total
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, headers=headers, params=params, timeout=self.timeout)
                    response.raise_for_status()

                    data = response.json()
                    break  # Success, exit retry loop

                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Attempt {attempt + 1} failed for {player_name_route}, retrying...")
                        time.sleep(1)  # Just 1 second delay
                        continue
                    else:
                        raise Exception(f"API request failed for {player_name_route} after {max_retries} attempts: {e}")

            # Extract dataSplits from the response
            if 'pageProps' in data and 'dataSplits' in data['pageProps']:
                splits_data = data['pageProps']['dataSplits']
                # Filter for 2025 season and clean splits only
                filtered_splits = []
                for split in splits_data:
                    if split.get('Season') == '2025':
                        split_type = split.get('Split', '')
                        # Only keep clean splits: vs R, vs L, Home, Away (no "as L" or "as R" combinations)
                        if any(keyword in split_type for keyword in ['vs R', 'vs L', 'Home', 'Away']) and ' as ' not in split_type:
                            filtered_splits.append(split)

                # Save with hash management
                if filtered_splits:
                    self._save_player_splits_with_hash(player_id, player_name_route, position, filtered_splits)

                return filtered_splits
            elif 'dataSplits' in data:
                splits_data = data['dataSplits']
                # Apply same filtering
                filtered_splits = []
                for split in splits_data:
                    if split.get('Season') == '2025':
                        split_type = split.get('Split', '')
                        if any(keyword in split_type for keyword in ['vs R', 'vs L', 'Home', 'Away']) and ' as ' not in split_type:
                            filtered_splits.append(split)

                # Save with hash management
                if filtered_splits:
                    self._save_player_splits_with_hash(player_id, player_name_route, position, filtered_splits)

                return filtered_splits
            else:
                print(f"⚠️ No dataSplits found in response for {player_name_route}")
                return None

        except Exception as e:
            print(f"❌ Failed to collect splits for {player_name_route}: {e}")
            return None

    def collect_all_players_splits(self, force_update: bool = False) -> Dict[str, Any]:
        """Collect splits data for active MLB players only."""
        print("🚀 Starting player-based splits collection...")
        print("📊 This approach handles traded players correctly by collecting full-season data")
        print("🎯 Only collecting for ACTIVE players from MLB API")

        # Load active rosters from MLB API
        active_rosters_file = Path("_data/mlb_api_2025/active_rosters/data/active_rosters.json")

        if not active_rosters_file.exists():
            print("❌ No active rosters file found. Please run MLB API roster collection first.")
            return {}

        with open(active_rosters_file, 'r') as f:
            active_rosters_data = json.load(f)

        # Extract all active players from rosters
        all_active_players = []
        rosters = active_rosters_data.get('rosters', {})

        for team_abbr, team_data in rosters.items():
            roster = team_data.get('roster', [])

            for player in roster:
                player['source_team'] = team_abbr
                all_active_players.append(player)

        print(f"📋 Found {len(all_active_players)} total active players")

        # Filter for hitters only (exclude pitchers)
        active_hitters = []
        for player in all_active_players:
            position = player.get('primaryPosition', {})
            pos_code = position.get('code', '')
            pos_abbr = position.get('abbreviation', '')

            # Exclude pitchers (position code 1 or abbreviation P)
            if pos_code != '1' and pos_abbr != 'P':
                active_hitters.append(player)

        print(f"🎯 Active hitters found: {len(active_hitters)}")

        # Load Fangraphs roster data to get player details
        roster_dir = self.data_dir.parent / 'roster'
        roster_files = list(roster_dir.glob('*_MLB.json'))

        if not roster_files:
            print("❌ No Fangraphs roster files found. Please run roster collection first.")
            return {}

        # Create lookup for Fangraphs player data by MLB ID
        fg_players_lookup = {}
        for roster_file in roster_files:
            try:
                with open(roster_file, 'r') as f:
                    roster_data = json.load(f)

                players = roster_data.get('players', [])
                for player in players:
                    mlb_id = player.get('mlbamid')
                    if mlb_id:
                        fg_players_lookup[mlb_id] = player

            except Exception as e:
                print(f"⚠️ Error reading {roster_file}: {e}")
                continue

        print(f"📊 Fangraphs player lookup created: {len(fg_players_lookup)} players")

        # Create player-based data structure
        collection_data = {
            'collection_timestamp': time.time(),
            'collection_method': 'active_player_based_splits',
            'total_players': len(active_hitters),
            'players_with_splits': 0,
            'total_splits': 0,
            'players': []
        }

        # Collect splits for each active hitter
        for i, player in enumerate(active_hitters, 1):
            mlb_id = player.get('id')
            player_name = player.get('fullName', 'Unknown')
            position = player.get('primaryPosition', {}).get('abbreviation', '')

            if not mlb_id:
                print(f"⚠️ Skipping player {player_name} - missing MLB ID")
                continue

                        # Get Fangraphs data for this player
            fg_player = fg_players_lookup.get(mlb_id)

            if not fg_player:
                print(f"⚠️ Skipping {player_name} (MLB ID: {mlb_id}) - not found in Fangraphs data")
                continue

            player_id = fg_player.get('playerid')
            player_name_route = fg_player.get('playerNameRoute')

            if not player_id or not player_name_route:
                print(f"⚠️ Skipping {player_name} - missing Fangraphs data")
                continue

            # Convert player name route to URL-friendly format
            player_name_route_url = self._sanitize_player_name_for_url(player_name_route)

            print(f"🔄 [{i}/{len(active_hitters)}] Collecting splits for {player_name} (MLB ID: {mlb_id})...")

            # Check if we already have this player's data (hash-based incremental update)
            player_file = self.data_dir / f"{mlb_id}.json"

            if not force_update and player_file.exists():
                try:
                    with open(player_file, 'r') as f:
                        existing_data = json.load(f)

                    # Check if data is recent (within 24 hours)
                    if time.time() - existing_data.get('collection_timestamp', 0) < 86400:
                        print(f"✅ Skipping {player_name} - recent data exists")
                        collection_data['players'].append(existing_data)
                        collection_data['players_with_splits'] += 1
                        collection_data['total_splits'] += len(existing_data.get('splits', []))
                        continue
                except Exception:
                    pass  # Continue to collect fresh data

            # Collect player splits (now includes hash management)
            splits_data = self.collect_player_splits(str(player_id), player_name_route_url, position)

            if splits_data and not isinstance(splits_data, dict) or not splits_data.get('skipped'):
                # Create player data structure
                player_data = {
                    'mlb_id': mlb_id,
                    'player_id': player_id,
                    'player_name': player_name,
                    'player_name_route': player_name_route,
                    'position': position,
                    'current_team': player.get('team_abbr'),
                    'source_team': player.get('source_team'),
                    'collection_timestamp': time.time(),
                    'splits': splits_data
                }

                # Save individual player file (hash already managed in collect_player_splits)
                with open(player_file, 'w') as f:
                    json.dump(player_data, f, indent=2)

                # Add to collection data
                collection_data['players'].append(player_data)
                collection_data['players_with_splits'] += 1
                collection_data['total_splits'] += len(splits_data)
                collection_data['collection_timestamp'] = time.time()

                print(f"✅ Saved splits for {player_name} ({len(splits_data)} splits)")
            else:
                print(f"⚠️ No splits data for {player_name}")

            # Add minimal delay between players
            time.sleep(0.1)  # Much faster

        # Save collection summary
        summary_file = self.data_dir / "splits_collection_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(collection_data, f, indent=2)

        print(f"\n✅ Active player-based splits collection completed!")
        print(f"📈 Results: {collection_data['players_with_splits']} players with splits")
        print(f"📊 Total splits collected: {collection_data['total_splits']}")
        print(f"💾 Data saved to: {self.data_dir}")

        return collection_data

    def collect_team_data(self, team_abbr: str, level: str = 'MLB') -> List[Dict[str, Any]]:
        """Legacy team-based collection method - now redirects to player-based collection."""
        print(f"⚠️ Team-based collection is deprecated. Use player-based collection instead.")
        print(f"🔄 Redirecting to player-based collection for {team_abbr}...")
        return self.collect_all_players_splits()

    def collect_all_teams_efficient(self, teams: List[str] = None, levels: List[str] = None,
                                   force_update: bool = False) -> Dict[str, Any]:
        """Efficient collection using player-based approach."""
        return self.collect_all_players_splits(force_update=force_update)

    def process_team_data(self, team_abbr: str, level: str,
                         raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process team splits data with enhanced metadata."""
        # This method is now deprecated in favor of player-based processing
        return {
            'team_abbr': team_abbr,
            'level': level,
            'collection_timestamp': time.time(),
            'players': raw_data,
            'metadata': {
                'total_players': len(raw_data),
                'players_with_splits': len([p for p in raw_data if p.get('splits')]),
                'total_splits': sum(len(p.get('splits', [])) for p in raw_data),
                'collection_method': 'player_based_splits',
                'note': 'Legacy team-based processing - consider using player-based approach'
            }
        }
