#!/usr/bin/env python3
"""
Fangraphs API Configuration

Team mappings, performance profiles, and API settings for Fangraphs data collection.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional


class FGConfig:
    """Configuration for Fangraphs API data collection."""
    
    # Base data directory
    BASE_DATA_DIR = Path("/mnt/storage_fast/workspaces/red_ocean/_data/fg_api_2025")
    
    # API settings
    BASE_URL = "https://www.fangraphs.com/api/depth-charts/roster"
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
    
    # Team ID mappings (Fangraphs team IDs)
    TEAM_IDS = {
        'ARI': 15, 'ATL': 16, 'BAL': 2, 'BOS': 3, 'CHC': 17, 'CIN': 18, 'CLE': 5, 'COL': 19,
        'CWS': 4, 'DET': 6, 'HOU': 21, 'KC': 7, 'LAA': 1, 'LAD': 22, 'MIA': 20, 'MIL': 23,
        'MIN': 8, 'NYM': 24, 'NYY': 10, 'OAK': 11, 'PHI': 26, 'PIT': 27, 'SD': 25, 'SEA': 12,
        'SF': 28, 'STL': 29, 'TB': 30, 'TEX': 13, 'TOR': 14, 'WSH': 20
    }
    
    # Team abbreviations (for file naming)
    TEAM_ABBREVIATIONS = {
        15: 'ARI', 16: 'ATL', 2: 'BAL', 3: 'BOS', 17: 'CHC', 18: 'CIN', 5: 'CLE', 19: 'COL',
        4: 'CWS', 6: 'DET', 21: 'HOU', 7: 'KC', 1: 'LAA', 22: 'LAD', 20: 'MIA', 23: 'MIL',
        8: 'MIN', 24: 'NYM', 10: 'NYY', 11: 'OAK', 26: 'PHI', 27: 'PIT', 25: 'SD', 12: 'SEA',
        28: 'SF', 29: 'STL', 30: 'TB', 13: 'TEX', 14: 'TOR', 20: 'WSH'
    }
    
    # Performance profiles
    PERFORMANCE_PROFILES = {
        'stealth': {
            'max_workers': 8,
            'request_delay': 0.5,
            'timeout': 30
        },
        'conservative': {
            'max_workers': 12,
            'request_delay': 0.3,
            'timeout': 30
        },
        'balanced': {
            'max_workers': 16,
            'request_delay': 0.2,
            'timeout': 30
        },
        'aggressive': {
            'max_workers': 20,
            'request_delay': 0.1,
            'timeout': 30
        },
        'ultra_aggressive': {
            'max_workers': 25,
            'request_delay': 0.05,
            'timeout': 30
        }
    }
    
    # Default settings
    DEFAULT_PROFILE = 'balanced'
    DEFAULT_MAX_WORKERS = 6
    DEFAULT_REQUEST_DELAY = 0.2
    DEFAULT_TIMEOUT = 30
    
    # Data organization
    LEVELS = ['MLB', 'AAA', 'AA', 'A+', 'A', 'SS']
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialize configuration."""
        self.data_dir = Path(data_dir) if data_dir else self.BASE_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.collectors_dir = self.data_dir / "collectors"
        self.hash_dir = self.data_dir / "hash"
        self.tests_dir = self.data_dir / "tests"
        
        for directory in [self.collectors_dir, self.hash_dir, self.tests_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_team_id(self, team_abbr: str) -> int:
        """Get Fangraphs team ID from abbreviation."""
        return self.TEAM_IDS.get(team_abbr.upper())
    
    def get_team_abbr(self, team_id: int) -> str:
        """Get team abbreviation from Fangraphs team ID."""
        return self.TEAM_ABBREVIATIONS.get(team_id, f"TEAM_{team_id}")
    
    def get_performance_settings(self, profile: str = None) -> Dict[str, Any]:
        """Get performance settings for a profile."""
        profile = profile or self.DEFAULT_PROFILE
        return self.PERFORMANCE_PROFILES.get(profile, self.PERFORMANCE_PROFILES[self.DEFAULT_PROFILE])
    
    def get_collector_dir(self, collector_name: str) -> Path:
        """Get directory for a specific collector."""
        return self.collectors_dir / collector_name
    
    def get_hash_dir(self, collector_name: str) -> Path:
        """Get hash directory for a specific collector."""
        return self.hash_dir / collector_name
    
    def generate_filename(self, team_abbr: str, level: str, year: int = 2025) -> str:
        """Generate standardized filename for team data."""
        return f"{year}_{team_abbr}_{level}.json"
    
    def get_all_teams(self) -> Dict[str, int]:
        """Get all team abbreviations and their IDs."""
        return self.TEAM_IDS.copy()
    
    def get_mlb_teams(self) -> Dict[str, int]:
        """Get only MLB teams (exclude any non-MLB teams)."""
        return {k: v for k, v in self.TEAM_IDS.items() if k != 'WSH'}  # WSH is duplicate of MIA


# Global config instance
fg_config = FGConfig()
