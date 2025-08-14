#!/usr/bin/env python3
"""
Fangraphs Incremental Updater

Base class for Fangraphs data collectors with hash-based incremental updates.
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import fg_config
from .hash_manager import FGHashManager


logger = logging.getLogger(__name__)


class FGIncrementalUpdater:
    """Base class for Fangraphs data collectors with incremental updates."""

    def __init__(self, collector_name: str, performance_profile: str = 'balanced',
                 max_workers: int = None, request_delay: float = None):
        """Initialize the incremental updater."""
        self.collector_name = collector_name
        self.performance_profile = performance_profile

        # Get performance settings
        settings = fg_config.get_performance_settings(performance_profile)
        self.max_workers = max_workers or settings['max_workers']
        self.request_delay = request_delay or settings['request_delay']
        self.timeout = settings['timeout']

        # Initialize directories and hash manager
        self.data_dir = fg_config.get_collector_dir(collector_name)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.hash_manager = FGHashManager(collector_name)

        # Progress tracking
        self.progress_stats = {
            'updated': 0,
            'skipped': 0,
            'failed': 0,
            'start_time': None,
            'current_item': 0,
            'total_items': 0
        }

    def set_performance_settings(self, profile: str):
        """Set performance profile."""
        self.performance_profile = profile
        settings = fg_config.get_performance_settings(profile)
        self.max_workers = settings['max_workers']
        self.request_delay = settings['request_delay']
        self.timeout = settings['timeout']

    def _update_progress(self, action: str):
        """Update progress statistics."""
        if action in self.progress_stats:
            self.progress_stats[action] += 1

        self.progress_stats['current_item'] += 1

        # Calculate ETA
        if self.progress_stats['start_time'] and self.progress_stats['current_item'] > 0:
            elapsed = time.time() - self.progress_stats['start_time']
            rate = self.progress_stats['current_item'] / elapsed
            remaining = self.progress_stats['total_items'] - self.progress_stats['current_item']
            eta = remaining / rate if rate > 0 else 0

            # Display progress
            progress_pct = (self.progress_stats['current_item'] /
                           self.progress_stats['total_items'] * 100)

            print(f"\r🔄 Progress: {progress_pct:.1f}% "
                  f"({self.progress_stats['current_item']}/{self.progress_stats['total_items']}) "
                  f"| Updated: {self.progress_stats['updated']} "
                  f"Skipped: {self.progress_stats['skipped']} "
                  f"Failed: {self.progress_stats['failed']} "
                  f"| ETA: {eta:.0f}s", end='', flush=True)

    def _display_final_progress(self):
        """Display final progress summary."""
        elapsed = time.time() - self.progress_stats['start_time']
        print(f"\n✅ Collection completed in {elapsed:.1f}s")
        print(f"📊 Summary: {self.progress_stats['updated']} updated, "
              f"{self.progress_stats['skipped']} skipped, "
              f"{self.progress_stats['failed']} failed")

    def collect_team_data(self, team_abbr: str, level: str = 'MLB') -> Dict[str, Any]:
        """Collect data for a specific team and level. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement collect_team_data")

    def process_team_data(self, team_abbr: str, level: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw team data. Override in subclasses for custom processing."""
        return {
            'team_abbr': team_abbr,
            'level': level,
            'collection_timestamp': datetime.now().isoformat(),
            'players': raw_data,
            'metadata': {
                'total_players': len(raw_data),
                'mlb_players': len([p for p in raw_data if p.get('mlevel') == 'MLB']),
                'collection_method': self.collector_name
            }
        }

    def save_team_data(self, team_abbr: str, level: str, data: Dict[str, Any]) -> str:
        """Save team data to file."""
        filename = fg_config.generate_filename(team_abbr, level)
        file_path = self.data_dir / filename

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

        return str(file_path)

    def collect_single_team(self, team_abbr: str, level: str = 'MLB') -> Dict[str, Any]:
        """Collect data for a single team with incremental update logic."""
        try:
            # Collect raw data
            raw_data = self.collect_team_data(team_abbr, level)

            # Process data
            processed_data = self.process_team_data(team_abbr, level, raw_data)

            # Check if update is needed
            needs_update, reason = self.hash_manager.needs_update(
                team_abbr, level, processed_data)

            if needs_update:
                # Save data and update hash
                file_path = self.save_team_data(team_abbr, level, processed_data)
                data_hash = self.hash_manager.calculate_data_hash(processed_data)
                self.hash_manager.save_hash(team_abbr, level, data_hash,
                                          processed_data, file_path)

                self._update_progress('updated')
                return {
                    'success': True,
                    'team_abbr': team_abbr,
                    'level': level,
                    'updated': True,
                    'reason': reason,
                    'player_count': len(processed_data.get('players', []))
                }
            else:
                self._update_progress('skipped')
                return {
                    'success': True,
                    'team_abbr': team_abbr,
                    'level': level,
                    'updated': False,
                    'reason': reason,
                    'player_count': len(processed_data.get('players', []))
                }

        except Exception as e:
            self._update_progress('failed')
            logger.error(f"Failed to collect {team_abbr} {level}: {e}")
            return {
                'success': False,
                'team_abbr': team_abbr,
                'level': level,
                'error': str(e)
            }

    def _pre_check_updates_needed(self, teams: List[str], levels: List[str]) -> Dict[str, List[str]]:
        """Pre-check which teams need updates by examining existing data files."""
        teams_needing_updates = {level: [] for level in levels}
        
        for team_abbr in teams:
            for level in levels:
                # Check if we have existing data file
                filename = fg_config.generate_filename(team_abbr, level)
                data_file = self.data_dir / filename
                
                if not data_file.exists():
                    # No existing data, needs update
                    teams_needing_updates[level].append(team_abbr)
                    continue
                
                # Check if hash file exists
                hash_file = self.hash_manager.get_hash_file_path(team_abbr, level)
                if not hash_file.exists():
                    # No hash file, needs update
                    teams_needing_updates[level].append(team_abbr)
                    continue
                
                # Check file age - if older than 24 hours, mark for update
                file_age_hours = (time.time() - data_file.stat().st_mtime) / 3600
                if file_age_hours > 24:
                    teams_needing_updates[level].append(team_abbr)
                    continue
        
        return teams_needing_updates

    def collect_all_teams(self, levels: List[str] = None,
                         teams: List[str] = None) -> Dict[str, Any]:
        """Collect data for all teams and levels."""
        levels = levels or ['MLB']
        teams = teams or list(fg_config.get_mlb_teams().keys())

        # Initialize progress tracking
        self.progress_stats = {
            'updated': 0,
            'skipped': 0,
            'failed': 0,
            'start_time': time.time(),
            'current_item': 0,
            'total_items': len(teams) * len(levels)
        }

        print(f"🚀 Starting {self.collector_name} collection")
        print(f"📊 Teams: {len(teams)}, Levels: {len(levels)}")
        print(f"⚙️  Workers: {self.max_workers}, Delay: {self.request_delay}s")

        results = []

        # Create collection tasks
        tasks = []
        for team_abbr in teams:
            for level in levels:
                tasks.append((team_abbr, level))

        # Execute with thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self.collect_single_team, team_abbr, level): (team_abbr, level)
                for team_abbr, level in tasks
            }

            for future in as_completed(future_to_task):
                result = future.result()
                results.append(result)

                # Add delay between requests
                time.sleep(self.request_delay)

        # Display final progress
        self._display_final_progress()

        # Generate summary
        summary = {
            'collector_name': self.collector_name,
            'collection_timestamp': datetime.now().isoformat(),
            'total_teams': len(teams),
            'levels': levels,
            'results': results,
            'summary': {
                'updated': self.progress_stats['updated'],
                'skipped': self.progress_stats['skipped'],
                'failed': self.progress_stats['failed'],
                'total_players': sum(r.get('player_count', 0) for r in results if r['success'])
            }
        }

        return summary

    def collect_all_teams_efficient(self, levels: List[str] = None,
                                  teams: List[str] = None, force_update: bool = False) -> Dict[str, Any]:
        """Efficient collection that pre-checks what needs updating."""
        levels = levels or ['MLB']
        teams = teams or list(fg_config.get_mlb_teams().keys())

        print(f"🚀 Starting efficient {self.collector_name} collection")
        print(f"📊 Teams: {len(teams)}, Levels: {len(levels)}")
        
        # Pre-check what needs updates (unless force update)
        if force_update:
            print("🔄 Force update mode - collecting all teams")
            teams_needing_updates = {level: teams for level in levels}
        else:
            print("🔍 Pre-checking which teams need updates...")
            teams_needing_updates = self._pre_check_updates_needed(teams, levels)
        
        total_needing_updates = sum(len(team_list) for team_list in teams_needing_updates.values())
        total_teams = len(teams) * len(levels)
        
        print(f"📈 Efficiency: {total_needing_updates}/{total_teams} teams need updates ({total_needing_updates/total_teams*100:.1f}%)")
        
        if total_needing_updates == 0:
            print("✅ All teams are current - no API calls needed!")
            return {
                'collector_name': self.collector_name,
                'collection_timestamp': datetime.now().isoformat(),
                'total_teams': total_teams,
                'levels': levels,
                'results': [],
                'summary': {
                    'updated': 0,
                    'skipped': total_teams,
                    'failed': 0,
                    'total_players': 0,
                    'api_calls_saved': total_teams
                }
            }
        
        # Only collect teams that need updates
        tasks = []
        for level in levels:
            for team_abbr in teams_needing_updates[level]:
                tasks.append((team_abbr, level))
        
        # Initialize progress tracking
        self.progress_stats = {
            'updated': 0,
            'skipped': 0,
            'failed': 0,
            'start_time': time.time(),
            'current_item': 0,
            'total_items': len(tasks)
        }
        
        print(f"⚙️  Workers: {self.max_workers}, Delay: {self.request_delay}s")
        print(f"🎯 Making API calls for {len(tasks)} teams that need updates")

        results = []

        # Execute with thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self.collect_single_team, team_abbr, level): (team_abbr, level)
                for team_abbr, level in tasks
            }

            for future in as_completed(future_to_task):
                result = future.result()
                results.append(result)

                # Add delay between requests
                time.sleep(self.request_delay)

        # Display final progress
        self._display_final_progress()

        # Generate summary
        summary = {
            'collector_name': self.collector_name,
            'collection_timestamp': datetime.now().isoformat(),
            'total_teams': total_teams,
            'levels': levels,
            'results': results,
            'summary': {
                'updated': self.progress_stats['updated'],
                'skipped': total_teams - self.progress_stats['updated'] - self.progress_stats['failed'],
                'failed': self.progress_stats['failed'],
                'total_players': sum(r.get('player_count', 0) for r in results if r['success']),
                'api_calls_saved': total_teams - len(tasks)
            }
        }

        return summary

    def get_collection_status(self) -> Dict[str, Any]:
        """Get current collection status."""
        return self.hash_manager.get_collection_summary()
