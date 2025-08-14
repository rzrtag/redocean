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
        """Calculate adjustment for hitter based on rolling xwOBA trends across all windows."""
        try:
            multi_window = player_data.get("multi_window_data", {})
            
            # Define window weights (50-game window gets highest weight)
            window_weights = {
                "50": 0.5,   # 50% weight for most recent data
                "100": 0.3,  # 30% weight for medium-term
                "250": 0.2   # 20% weight for long-term
            }
            
            adjustments = []
            total_weight = 0
            
            for window_size, weight in window_weights.items():
                window_data = multi_window.get(window_size, {})
                if not window_data:
                    continue
                    
                series = window_data.get("series", [])
                if len(series) < 10:  # Need at least 10 games for meaningful trend
                    continue
                
                # Calculate trend: recent vs older performance
                recent_games = series[:10]  # Last 10 games
                older_games = series[-10:]  # 10 games from older part of window
                
                recent_xwoba = sum(g.get("xwoba", 0) for g in recent_games) / len(recent_games)
                older_xwoba = sum(g.get("xwoba", 0) for g in older_games) / len(older_games)
                
                # Calculate adjustment as percentage change
                if older_xwoba > 0:
                    trend_pct = (recent_xwoba - older_xwoba) / older_xwoba
                else:
                    trend_pct = 0.0
                
                # Apply confidence based on sample size
                confidence = min(1.0, len(series) / int(window_size))
                
                # Weighted adjustment
                weighted_adj = trend_pct * confidence * weight
                adjustments.append(weighted_adj)
                total_weight += weight
            
            if not adjustments:
                return {"adjustment": 0.0, "confidence": 0.0, "reason": "No valid window data"}
            
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
                "reason": f"Multi-window trend: {capped_adjustment:.1%} adjustment using {len(adjustments)} windows"
            }
            
        except Exception as e:
            logger.error(f"Error calculating hitter adjustment: {e}")
            return {"adjustment": 0.0, "confidence": 0.0, "reason": f"Calculation error: {e}"}
    
    def calculate_pitcher_adjustment(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate adjustment for pitcher based on rolling performance trends across all windows."""
        try:
            multi_window = player_data.get("multi_window_data", {})
            
            # Define window weights (50-game window gets highest weight)
            window_weights = {
                "50": 0.5,   # 50% weight for most recent data
                "100": 0.3,  # 30% weight for medium-term
                "250": 0.2   # 20% weight for long-term
            }
            
            adjustments = []
            total_weight = 0
            
            for window_size, weight in window_weights.items():
                window_data = multi_window.get(window_size, {})
                if not window_data:
                    continue
                    
                series = window_data.get("series", [])
                if len(series) < 10:
                    continue
                
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
                
                # Apply confidence based on sample size
                confidence = min(1.0, len(series) / int(window_size))
                
                # Weighted adjustment
                weighted_adj = trend_pct * confidence * weight
                adjustments.append(weighted_adj)
                total_weight += weight
            
            if not adjustments:
                return {"adjustment": 0.0, "confidence": 0.0, "reason": "No valid window data"}
            
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
                "reason": f"Multi-window trend: {capped_adjustment:.1%} adjustment using {len(adjustments)} windows"
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
