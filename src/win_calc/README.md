# Win Calculator Module

Adjusts SaberSim projections using rolling windows data and Statcast statistics.

## Overview

This module provides a focused pipeline for adjusting SaberSim projections using:
- **Rolling Windows Data**: Event-based 50/100/250 event windows with 2-4 week recency
- **Statcast Statistics**: xwOBA, exit velocity, launch angle, barrel rates, hard hit rates
- **Quality Metrics**: Contact quality trends and performance indicators
- **Configurable Parameters**: Transparent and detailed adjustment formulas with tunable weights

## Module Structure

```
src/win_calc/
├── config.py                 # Centralized parameter configuration
├── formulas.py               # Configurable adjustment formulas
├── data_loader.py            # Load SaberSim and rolling windows data
├── rolling_adjuster.py       # Rolling windows adjustment calculations
├── statcast_metrics.py       # Statcast statistics and quality metrics
├── projection_calculator.py  # Core projection adjustment logic
├── exporter.py               # CSV export functionality
├── run_adj.py                # Main adjustment pipeline runner
└── README.md                 # This file
```

## Core Focus: Statcast Statistics & Rolling Windows

### Rolling Window Adjustments
We focus on blending recent performance signals with SaberSim's baseline projections:

**Event-Based Windows:**
- **50 events**: Most recent 50 batted ball events (~2-4 weeks)
- **100 events**: Recent 100 batted ball events (~4-6 weeks)
- **250 events**: Baseline 250 batted ball events (~8-12 weeks)

**Key Statcast Metrics:**
- **xwOBA**: Expected weighted on-base average (primary adjustment metric)
- **Exit Velocity**: Contact quality and power indicators
- **Launch Angle**: Optimal contact patterns
- **Barrel Rate**: Perfect contact combinations
- **Hard Hit Rate**: Quality contact percentage

### Adjustment Formula
```python
# Recency-weighted blend of event-based windows
S_recent = w50*z50 + w100*z100 + w250*z250

# Apply to SaberSim projections
P_adj = P_base * (1 + k * S_recent)
Cap |k * S_recent| ≤ 0.20  # Maximum 20% adjustment
```

## Configurable Parameter System

### Centralized Configuration (`config.py`)
```python
# Rolling Window Parameters
ROLLING_CONFIG = {
    "weights": {
        "w50": 0.5,    # Most recent 50 events (highest weight)
        "w100": 0.3,   # Recent 100 events (medium weight)
        "w250": 0.2    # Baseline 250 events (lowest weight)
    },
    "adjustment_cap": 0.20,  # Maximum 20% adjustment
    "base_aggressiveness": 0.15,  # Base adjustment multiplier
    "xwoba_baseline": 0.320  # League average xwOBA baseline
}

# Statcast Quality Thresholds
STATCAST_CONFIG = {
    "hard_hit_threshold": 95,       # mph exit velocity
    "barrel_threshold": 0.08,       # 8% barrel rate
    "optimal_launch_angle": (8, 32), # degrees
    "optimal_exit_velocity": (95, 105) # mph
}
```

### Transparent Formula System (`formulas.py`)
```python
def calculate_rolling_adjustment(player_data, config):
    """
    Transparent rolling window adjustment calculation.

    Formula: S_recent = w50*z50 + w100*z100 + w250*z250
    Where z = standardized xwOBA difference from baseline
    """
    weights = config["weights"]
    z50 = standardize_xwoba(player_data["rolling_50"])
    z100 = standardize_xwoba(player_data["rolling_100"])
    z250 = standardize_xwoba(player_data["rolling_250"])

    return (weights["w50"] * z50 +
            weights["w100"] * z100 +
            weights["w250"] * z250)

def apply_adjustment(base_projection, rolling_adj, aggressiveness, config):
    """
    Apply rolling window adjustment to base projection.

    Formula: P_adj = P_base * (1 + k * S_recent)
    Where k = aggressiveness, S_recent = rolling adjustment
    """
    adjusted = base_projection * (1 + rolling_adj * aggressiveness)

    # Apply cap
    max_adjustment = config["adjustment_cap"]
    return cap_adjustment(adjusted, base_projection, max_adjustment)
```

## Key Features

### Revolutionary Data Infrastructure
- **Event-based windows**: 50/100/250 batted ball events (not game-based)
- **Pre-calculated histograms**: No complex Statcast calculations needed
- **Quality metrics ready**: Hard hit rate, barrel rate, contact quality trends
- **Super aggressive collection**: 796 players with rolling windows data

### Transparent Adjustment Methodology
- **Configurable weights**: Recency weighting (50/30/20) easily tunable
- **Statcast-focused**: xwOBA, exit velocity, launch angle, barrel rates
- **Quality-based weighting**: Histogram-derived quality indicators
- **Parameter transparency**: All formulas and weights clearly documented

### Pipeline Execution
- **CLI interface**: `python src/win_calc/run_adj.py --site fanduel --date 0813`
- **CSV export**: Platform-specific upload files (DK/FD)
- **Parameter tuning**: Weights, caps, and thresholds optimization

## Quick Start

```python
from win_calc import run_adjustment_pipeline

# Run adjustment pipeline focused on Statcast statistics
run_adjustment_pipeline(
    site="fanduel",  # or "draftkings"
    date="0813",
    slate="main_slate",
    k=0.15,  # Aggressiveness
    cap=0.20  # Maximum adjustment
)
```

## Data Sources

- **SaberSim**: `_data/sabersim_2025/<site>/<mmdd>_<slate>/atoms_output/tables/`
- **Rolling Windows**: `_data/mlb_api_2025/rolling_windows/data/<role>/<mlb_id>.json`
- **Statcast BBE**: `_data/mlb_api_2025/statcast_adv_box/data/<role>/<mlb_id>.json`

## Output

- **JSON**: Adjusted projections with metadata for auditing
- **CSV (upload-ready)**: Platform-specific upload files
  - DK: `/mnt/storage_fast/workspaces/red_ocean/dfs_1/entries/dk_upload.csv`
  - FD: `/mnt/storage_fast/workspaces/red_ocean/dfs_1/entries/fd_upload.csv`

## Workflow Integration

1. **Extract SaberSim projections** from simulation data
2. **Apply rolling window adjustments** using Statcast statistics
3. **Export adjusted projections** for re-upload to SaberSim
4. **Let SaberSim handle** contest-specific optimization and lineup ranking

## Parameter Transparency

All adjustment formulas and parameters are:
- **Documented**: Clear mathematical formulas with explanations
- **Configurable**: Easy to modify weights, caps, and thresholds
- **Testable**: Unit tests for each formula component
- **Auditable**: Full adjustment history and metadata tracking
