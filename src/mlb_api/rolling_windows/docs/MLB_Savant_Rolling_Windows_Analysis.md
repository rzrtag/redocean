# MLB Savant Rolling Windows Analysis Report

## Executive Summary

This report analyzes the official MLB Savant rolling windows data to understand the qualification system and data structure for qualified windows. The analysis reveals that window size 50 refers to **50 events/at-bats**, not 50 pitches, and provides insights for implementing similar qualification logic in custom rolling window systems.

---

## Table of Contents

1. [Data Structure Overview](#data-structure-overview)
2. [Qualification Mechanism](#qualification-mechanism)
3. [Player Case Studies](#player-case-studies)
4. [Histogram Data Analysis](#histogram-data-analysis)
5. [Key Findings](#key-findings)
6. [Implementation Recommendations](#implementation-recommendations)
7. [Technical Details](#technical-details)

---

## Data Structure Overview

### File Organization
```
_data/rolling/players/
├── hitters/          # 369 hitter files
└── pitchers/         # 377 pitcher files
```

### Data Schema
Each player file contains:
- **Basic Info**: Player ID, name, position, collection timestamp
- **Multi-Window Data**: Rolling window analysis (currently only window size 50)
- **Histogram Data**: Binned performance metrics by launch angle, exit velocity, etc.
- **Enhanced Metrics**: Weighted averages, confidence metrics, recency analysis

---

## Qualification Mechanism

### Window Size 50 = 50 Events/At-Bats
- **NOT 50 pitches** as initially assumed
- All players with recent game activity qualify
- No minimum pitch count requirement
- Qualification based on recent game participation

### Key Insights
- **All 369 hitters qualify** for window size 50
- **All 377 pitchers qualify** for window size 50
- Players with 0 pitches can still qualify
- The "games" field shows games included in the rolling window

---

## Player Case Studies

### 🏟️ Bobby Witt Jr. (Hitter)
- **Total Pitches**: 3,499
- **Current xwOBA**: 0.3273
- **Window Size**: 50 events/at-bats
- **Games Tracked**: 50 games
- **Date Range**: July 28 - August 9, 2025
- **Statistical Stability**: Coefficient of variation 0.0581 (low variance)

**Performance Trend**: Shows improvement from 0.3460 (game 50) to 0.3273 (game 1)

### ⚾ Jacob deGrom (Pitcher)
- **Total Pitches**: 331
- **Current xwOBA**: 0.3520
- **Window Size**: 50 events/at-bats
- **Games Tracked**: 50 games
- **Date Range**: July 28 - August 9, 2025
- **Statistical Stability**: Coefficient of variation 0.0596 (low variance)

**Performance Trend**: Shows decline from 0.2967 (game 50) to 0.3520 (game 1)

---

## Histogram Data Analysis

### What `histogram_value` Represents
The `histogram_value` represents **binned/categorized values** for different baseball metrics:

1. **Exit Velocity (ev)**: Range -90 to +90
2. **Launch Angle (la)**: Range -90 to +90
3. **Pitch Speed**: Various speed ranges

### Launch Angle Interpretation
- **Negative values (-90 to -1)**: Ground balls, bunts, downward contact
- **0**: Line drives parallel to the ground
- **Positive values (1 to 90)**: Fly balls, line drives, upward contact

### Example Data Point
```json
"histogram_value": "5",
"pitch_count": "335",
"ev": "92.4",
"la": "5.0"
```
- **335 pitches** had launch angles around **5 degrees**
- These are **line drives** with good exit velocity (92.4 mph)
- The 5-degree launch angle represents **shallow line drives**

---

## Key Findings

### 1. Qualification System
- **Universal Qualification**: All active players qualify for window size 50
- **Event-Based**: 50 events/at-bats threshold, not pitch count
- **Game Activity**: Recent game participation is the primary qualification metric

### 2. Data Structure
- **Top-level `number_of_pitches`**: Often null or misleading
- **Histogram Data**: Contains actual pitch counts in `pitch_count` fields
- **Window Data**: Shows games included and xwOBA metrics for rolling windows

### 3. Statistical Framework
- **Effective Sample Size**: 50.0 events for statistical significance
- **Confidence Metrics**: Standard deviation and coefficient of variation
- **Recency Analysis**: Weighted averages with time decay factors

---

## Implementation Recommendations

### For Your `calc_rolling` System

1. **Qualification Threshold**
   - Use **50-event threshold** (at-bats, plate appearances, or similar)
   - Focus on events rather than raw pitch counts
   - Consider recent game activity as primary qualification metric

2. **Data Structure**
   - Implement series progression tracking over the window
   - Include confidence metrics for statistical significance
   - Add recency weighting for recent performance

3. **Enhanced Metrics**
   - Weighted averages with confidence intervals
   - Coefficient of variation for stability analysis
   - Recency analysis with time decay factors

4. **Histogram Integration**
   - Use histogram buckets for performance pattern analysis
   - Track launch angle and exit velocity distributions
   - Implement pitch count aggregation from histogram data

---

## Technical Details

### Enhanced Metrics Structure
```json
"enhanced_metrics": {
  "weighted_averages": {
    "weighted_xwoba": 0.3352,
    "weighted_games": 1.0
  },
  "confidence_metrics": {
    "effective_sample_size": 50.0,
    "weighted_xwoba_std": 0.0195,
    "weighted_xwoba_cv": 0.0581
  },
  "recency_analysis": {
    "total_windows": 1,
    "weight_decay_factor": 0.85,
    "recency_boost_factor": 1.2,
    "window_coverage": "50-50"
  }
}
```

### Window Data Structure
```json
"multi_window_data": {
  "50": {
    "games": 1,
    "xwoba": 0.3273,
    "max_game_date": "2025-08-09T00:00:00.000Z",
    "window_size": 50,
    "series": [
      {
        "games": 1,
        "xwoba": 0.3273,
        "max_game_date": "2025-08-09T00:00:00.000Z"
      }
      // ... 49 more entries
    ]
  }
}
```

---

## Conclusion

The MLB Savant rolling windows system uses a **50-event qualification threshold** based on recent game activity rather than pitch counts. The system provides comprehensive statistical analysis including confidence metrics, recency weighting, and performance progression tracking.

For your `calc_rolling` implementation, focus on:
- **Event-based qualification** (50 events/at-bats)
- **Series progression tracking** over the window
- **Enhanced statistical metrics** for confidence and stability
- **Histogram data integration** for detailed performance analysis

This approach will align your system with the official MLB Savant methodology while providing the statistical rigor needed for meaningful rolling window analysis.

---

## Appendix

### Data Sources
- **Hitters**: 369 player files analyzed
- **Pitchers**: 377 player files analyzed
- **Collection Date**: August 11-12, 2025
- **Window Size**: 50 events/at-bats

### Files Analyzed
- `_data/rolling/players/hitters/677951.json` (Bobby Witt Jr.)
- `_data/rolling/players/pitchers/594798.json` (Jacob deGrom)
- Sample analysis of 100+ additional player files

### Analysis Tools
- Custom Python scripts for data extraction and analysis
- Statistical analysis of qualification patterns
- Comparative analysis of hitter vs. pitcher data structures