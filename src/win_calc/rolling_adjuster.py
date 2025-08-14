from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

BASE_DATA = Path("/mnt/storage_fast/workspaces/red_ocean/_data")
ROLLING_DATA = (BASE_DATA / "mlb_api_2025" /
                "rolling_windows" / "data")


class RollingAdjuster:
    """Calculate rolling window adjustments for SaberSim projections."""

    def __init__(self):
        self.hitters_dir = ROLLING_DATA / "hitters"
        self.pitchers_dir = ROLLING_DATA / "pitchers"

    def load_player_rolling_data(self, player_id: str, player_type: str) -> Optional[Dict[str, Any]]:
        """Load rolling window data for a specific player."""
        try:
            if player_type == "hitter":
                data_file = self.hitters_dir / f"{player_id}.json"
            else:
                data_file = self.pitchers_dir / f"{player_id}.json"

            if not data_file.exists():
                logger.warning(f"No rolling data found for {player_type} {player_id}")
                return None

            with open(data_file, 'r') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error loading rolling data for {player_type} {player_id}: {e}")
            return None

    def calculate_hitter_adjustment(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate adjustment for hitter based on rolling xwOBA trends across event-based windows."""
        try:
            multi_window = player_data.get("multi_window_data", {})

            # Define window weights (50 events gets highest weight - most recent)
            window_weights = {
                "50": 0.5,   # 50% weight for most recent 50 events
                "100": 0.3,  # 30% weight for medium-term 100 events
                "250": 0.2   # 20% weight for long-term 250 events
            }

            adjustments = []
            total_weight = 0

            for window_size, weight in window_weights.items():
                window_data = multi_window.get(window_size, {})
                if not window_data:
                    continue

                series = window_data.get("series", [])
                if len(series) < 5:  # Need at least 5 events for meaningful trend
                    continue

                # For event-based windows, analyze trend across the series
                # Recent events are at the beginning of the series (most recent first)
                recent_events = series[:min(10, len(series)//2)]  # First 10 events or half
                older_events = series[-min(10, len(series)//2):]  # Last 10 events or half

                if len(recent_events) < 3 or len(older_events) < 3:
                    continue

                recent_xwoba = sum(e.get("xwoba", 0) for e in recent_events) / len(recent_events)
                older_xwoba = sum(e.get("xwoba", 0) for e in older_events) / len(older_events)

                # Calculate adjustment as percentage change
                if older_xwoba > 0:
                    trend_pct = (recent_xwoba - older_xwoba) / older_xwoba
                else:
                    trend_pct = 0.0

                # Apply confidence based on event sample size
                confidence = min(1.0, len(series) / int(window_size))

                # Weighted adjustment
                weighted_adj = trend_pct * confidence * weight
                adjustments.append(weighted_adj)
                total_weight += weight

            if not adjustments:
                return {"adjustment": 0.0, "confidence": 0.0, "reason": "No valid event window data"}

            # Calculate weighted average adjustment
            avg_adjustment = sum(adjustments) / total_weight if total_weight > 0 else 0.0

            # Cap adjustment at ±5% for MVP
            capped_adjustment = max(-0.05, min(0.05, avg_adjustment * 0.5))

            # Overall confidence based on available windows
            overall_confidence = min(1.0, total_weight)

            return {
                "adjustment": capped_adjustment,
                "confidence": overall_confidence,
                "windows_used": len(adjustments),
                "total_weight": total_weight,
                "reason": f"Multi-event trend: {capped_adjustment:.1%} adjustment using {len(adjustments)} event windows"
            }

        except Exception as e:
            logger.error(f"Error calculating hitter adjustment: {e}")
            return {"adjustment": 0.0, "confidence": 0.0, "reason": f"Calculation error: {e}"}

    def calculate_pitcher_adjustment(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate adjustment for pitcher based on rolling performance trends across event-based windows."""
        try:
            multi_window = player_data.get("multi_window_data", {})

            # Define window weights (50 events gets highest weight - most recent)
            window_weights = {
                "50": 0.5,   # 50% weight for most recent 50 events
                "100": 0.3,  # 30% weight for medium-term 100 events
                "250": 0.2   # 20% weight for long-term 250 events
            }

            adjustments = []
            total_weight = 0

            for window_size, weight in window_weights.items():
                window_data = multi_window.get(window_size, {})
                if not window_data:
                    continue

                series = window_data.get("series", [])
                if len(series) < 5:
                    continue

                # For pitchers, we want to see if they're improving (lower xwOBA = better)
                # Recent events are at the beginning of the series (most recent first)
                recent_events = series[:min(10, len(series)//2)]
                older_events = series[-min(10, len(series)//2):]

                if len(recent_events) < 3 or len(older_events) < 3:
                    continue

                recent_xwoba = sum(e.get("xwoba", 0) for e in recent_events) / len(recent_events)
                older_xwoba = sum(e.get("xwoba", 0) for e in older_events) / len(older_events)

                # For pitchers: improving = lower xwOBA, so we invert the trend
                if older_xwoba > 0:
                    trend_pct = (older_xwoba - recent_xwoba) / older_xwoba  # Inverted for pitchers
                else:
                    trend_pct = 0.0

                # Apply confidence based on event sample size
                confidence = min(1.0, len(series) / int(window_size))

                # Weighted adjustment
                weighted_adj = trend_pct * confidence * weight
                adjustments.append(weighted_adj)
                total_weight += weight

            if not adjustments:
                return {"adjustment": 0.0, "confidence": 0.0, "reason": "No valid event window data"}

            # Calculate weighted average adjustment
            avg_adjustment = sum(adjustments) / total_weight if total_weight > 0 else 0.0

            # Cap adjustment at ±5% for MVP
            capped_adjustment = max(-0.05, min(0.05, avg_adjustment * 0.5))

            # Overall confidence based on available windows
            overall_confidence = min(1.0, total_weight)

            return {
                "adjustment": capped_adjustment,
                "confidence": overall_confidence,
                "windows_used": len(adjustments),
                "total_weight": total_weight,
                "reason": f"Multi-event trend: {capped_adjustment:.1%} adjustment using {len(adjustments)} event windows"
            }

        except Exception as e:
            logger.error(f"Error calculating pitcher adjustment: {e}")
            return {"adjustment": 0.0, "confidence": 0.0, "reason": f"Calculation error: {e}"}

    def get_adjustment(self, player_id: str, player_type: str) -> Dict[str, Any]:
        """Get rolling window adjustment for a player."""
        player_data = self.load_player_rolling_data(player_id, player_type)
        if not player_data:
            return {"adjustment": 0.0, "confidence": 0.0, "reason": "No rolling data available"}

        if player_type == "hitter":
            return self.calculate_hitter_adjustment(player_data)
        else:
            return self.calculate_pitcher_adjustment(player_data)
