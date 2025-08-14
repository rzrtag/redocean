#!/usr/bin/env python3
"""
Enhanced Statcast BBE Collector

Uses super aggressive parallel collection like rolling windows collector.
Collects all players at once, then splits into hitter/pitcher after collection.
"""

import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import requests

sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class StatcastConfig:
    """Configuration for Statcast BBE collection"""
    max_workers: int = 16
    request_delay: float = 0.1
    timeout: int = 30
    retry_attempts: int = 3

class EnhancedStatcastCollector:
    """Enhanced Statcast BBE collector using super aggressive parallel collection"""
    
    def __init__(self, data_dir: Path, performance_profile: str = "super_aggressive"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "data" / "raw"
        self.batter_dir = self.data_dir / "data" / "batter"
        self.pitcher_dir = self.data_dir / "data" / "pitcher"
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.batter_dir.mkdir(parents=True, exist_ok=True)
        self.pitcher_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance profiles
        profiles = {
            "conservative": StatcastConfig(max_workers=4, request_delay=1.0),
            "balanced": StatcastConfig(max_workers=8, request_delay=0.5),
            "aggressive": StatcastConfig(max_workers=12, request_delay=0.2),
            "super_aggressive": StatcastConfig(max_workers=16, request_delay=0.1)
        }
        self.config = profiles.get(performance_profile, profiles["balanced"])
        
        # Baseball Savant game feed endpoint
        self.savant_base = "https://baseballsavant.mlb.com/gf"
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'),
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest'
        })
        
        # Increase connection pool for super aggressive mode
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=20,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        logger.info(
            f"🚀 Enhanced Statcast collector initialized with {performance_profile} "
            f"profile: {self.config.max_workers} workers, {self.config.request_delay}s delay"
        )

    def collect_all_players(self, player_ids: List[str]) -> Dict[str, Any]:
        """Collect Statcast BBE data for all players in parallel"""
        results = {
            "success": [],
            "failed": [],
            "skipped": []
        }
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = []
            
            for player_id in player_ids:
                future = executor.submit(self._collect_single_player, player_id)
                futures.append((future, player_id))
            
            for future, player_id in futures:
                try:
                    result = future.result()
                    if result["success"]:
                        results["success"].append(player_id)
                    else:
                        results["failed"].append(f"{player_id}: {result['error']}")
                except Exception as e:
                    results["failed"].append(f"{player_id}: {str(e)}")
                
                time.sleep(self.config.request_delay)
        
        logger.info(
            f"✅ Collection complete: {len(results['success'])} success, "
            f"{len(results['failed'])} failed, {len(results['skipped'])} skipped"
        )
        return results

    def _collect_single_player(self, player_id: str) -> Dict[str, Any]:
        """Collect Statcast BBE data for a single player"""
        try:
            # Get current season dates
            season_start, season_end = self._get_regular_season_dates()
            if not season_start or not season_end:
                return {"success": False, "error": "Could not determine season dates"}
            
            # Collect data for the entire season
            player_data = self._fetch_player_statcast_data(player_id, season_start, season_end)
            
            if not player_data:
                return {"success": False, "error": "No Statcast data available"}
            
            # Save raw data first
            raw_file = self.raw_dir / f"{player_id}.json"
            with open(raw_file, 'w') as f:
                json.dump(player_data, f, indent=2)
            
            logger.info(f"✅ Collected Statcast data for player {player_id}")
            return {"success": True, "data": player_data}
            
        except Exception as e:
            logger.error(f"❌ Failed to collect Statcast data for player {player_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    def _fetch_player_statcast_data(self, player_id: str, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """Fetch Statcast BBE data for a player across date range"""
        try:
            # Baseball Savant game feed endpoint for player data
            url = f"{self.savant_base}/player/{player_id}"
            
            params = {
                'start_date': start_date,
                'end_date': end_date,
                'type': 'batter'  # We'll determine hitter/pitcher from data
            }
            
            for attempt in range(self.config.retry_attempts):
                try:
                    response = self.session.get(url, params=params, timeout=self.config.timeout)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # Transform to our format
                    transformed_data = self._transform_statcast_data(player_id, data)
                    
                    return transformed_data
                    
                except requests.exceptions.RequestException as e:
                    if attempt == self.config.retry_attempts - 1:
                        logger.error(f"Failed to fetch Statcast data for {player_id}: {str(e)}")
                        return None
                    time.sleep(1)
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Statcast data for {player_id}: {str(e)}")
            return None

    def _transform_statcast_data(self, player_id: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw Statcast data to our format"""
        transformed = {
            "player_id": player_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_games": 0,
            "total_at_bats": 0,
            "games": {},
            "events": []
        }
        
        # Process the raw data and extract events
        if 'events' in raw_data:
            for event in raw_data['events']:
                # Extract key Statcast fields
                event_data = {
                    "game_pk": event.get("game_pk"),
                    "game_date": event.get("game_date"),
                    "inning": event.get("inning"),
                    "batter_id": event.get("batter_id"),
                    "pitcher_id": event.get("pitcher_id"),
                    "exit_velocity": event.get("launch_speed"),
                    "launch_angle": event.get("launch_angle"),
                    "release_speed": event.get("release_speed"),
                    "spin_rate": event.get("release_spin_rate"),
                    "pitch_type": event.get("pitch_type"),
                    "events": event.get("events"),
                    "description": event.get("description")
                }
                transformed["events"].append(event_data)
        
        transformed["total_at_bats"] = len(transformed["events"])
        
        return transformed

    def _get_regular_season_dates(self) -> Tuple[Optional[str], Optional[str]]:
        """Get current MLB regular season start and end dates"""
        try:
            # 2025 MLB season dates
            season_start = "2025-03-18"
            season_end = "2025-09-28"
            
            # Adjust end date to not exceed today
            today = datetime.now().date()
            end_date = datetime.strptime(season_end, '%Y-%m-%d').date()
            
            if today < end_date:
                season_end = today.strftime('%Y-%m-%d')
            
            return season_start, season_end
            
        except Exception as e:
            logger.error(f"Error getting season dates: {e}")
            return None, None

    def split_data_by_type(self):
        """Split collected raw data into batter/pitcher directories"""
        logger.info("🔄 Splitting raw data into batter/pitcher directories...")
        
        batter_count = 0
        pitcher_count = 0
        
        for raw_file in self.raw_dir.glob("*.json"):
            try:
                with open(raw_file, 'r') as f:
                    data = json.load(f)
                
                player_id = data.get('player_id')
                events = data.get('events', [])
                
                if not events:
                    continue
                
                # Determine if player is primarily a batter or pitcher
                # Count batter vs pitcher events
                batter_events = sum(1 for e in events if e.get('batter_id') == int(player_id))
                pitcher_events = sum(1 for e in events if e.get('pitcher_id') == int(player_id))
                
                if batter_events > pitcher_events:
                    # Save as batter
                    output_file = self.batter_dir / f"{player_id}.json"
                    with open(output_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    batter_count += 1
                else:
                    # Save as pitcher
                    output_file = self.pitcher_dir / f"{player_id}.json"
                    with open(output_file, 'w') as f:
                        json.dump(data, f, indent=2)
                    pitcher_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {raw_file}: {e}")
        
        logger.info(f"✅ Data split complete: {batter_count} batters, {pitcher_count} pitchers")

    def collect_single_player(self, player_id: str) -> Dict[str, Any]:
        """Collect data for a single player (public interface)"""
        return self._collect_single_player(player_id)
