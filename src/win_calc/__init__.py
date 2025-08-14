"""Win calculation utilities for building site-specific adjusted tables.

This package provides tooling to construct simplified, analysis-ready
"adj" tables from SaberSim atoms outputs (specifically build_optimization).

Sites are processed independently (DraftKings vs FanDuel) to maintain
transparency in inputs and parameters.
"""

__all__ = [
	"adj_builder",
]


