"""
MLB API configuration and settings.
"""

import os
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MLBConfig:
    """Configuration for MLB API collectors."""

    # Base paths
    base_data_path: Path = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025")

    # API settings
    mlb_api_base_url: str = "https://statsapi.mlb.com/api/v1"
    statcast_base_url: str = "https://baseballsavant.mlb.com/statcast_search/csv"

    # Rate limiting
    requests_per_second: int = 10
    max_retries: int = 3
    retry_delay: float = 1.0

    # Performance profiles
    PERFORMANCE_PROFILES = {
        'conservative': {'max_workers': 3, 'request_delay': 0.1},
        'balanced': {'max_workers': 5, 'request_delay': 0.05},
        'aggressive': {'max_workers': 8, 'request_delay': 0.02},
        'ultra_aggressive': {'max_workers': 12, 'request_delay': 0.01}
    }

    # Default performance profile
    default_performance_profile: str = 'aggressive'

    # Data retention
    max_cache_age_hours: int = 24
    enable_incremental_updates: bool = True

    # File patterns
    date_format: str = "%Y%m%d"
    timestamp_format: str = "%Y%m%d_%H%M%S"

    def __post_init__(self):
        """Convert string paths to Path objects."""
        if isinstance(self.base_data_path, str):
            self.base_data_path = Path(self.base_data_path)

    @property
    def active_rosters_path(self) -> Path:
        """Path to active rosters data."""
        return self.base_data_path / "active_rosters"

    @property
    def rolling_windows_path(self) -> Path:
        """Path to rolling windows data."""
        return self.base_data_path / "rolling_windows"

    @property
    def statcast_path(self) -> Path:
        """Path to Statcast data."""
        return self.base_data_path / "statcast_adv_box"

    def ensure_directories(self):
        """Create all necessary directories."""
        for path in [self.active_rosters_path, self.rolling_windows_path, self.statcast_path]:
            path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> 'MLBConfig':
        """Create config from environment variables."""
        return cls(
            base_data_path=os.getenv('MLB_DATA_PATH', "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025"),
            requests_per_second=int(os.getenv('MLB_REQUESTS_PER_SECOND', '10')),
            max_retries=int(os.getenv('MLB_MAX_RETRIES', '3')),
            enable_incremental_updates=os.getenv('MLB_INCREMENTAL_UPDATES', 'true').lower() == 'true'
        )

    def get_performance_settings(self, profile: str = None) -> dict:
        """Get performance settings for a specific profile."""
        if profile is None:
            profile = self.default_performance_profile

        if profile not in self.PERFORMANCE_PROFILES:
            logger.warning(f"Unknown performance profile '{profile}', using 'balanced'")
            profile = 'balanced'

        return self.PERFORMANCE_PROFILES[profile].copy()
