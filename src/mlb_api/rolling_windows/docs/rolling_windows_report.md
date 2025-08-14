# Rolling Windows Data Report
*Generated from Baseball Savant API Data*

## Overview
This report showcases the rolling windows data collected from Baseball Savant for two randomly selected players.

---

## Player Analysis

### 🏃‍♂️ Hitter #666200
**Status**: Limited Data Available

#### Rolling Windows Performance
- **50-Event Window**: No recent data available
- **100-Event Window**: No recent data available
- **250-Event Window**: No recent data available

#### Histogram Data
- **Exit Velocity**: 7 bins available
- **Launch Angle**: Data available
- **Pitch Speed**: Not applicable for hitters

#### Analysis
This player appears to have limited recent batted ball events, which is common for:
- Players with limited playing time
- Recently called up players
- Players returning from injury

---

### ⚾ Pitcher #678606
**Status**: Active with Full Data

#### Rolling Windows Performance
- **50-Event Window**: 50 data points
  - Latest xwOBA: **0.304** (vs. league average ~0.320)
  - Average xwOBA: **0.302**
  - Performance: **Above Average** (lower xwOBA is better for pitchers)

- **100-Event Window**: 100 data points
- **250-Event Window**: 250 data points

#### Histogram Data
- **Exit Velocity**: Data available
- **Launch Angle**: Data available
- **Pitch Speed**: 5 bins available

#### Performance Analysis
This pitcher shows **strong performance** with:
- xwOBA consistently below league average
- Full dataset across all window sizes
- Comprehensive histogram data for analysis

---

## Data Quality Assessment

### ✅ Strengths
- **Real-time data** from Baseball Savant
- **Event-based windows** (50/100/250 events) for precise analysis
- **Comprehensive histograms** for quality metrics
- **Fast collection** with super aggressive mode (16 workers)

### 📊 Data Coverage
- **Total Players**: 1,560 (780 hitters + 780 pitchers)
- **Data Completeness**: Varies by player activity
- **Collection Speed**: ~1560 files in seconds

### 🔄 Update Frequency
- **Hash-based tracking** for change detection
- **Full refresh capability** for fresh data
- **Incremental potential** for future optimization

---

## Technical Details

### Data Structure
```json
{
  "player_id": "678606",
  "player_type": "pitcher",
  "rolling_windows": {
    "50": {"series": [...], "summary": {...}},
    "100": {"series": [...], "summary": {...}},
    "250": {"series": [...], "summary": {...}}
  },
  "histogram_data": {
    "exit_velocity": [...],
    "launch_angle": [...],
    "pitch_speed": [...]
  }
}
```

### Collection Metrics
- **API Endpoints**: Baseball Savant JSON APIs
- **Performance**: Super aggressive mode (16 workers, 0.1s delay)
- **Reliability**: Retry logic with exponential backoff
- **Storage**: JSON files with hash tracking

---

## Next Steps

This data is ready for:
1. **Adjustment system integration** (`win_calc` module)
2. **SaberSim projection adjustments**
3. **Platform-specific scoring** (DraftKings vs FanDuel)
4. **Real-time lineup optimization**

---

*Report generated on: August 14, 2025*
*Data source: Baseball Savant API*
*Collection method: Super Aggressive Mode*
