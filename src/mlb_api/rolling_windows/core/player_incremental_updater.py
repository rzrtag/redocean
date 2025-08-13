#!/usr/bin/env python3
"""
Player-Level Incremental Updater for Rolling Windows

This module extends the shared incremental updater to handle individual player files
for rolling windows data, allowing for granular updates without re-collecting all data.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

# Import shared modules
try:
    from ...shared.incremental_updater import IncrementalUpdater
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent.parent))
    from shared.incremental_updater import IncrementalUpdater

logger = logging.getLogger(__name__)

class PlayerIncrementalUpdater(IncrementalUpdater):
    """
    Handles incremental updates for individual player files in rolling windows.

    Each player gets their own hash file, allowing for granular updates.
    """

    def __init__(self, collector_name: str, base_data_dir: str = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025"):
        super().__init__(collector_name, base_data_dir)

        # Create player-specific hash directories
        (self.hash_dir / "hitters").mkdir(exist_ok=True)
        (self.hash_dir / "pitchers").mkdir(exist_ok=True)

        # Player hash tracking
        self.player_hashes = {}  # Cache for current session
        self._load_existing_player_hashes()

    def _load_existing_player_hashes(self):
        """Load existing player hash files into memory"""
        self.player_hashes = {}

        # Load hitter hashes
        hitters_hash_dir = self.hash_dir / "hitters"
        if hitters_hash_dir.exists():
            for hash_file in hitters_hash_dir.glob("*.json"):
                try:
                    with open(hash_file, 'r') as f:
                        hash_data = json.load(f)
                        player_id = hash_data.get('player_id')
                        if player_id:
                            self.player_hashes[f"hitters_{player_id}"] = hash_data
                except Exception as e:
                    logger.warning(f"Failed to load hash file {hash_file}: {e}")

        # Load pitcher hashes
        pitchers_hash_dir = self.hash_dir / "pitchers"
        if pitchers_hash_dir.exists():
            for hash_file in pitchers_hash_dir.glob("*.json"):
                try:
                    with open(hash_file, 'r') as f:
                        hash_data = json.load(f)
                        player_id = hash_data.get('player_id')
                        if player_id:
                            self.player_hashes[f"pitchers_{player_id}"] = hash_data
                except Exception as e:
                    logger.warning(f"Failed to load hash file {hash_file}: {e}")

        logger.info(f"Loaded {len(self.player_hashes)} existing player hashes")

    def _calculate_player_hash(self, data: Dict[str, Any]) -> str:
        """Calculate hash for player data (excluding metadata)"""
        # Create a copy without metadata for consistent hashing
        data_copy = data.copy()

        # Remove metadata fields that shouldn't affect the hash
        metadata_fields = ['collection_timestamp', 'collection_date', 'file_path']
        for field in metadata_fields:
            if field in data_copy:
                del data_copy[field]

        # Convert to sorted JSON string for consistent hashing
        json_str = json.dumps(data_copy, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    def check_player_needs_update(self, player_id: str, player_type: str, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if a specific player needs updating.

        Args:
            player_id: Player ID
            player_type: 'hitters' or 'pitchers'
            data: Current player data

        Returns:
            Tuple of (needs_update, reason)
        """
        player_key = f"{player_type}_{player_id}"
        current_hash = self._calculate_player_hash(data)

        # Check if we have a previous hash for this player
        if player_key not in self.player_hashes:
            reason = f"New player {player_id} - no previous hash found"
            logger.info(f"New player detected: {player_type} {player_id}")
            return True, reason

        previous_hash = self.player_hashes[player_key].get('content_hash')

        if current_hash == previous_hash:
            reason = f"Player {player_id} unchanged - hash matches"
            return False, reason

        reason = f"Player {player_id} changed - hash: {previous_hash[:8]} -> {current_hash[:8]}"
        logger.info(f"Player update detected: {player_type} {player_id}")
        return True, reason

    def update_player_hash(self, player_id: str, player_type: str, data: Dict[str, Any], file_path: str = None):
        """
        Update hash for a specific player after successful collection.

        Args:
            player_id: Player ID
            player_type: 'hitters' or 'pitchers'
            data: Player data that was collected
            file_path: Path to the saved data file
        """
        player_key = f"{player_type}_{player_id}"
        content_hash = self._calculate_player_hash(data)

        # Create hash record
        hash_record = {
            "player_id": player_id,
            "player_type": player_type,
            "content_hash": content_hash,
            "file_size": len(str(data)),
            "last_updated": datetime.now().isoformat(),
            "file_path": file_path or f"data/{player_type}/{player_id}.json"
        }

        # Save hash file
        hash_file = self.hash_dir / player_type / f"{player_id}.json"
        with open(hash_file, 'w') as f:
            json.dump(hash_record, f, indent=2)

        # Update in-memory cache
        self.player_hashes[player_key] = hash_record

        logger.debug(f"Updated hash for {player_type} {player_id}: {content_hash[:8]}")

    def get_player_hash_info(self, player_id: str, player_type: str) -> Optional[Dict[str, Any]]:
        """Get hash information for a specific player"""
        player_key = f"{player_type}_{player_id}"
        return self.player_hashes.get(player_key)

    def get_all_player_hashes(self) -> Dict[str, Dict[str, Any]]:
        """Get all player hash information"""
        return self.player_hashes.copy()

    def cleanup_old_player_hashes(self, max_age_days: int = 30):
        """Clean up old player hash files"""
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
        cleaned_count = 0

        for player_type in ['hitters', 'pitchers']:
            hash_dir = self.hash_dir / player_type
            if hash_dir.exists():
                for hash_file in hash_dir.glob("*.json"):
                    try:
                        if hash_file.stat().st_mtime < cutoff_time:
                            hash_file.unlink()
                            cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to clean up {hash_file}: {e}")

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old player hash files")
            # Reload hashes after cleanup
            self._load_existing_player_hashes()
