# Weight Refinement Workflow - Step-by-Step Guide

## 🎯 Overview

This guide provides a practical, step-by-step workflow for refining histogram analysis weights based on real-world DFS performance. The process is designed to be systematic, data-driven, and safe.

## 📋 Prerequisites

- Enhanced rolling windows system deployed and running
- Histogram data collection operational (746+ players)
- Base projection system (SaberSim integration) working
- Access to actual DFS contest results

## 🚀 Phase 1: Data Collection Setup (Week 1)

### Step 1: Deploy Enhanced System
```bash
# Run the enhanced system to generate baseline projections
cd /path/to/cosmic_grid
python3 scripts/run_enhanced_rolling_windows.py draftkings 0808 1000

# Verify output files are generated
ls -la _data/rolling/pool_upload_draftkings_0808.csv
ls -la _data/rolling/enhanced_analysis_draftkings_0808.csv
```

### Step 2: Collect Actual Results
```bash
# Generate sample data for testing (replace with real collection)
python3 scripts/collect_actual_results.py \
    --start-date 2025-08-08 \
    --end-date 2025-08-08 \
    --site draftkings \
    --generate-sample \
    --sample-size 100

# For production, implement real data collection:
# python3 scripts/collect_actual_results.py \
#     --start-date 2025-08-08 \
#     --end-date 2025-08-08 \
#     --site draftkings
```

### Step 3: Daily Data Correlation
```bash
# Match projections with actual results
python3 scripts/weight_optimization.py \
    --collect-daily \
    --date 2025-08-08 \
    --projections-file _data/rolling/enhanced_analysis_draftkings_0808.csv \
    --results-file _data/actual_results/actual_results_draftkings_20250808.json
```

## 📊 Phase 2: Initial Assessment (Week 2)

### Step 4: Daily Monitoring
```bash
# Run daily for 7-14 days to build dataset
for date in $(seq -f "2025-08-%02g" 8 21); do
    # Generate projections
    python3 scripts/run_enhanced_rolling_windows.py draftkings ${date/2025-08-/} 1000

    # Collect actual results (or generate sample)
    python3 scripts/collect_actual_results.py \
        --start-date $date \
        --end-date $date \
        --site draftkings \
        --generate-sample

    # Correlate data
    python3 scripts/weight_optimization.py \
        --collect-daily \
        --date $date \
        --projections-file "_data/rolling/enhanced_analysis_draftkings_${date/2025-08-/}.csv" \
        --results-file "_data/actual_results/actual_results_draftkings_${date//--/}.json"
done
```

### Step 5: Initial Performance Analysis
```bash
# Analyze 2 weeks of data
python3 scripts/weight_optimization.py \
    --start-date 2025-08-08 \
    --end-date 2025-08-21 \
    --validation-split 0.3
```

**Expected Output:**
```
🎯 Weight Optimization Complete!
📊 Report saved to: _data/weight_optimization/optimization_report_20250822_143052.md
✅ Improvement: True

## Key Metrics to Look For:
- RMSE Improvement: >2% better than baseline
- Directional Accuracy: >55% (adjustments in right direction)
- Component Correlations: >0.1 for effective components
- Sample Size: >200 player-games for reliability
```

## ⚖️ Phase 3: Weight Optimization (Week 3)

### Step 6: Analyze Current Performance
```python
# Key questions to answer:
# 1. Which histogram components are most predictive?
# 2. Are our confidence scores accurate?
# 3. What's our baseline vs enhanced accuracy?

# Example analysis results:
"""
Component Effectiveness Analysis:
Pitcher Components:
- pitch_type_effectiveness: correlation=0.15, effectiveness=0.023
- zone_command: correlation=0.08, effectiveness=0.008
- movement_quality: correlation=0.02, effectiveness=0.002
- contact_suppression: correlation=0.12, effectiveness=0.014

Hitter Components:
- contact_quality: correlation=0.18, effectiveness=0.036
- launch_profile: correlation=0.14, effectiveness=0.025
- zone_coverage: correlation=0.06, effectiveness=0.006
"""
```

