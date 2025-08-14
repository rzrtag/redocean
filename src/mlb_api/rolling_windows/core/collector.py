"""
Enhanced Rolling Windows Collector with Hash-Based Incremental Updates

Provides comprehensive data collection for MLB player rolling windows
data from Baseball Savant, including all window sizes and histogram data.
Uses the shared hash system for intelligent incremental updates.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RollingWindowConfig:
    """Configuration for rolling windows collection"""
    max_workers: int = 4
    request_delay: float = 0.5
    timeout: int = 30
    retry_attempts: int = 3
    season_year: int = 2025


class EnhancedRollingCollector:
    """Enhanced rolling windows collector using Baseball Savant JSON endpoints"""

    def __init__(self, data_dir: Path, performance_profile: str = "balanced",
                 season_year: int = 2025):
        self.data_dir = Path(data_dir)
        self.hitters_dir = self.data_dir / "data" / "hitters"
        self.pitchers_dir = self.data_dir / "data" / "pitchers"

        # Create directories
        self.hitters_dir.mkdir(parents=True, exist_ok=True)
        self.pitchers_dir.mkdir(parents=True, exist_ok=True)

        # Performance configuration
        profiles = {
            "conservative": RollingWindowConfig(max_workers=2, request_delay=1.0),
            "balanced": RollingWindowConfig(max_workers=4, request_delay=0.5),
            "aggressive": RollingWindowConfig(max_workers=8, request_delay=0.2),
            "super_aggressive": RollingWindowConfig(max_workers=20, request_delay=0.005)
        }
        # Base profile
        self.config = profiles.get(performance_profile, profiles["balanced"])
        # Override season if provided
        self.config.season_year = season_year

        # Baseball Savant endpoints
        self.rolling_url = "https://baseballsavant.mlb.com/player-services/rolling-thumb"
        self.histogram_url = "https://baseballsavant.mlb.com/player-services/histogram"

        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'),
            'Accept': '*/*',
            'X-Requested-With': 'XMLHttpRequest'
        })

        logger.info(
            f"🚀 Rolling windows collector initialized with {performance_profile} "
            f"profile: {self.config.max_workers} workers, {self.config.request_delay}s delay, "
            f"season={self.config.season_year}"
        )

    def collect_all_players(self, player_ids: List[str],
                           player_types: List[str] = None) -> Dict[str, Any]:
        """Collect rolling windows data for all players"""
        if player_types is None:
            player_types = ["hitter", "pitcher"]

        results = {
            "success": [],
            "failed": [],
            "skipped": []
        }

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {}

            # submit with gentle pacing to avoid bursty traffic
            for player_id in player_ids:
                for player_type in player_types:
                    fut = executor.submit(
                        self._collect_single_player, player_id, player_type
                    )
                    futures[fut] = (player_id, player_type)
                    time.sleep(self.config.request_delay)

            # process completions as they finish to avoid head-of-line blocking
            for fut in as_completed(futures):
                player_id, player_type = futures[fut]
                try:
                    result = fut.result(timeout=self.config.timeout * 2)
                    if result.get("skipped"):
                        results["skipped"].append(
                            f"{player_id}_{player_type}"
                        )
                    elif result.get("success"):
                        results["success"].append(
                            f"{player_id}_{player_type}"
                        )
                    else:
                        results["failed"].append(
                            f"{player_id}_{player_type}: "
                            f"{result.get('error','unknown')}"
                        )
                except Exception as e:
                    results["failed"].append(
                        f"{player_id}_{player_type}: {str(e)}"
                    )

        logger.info(
            f"✅ Collection complete: {len(results['success'])} success, "
            f"{len(results['failed'])} failed, {len(results['skipped'])} skipped"
        )
        return results

    def _collect_single_player(self, player_id: str,
                              player_type: str) -> Dict[str, Any]:
        """Collect rolling windows data for a single player"""
        try:
            # Determine position code for API
            pos_code = self._get_position_code(player_type)

            # Collect rolling windows data
            rolling_data = self._fetch_rolling_windows(player_id, pos_code)
            if not rolling_data:
                return {
                    "success": False,
                    "skipped": True,
                    "error": "No rolling windows data available",
                }

            # Skip writing empty files: ensure at least one window has data
            def _series_len(win_key: str) -> int:
                return len(rolling_data.get(win_key, {}).get("series", []))

            if _series_len("50") == 0 and _series_len("100") == 0 and _series_len("250") == 0:
                return {
                    "success": False,
                    "skipped": True,
                    "error": "Empty rolling windows (no qualified events)",
                }

            # Collect histogram data
            histogram_data = self._fetch_histogram_data(player_id, pos_code)

            # Combine data
            combined_data = {
                "player_id": player_id,
                "player_type": player_type,
                "rolling_windows": rolling_data,
                "histogram_data": histogram_data,
                "collected_at": time.time()
            }

            # Save to file
            output_file = self._get_output_file(player_id, player_type)
            with open(output_file, 'w') as f:
                json.dump(combined_data, f, indent=2)

            logger.info(f"✅ Collected data for {player_type} {player_id}")
            return {"success": True, "data": combined_data}

        except Exception as e:
            logger.error(
                f"❌ Failed to collect data for {player_type} {player_id}: {str(e)}"
            )
            return {"success": False, "error": str(e)}

    def _fetch_rolling_windows(self, player_id: str,
                              pos_code: str) -> Optional[Dict[str, Any]]:
        """Fetch rolling windows data from Baseball Savant"""
        params = {
            'playerId': player_id,
            'playerType': pos_code
        }

        for attempt in range(self.config.retry_attempts):
            try:
                response = self.session.get(self.rolling_url, params=params,
                                          timeout=self.config.timeout)
                response.raise_for_status()

                data = response.json()

                # Transform data to our format
                transformed_data = {
                    "50": self._transform_window_data(data.get("plate50", [])),
                    "100": self._transform_window_data(data.get("plate100", [])),
                    "250": self._transform_window_data(data.get("plate250", []))
                }

                return transformed_data

            except requests.exceptions.RequestException as e:
                if attempt == self.config.retry_attempts - 1:
                    logger.error(
                        f"Failed to fetch rolling windows for {player_id}: {str(e)}"
                    )
                    return None
                time.sleep(1)

        return None

    def _fetch_histogram_data(self, player_id: str,
                             pos_code: str) -> Dict[str, Any]:
        """Fetch histogram data from Baseball Savant"""
        histogram_data = {}

        # Exit velocity histogram
        ev_data = self._fetch_single_histogram(player_id, pos_code,
                                              "api_h_launch_speed")
        if ev_data:
            histogram_data["exit_velocity"] = ev_data

        # Launch angle histogram
        la_data = self._fetch_single_histogram(player_id, pos_code,
                                              "api_h_launch_angle")
        if la_data:
            histogram_data["launch_angle"] = la_data

        # Pitch speed histogram (for pitchers)
        if pos_code in ["1", "2", "3", "4", "5"]:  # Pitcher position codes
            ps_data = self._fetch_single_histogram(player_id, pos_code,
                                                  "api_p_release_speed")
            if ps_data:
                histogram_data["pitch_speed"] = ps_data

        return histogram_data

    def _fetch_single_histogram(self, player_id: str, pos_code: str,
                                field_type: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch a single histogram from Baseball Savant"""
        params = {
            'playerId': player_id,
            'pos': pos_code,
            'fieldType': field_type,
            'hand': '',
            'size': '5',
            'season': str(self.config.season_year),
            'event': 'pitch_count',
            'pitchType': ''
        }

        try:
            response = self.session.get(self.histogram_url, params=params,
                                      timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Failed to fetch {field_type} histogram for {player_id}: {str(e)}"
            )
            return None

    def _transform_window_data(self, window_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform rolling window data to our format"""
        if not window_data:
            return {"series": [], "summary": {}}

        # Filter to desired season year (keep only entries within the season)
        season_str = str(self.config.season_year)
        filtered = []
        for entry in window_data:
            dt = entry.get("max_game_date", "")
            year_ok = isinstance(dt, str) and dt[:4] == season_str
            if year_ok:
                filtered.append(entry)

        series = []
        for entry in filtered:
            series.append({
                "xwoba": float(entry.get("xwoba", 0)),
                "max_game_date": entry.get("max_game_date", ""),
                "x_numer": float(entry.get("x_numer", 0)),
                "x_denom": float(entry.get("x_denom", 0)),
                "rn": int(entry.get("rn", 0))
            })

        # Calculate summary stats
        if series:
            xwobas = [s["xwoba"] for s in series]
            summary = {
                "count": len(series),
                "avg_xwoba": sum(xwobas) / len(xwobas),
                "min_xwoba": min(xwobas),
                "max_xwoba": max(xwobas),
                "latest_xwoba": series[0]["xwoba"] if series else 0
            }
        else:
            summary = {"count": 0, "avg_xwoba": 0, "min_xwoba": 0,
                      "max_xwoba": 0, "latest_xwoba": 0}

        return {
            "series": series,
            "summary": summary
        }

    def _get_position_code(self, player_type: str) -> str:
        """Get position code for Baseball Savant API"""
        # Position codes: 1=P, 2=C, 3=1B, 4=2B, 5=3B, 6=SS, 7=LF, 8=CF, 9=RF
        if player_type == "pitcher":
            return "1"
        elif player_type == "hitter":
            return "9"  # Default to RF for hitters, API will return all positions
        else:
            return "9"

    def _get_output_file(self, player_id: str, player_type: str) -> Path:
        """Get output file path for player data"""
        if player_type == "hitter":
            return self.hitters_dir / f"{player_id}.json"
        else:
            return self.pitchers_dir / f"{player_id}.json"

    def collect_single_player(self, player_id: str,
                             player_type: str) -> Dict[str, Any]:
        """Collect data for a single player (public interface)"""
        return self._collect_single_player(player_id, player_type)
