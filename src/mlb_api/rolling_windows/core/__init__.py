"""
Core Rolling Windows Collection Module

Provides the fundamental data collection and API interaction
for MLB Savant rolling windows data.
"""

from .collector import EnhancedRollingCollector

__all__ = [
    'EnhancedRollingCollector',
]
