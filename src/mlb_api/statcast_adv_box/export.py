#!/usr/bin/env python3
"""
Simple Export Helper

Just returns the main statcast data file path - no separate exports needed.
"""

from pathlib import Path
from typing import Optional

def get_statcast_file_path(collector, date_str: str) -> Optional[Path]:
    """
    Get the path to the main statcast data file for a specific date.

    Args:
        collector: StatcastCollector instance
        date_str: Date in YYYY-MM-DD format

    Returns:
        Path to the statcast data file, or None if no data exists
    """
    # Check if we have data for this date
    filename = f"advanced_statcast_{date_str.replace('-', '')}.json"
    filepath = collector.output_dir / filename

    if not filepath.exists():
        print(f"No data found for {date_str}")
        return None

    return filepath