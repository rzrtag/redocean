# Platform-Specific Adjustments

Standardized adjustments for DraftKings vs FanDuel based on scoring differences. These adjustments are automatically applied to all projections.

## Overview

The `PlatformAdjustments` class provides standardized, maintainable platform-specific adjustments based on the DK vs FD scoring differences documented in `dk_vs_fd.md`.

## Usage

### Basic Usage

```python
from platform_adjustments import PlatformAdjustments

# Apply platform adjustment
result = PlatformAdjustments.apply_platform_adjustment(
    projection=10.0,
    platform='fd',
    position='OF',
    player_type='hitter'
)

print(f"Original: {result['original_projection']}")
print(f"Adjusted: {result['adjusted_projection']}")
print(f"Factor: {result['adjustment_factor']}")
print(f"Changes: {result['adjustment_factors']}")
```

### Convenience Functions

```python
from platform_adjustments import apply_fd_adjustment, apply_dk_adjustment

# FD adjustment
fd_result = apply_fd_adjustment(10.0, 'OF', 'hitter')

# DK adjustment
dk_result = apply_dk_adjustment(10.0, 'OF', 'hitter')
```

## Adjustment Factors

### FanDuel Premiums

#### Hitters
- **HR Premium**: +20% (12 vs 10 points)
- **RBI Premium**: +75% (3.5 vs 2 points)
- **Run Premium**: +60% (3.2 vs 2 points)
- **SB Premium**: +20% (6 vs 5 points)
- **BB Premium**: +50% (3 vs 2 points)
- **HBP Premium**: +50% (3 vs 2 points)
- **Power/Speed Bonus**: +8% overall

#### Pitchers
- **IP Premium**: +33% (3 vs 2.25 points)
- **K Premium**: +50% (3 vs 2 points)
- **Win Premium**: +50% (6 vs 4 points)
- **QS Bonus**: +4 points (FD exclusive)
- **ER Penalty**: +50% (-3 vs -2 points)
- **Risk Factor**: -5% (single-pitcher concentration)

### DraftKings Premiums

#### Hitters
- **Balanced Scoring**: +1% (more balanced approach)
- **Stack Bonus**: +1% (5-player stack advantage)

#### Pitchers
- **Flexibility Bonus**: +2% (2-pitcher flexibility)
- **Balanced Scoring**: +1% (more balanced IP/K values)

## Position-Specific Adjustments

### FanDuel
- **SP**: QS focus (+2%), durability bonus (+1%), K rate bonus (+1%)
- **RP**: Risk factor (-2%), K rate bonus (+1%)
- **OF**: Power/speed bonus (+3%), SB bonus (+1%)
- **1B**: Power bonus (+2%)
- **2B**: Balanced bonus (+1%)
- **3B**: Power bonus (+2%)
- **SS**: Power/speed bonus (+2%)
- **C**: Power bonus (+1%)

### DraftKings
- **SP**: Flexibility bonus (+1%)
- **RP**: Flexibility bonus (+1%)
- **All Hitters**: Stack bonus (+1%)

## Integration

The platform adjustments are automatically integrated into the projection engine:

```python
# In custom_projection_engine.py
from platform_adjustments import PlatformAdjustments

# Apply standardized platform adjustments
platform_result = PlatformAdjustments.apply_platform_adjustment(
    custom_projection, platform, position, player_type
)

custom_projection = platform_result['adjusted_projection']
adjustment_factors.extend(platform_result['adjustment_factors'])
```

## Maintenance

### Adding New Adjustments

1. Update the `SCORING_PREMIUMS` dictionary in `platform_adjustments.py`
2. Add position-specific adjustments to `POSITION_ADJUSTMENTS`
3. Update the adjustment logic in `get_platform_adjustment()`

### Modifying Existing Adjustments

1. Edit the values in `SCORING_PREMIUMS` or `POSITION_ADJUSTMENTS`
2. The changes will automatically apply to all projections

### Testing Adjustments

Run the test script to verify adjustments:

```bash
python src/star_cannon/core/projections/test_platform_adjustments.py
```

## Example Results

### FanDuel Adjustments
- **FD SP (40.0)**: 38.76 (-5% risk, +2% QS focus)
- **FD OF (12.0)**: 13.48 (+8% power/speed, +3% OF bonus, +1% SB)
- **FD 1B (10.0)**: 11.02 (+8% power/speed, +2% power bonus)

### DraftKings Adjustments
- **DK SP (25.0)**: 25.50 (+2% flexibility)
- **DK OF (9.0)**: 9.18 (+1% balanced, +1% stack)
- **DK RP (15.0)**: 15.30 (+2% flexibility)

## Benefits

1. **Standardized**: All platform adjustments in one place
2. **Maintainable**: Easy to update scoring differences
3. **Documented**: Clear mapping to DK vs FD differences
4. **Testable**: Automated testing of adjustment logic
5. **Consistent**: Same adjustments applied across all projections

## Future Enhancements

- Weather-based adjustments
- Ballpark factor adjustments
- Opponent-specific adjustments
- Real-time lineup adjustments
- Advanced trend detection 