# Enhanced Rolling Windows with Histogram Data - Implementation Guide

## Executive Summary

This document outlines the implementation of histogram-based rolling window adjustments to enhance SaberSim's conservative baseline projections. Our goal is to inject recent performance insights into SaberSim's robust simulation engine to catch performance trends that the conservative 50th percentile baseline might miss.

**Key Strategy**: Use SaberSim's comprehensive simulation capabilities as the foundation, then apply sophisticated histogram-based rolling window adjustments to capture recent form and performance trends.

## Current System vs. Enhanced System

### Current System (Simple Window Stats)
- Basic rolling averages (5, 10, 15, 20, 30, 50 games)
- Simple weighted means and variances
- Basic confidence scoring
- Limited to aggregate statistics

### Enhanced System (Histogram-Based)
- **Rich statistical distributions** from 12 histogram types per player
- **Pitch-by-pitch outcomes** with run values and contact quality
- **Spatial analysis** (zone effectiveness, plate location, movement)
- **Velocity and spin characteristics** for pitchers
- **Contact quality trends** (barrel%, hard hit%, sweet spot%) for hitters

## Strategic Approach

### Why Histogram Data?
1. **Granular Insights**: 25-35 data points per metric vs. simple averages
2. **Recent Trends**: Can identify when a pitcher's fastball command is improving
3. **Contact Quality**: Know when a hitter's barrel rate is trending up
4. **Spatial Analysis**: Understand zone effectiveness and command improvements
5. **Run Value Integration**: Direct run value calculations from pitch outcomes

### Integration with SaberSim
- **SaberSim**: Provides robust 50th percentile baseline (conservative)
- **Our Adjustments**: Add calculated recent performance insights
- **Result**: Enhanced projections that maintain SaberSim's reliability while adding our edge

## Histogram Data Analysis

### Available Histogram Types

#### Pitchers (12 types)
- **Pitch Characteristics**: `pitch_type`, `release_speed`, `release_spin_rate`
- **Movement**: `pfx_x`, `pfx_z`, `spin_axis`
- **Command**: `zone`, `release_pos_x`, `release_pos_z`
- **Contact Suppression**: `launch_angle`, `launch_speed`, `pitch_velocity`

#### Hitters (12 types)
- **Contact Quality**: `barrel`, `hard_hit`, `sweet_spot`
- **Power**: `exit_velocity`, `launch_angle`, `launch_speed`
- **Plate Discipline**: `pitch_type`, `zone`
- **Spatial**: `plate_x`, `plate_z`, `hc_x`, `hc_y`

### Histogram Data Structure
Each histogram entry contains:
- **Outcome Data**: hits, walks, strikeouts, home runs
- **Quality Metrics**: exit velocity, launch angle, run expectancy
- **Run Values**: pitcher_run_value_per_100, batter_run_value_per_100
- **Frequency**: pitch_count, total_pitches, pitch_percent

### Rolling Window Analysis
- **Time Series**: Analyze histogram trends over 5, 10, 15, 20, 30, 50 game windows
- **Statistical Moments**: Calculate weighted means, variances, and trends
- **Run Value Trends**: Track performance changes in run value terms
- **Quality Shifts**: Identify improvements in contact quality or command

## Enhanced Adjustment Formulas

### Pitcher Adjustments (Histogram-Based)

#### 1. Pitch Type Effectiveness
```python
def analyze_pitch_type_effectiveness(pitch_type_data):
    """Analyze run values by pitch type over rolling windows"""
    adjustments = {}

    for pitch_type in ['FF', 'SI', 'SL', 'CT', 'CH', 'CB']:
        # Calculate rolling run values for each pitch type
        recent_run_values = get_recent_run_values(pitch_type_data, pitch_type)
        baseline_run_values = get_baseline_run_values(pitch_type_data, pitch_type)

        # Calculate improvement/decline
        run_value_change = recent_run_values - baseline_run_values

        # Apply confidence weighting
        confidence = calculate_pitch_confidence(pitch_type_data, pitch_type)
        adjustments[pitch_type] = run_value_change * confidence * 0.15

    return adjustments
```

