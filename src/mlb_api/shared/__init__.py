"""
Shared modules for MLB API collectors.

This package provides common functionality for all MLB API collectors:
- Incremental update framework
- Hash-based change detection
- Base collector classes
"""

from .incremental_updater import IncrementalUpdater, MLBAPICollector

__all__ = ['IncrementalUpdater', 'MLBAPICollector']
__version__ = '1.0.0'
