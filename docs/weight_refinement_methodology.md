# Weight Refinement Methodology - Real-World Performance Optimization

## 🎯 Overview

After deploying the enhanced histogram analysis system, we need to continuously refine the adjustment weights based on how well our enhanced projections predict actual DFS performance. This document outlines a systematic approach to weight optimization using real-world results.

## 📊 Data Collection Framework

### Required Data Points

#### 1. **Projection Data** (Our Output)
```python
# For each player, each contest
projection_data = {
    'player_id': '681481',
    'player_name': 'Kerry Carpenter',
    'contest_date': '2025-08-08',
    'contest_id': 'dk_main_123456',
    'base_projection': 10.5,           # SaberSim baseline
    'rolling_adjustment': 0.05,        # Traditional rolling adjustment
    'histogram_adjustment': 0.03,      # Our histogram adjustment
    'combined_adjustment': 0.04,       # Blended final adjustment
    'final_projection': 10.92,         # Our enhanced projection
    'confidence_score': 0.85,          # Data quality confidence
    'histogram_breakdown': {
        'contact_quality': 0.01,
        'launch_profile': 0.012,
        'zone_coverage': 0.005
    }
}
```

#### 2. **Actual Performance Data** (Reality)
```python
# Actual DFS points scored
actual_performance = {
    'player_id': '681481',
    'contest_date': '2025-08-08',
    'actual_fpts': 12.3,              # Actual fantasy points scored
    'actual_stats': {
        'at_bats': 4,
        'hits': 2,
        'home_runs': 1,
        'rbis': 3,
        'runs': 2,
        'stolen_bases': 0
    }
}
```

#### 3. **Market Data** (Benchmarks)
```python
# Other projection sources for comparison
market_data = {
    'player_id': '681481',
    'contest_date': '2025-08-08',
    'sabersim_baseline': 10.5,         # SaberSim's raw projection
    'traditional_rolling': 11.03,      # Our old rolling-only system
    'rotogrinders_proj': 10.8,        # External benchmark
    'ownership_pct': 8.5               # Actual ownership percentage
}
```

## 🔬 Analysis Methodology

### Step 1: Projection Accuracy Metrics

#### A. **Root Mean Square Error (RMSE)**
```python
def calculate_rmse(projections, actuals):
    """Calculate RMSE for projection accuracy."""
    import numpy as np

    squared_errors = [(proj - actual)**2 for proj, actual in zip(projections, actuals)]
    mse = np.mean(squared_errors)
    rmse = np.sqrt(mse)
    return rmse

# Compare different projection methods
baseline_rmse = calculate_rmse(sabersim_projections, actual_fpts)
rolling_rmse = calculate_rmse(rolling_enhanced_projections, actual_fpts)
histogram_rmse = calculate_rmse(histogram_enhanced_projections, actual_fpts)
combined_rmse = calculate_rmse(our_final_projections, actual_fpts)
```

#### B. **Mean Absolute Error (MAE)**
```python
def calculate_mae(projections, actuals):
    """Calculate MAE - more interpretable than RMSE."""
    import numpy as np

    absolute_errors = [abs(proj - actual) for proj, actual in zip(projections, actuals)]
    mae = np.mean(absolute_errors)
    return mae
```

#### C. **Directional Accuracy**
```python
def calculate_directional_accuracy(base_proj, enhanced_proj, actual):
    """Did our adjustment move in the right direction?"""
    correct_predictions = 0
    total_predictions = 0

    for base, enhanced, actual in zip(base_proj, enhanced_proj, actual):
        adjustment = enhanced - base
        actual_diff = actual - base

        # Did we adjust in the right direction?
        if adjustment * actual_diff > 0:  # Same sign = correct direction
            correct_predictions += 1
        total_predictions += 1

    return correct_predictions / total_predictions
```

### Step 2: Component Analysis

#### A. **Individual Adjustment Component Effectiveness**
```python
def analyze_component_effectiveness(data):
    """Analyze which histogram components are most predictive."""
    results = {}

    for component in ['contact_quality', 'launch_profile', 'zone_coverage']:
        # Isolate the effect of this component
        component_adjustments = [d['histogram_breakdown'][component] for d in data]
        actual_performance = [d['actual_fpts'] - d['base_projection'] for d in data]

        # Calculate correlation
        correlation = np.corrcoef(component_adjustments, actual_performance)[0, 1]
        results[component] = {
            'correlation': correlation,
            'avg_adjustment': np.mean(component_adjustments),
            'effectiveness_score': correlation * abs(np.mean(component_adjustments))
        }

    return results
```

