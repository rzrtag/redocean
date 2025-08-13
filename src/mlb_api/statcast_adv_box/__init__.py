"""
Statcast Advanced Box Score Data Collection Module

Provides comprehensive MLB Statcast data collection with hash-based incremental updates.
Collects advanced metrics per at-bat including expected stats, pitch physics,
and contact quality data with integrated fantasy points.

Clean, consolidated structure:
- statcast_collector: Integrated hash-based collector with ultra-aggressive performance
- run_statcast_collector: Modern runner script with performance profiles
- stats: Boxscore stats extraction for fantasy points
- scoring: DraftKings and FanDuel fantasy points calculation

Output: Hybrid structure with both date-based files (like cosmic_grid) AND player-based files for analysis
"""

from .statcast_collector import StatcastAdvancedCollector
from .scoring import FantasyScoring
from .stats import extract_boxscore_stats

__all__ = [
    'StatcastAdvancedCollector',   # Main integrated collector
    'FantasyScoring',              # Fantasy points calculation
    'extract_boxscore_stats'       # Boxscore stats extraction
]

__version__ = '3.0.0'
