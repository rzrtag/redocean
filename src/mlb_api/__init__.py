"""
MLB API Collectors Package

A comprehensive system for collecting MLB data with incremental update support.
Each collector uses hash-based change detection to minimize API calls and ensure
only new/changed data is downloaded.

Available Collectors:
- rosters: Active player rosters from all teams
- stats: Player statistics and performance data
- schedules: Game schedules and results

Features:
- True incremental updates using SHA-256 hashing
- Automatic change detection
- Efficient caching and storage
- Shared framework for consistency
"""

from .shared import IncrementalUpdater, MLBAPICollector

__all__ = ['IncrementalUpdater', 'MLBAPICollector']
__version__ = '1.0.0'
__description__ = 'MLB API Collectors with Incremental Update Support'
