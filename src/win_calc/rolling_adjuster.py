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
        """Calculate adjustment for hitter based on rolling xwOBA trends."""
        try:
            multi_window = player_data.get("multi_window_data", {})

            # Focus on 50-game window for MVP (most recent data)
            window_50 = multi_window.get("50", {})
            if not window_50:
                return {"adjustment": 0.0, "confidence": 0.0, "reason": "No 50-game window data"}

            series = window_50.get("series", [])
            if len(series) < 10:  # Need at least 10 games for meaningful trend
                return {"adjustment": 0.0, "confidence": 0.0, "reason": "Insufficient recent games"}

            # Calculate trend: recent vs older performance
            recent_games = series[:10]  # Last 10 games
            older_games = series[-10:]  # 10 games from 40-50 games ago

            recent_xwoba = sum(g.get("xwoba", 0) for g in recent_games) / len(recent_games)
            older_xwoba = sum(g.get("xwoba", 0) for g in older_games) / len(older_games)

            # Calculate adjustment as percentage change
            if older_xwoba > 0:
                trend_pct = (recent_xwoba - older_xwoba) / older_xwoba
            else:
                trend_pct = 0.0

            # Apply confidence based on sample size and variance
            confidence = min(1.0, len(series) / 50.0)  # Scale confidence by games available

            # Cap adjustment at ±5% for MVP
            capped_adjustment = max(-0.05, min(0.05, trend_pct * 0.5))  # Scale down trend

            return {
                "adjustment": capped_adjustment,
                "confidence": confidence,
                "recent_xwoba": recent_xwoba,
                "older_xwoba": older_xwoba,
                "trend_pct": trend_pct,
                "games_analyzed": len(series),
                "reason": f"Recent trend: {trend_pct:.1%} change over {len(series)} games"
            }

        except Exception as e:
            logger.error(f"Error calculating hitter adjustment: {e}")
            return {"adjustment": 0.0, "confidence": 0.0, "reason": f"Calculation error: {e}"}

    def calculate_pitcher_adjustment(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate adjustment for pitcher based on rolling performance trends."""
        try:
            multi_window = player_data.get("multi_window_data", {})

            # Focus on 50-game window for MVP
            window_50 = multi_window.get("50", {})
            if not window_50:
                return {"adjustment": 0.0, "confidence": 0.0, "reason": "No 50-game window data"}

            series = window_50.get("series", [])
            if len(series) < 10:
                return {"adjustment": 0.0, "confidence": 0.0, "reason": "Insufficient recent games"}

            # For pitchers, we want to see if they're improving (lower xwOBA = better)
            recent_games = series[:10]
            older_games = series[-10:]

            recent_xwoba = sum(g.get("xwoba", 0) for g in recent_games) / len(recent_games)
            older_xwoba = sum(g.get("xwoba", 0) for g in older_games) / len(older_games)

            # For pitchers: improving = lower xwOBA, so we invert the trend
            if older_xwoba > 0:
                trend_pct = (older_xwoba - recent_xwoba) / older_xwoba  # Inverted for pitchers
            else:
                trend_pct = 0.0

            confidence = min(1.0, len(series) / 50.0)
            capped_adjustment = max(-0.05, min(0.05, trend_pct * 0.5))

            return {
                "adjustment": capped_adjustment,
                "confidence": confidence,
                "recent_xwoba": recent_xwoba,
                "older_xwoba": older_xwoba,
                "trend_pct": trend_pct,
                "games_analyzed": len(series),
                "reason": f"Recent trend: {trend_pct:.1%} improvement over {len(series)} games"
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
