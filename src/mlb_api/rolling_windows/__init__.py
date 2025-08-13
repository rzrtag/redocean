"""
Rolling Windows Analysis Module

A comprehensive system for collecting and analyzing MLB player performance
using rolling windows data from Baseball Savant.

This module provides:
- Enhanced data collection for all window sizes (50, 100, 250 PA)
- Histogram data integration for comprehensive player analysis
- Advanced statistical analysis and projections
- Optimized data processing and storage
"""

from .core.collector import EnhancedRollingCollector
from .analysis.rolling_analyzer import RollingWindowsAnalyzer
from .analysis.histogram_analyzer import HistogramAnalyzer
from .analysis.enhanced_analyzer import EnhancedRollingAnalyzer
from .projections.rolling_projections import ProjectionGenerator

__version__ = "2.0.0"

__all__ = [
    # Core collection
    'EnhancedRollingCollector',

    # Analysis
    'RollingWindowsAnalyzer',
    'HistogramAnalyzer',
    'EnhancedRollingAnalyzer',

            # Projections
        'ProjectionGenerator',
]