### Step 7: Calculate New Weights
Based on the analysis, the optimization script will suggest new weights:

```python
# Example weight changes:
"""
Current vs Proposed Weights:

Pitcher Weights:
| Component              | Current | Proposed | Change  |
|------------------------|---------|----------|---------|
| pitch_type_effectiveness| 0.150   | 0.180   | +20.0%  |
| zone_command           | 0.100   | 0.080   | -20.0%  |
| movement_quality       | 0.080   | 0.064   | -20.0%  |
| contact_suppression    | 0.120   | 0.144   | +20.0%  |

Hitter Weights:
| Component              | Current | Proposed | Change  |
|------------------------|---------|----------|---------|
| contact_quality        | 0.200   | 0.240   | +20.0%  |
| launch_profile         | 0.180   | 0.196   | +8.9%   |
| zone_coverage          | 0.100   | 0.080   | -20.0%  |

Validation Results:
- New RMSE: 4.567 (vs 4.892 current)
- RMSE Improvement: +6.6%
- Directional Accuracy: +3.2%
- Recommendation: ✅ IMPLEMENT
"""
```

### Step 8: Implement New Weights
```python
# Update the HistogramAnalyzer with new weights
# File: src/star_cannon/core/rolling_windows/histogram_analyzer.py

# Old weights:
self.adjustment_weights = {
    'pitcher': {
        'pitch_type_effectiveness': 0.15,
        'zone_command': 0.10,
        'movement_quality': 0.08,
        'contact_suppression': 0.12
    },
    'hitter': {
        'contact_quality': 0.20,
        'launch_profile': 0.18,
        'zone_coverage': 0.10
    }
}

# New optimized weights:
self.adjustment_weights = {
    'pitcher': {
        'pitch_type_effectiveness': 0.18,  # +20%
        'zone_command': 0.08,              # -20%
        'movement_quality': 0.064,         # -20%
        'contact_suppression': 0.144       # +20%
    },
    'hitter': {
        'contact_quality': 0.24,           # +20%
        'launch_profile': 0.196,           # +8.9%
        'zone_coverage': 0.08              # -20%
    }
}
```

## 🧪 Phase 4: Gradual Rollout (Week 4)

### Step 9: A/B Testing Setup
```python
# Implement gradual rollout in ProjectionGenerator
def _blend_adjustments(self, rolling_adj: float, histogram_adj: float, player_id: str) -> float:
    # Get rollout percentage from config
    rollout_pct = self.get_rollout_percentage()  # Start at 25%

    if random.random() < rollout_pct:
        # Use new weights
        return self._blend_with_new_weights(rolling_adj, histogram_adj, player_id)
    else:
        # Use original weights
        return self._blend_with_original_weights(rolling_adj, histogram_adj, player_id)
```

### Step 10: Monitor Rollout Performance
```bash
# Week 4.1: 25% rollout
# Update config: rollout_percentage = 0.25
python3 scripts/run_enhanced_rolling_windows.py draftkings 0815 1000

# Monitor daily performance
python3 scripts/monitor_rollout_performance.py --date 2025-08-15

# Week 4.2: 50% rollout (if no issues)
# Update config: rollout_percentage = 0.50

# Week 4.3: 75% rollout
# Update config: rollout_percentage = 0.75

# Week 4.4: 100% rollout
# Update config: rollout_percentage = 1.00
```

## 📈 Phase 5: Continuous Monitoring (Ongoing)

