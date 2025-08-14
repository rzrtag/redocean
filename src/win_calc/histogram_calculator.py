#!/usr/bin/env python3
"""
Histogram Calculator for Statcast Data

Calculates histograms from our existing Statcast data instead of fetching from Baseball Savant API.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

BASE_DATA = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/statcast_adv_box/data")


class HistogramCalculator:
    """Calculate histograms from existing Statcast data."""
    
    def __init__(self):
        self.batter_dir = BASE_DATA / "batter"
        self.pitcher_dir = BASE_DATA / "pitcher"
    
    def get_player_histograms(self, player_id: str, player_type: str = "batter") -> Dict[str, Any]:
        """Get histogram data for a player from existing Statcast data."""
        
        if player_type == "batter":
            data_file = self.batter_dir / f"{player_id}.json"
        else:
            data_file = self.pitcher_dir / f"{player_id}.json"
        
        if not data_file.exists():
            logger.warning(f"No Statcast data found for {player_type} {player_id}")
            return {}
        
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            # Extract all at-bats
            all_at_bats = []
            for game_data in data['games'].values():
                all_at_bats.extend(game_data.get('batter_at_bats', []))
            
            if not all_at_bats:
                logger.warning(f"No at-bats found for {player_type} {player_id}")
                return {}
            
            logger.info(f"Processing {len(all_at_bats)} at-bats for {player_type} {player_id}")
            
            # Calculate histograms
            if player_type == "batter":
                return {
                    "exit_velocity": self._calculate_exit_velocity_histogram(all_at_bats),
                    "launch_angle": self._calculate_launch_angle_histogram(all_at_bats),
                    "pitch_speed": self._calculate_pitch_speed_histogram(all_at_bats)
                }
            else:
                return {
                    "pitch_speed": self._calculate_pitch_speed_histogram(all_at_bats),
                    "spin_rate": self._calculate_spin_rate_histogram(all_at_bats)
                }
                
        except Exception as e:
            logger.error(f"Error processing {player_type} {player_id}: {e}")
            return {}
    
    def _calculate_exit_velocity_histogram(self, at_bats: List[Dict]) -> List[Dict[str, Any]]:
        """Calculate exit velocity histogram from at-bats."""
        histogram = []
        
        # Extract exit velocities (only for actual hits)
        exit_velocities = []
        for ab in at_bats:
            try:
                ev = float(ab.get('exit_velocity', 0))
                if ev > 0:  # Only include actual hits
                    exit_velocities.append(ev)
            except (ValueError, TypeError):
                continue
        
        if not exit_velocities:
            return []
        
        # Create histogram bins (80-110 mph in 2 mph increments)
        bins = list(range(80, 112, 2))
        hist, bin_edges = np.histogram(exit_velocities, bins=bins)
        
        total_at_bats = len(at_bats)
        
        for i, count in enumerate(hist):
            if count > 0:
                bin_center = (bin_edges[i] + bin_edges[i+1]) / 2
                histogram.append({
                    "histogram_value": str(int(bin_center)),
                    "pitch_count": str(count),
                    "total_pitches": str(total_at_bats),
                    "ev": str(bin_center),
                    "pitch_percent": str(round(count / total_at_bats * 100, 1))
                })
        
        return histogram
    
    def _calculate_launch_angle_histogram(self, at_bats: List[Dict]) -> List[Dict[str, Any]]:
        """Calculate launch angle histogram from at-bats."""
        histogram = []
        
        # Extract launch angles (only for actual hits)
        launch_angles = []
        for ab in at_bats:
            try:
                la = float(ab.get('launch_angle', 0))
                if la != 0:  # Only include actual hits
                    launch_angles.append(la)
            except (ValueError, TypeError):
                continue
        
        if not launch_angles:
            return []
        
        # Create histogram bins (-45 to +45 degrees in 5 degree increments)
        bins = list(range(-45, 50, 5))
        hist, bin_edges = np.histogram(launch_angles, bins=bins)
        
        total_at_bats = len(at_bats)
        
        for i, count in enumerate(hist):
            if count > 0:
                bin_center = (bin_edges[i] + bin_edges[i+1]) / 2
                histogram.append({
                    "histogram_value": str(int(bin_center)),
                    "pitch_count": str(count),
                    "total_pitches": str(total_at_bats),
                    "la": str(bin_center),
                    "pitch_percent": str(round(count / total_at_bats * 100, 1))
                })
        
        return histogram
    
    def _calculate_pitch_speed_histogram(self, at_bats: List[Dict]) -> List[Dict[str, Any]]:
        """Calculate pitch speed histogram from at-bats."""
        histogram = []
        
        # Extract pitch speeds (start_speed)
        pitch_speeds = []
        for ab in at_bats:
            try:
                speed = float(ab.get('start_speed', 0))
                if speed > 0:
                    pitch_speeds.append(speed)
            except (ValueError, TypeError):
                continue
        
        if not pitch_speeds:
            return []
        
        # Create histogram bins (75-105 mph in 2 mph increments)
        bins = list(range(75, 107, 2))
        hist, bin_edges = np.histogram(pitch_speeds, bins=bins)
        
        total_at_bats = len(at_bats)
        
        for i, count in enumerate(hist):
            if count > 0:
                bin_center = (bin_edges[i] + bin_edges[i+1]) / 2
                histogram.append({
                    "histogram_value": str(int(bin_center)),
                    "pitch_count": str(count),
                    "total_pitches": str(total_at_bats),
                    "pitch_speed": str(bin_center),
                    "pitch_percent": str(round(count / total_at_bats * 100, 1))
                })
        
        return histogram
    
    def _calculate_spin_rate_histogram(self, at_bats: List[Dict]) -> List[Dict[str, Any]]:
        """Calculate spin rate histogram from at-bats."""
        histogram = []
        
        # Extract spin rates
        spin_rates = []
        for ab in at_bats:
            try:
                spin = float(ab.get('spin_rate', 0))
                if spin > 0:
                    spin_rates.append(spin)
            except (ValueError, TypeError):
                continue
        
        if not spin_rates:
            return []
        
        # Create histogram bins (1500-3500 rpm in 200 rpm increments)
        bins = list(range(1500, 3700, 200))
        hist, bin_edges = np.histogram(spin_rates, bins=bins)
        
        total_at_bats = len(at_bats)
        
        for i, count in enumerate(hist):
            if count > 0:
                bin_center = (bin_edges[i] + bin_edges[i+1]) / 2
                histogram.append({
                    "histogram_value": str(int(bin_center)),
                    "pitch_count": str(count),
                    "total_pitches": str(total_at_bats),
                    "spin_rate": str(bin_center),
                    "pitch_percent": str(round(count / total_at_bats * 100, 1))
                })
        
        return histogram


def test_histogram_calculator():
    """Test the histogram calculator with a sample player."""
    calculator = HistogramCalculator()
    
    # Test with the player we know has data
    player_id = "455117"
    
    print(f"🧪 Testing histogram calculator for player {player_id}")
    
    histograms = calculator.get_player_histograms(player_id, "batter")
    
    print(f"📊 Histogram results:")
    for hist_type, hist_data in histograms.items():
        print(f"   {hist_type}: {len(hist_data)} entries")
        if hist_data:
            print(f"     Sample: {hist_data[0]}")


if __name__ == "__main__":
    test_histogram_calculator()
