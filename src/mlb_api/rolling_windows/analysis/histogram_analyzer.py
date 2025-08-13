"""
Histogram Analyzer

Provides analysis functionality for histogram data from rolling windows.
"""

import logging
from typing import Dict, List, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)


class HistogramAnalyzer:
    """Analyzer for histogram data."""

    def __init__(self):
        """Initialize the histogram analyzer."""
        pass

    def analyze_exit_velocity_distribution(self, exit_velocities: List[float]) -> Dict[str, Any]:
        """Analyze exit velocity distribution.

        Args:
            exit_velocities: List of exit velocity values

        Returns:
            Dict containing analysis results
        """
        if not exit_velocities:
            return {"error": "No exit velocity data provided"}

        try:
            velocities = np.array(exit_velocities)

            analysis = {
                "count": len(velocities),
                "mean": float(np.mean(velocities)),
                "median": float(np.median(velocities)),
                "std": float(np.std(velocities)),
                "min": float(np.min(velocities)),
                "max": float(np.max(velocities)),
                "percentiles": {
                    "25": float(np.percentile(velocities, 25)),
                    "75": float(np.percentile(velocities, 75)),
                    "90": float(np.percentile(velocities, 90))
                }
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing exit velocity distribution: {e}")
            return {"error": str(e)}

    def analyze_launch_angle_distribution(self, launch_angles: List[float]) -> Dict[str, Any]:
        """Analyze launch angle distribution.

        Args:
            launch_angles: List of launch angle values

        Returns:
            Dict containing analysis results
        """
        if not launch_angles:
            return {"error": "No launch angle data provided"}

        try:
            angles = np.array(launch_angles)

            analysis = {
                "count": len(angles),
                "mean": float(np.mean(angles)),
                "median": float(np.median(angles)),
                "std": float(np.std(angles)),
                "min": float(np.min(angles)),
                "max": float(np.max(angles)),
                "percentiles": {
                    "25": float(np.percentile(angles, 25)),
                    "75": float(np.percentile(angles, 75)),
                    "90": float(np.percentile(angles, 90))
                }
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing launch angle distribution: {e}")
            return {"error": str(e)}

    def create_histogram_bins(self, data: List[float], num_bins: int = 10) -> Dict[str, Any]:
        """Create histogram bins for data.

        Args:
            data: List of numerical values
            num_bins: Number of bins to create

        Returns:
            Dict containing bin edges and counts
        """
        if not data:
            return {"error": "No data provided"}

        try:
            counts, bin_edges = np.histogram(data, bins=num_bins)

            return {
                "bin_edges": bin_edges.tolist(),
                "counts": counts.tolist(),
                "bin_centers": [(bin_edges[i] + bin_edges[i+1])/2 for i in range(len(bin_edges)-1)]
            }

        except Exception as e:
            logger.error(f"Error creating histogram bins: {e}")
            return {"error": str(e)}
