#!/usr/bin/env python3
"""
Fangraphs Hash Manager

Manages hash-based incremental updates for Fangraphs data collection.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from .config import fg_config


class FGHashManager:
    """Hash manager for Fangraphs data incremental updates."""

    def __init__(self, collector_name: str):
        """Initialize hash manager for a specific collector."""
        self.collector_name = collector_name
        self.hash_dir = fg_config.get_hash_dir(collector_name)
        self.hash_dir.mkdir(parents=True, exist_ok=True)

    def calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate hash for data dictionary."""
        # Create a copy of data without timestamp fields for stable hashing
        hash_data = data.copy()

        # Remove timestamp fields that change on every collection
        if 'collection_timestamp' in hash_data:
            del hash_data['collection_timestamp']

        # Remove timestamp from metadata if it exists
        if 'metadata' in hash_data and 'last_updated' in hash_data['metadata']:
            del hash_data['metadata']['last_updated']

        # Remove loaddate from all player records (changes on every API call)
        if 'players' in hash_data:
            for player in hash_data['players']:
                if 'loaddate' in player:
                    del player['loaddate']

        # Sort data for consistent hashing
        data_str = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        return hashlib.md5(data_str.encode()).hexdigest()[:8]

    def get_hash_file_path(self, team_abbr: str, level: str) -> Path:
        """Get hash file path for a team and level."""
        filename = fg_config.generate_filename(team_abbr, level).replace('.json', '_hash.json')
        return self.hash_dir / filename

    def load_hash(self, team_abbr: str, level: str) -> Optional[Dict[str, Any]]:
        """Load hash data for a team and level."""
        hash_file = self.get_hash_file_path(team_abbr, level)

        if not hash_file.exists():
            return None

        try:
            with open(hash_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    def save_hash(self, team_abbr: str, level: str, data_hash: str,
                  data: Dict[str, Any], file_path: str) -> None:
        """Save hash data for a team and level."""
        hash_file = self.get_hash_file_path(team_abbr, level)

        hash_data = {
            'team_abbr': team_abbr,
            'level': level,
            'data_hash': data_hash,
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'player_count': len(data.get('players', [])),
            'collection_metadata': {
                'total_players': len(data.get('players', [])),
                'mlb_players': len([p for p in data.get('players', [])
                                  if p.get('mlevel') == 'MLB']),
                'last_updated': datetime.now().isoformat()
            }
        }

        with open(hash_file, 'w') as f:
            json.dump(hash_data, f, indent=2)

    def needs_update(self, team_abbr: str, level: str, new_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if data needs updating based on hash comparison."""
        new_hash = self.calculate_data_hash(new_data)
        existing_hash_data = self.load_hash(team_abbr, level)

        if not existing_hash_data:
            return True, f"New data for {team_abbr} {level}"

        existing_hash = existing_hash_data.get('data_hash')

        if new_hash != existing_hash:
            return True, f"Hash changed: {existing_hash} -> {new_hash}"

        return False, f"Data current for {team_abbr} {level}"

    def get_all_hashes(self) -> Dict[str, Dict[str, Any]]:
        """Get all hash files for this collector."""
        hashes = {}

        for hash_file in self.hash_dir.glob("*_hash.json"):
            try:
                with open(hash_file, 'r') as f:
                    hash_data = json.load(f)
                    key = f"{hash_data['team_abbr']}_{hash_data['level']}"
                    hashes[key] = hash_data
            except Exception:
                continue

        return hashes

    def cleanup_old_hashes(self, max_age_hours: int = 24) -> int:
        """Clean up old hash files."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0

        for hash_file in self.hash_dir.glob("*_hash.json"):
            try:
                if hash_file.stat().st_mtime < cutoff_time:
                    hash_file.unlink()
                    cleaned_count += 1
            except Exception:
                continue

        return cleaned_count

    def get_collection_summary(self) -> Dict[str, Any]:
        """Get summary of all collected data."""
        hashes = self.get_all_hashes()

        summary = {
            'collector_name': self.collector_name,
            'total_teams': len(hashes),
            'teams_by_level': {},
            'total_players': 0,
            'mlb_players': 0,
            'last_updated': None
        }

        for key, hash_data in hashes.items():
            level = hash_data.get('level', 'Unknown')
            if level not in summary['teams_by_level']:
                summary['teams_by_level'][level] = 0
            summary['teams_by_level'][level] += 1

            summary['total_players'] += hash_data.get('player_count', 0)
            summary['mlb_players'] += hash_data.get('collection_metadata', {}).get('mlb_players', 0)

            timestamp = hash_data.get('timestamp')
            if timestamp:
                if not summary['last_updated'] or timestamp > summary['last_updated']:
                    summary['last_updated'] = timestamp

        return summary
