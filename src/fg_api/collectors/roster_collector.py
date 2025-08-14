#!/usr/bin/env python3
"""
Stealth Fangraphs Roster Collector

Advanced collector with comprehensive Cloudflare bypass techniques.
"""

import json
import time
import random
import requests
import urllib3
from typing import Dict, Any, List

from ..shared.incremental_updater import FGIncrementalUpdater
from ..shared.config import fg_config

# Disable SSL warnings for Cloudflare bypass
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FGRosterCollector(FGIncrementalUpdater):
    """Advanced stealth collector for Fangraphs roster data."""
    
    def __init__(self, performance_profile: str = 'stealth', 
                 max_workers: int = None, request_delay: float = None):
        """Initialize the stealth roster collector."""
        super().__init__(
            collector_name="roster",
            performance_profile=performance_profile,
            max_workers=max_workers,
            request_delay=request_delay
        )
        
        # API settings
        self.base_url = fg_config.BASE_URL
        
        # Create persistent session with advanced stealth settings
        self.session = requests.Session()
        self.session.verify = False
        self.session.trust_env = False
        
        # Comprehensive cookies for Cloudflare bypass
        self._setup_cookies()
        
        # Advanced browser headers
        self._setup_headers()
        
        # User agent rotation
        self.user_agents = [
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
        ]
    
    def _setup_cookies(self):
        """Setup comprehensive cookies for Cloudflare bypass."""
        cookies = {
            '__qca': 'P1-c6b07ce3-6756-437b-b705-cef1b10bb0c3',
            'aym_t_S2S': 'on',
            '_ga': 'GA1.1.288863766.1755124920',
            '_ga_757YGY2LKP': 'GS2.1.s1755124920$o1$g1$t1755125553$j60$l0$h0',
            'fg_uuid': '9b5d68ce-aba2-4568-8296-f996fcd5518a'
        }
        
        for name, value in cookies.items():
            self.session.cookies.set(name, value, domain='.fangraphs.com')
    
    def _setup_headers(self):
        """Setup advanced browser headers."""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(headers)
    
    def _get_stealth_headers(self, team_abbr: str) -> Dict[str, str]:
        """Generate stealth headers for each request."""
        headers = self.session.headers.copy()
        
        # Rotate user agent
        headers['User-Agent'] = random.choice(self.user_agents)
        
        # Add team-specific referer
        headers['Referer'] = f'https://www.fangraphs.com/roster-resource/depth-charts/{team_abbr.lower()}'
        
        # Random accept-language variations
        accept_langs = [
            'en-US,en;q=0.9,en;q=0.8',
            'en-US,en;q=0.9',
            'en-US,en;q=0.9,en;q=0.8,es;q=0.7',
            'en-US,en;q=0.9,en;q=0.8,fr;q=0.7'
        ]
        headers['Accept-Language'] = random.choice(accept_langs)
        
        return headers
    
    def _stealth_delay(self):
        """Add random delay to mimic human behavior."""
        delay = random.uniform(1.0, 3.0)  # Faster but still stealthy
        time.sleep(delay)
    
    def _pre_request_setup(self, team_abbr: str):
        """Advanced pre-request setup to bypass Cloudflare."""
        try:
            # First, access the main team page to establish session
            team_url = f'https://www.fangraphs.com/roster-resource/depth-charts/{team_abbr.lower()}'
            self.session.get(team_url, timeout=10, allow_redirects=True)
            time.sleep(random.uniform(2.0, 4.0))
        except Exception:
            pass  # Continue even if this fails
    
    def collect_team_data(self, team_abbr: str, level: str = 'MLB') -> List[Dict[str, Any]]:
        """Collect roster data with advanced stealth measures."""
        team_id = fg_config.get_team_id(team_abbr)
        if not team_id:
            raise ValueError(f"Unknown team abbreviation: {team_abbr}")
        
        # Advanced pre-request setup
        self._pre_request_setup(team_abbr)
        
        # Add stealth delay
        self._stealth_delay()
        
        # Build URL with current timestamp
        load_date = int(time.time())
        url = f"{self.base_url}?teamid={team_id}&loaddate={load_date}"
        
        # Get stealth headers
        headers = self._get_stealth_headers(team_abbr)
        
        # Retry mechanism with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                break  # Success, exit retry loop
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    backoff_delay = 10 * (2 ** attempt)
                    print(f"⚠️ Attempt {attempt + 1} failed for {team_abbr}, retrying in {backoff_delay}s...")
                    time.sleep(backoff_delay)
                    continue
                else:
                    raise Exception(f"API request failed for {team_abbr} after {max_retries} attempts: {e}")
        
        # Extract players from the response
        players = []
        
        if isinstance(data, list):
            for player in data:
                if isinstance(player, dict):
                    # Add team info to player data
                    player['team_abbr'] = team_abbr
                    player['team_id'] = team_id
                    
                    # Determine section based on position/type
                    if player.get('type', '').startswith('mlb'):
                        player['section'] = 'hitters'
                    elif player.get('type', '').startswith('mlb-p'):
                        player['section'] = 'pitchers'
                    else:
                        player['section'] = 'other'
                    
                    players.append(player)
        
        return players
    
    def process_team_data(self, team_abbr: str, level: str, 
                         raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process raw roster data with enhanced metadata."""
        # Filter players by level if needed
        if level != 'MLB':
            filtered_players = [p for p in raw_data if p.get('mlevel') == level]
        else:
            filtered_players = raw_data
        
        # Enhanced metadata
        metadata = {
            'total_players': len(filtered_players),
            'mlb_players': len([p for p in filtered_players if p.get('mlevel') == 'MLB']),
            'hitters': len([p for p in filtered_players if p.get('section') == 'hitters']),
            'pitchers': len([p for p in filtered_players if p.get('section') == 'pitchers']),
            'collection_method': 'roster',
            'api_endpoint': self.base_url,
            'team_id': fg_config.get_team_id(team_abbr)
        }
        
        return {
            'team_abbr': team_abbr,
            'level': level,
            'collection_timestamp': time.time(),
            'players': filtered_players,
            'metadata': metadata
        }
