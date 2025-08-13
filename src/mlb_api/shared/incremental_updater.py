"""
Shared Incremental Update Framework for MLB API Collectors

This module provides hash-based incremental update logic that ensures:
- Only changed data is downloaded
- Minimal API calls
- Efficient caching and hash management
- True incremental updates with hash verification
- Concurrent processing and batch operations for speed
"""

import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IncrementalUpdater:
    """
    Handles incremental updates using hash-based change detection.

    Each collector gets its own hash directory and cache management.
    Optimized with concurrent processing and batch operations.
    """

    def __init__(self, collector_name: str, base_data_dir: str = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025"):
        """
        Initialize the incremental updater for a specific collector.

        Args:
            collector_name: Name of the collector (e.g., 'active_rosters', 'stats', 'schedules')
            base_data_dir: Base data directory for MLB API collectors
        """
        self.collector_name = collector_name
        self.base_data_dir = Path(base_data_dir)
        self.collector_dir = self.base_data_dir / collector_name
        self.hash_dir = self.collector_dir / "hash"
        self.cache_dir = self.collector_dir / "cache"
        self.data_dir = self.collector_dir / "data"

        # Create necessary directories
        self.hash_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Hash file paths
        self.current_hash_file = self.hash_dir / "current_hash.json"
        self.previous_hash_file = self.hash_dir / "previous_hash.json"
        self.update_log_file = self.hash_dir / "update_log.json"

        # Performance settings
        self.max_workers = 3  # Concurrent workers for API calls
        self.request_delay = 0.1  # Delay between requests to be respectful

        logger.info(f"Initialized IncrementalUpdater for {collector_name}")
        logger.info(f"Hash directory: {self.hash_dir}")
        logger.info(f"Cache directory: {self.cache_dir}")
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Max workers: {self.max_workers}")

    def _compute_hash(self, data: Union[str, bytes, Dict, List]) -> str:
        """
        Compute SHA-256 hash of data.

        Args:
            data: Data to hash (string, bytes, dict, or list)

        Returns:
            SHA-256 hash string
        """
        if isinstance(data, (dict, list)):
            # Create a copy of the data for stable hashing
            if isinstance(data, dict):
                stable_data = data.copy()
                # Remove timestamp-dependent fields for stable hashing
                if 'metadata' in stable_data:
                    metadata = stable_data['metadata'].copy()
                    metadata.pop('collection_timestamp', None)
                    metadata.pop('performance', None)  # Also remove performance metrics
                    stable_data['metadata'] = metadata

                # For roster data, create a more focused hash on just the essential data
                if 'rosters' in stable_data and 'teams' in stable_data:
                    # Create a simplified hash based on just the core roster structure
                    roster_hash_data = {
                        'teams': stable_data['teams'],
                        'rosters': {}
                    }

                    # For each team, just include player IDs and positions (the stable identifiers)
                    for team_abbr, team_data in stable_data.get('rosters', {}).items():
                        roster_hash_data['rosters'][team_abbr] = {
                            'team_info': team_data.get('team_info', {}),
                            'roster': [
                                {
                                    'id': player.get('id'),
                                    'primaryPosition': player.get('primaryPosition', {}),
                                    'team_abbr': player.get('team_abbr')
                                }
                                for player in team_data.get('roster', [])
                            ]
                        }

                    stable_data = roster_hash_data

                data_str = json.dumps(stable_data, sort_keys=True, separators=(',', ':'))
            else:
                # For lists, just use the original logic
                data_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        elif isinstance(data, bytes):
            data_str = data.decode('utf-8')
        else:
            data_str = str(data)

        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

    def _load_hash_file(self, hash_file: Path) -> Optional[Dict[str, Any]]:
        """Load hash file if it exists."""
        if hash_file.exists():
            try:
                with open(hash_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load hash file {hash_file}: {e}")
        return None

    def _save_hash_file(self, hash_file: Path, data: Dict[str, Any]) -> None:
        """Save hash file with error handling."""
        try:
            with open(hash_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except IOError as e:
            logger.error(f"Could not save hash file {hash_file}: {e}")

    def _log_update(self, action: str, details: Dict[str, Any]) -> None:
        """Log update actions for debugging and monitoring."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "collector": self.collector_name,
            **details
        }

        # Load existing log
        log_data = []
        if self.update_log_file.exists():
            try:
                with open(self.update_log_file, 'r') as f:
                    loaded_data = json.load(f)
                    # Ensure we have the correct structure
                    if isinstance(loaded_data, dict) and "updates" in loaded_data:
                        log_data = loaded_data["updates"]
                    elif isinstance(loaded_data, list):
                        log_data = loaded_data
                    else:
                        log_data = []
            except (json.JSONDecodeError, IOError):
                log_data = []

        # Ensure log_data is a list
        if not isinstance(log_data, list):
            log_data = []

        # Add new entry and keep only last 100 entries
        log_data.append(log_entry)
        if len(log_data) > 100:
            log_data = log_data[-100:]

        # Save updated log
        self._save_hash_file(self.update_log_file, {"updates": log_data})

    def check_for_updates(self, data: Union[Dict, List], data_key: str = "data") -> Tuple[bool, Optional[str]]:
        """
        Check if data needs to be updated by comparing hashes.

        Args:
            data: Current data to check
            data_key: Key to use for storing data in hash files

        Returns:
            Tuple of (needs_update, reason)
        """
        current_hash = self._compute_hash(data)

        # Load previous hash
        previous_hash_data = self._load_hash_file(self.previous_hash_file)
        previous_hash = previous_hash_data.get(data_key) if previous_hash_data else None

        if previous_hash is None:
            reason = "No previous hash found - first run"
            logger.info(f"First run for {self.collector_name}: {reason}")
            return True, reason

        if current_hash == previous_hash:
            logger.info(f"No updates needed for {self.collector_name} - hash unchanged")
            return False, "Hash unchanged - no updates needed"

        reason = f"Hash changed: {previous_hash[:8]} -> {current_hash[:8]}"
        logger.info(f"Updates detected for {self.collector_name}: {reason}")
        return True, reason

    def update_hash(self, data: Union[Dict, List], data_key: str = "data") -> None:
        """
        Update hash files after successful data collection.

        Args:
            data: Data that was collected
            data_key: Key to use for storing data in hash files
        """
        current_hash = self._compute_hash(data)
        timestamp = datetime.now().isoformat()

        # Move current hash to previous
        if self.current_hash_file.exists():
            current_data = self._load_hash_file(self.current_hash_file)
            if current_data:
                self._save_hash_file(self.previous_hash_file, current_data)

        # Create new current hash
        new_hash_data = {
            data_key: current_hash,
            "timestamp": timestamp,
            "collector": self.collector_name,
            "data_size": len(str(data)) if isinstance(data, (dict, list)) else len(str(data))
        }

        self._save_hash_file(self.current_hash_file, new_hash_data)

        # Log the update
        self._log_update("hash_updated", {
            "data_key": data_key,
            "hash": current_hash,
            "timestamp": timestamp
        })

        logger.info(f"Updated hash for {self.collector_name}: {current_hash[:8]}")

    def get_last_update_time(self) -> Optional[datetime]:
        """Get the timestamp of the last successful update."""
        current_hash_data = self._load_hash_file(self.current_hash_file)
        if current_hash_data and "timestamp" in current_hash_data:
            try:
                return datetime.fromisoformat(current_hash_data["timestamp"])
            except ValueError:
                pass
        return None

    def get_hash_info(self) -> Dict[str, Any]:
        """Get current hash information for debugging."""
        current = self._load_hash_file(self.current_hash_file)
        previous = self._load_hash_file(self.previous_hash_file)

        return {
            "collector": self.collector_name,
            "current_hash": current,
            "previous_hash": previous,
            "last_update": self.get_last_update_time(),
            "hash_dir": str(self.hash_dir),
            "cache_dir": str(self.cache_dir),
            "data_dir": str(self.data_dir),
            "max_workers": self.max_workers
        }

    def force_update(self, reason: str = "Manual force update") -> None:
        """
        Force an update by clearing previous hash.

        Args:
            reason: Reason for forcing update
        """
        if self.previous_hash_file.exists():
            self.previous_hash_file.unlink()
            logger.info(f"Forced update for {self.collector_name}: {reason}")
            self._log_update("force_update", {"reason": reason})

    def cleanup_old_files(self, max_age_days: int = 30) -> None:
        """
        Clean up old cache and hash files.

        Args:
            max_age_days: Maximum age of files to keep
        """
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cleaned_count = 0

        for file_path in self.cache_dir.glob("*"):
            if file_path.is_file():
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
                except (OSError, ValueError):
                    pass

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old files from {self.collector_name}")
            self._log_update("cleanup", {"files_removed": cleaned_count})

    def process_batch_concurrent(self, items: List[Any], process_func, max_workers: int = None) -> List[Any]:
        """
        Process items concurrently using ThreadPoolExecutor.

        Args:
            items: List of items to process
            process_func: Function to process each item
            max_workers: Number of concurrent workers (defaults to self.max_workers)

        Returns:
            List of processed results
        """
        if max_workers is None:
            max_workers = self.max_workers

        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {
                executor.submit(process_func, item): item
                for item in items
            }

            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)

                    # Small delay to be respectful to APIs
                    time.sleep(self.request_delay)

                except Exception as e:
                    logger.error(f"Error processing item {item}: {e}")
                    continue

        return results

    def set_performance_settings(self, max_workers: int = None, request_delay: float = None) -> None:
        """
        Update performance settings.

        Args:
            max_workers: Number of concurrent workers
            request_delay: Delay between requests in seconds
        """
        if max_workers is not None:
            self.max_workers = max_workers
            logger.info(f"Updated max_workers to {max_workers}")

        if request_delay is not None:
            self.request_delay = request_delay
            logger.info(f"Updated request_delay to {request_delay}")


class MLBAPICollector:
    """
    Base class for MLB API collectors with incremental update support.

    All collectors should inherit from this class.
    Optimized with concurrent processing and batch operations.
    """

    def __init__(self, collector_name: str, base_data_dir: str = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025"):
        """
        Initialize the collector with incremental update support.

        Args:
            collector_name: Name of the collector
            base_data_dir: Base data directory for MLB API collectors
        """
        self.collector_name = collector_name
        self.updater = IncrementalUpdater(collector_name, base_data_dir)
        self.session = None  # Will be set by subclasses

        # Performance settings
        self.max_workers = 3
        self.request_delay = 0.1

        logger.info(f"Initialized MLB API Collector: {collector_name}")
        logger.info(f"Performance: {self.max_workers} workers, {self.request_delay}s delay")

    def collect_data(self) -> Union[Dict, List]:
        """
        Collect data from MLB API. Must be implemented by subclasses.

        Returns:
            Collected data
        """
        raise NotImplementedError("Subclasses must implement collect_data()")

    def collect_data_concurrent(self, items: List[Any], process_func) -> List[Any]:
        """
        Collect data concurrently for multiple items.

        Args:
            items: List of items to process
            process_func: Function to process each item

        Returns:
            List of collected results
        """
        return self.updater.process_batch_concurrent(items, process_func, self.max_workers)

    def run_collection(self, force_update: bool = False) -> Tuple[bool, Union[Dict, List], str]:
        """
        Run the collection with incremental update logic.

        Args:
            force_update: Force update regardless of hash

        Returns:
            Tuple of (was_updated, data, reason)
        """
        if force_update:
            self.updater.force_update("Force update requested")

        # Collect data
        logger.info(f"Starting data collection for {self.collector_name}")
        start_time = time.time()

        data = self.collect_data()

        collection_time = time.time() - start_time
        logger.info(f"Data collection completed in {collection_time:.2f} seconds")

        # Check if update is needed
        needs_update, reason = self.updater.check_for_updates(data)

        if needs_update:
            # Update hash and save data
            self.updater.update_hash(data)
            self._save_data(data)
            logger.info(f"Data updated for {self.collector_name}: {reason}")
            return True, data, reason
        else:
            logger.info(f"No update needed for {self.collector_name}: {reason}")
            return False, data, reason

    def _save_data(self, data: Union[Dict, List]) -> None:
        """Save collected data to file."""
        # Save to single file without timestamp
        data_file = self.updater.data_dir / f"{self.collector_name}.json"

        try:
            # Clean up old timestamped files first
            self._cleanup_old_data_files()

            # Save new data
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved data to {data_file}")
        except IOError as e:
            logger.error(f"Could not save data to {data_file}: {e}")

    def _cleanup_old_data_files(self) -> None:
        """Clean up old timestamped data files, keeping only the main file."""
        try:
            # Remove all timestamped files for this collector
            pattern = f"{self.collector_name}_*.json"
            for old_file in self.updater.data_dir.glob(pattern):
                old_file.unlink()
                logger.info(f"Removed old data file: {old_file}")
        except Exception as e:
            logger.warning(f"Could not clean up old data files: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get collector status and hash information."""
        return {
            "collector_name": self.collector_name,
            "hash_info": self.updater.get_hash_info(),
            "last_update": self.updater.get_last_update_time(),
            "data_files": [str(f) for f in self.updater.data_dir.glob("*.json")],
            "performance": {
                "max_workers": self.max_workers,
                "request_delay": self.request_delay
            }
        }

    def cleanup(self, max_age_days: int = 30) -> None:
        """Clean up old files."""
        self.updater.cleanup_old_files(max_age_days)

    def set_performance_settings(self, max_workers: int = None, request_delay: float = None) -> None:
        """
        Update performance settings for the collector.

        Args:
            max_workers: Number of concurrent workers
            request_delay: Delay between requests in seconds
        """
        if max_workers is not None:
            self.max_workers = max_workers

        if request_delay is not None:
            self.request_delay = request_delay

        # Update the updater as well
        self.updater.set_performance_settings(max_workers, request_delay)


# Example usage and testing
if __name__ == "__main__":
    # Test the incremental updater
    updater = IncrementalUpdater("test_collector")

    # Test data
    test_data = {"players": ["Mike Trout", "Shohei Ohtani"], "count": 2}

    # Check for updates
    needs_update, reason = updater.check_for_updates(test_data)
    print(f"Needs update: {needs_update}, Reason: {reason}")

    # Update hash
    updater.update_hash(test_data)

    # Check again
    needs_update, reason = updater.check_for_updates(test_data)
    print(f"After update - Needs update: {needs_update}, Reason: {reason}")

    # Get status
    status = updater.get_hash_info()
    print(f"Status: {json.dumps(status, indent=2, default=str)}")