#### 2. Zone Command Analysis
```python
def analyze_zone_effectiveness(zone_data):
    """Analyze zone effectiveness trends"""
    # Group by zone (1-9, 11-14)
    zone_performance = {}

    for zone in range(1, 15):
        if zone != 10:  # Skip middle-middle
            recent_performance = get_recent_zone_performance(zone_data, zone)
            baseline_performance = get_baseline_zone_performance(zone_data, zone)

            # Calculate zone command improvement
            zone_improvement = recent_performance - baseline_performance
            zone_performance[zone] = zone_improvement * 0.10

    return zone_performance
```

#### 3. Movement Quality Trends
```python
def analyze_movement_quality(pfx_x_data, pfx_z_data):
    """Analyze horizontal and vertical movement trends"""
    # Calculate recent vs. baseline movement characteristics
    recent_movement = calculate_movement_stats(pfx_x_data, pfx_z_data, 'recent')
    baseline_movement = calculate_movement_stats(pfx_x_data, pfx_z_data, 'baseline')

    # Movement improvement factor
    movement_improvement = (recent_movement - baseline_movement) * 0.08

    return movement_improvement
```

#### 4. Contact Suppression
```python
def analyze_contact_suppression(launch_angle_data, launch_speed_data):
    """Analyze contact quality suppression trends"""
    # Calculate recent vs. baseline contact quality allowed
    recent_contact_quality = calculate_contact_quality(launch_angle_data, launch_speed_data, 'recent')
    baseline_contact_quality = calculate_contact_quality(launch_angle_data, launch_speed_data, 'baseline')

    # Contact suppression improvement
    suppression_improvement = (baseline_contact_quality - recent_contact_quality) * 0.12

    return suppression_improvement
```

### Hitter Adjustments (Histogram-Based)

#### 1. Contact Quality Trends
```python
def analyze_contact_quality(barrel_data, hard_hit_data, sweet_spot_data):
    """Analyze barrel%, hard hit%, sweet spot% trends"""
    adjustments = {}

    # Barrel rate improvement
    recent_barrel_rate = get_recent_rate(barrel_data, 'barrel')
    baseline_barrel_rate = get_baseline_rate(barrel_data, 'barrel')
    barrel_improvement = (recent_barrel_rate - baseline_barrel_rate) * 0.20

    # Hard hit rate improvement
    recent_hard_hit_rate = get_recent_rate(hard_hit_data, 'hard_hit')
    baseline_hard_hit_rate = get_baseline_rate(hard_hit_data, 'hard_hit')
    hard_hit_improvement = (recent_hard_hit_rate - baseline_hard_hit_rate) * 0.15

    # Sweet spot rate improvement
    recent_sweet_spot_rate = get_recent_rate(sweet_spot_data, 'sweet_spot')
    baseline_sweet_spot_rate = get_baseline_rate(sweet_spot_data, 'sweet_spot')
    sweet_spot_improvement = (recent_sweet_spot_rate - baseline_sweet_spot_rate) * 0.12

    adjustments['contact_quality'] = barrel_improvement + hard_hit_improvement + sweet_spot_improvement

    return adjustments
```

#### 2. Launch Profile Optimization
```python
def analyze_launch_profile(launch_angle_data, exit_velocity_data):
    """Analyze launch angle and exit velocity optimization"""
    # Calculate optimal launch angle range (15-35 degrees)
    recent_optimal_launch = get_optimal_launch_percentage(launch_angle_data, 'recent')
    baseline_optimal_launch = get_optimal_launch_percentage(launch_angle_data, 'baseline')

    # Exit velocity improvement
    recent_exit_vel = get_recent_exit_velocity(exit_velocity_data)
    baseline_exit_vel = get_baseline_exit_velocity(exit_velocity_data)

    # Launch profile optimization
    launch_optimization = (recent_optimal_launch - baseline_optimal_launch) * 0.18
    exit_vel_improvement = (recent_exit_vel - baseline_exit_vel) * 0.001

    return launch_optimization + exit_vel_improvement
```

