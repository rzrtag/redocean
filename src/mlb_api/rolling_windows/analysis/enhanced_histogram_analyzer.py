"""
Enhanced Histogram Analyzer

Provides advanced histogram analysis functionality with statistical insights.
"""

import logging
from typing import Dict, List, Optional, Any
import numpy as np
from .histogram_analyzer import HistogramAnalyzer

logger = logging.getLogger(__name__)


class EnhancedHistogramAnalyzer(HistogramAnalyzer):
    """Enhanced analyzer for histogram data with advanced statistical methods."""

    def __init__(self):
        """Initialize the enhanced histogram analyzer."""
        super().__init__()

    def analyze_combined_distributions(self, exit_velocities: List[float], launch_angles: List[float]) -> Dict[str, Any]:
        """Analyze combined exit velocity and launch angle distributions.

        Args:
            exit_velocities: List of exit velocity values
            launch_angles: List of launch angle values

        Returns:
            Dict containing combined analysis results
        """
        try:
            # Individual analyses
            ev_analysis = self.analyze_exit_velocity_distribution(exit_velocities)
            la_analysis = self.analyze_launch_angle_distribution(launch_angles)

            # Combined insights
            combined_analysis = {
                "exit_velocity": ev_analysis,
                "launch_angle": la_analysis,
                "combined_insights": {}
            }

            # Calculate correlation if we have paired data
            if len(exit_velocities) == len(launch_angles) and len(exit_velocities) > 1:
                correlation = np.corrcoef(exit_velocities, launch_angles)[0, 1]
                combined_analysis["combined_insights"]["correlation"] = float(correlation)

                # Quality metrics
                combined_analysis["combined_insights"]["data_quality"] = {
                    "paired_observations": len(exit_velocities),
                    "correlation_strength": "strong" if abs(correlation) > 0.7 else "moderate" if abs(correlation) > 0.3 else "weak"
                }

            return combined_analysis

        except Exception as e:
            logger.error(f"Error in combined distribution analysis: {e}")
            return {"error": str(e)}

    def detect_outliers(self, data: List[float], threshold: float = 2.0) -> Dict[str, Any]:
        """Detect outliers in data using z-score method.

        Args:
            data: List of numerical values
            threshold: Z-score threshold for outlier detection

        Returns:
            Dict containing outlier information
        """
        if not data or len(data) < 3:
            return {"error": "Insufficient data for outlier detection"}

        try:
            values = np.array(data)
            z_scores = np.abs((values - np.mean(values)) / np.std(values))
            outliers = values[z_scores > threshold]

            return {
                "total_values": len(values),
                "outlier_count": len(outliers),
                "outlier_percentage": float(len(outliers) / len(values) * 100),
                "outlier_values": outliers.tolist(),
                "outlier_indices": np.where(z_scores > threshold)[0].tolist(),
                "threshold_used": threshold
            }

        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            return {"error": str(e)}

    def calculate_percentile_ranks(self, data: List[float], target_values: List[float]) -> Dict[str, Any]:
        """Calculate percentile ranks for target values within a dataset.

        Args:
            data: Reference dataset
            target_values: Values to find percentile ranks for

        Returns:
            Dict containing percentile rank information
        """
        if not data:
            return {"error": "No reference data provided"}

        try:
            reference_data = np.array(data)
            target_array = np.array(target_values)

            percentile_ranks = []
            for target in target_array:
                rank = (reference_data < target).sum() / len(reference_data) * 100
                percentile_ranks.append(float(rank))

            return {
                "reference_dataset_size": len(reference_data),
                "target_values": target_values,
                "percentile_ranks": percentile_ranks,
                "interpretation": [
                    f"{target} is at {rank:.1f}th percentile"
                    for target, rank in zip(target_values, percentile_ranks)
                ]
            }

        except Exception as e:
            logger.error(f"Error calculating percentile ranks: {e}")
            return {"error": str(e)}