#### B. **Confidence Score Validation**
```python
def validate_confidence_scores(data):
    """Check if higher confidence scores correlate with better accuracy."""
    # Group by confidence levels
    high_conf = [d for d in data if d['confidence_score'] > 0.8]
    med_conf = [d for d in data if 0.6 <= d['confidence_score'] <= 0.8]
    low_conf = [d for d in data if d['confidence_score'] < 0.6]

    # Calculate accuracy for each group
    results = {}
    for name, group in [('high', high_conf), ('medium', med_conf), ('low', low_conf)]:
        if group:
            projections = [d['final_projection'] for d in group]
            actuals = [d['actual_fpts'] for d in group]
            rmse = calculate_rmse(projections, actuals)
            results[name] = {'count': len(group), 'rmse': rmse}

    return results
```

## ⚖️ Weight Optimization Process

### Phase 1: Baseline Performance Assessment

#### Week 1-2: Collect Initial Data
```python
# Collection script to run daily
def collect_daily_performance_data(date):
    """Collect all required data for a contest date."""

    # 1. Load our projections for the date
    projections = load_enhanced_projections(date)

    # 2. Scrape actual performance from DFS sites
    actual_results = scrape_actual_results(date)

    # 3. Store for analysis
    store_performance_data(projections, actual_results, date)

    return len(projections)
```

#### Analysis After 2 Weeks
```python
def initial_performance_assessment():
    """Analyze first 2 weeks of data."""

    data = load_performance_data(start_date='2025-08-08', end_date='2025-08-22')

    # Overall accuracy metrics
    baseline_accuracy = calculate_accuracy_metrics(data, 'sabersim_baseline')
    enhanced_accuracy = calculate_accuracy_metrics(data, 'final_projection')

    # Component effectiveness
    component_analysis = analyze_component_effectiveness(data)

    # Confidence validation
    confidence_analysis = validate_confidence_scores(data)

    # Generate report
    generate_performance_report(baseline_accuracy, enhanced_accuracy,
                              component_analysis, confidence_analysis)
```

### Phase 2: Weight Optimization

#### A. **Grid Search Optimization**
```python
def optimize_weights_grid_search(historical_data):
    """Use grid search to find optimal weights."""

    # Current weights
    pitcher_weights = {
        'pitch_type_effectiveness': 0.15,
        'zone_command': 0.10,
        'movement_quality': 0.08,
        'contact_suppression': 0.12
    }

    hitter_weights = {
        'contact_quality': 0.20,
        'launch_profile': 0.18,
        'zone_coverage': 0.10
    }

    # Grid search ranges (±50% of current weights)
    search_ranges = {
        'pitch_type_effectiveness': np.arange(0.075, 0.225, 0.025),
        'zone_command': np.arange(0.05, 0.15, 0.02),
        'movement_quality': np.arange(0.04, 0.12, 0.02),
        'contact_suppression': np.arange(0.06, 0.18, 0.02),
        'contact_quality': np.arange(0.10, 0.30, 0.02),
        'launch_profile': np.arange(0.09, 0.27, 0.02),
        'zone_coverage': np.arange(0.05, 0.15, 0.02)
    }

    best_rmse = float('inf')
    best_weights = None

    # Test all combinations (warning: computationally expensive)
    for combo in itertools.product(*search_ranges.values()):
        test_weights = dict(zip(search_ranges.keys(), combo))

        # Recalculate projections with new weights
        test_projections = recalculate_projections(historical_data, test_weights)

        # Calculate RMSE
        actuals = [d['actual_fpts'] for d in historical_data]
        rmse = calculate_rmse(test_projections, actuals)

        if rmse < best_rmse:
            best_rmse = rmse
            best_weights = test_weights

    return best_weights, best_rmse
```

