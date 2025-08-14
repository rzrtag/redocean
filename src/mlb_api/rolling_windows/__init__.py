"""
Rolling Windows Analysis Module

A comprehensive system for collecting and analyzing MLB player performance
using rolling windows data from Baseball Savant.

This module provides:
- Enhanced data collection for all window sizes (50, 100, 250 PA)
"""

from .core.collector import EnhancedRollingCollector

__version__ = "2.0.0"

__all__ = [
    'EnhancedRollingCollector',
]