### Step 11: Daily Performance Dashboard
```python
# Automated daily monitoring
def daily_monitoring_check():
    """Run this every morning to check performance."""

    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    metrics = {
        'rmse_vs_baseline': check_rmse_improvement(yesterday),
        'directional_accuracy': check_directional_accuracy(yesterday),
        'confidence_calibration': check_confidence_accuracy(yesterday),
        'outlier_count': count_projection_outliers(yesterday),
        'system_health': check_system_health(yesterday)
    }

    # Alert conditions
    alerts = []
    if metrics['rmse_vs_baseline'] < -0.02:
        alerts.append("🚨 Performance degradation detected")
    if metrics['outlier_count'] > 10:
        alerts.append("⚠️ High outlier count")

    # Send alerts if needed
    if alerts:
        send_performance_alert(metrics, alerts)

    return metrics
```

### Step 12: Weekly Weight Reviews
```bash
# Every Monday, review the past week
python3 scripts/weekly_weight_review.py \
    --start-date $(date -d "7 days ago" +%Y-%m-%d) \
    --end-date $(date -d "yesterday" +%Y-%m-%d)
```

### Step 13: Monthly Comprehensive Analysis
```bash
# First Monday of each month
python3 scripts/monthly_optimization.py \
    --start-date $(date -d "1 month ago" +%Y-%m-%d) \
    --end-date $(date -d "yesterday" +%Y-%m-%d) \
    --comprehensive-analysis
```

## 🔍 Key Performance Indicators (KPIs)

### Daily Monitoring
- **RMSE vs Baseline**: Target >3% improvement
- **Directional Accuracy**: Target >55%
- **Coverage**: Target >90% players with histogram data
- **System Uptime**: Target >99%

### Weekly Reviews
- **Component Effectiveness**: All components showing positive correlation
- **Confidence Calibration**: High confidence = better accuracy
- **Adjustment Distribution**: Most adjustments within ±10%

### Monthly Analysis
- **Overall ROI**: Improved contest performance
- **Model Drift**: Weights remaining stable
- **Seasonal Adjustments**: Account for changing player performance

## 🚨 Alert Conditions

### Immediate Action Required
- **RMSE degradation** >5% vs baseline
- **System failures** or data collection issues
- **Outlier rate** >10% of projections

### Weekly Review Triggers
- **RMSE degradation** >2% for 3+ consecutive days
- **Directional accuracy** <50% for 3+ consecutive days
- **High variance** in daily performance metrics

### Monthly Recalibration Triggers
- **Consistent underperformance** vs baseline
- **Seasonal performance changes** (playoffs, weather, etc.)
- **Model drift** detected in weight effectiveness

## 🎯 Success Criteria

### Short-term (1 month)
- ✅ Consistent 3-5% RMSE improvement vs baseline
- ✅ 55%+ directional accuracy
- ✅ Stable daily performance (low variance)
- ✅ No system reliability issues

### Medium-term (3 months)
- ✅ 5-8% RMSE improvement maintained
- ✅ Improved contest ROI/rankings
- ✅ Refined weights showing stability
- ✅ Seasonal adaptations working

### Long-term (6+ months)
- ✅ Sustained competitive advantage
- ✅ Advanced features (weather, injuries, etc.)
- ✅ Multi-sport expansion potential
- ✅ Automated optimization pipeline

## 📁 File Structure

```
_data/
├── weight_optimization/
│   ├── performance_2025-08-08.json
│   ├── performance_2025-08-09.json
│   └── optimization_report_20250822_143052.md
├── actual_results/
│   ├── actual_results_draftkings_20250808.json
│   └── actual_results_fanduel_20250808.json
└── rolling/
    ├── pool_upload_draftkings_0808.csv
    └── enhanced_analysis_draftkings_0808.csv
```

## 🔧 Automation Scripts

The complete workflow can be automated with:

1. **Daily Collection**: `collect_daily_data.sh`
2. **Weekly Analysis**: `weekly_review.py`
3. **Monthly Optimization**: `monthly_optimization.py`
4. **Alert System**: `performance_monitor.py`

This systematic approach ensures continuous improvement while maintaining system reliability and avoiding over-optimization!