#### B. **Bayesian Optimization** (More Efficient)
```python
def optimize_weights_bayesian(historical_data):
    """Use Bayesian optimization for more efficient weight tuning."""
    from skopt import gp_minimize
    from skopt.space import Real

    # Define search space
    space = [
        Real(0.075, 0.225, name='pitch_type_effectiveness'),
        Real(0.05, 0.15, name='zone_command'),
        Real(0.04, 0.12, name='movement_quality'),
        Real(0.06, 0.18, name='contact_suppression'),
        Real(0.10, 0.30, name='contact_quality'),
        Real(0.09, 0.27, name='launch_profile'),
        Real(0.05, 0.15, name='zone_coverage')
    ]

    def objective_function(weights):
        """Objective function to minimize (RMSE)."""
        weight_dict = {
            'pitch_type_effectiveness': weights[0],
            'zone_command': weights[1],
            'movement_quality': weights[2],
            'contact_suppression': weights[3],
            'contact_quality': weights[4],
            'launch_profile': weights[5],
            'zone_coverage': weights[6]
        }

        # Recalculate projections
        test_projections = recalculate_projections(historical_data, weight_dict)
        actuals = [d['actual_fpts'] for d in historical_data]

        return calculate_rmse(test_projections, actuals)

    # Run optimization
    result = gp_minimize(objective_function, space, n_calls=100, random_state=42)

    return result.x, result.fun
```

### Phase 3: Validation & Implementation

#### A. **Out-of-Sample Testing**
```python
def validate_new_weights(new_weights, validation_data):
    """Test new weights on held-out validation data."""

    # Original weights performance
    original_projections = [d['final_projection'] for d in validation_data]
    original_actuals = [d['actual_fpts'] for d in validation_data]
    original_rmse = calculate_rmse(original_projections, original_actuals)

    # New weights performance
    new_projections = recalculate_projections(validation_data, new_weights)
    new_rmse = calculate_rmse(new_projections, original_actuals)

    improvement = (original_rmse - new_rmse) / original_rmse

    return {
        'original_rmse': original_rmse,
        'new_rmse': new_rmse,
        'improvement_pct': improvement * 100,
        'is_better': new_rmse < original_rmse
    }
```

#### B. **Gradual Rollout**
```python
def implement_weight_changes(new_weights, rollout_schedule):
    """Gradually implement new weights with monitoring."""

    # Week 1: 25% of adjustments use new weights
    # Week 2: 50% of adjustments use new weights
    # Week 3: 75% of adjustments use new weights
    # Week 4: 100% of adjustments use new weights

    for week, percentage in rollout_schedule.items():
        print(f"Week {week}: Rolling out to {percentage}% of players")

        # Update configuration
        update_weight_config(new_weights, percentage)

        # Monitor performance daily
        for day in range(7):
            daily_performance = monitor_daily_performance()
            if daily_performance['rmse'] > rollout_thresholds['max_rmse']:
                print(f"Performance degradation detected! Rolling back...")
                rollback_weights()
                break
```

## 📈 Continuous Monitoring

### Daily Performance Dashboard
```python
def generate_daily_dashboard(date):
    """Generate daily performance monitoring dashboard."""

    data = load_performance_data(date)

    metrics = {
        'total_players': len(data),
        'avg_confidence': np.mean([d['confidence_score'] for d in data]),
        'rmse_vs_baseline': calculate_rmse_improvement(data),
        'directional_accuracy': calculate_directional_accuracy(data),
        'component_effectiveness': analyze_component_effectiveness(data),
        'outlier_count': count_projection_outliers(data),
        'histogram_coverage': calculate_histogram_coverage(data)
    }

    # Alert conditions
    alerts = []
    if metrics['rmse_vs_baseline'] < -0.02:  # Performance degraded
        alerts.append("Performance degradation detected")
    if metrics['outlier_count'] > 10:  # Too many outliers
        alerts.append("High number of projection outliers")

    return metrics, alerts
```

### Weekly Weight Review
```python
def weekly_weight_review():
    """Weekly review and potential micro-adjustments."""

    # Last 7 days of data
    week_data = load_performance_data(days=7)

    # Component performance analysis
    component_perf = analyze_component_effectiveness(week_data)

    # Micro-adjustments (±5% max per week)
    adjustments = {}
    for component, perf in component_perf.items():
        current_weight = get_current_weight(component)

        if perf['effectiveness_score'] > 0.1:  # Strong positive correlation
            adjustments[component] = min(current_weight * 1.05, current_weight + 0.01)
        elif perf['effectiveness_score'] < -0.1:  # Strong negative correlation
            adjustments[component] = max(current_weight * 0.95, current_weight - 0.01)

    return adjustments
```