#### 3. Zone Coverage Analysis
```python
def analyze_zone_coverage(zone_data):
    """Analyze zone coverage effectiveness"""
    # Calculate success rates by zone
    zone_success_rates = {}

    for zone in range(1, 15):
        if zone != 10:  # Skip middle-middle
            recent_success = get_recent_zone_success(zone_data, zone)
            baseline_success = get_baseline_zone_success(zone_data, zone)

            zone_improvement = (recent_success - baseline_success) * 0.10
            zone_success_rates[zone] = zone_improvement

    return sum(zone_success_rates.values())
```

### Combined Adjustment Calculation
```python
def calculate_enhanced_adjustment(player_id, histogram_data, player_type):
    """Calculate comprehensive histogram-based adjustment"""

    if player_type == 'pitcher':
        # Sum all pitcher adjustments
        pitch_type_adj = analyze_pitch_type_effectiveness(histogram_data['pitch_type'])
        zone_adj = analyze_zone_effectiveness(histogram_data['zone'])
        movement_adj = analyze_movement_quality(histogram_data['pfx_x'], histogram_data['pfx_z'])
        contact_adj = analyze_contact_suppression(histogram_data['launch_angle'], histogram_data['launch_speed'])

        total_adjustment = sum(pitch_type_adj.values()) + zone_adj + movement_adj + contact_adj

    else:  # Hitter
        # Sum all hitter adjustments
        contact_adj = analyze_contact_quality(histogram_data['barrel'], histogram_data['hard_hit'], histogram_data['sweet_spot'])
        launch_adj = analyze_launch_profile(histogram_data['launch_angle'], histogram_data['exit_velocity'])
        zone_adj = analyze_zone_coverage(histogram_data['zone'])

        total_adjustment = contact_adj + launch_adj + zone_adj

    # Apply confidence weighting and safety caps
    confidence = calculate_histogram_confidence(histogram_data)
    capped_adjustment = apply_safety_caps(total_adjustment, confidence)

    return capped_adjustment
```

## Implementation Steps

### Phase 1: Histogram Analysis Engine
1. **Create HistogramAnalyzer class** for processing rich data
2. **Implement rolling window analysis** for each histogram type
3. **Calculate statistical moments** and trends
4. **Build confidence scoring** based on data quality

### Phase 2: Enhanced Projection Generator
1. **Integrate histogram analysis** with existing projection system
2. **Apply platform-specific adjustments** (DK vs FD)
3. **Calculate final enhanced projections**
4. **Generate proper pool files** for uploads

### Phase 3: Pool File Format Fix
1. **Fix current broken format** (dfs_id,name,team,my_proj)
2. **Implement required format** (player_id, player_name, sabersim_proj, my_proj)
3. **Ensure proper player identification** for each platform
4. **Generate upload-ready files**

## Pool File Format Requirements

### Current Broken Format
```csv
dfs_id,name,team,my_proj
00BQ742HG27B1F0GTVDP5I3SB,00BQ742HG27B1F0GTVDP5I3SB,,0.0
```

### Required Format for Uploads
```csv
player_id,player_name,sabersim_projection,my_projection
543243,Max Scherzer,18.5,19.2
596146,Ronald Acuña Jr.,12.8,13.1
```

### Platform-Specific Requirements
- **DraftKings**: Use DK player IDs
- **FanDuel**: Use FD player IDs
- **Player Names**: Full, readable names
- **Projections**: SaberSim baseline and our enhanced projection

## Expected Improvements

1. **More Accurate Adjustments**: Histogram data provides 25-35 data points per metric
2. **Better Trend Detection**: Identify when a pitcher's fastball command is improving
3. **Contact Quality Insights**: Know when a hitter's barrel rate is trending up
4. **Spatial Analysis**: Understand zone effectiveness and command improvements
5. **Run Value Integration**: Direct run value calculations from pitch outcomes

## Migration Strategy

1. **Phase 1**: Implement histogram analysis alongside current system
2. **Phase 2**: A/B test histogram vs. simple adjustments
3. **Phase 3**: Gradually increase histogram weight in final adjustments
4. **Phase 4**: Full migration to histogram-based system

## Next Steps

1. **Implement HistogramAnalyzer class**
2. **Create enhanced projection generator**
3. **Fix pool file format**
4. **Test with sample data**
5. **Deploy to production pipeline**