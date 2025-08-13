# Enhanced Rolling Windows - Quick Start Guide

## 🚀 Running the Enhanced System

### Prerequisites
- Histogram data collected in `_data/rolling/players/`
- SaberSim baseline projections (from atoms or demo data)
- Enhanced rolling metrics

### Basic Usage

```bash
# Run the enhanced system (includes histogram analysis)
cd /path/to/cosmic_grid
python3 scripts/run_enhanced_rolling_windows.py draftkings 0808 50

# Test the system
python3 scripts/test_enhanced_system.py
```

### Key Parameters
- `site`: `draftkings` or `fanduel`
- `date_mmdd`: Date in MMDD format (e.g., `0808` for August 8th)
- `max_players`: Maximum players to process (e.g., `50` for testing, `1000` for production)

## 📁 Generated Files

### Pool Upload File (Ready for SaberSim)
**Location**: `_data/rolling/pool_upload_{site}_{date}.csv`
**Format**: `player_id,player_name,sabersim_projection,my_projection`
```csv
player_id,player_name,sabersim_projection,my_projection
123456,Aaron Judge,12.50,13.15
789012,Shohei Ohtani,15.20,15.66
```

### Detailed Analysis Report
**Location**: `_data/rolling/enhanced_analysis_{site}_{date}.csv`
**Format**: Full breakdown of adjustments
```csv
Player,Position,Base_Projection,Enhanced_Projection,Rolling_Adj,Histogram_Adj,Combined_Adj,Confidence,Histogram_Available
Aaron Judge,hitter,12.50,13.15,0.0200,0.0320,0.0280,0.850,True
```

## 🔧 How It Works

### 1. Data Integration
- **Traditional Rolling**: 5-50 game windows with weighted stats
- **Histogram Analysis**: 25-35 data points per metric from pitch-by-pitch data
- **Weighted Blending**: High confidence = more histogram weight

### 2. Adjustment Types

#### Pitchers
- **Pitch Type Effectiveness** (15% weight): Run values by pitch type
- **Zone Command** (10% weight): Effectiveness by strike zone
- **Movement Quality** (8% weight): Horizontal/vertical movement trends
- **Contact Suppression** (12% weight): Launch angle/exit velocity allowed

#### Hitters
- **Contact Quality** (20% weight): Barrel%, hard hit%, sweet spot%
- **Launch Profile** (18% weight): Optimal launch angle (15-35°) + exit velocity
- **Zone Coverage** (10% weight): Success rate by strike zone

### 3. Safety Features
- **Confidence Scoring**: Based on data quality and sample size
- **Safety Caps**: 15% (low), 25% (medium), 35% (high confidence)
- **Graceful Fallback**: Uses traditional rolling if histogram data unavailable

## 📊 Understanding Output

### Adjustment Interpretation
- **Positive**: Player performing better than baseline
- **Negative**: Player performing worse than baseline
- **Range**: ±35% maximum (confidence-based)

### Confidence Levels
- **> 0.8**: High confidence - more histogram weight
- **0.6-0.8**: Medium confidence - balanced weighting
- **< 0.6**: Low confidence - more traditional rolling weight

### Example Analysis
```
Player: Kerry Carpenter (681481)
Type: Hitter
Confidence: 1.000 (perfect data)
Total Adjustment: +2.72%
Breakdown:
  - Contact Quality: +1.01% (improving barrel rate)
  - Launch Profile: +1.20% (optimal launch angles)
  - Zone Coverage: +0.51% (better zone discipline)
```

## 🎯 Production Usage

### Step 1: Collect Histogram Data
```bash
# Ensure histogram collection is current
python3 scripts/collect_rolling.py  # Updates histogram data
```

### Step 2: Run Enhanced Analysis
```bash
# Full production run
python3 scripts/run_enhanced_rolling_windows.py draftkings 0808 1000
```

### Step 3: Upload to SaberSim
1. Use generated `pool_upload_{site}_{date}.csv`
2. Upload via SaberSim interface
3. Monitor performance vs baseline

### Step 4: Analysis & Refinement
1. Review `enhanced_analysis_{site}_{date}.csv` for insights
2. Track actual vs projected performance
3. Adjust weights based on real-world results

## 🔍 Troubleshooting

### Common Issues

#### No Histogram Data
```
⚠️ Histogram data not found, using traditional rolling metrics only...
```
**Solution**: Run histogram collection first

#### Low Confidence Scores
**Causes**: Limited sample size, poor data quality
**Effect**: More conservative adjustments (traditional rolling weighted higher)

#### No Base Projections
**Solution**: Ensure atoms data available or use demo projections for testing

### Validation
```bash
# Run tests to verify system health
python3 scripts/test_enhanced_system.py
```

## 📈 Performance Monitoring

### Key Metrics to Track
1. **Adjustment Accuracy**: How well enhanced projections predict actual performance
2. **Confidence Distribution**: Percentage of players with high vs low confidence
3. **Histogram Coverage**: Percentage of players with histogram data available
4. **Adjustment Magnitude**: Average size of adjustments being applied

### Success Indicators
- ✅ High confidence scores (> 0.8) for majority of players
- ✅ Reasonable adjustment distributions (most within ±10%)
- ✅ Improved projection accuracy vs traditional rolling
- ✅ Proper file format generation for uploads

---

## 🎉 You're Ready!

The enhanced system is now operational and ready for production use. The combination of SaberSim's robust baseline with our sophisticated histogram analysis provides a powerful competitive advantage while maintaining reliability.

**Questions?** Refer to the full implementation guide or run the test suite for validation.