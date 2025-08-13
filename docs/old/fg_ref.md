# FanGraphs Reference System

## Overview

The **FanGraphs Reference System** is a comprehensive mapping of baseball statistics to their standard FanGraphs abbreviations. This system serves as the authoritative source for stat abbreviations in our table system, ensuring consistency with the industry standard.

## Key Features

### 🎯 **FanGraphs as Primary Reference**
- Uses FanGraphs API structure as the source of truth
- Preserves original case and symbols (e.g., `K/9`, `BB%`, `wRC+`)
- Comprehensive coverage of all major baseball statistics

### 📊 **13 Categories of Statistics**
- **Batting**: 42 stats (G, AB, PA, H, HR, R, RBI, BB, SO, SB, AVG, OBP, SLG, OPS, wOBA, wRC+, WAR, etc.)
- **Pitching**: 11 stats (W, L, ERA, WHIP, IP, K, BB, K/9, BB/9, K/BB, WAR, etc.)
- **Advanced**: 7 stats (wOBA, wRAA, wRC, wRC+, WAR, WAROld, Dollars)
- **Fielding**: 3 stats (Fielding, Defense, CFraming)
- **Base Running**: 4 stats (BaseRunning, Spd, wBsR, UBR)
- **Clutch**: 9 stats (WPA, -WPA, +WPA, RE24, REW, pLI, phLI, WPA/LI, Clutch)
- **Pitch Types**: 8 stats (FB%, SL%, CT%, CB%, CH%, SF%, KN%, XX%)
- **Velocity**: 8 stats (FBv, SLv, CTv, CBv, CHv, SFv, KNv, XXv)
- **Pitch Value**: 14 stats (wFB, wSL, wCT, wCB, wCH, wSF, wKN, etc.)
- **Plate Discipline**: 11 stats (O-Swing%, Z-Swing%, Swing%, O-Contact%, Z-Contact%, Contact%, Zone%, F-Strike%, SwStr%, CStr%, C+SwStr%)
- **Batted Ball**: 12 stats (Pull, Cent, Oppo, Pull%, Cent%, Oppo%, Soft, Med, Hard, Soft%, Med%, Hard%)
- **Statcast**: 7 stats (EV, LA, Barrels, Barrel%, maxEV, HardHit, HardHit%)
- **DFS**: 8 stats (pts, pts/$, sal, own, stack_own, primary, secondary, tertiary)

### 🔍 **Smart Lookup System**
- **Direct lookup**: Exact match for abbreviations
- **Full name matching**: "Home Runs" → "HR"
- **Partial matching**: "home" → "HR"
- **Case-insensitive**: Works regardless of input case

### 🎨 **Symbol Preservation**
- **Slashes**: `K/9`, `BB/9`, `pts/$`
- **Percentages**: `BB%`, `K%`, `O-Swing%`
- **Plus signs**: `wRC+`
- **Dashes**: `O-Swing%`, `Z-Swing%`

## Usage Examples

### Basic Usage

```python
from star_cannon.core.tables.utils.fangraphs_reference import get_fangraphs_abbreviation

# Full names to abbreviations
get_fangraphs_abbreviation("Home Runs")  # Returns: "HR"
get_fangraphs_abbreviation("Batting Average")  # Returns: "AVG"
get_fangraphs_abbreviation("Earned Run Average")  # Returns: "ERA"
get_fangraphs_abbreviation("Weighted On Base Average")  # Returns: "wOBA"

# Already abbreviated stats (preserved)
get_fangraphs_abbreviation("K/9")  # Returns: "K/9"
get_fangraphs_abbreviation("BB%")  # Returns: "BB%"
get_fangraphs_abbreviation("wRC+")  # Returns: "wRC+"
```

### Table Standards Integration

```python
from star_cannon.core.tables.utils.table_standards import get_column_abbreviation

# Automatically uses FanGraphs as primary reference
get_column_abbreviation("Home Runs")  # Returns: "HR"
get_column_abbreviation("K/9")  # Returns: "K/9" (preserves case and symbols)
get_column_abbreviation("Points Per Dollar")  # Returns: "pts/$"
```

### Advanced Usage

```python
from star_cannon.core.tables.utils.fangraphs_reference import fangraphs_ref

# Get all stats in a category
batting_stats = fangraphs_ref.get_stats_by_category("batting")
pitching_stats = fangraphs_ref.get_stats_by_category("pitching")

# Get common stats
common_batting = fangraphs_ref.get_common_batting_stats()
common_pitching = fangraphs_ref.get_common_pitching_stats()
dfs_stats = fangraphs_ref.get_dfs_stats()

# Search for stats
results = fangraphs_ref.search_stats("home")  # Returns: ['HR', 'HR/FB']

# Validate stats
fangraphs_ref.validate_stat("HR")  # Returns: True
fangraphs_ref.validate_stat("invalid")  # Returns: False

# Get comprehensive stat info
info = fangraphs_ref.get_stat_info("HR")
# Returns: {
#     "stat": "HR",
#     "full_name": "Home Runs",
#     "abbreviation": "HR",
#     "category": "batting",
#     "description": "Home runs",
#     "data_type": "numeric",
#     "decimal_places": 0
# }
```

## Integration with Table Standards

The FanGraphs reference system is seamlessly integrated with our table standards:

### Priority Order
1. **Predefined standards** (table-specific overrides)
2. **FanGraphs validation** (if input is already a valid abbreviation)
3. **FanGraphs lookup** (full name to abbreviation)
4. **Common stats mapping** (snake_case to abbreviation)
5. **Fallback logic** (general abbreviation rules)

### Benefits
- **Consistency**: All baseball stats use FanGraphs abbreviations
- **Flexibility**: Non-baseball stats still use general rules
- **Preservation**: Original case and symbols maintained
- **Extensibility**: Easy to add new stats or categories

## Common Statistics

### Batting Stats
```python
COMMON_STATS = {
    "home_runs": "HR",
    "batting_average": "AVG",
    "on_base_percentage": "OBP",
    "slugging_percentage": "SLG",
    "ops": "OPS",
    "woba": "wOBA",
    "wrc_plus": "wRC+",
    "war": "WAR",
    # ... and many more
}
```

### Pitching Stats
```python
COMMON_STATS = {
    "era": "ERA",
    "whip": "WHIP",
    "k_per_9": "K/9",
    "bb_per_9": "BB/9",
    "k_bb_ratio": "K/BB",
    # ... and many more
}
```

### DFS Stats
```python
COMMON_STATS = {
    "points": "pts",
    "points_per_dollar": "pts/$",
    "salary": "sal",
    "ownership": "own",
    "stack_ownership": "stack_own",
}
```

## Data Types and Formatting

Each statistic includes metadata for proper formatting:

```python
@dataclass
class StatDefinition:
    full_name: str          # "Home Runs"
    abbreviation: str       # "HR"
    category: str          # "batting"
    description: str       # "Home runs"
    data_type: str         # "numeric", "percentage", "currency", "text"
    decimal_places: int    # 0, 1, 2, 3
```

### Formatting Examples
- **Numeric**: `123.46` (2 decimal places)
- **Percentage**: `12.34%` (2 decimal places)
- **Currency**: `$1,234` (0 decimal places)
- **Text**: `"Hello World"` (as-is)

## Testing

Comprehensive tests verify the system:

```bash
# Run FanGraphs integration tests
PYTHONPATH=src python src/star_cannon/core/tables/tests/test_fangraphs_integration.py

# Run table standards tests
PYTHONPATH=src python src/star_cannon/core/tables/tests/test_table_standards.py
```

## Future Enhancements

### Planned Features
- **Dynamic updates**: Fetch latest stats from FanGraphs API
- **Custom categories**: User-defined stat groupings
- **Export formats**: JSON, CSV, YAML configurations
- **Validation rules**: Stat-specific validation logic
- **Historical tracking**: Version control for stat definitions

### Extensibility
- **New platforms**: Support for other stat providers
- **Custom stats**: User-defined statistics
- **International**: Support for different languages
- **Analytics**: Usage tracking and optimization

## Best Practices

### When to Use FanGraphs Reference
✅ **Use for**: Baseball statistics, DFS metrics, standard abbreviations
✅ **Use for**: Maintaining consistency with industry standards
✅ **Use for**: Preserving original case and symbols

### When to Use Fallback Logic
✅ **Use for**: Non-baseball statistics
✅ **Use for**: Custom application-specific fields
✅ **Use for**: General text processing

### Performance Considerations
- **Caching**: FanGraphs reference is initialized once
- **Lookup**: O(1) for direct matches, O(n) for searches
- **Memory**: Minimal footprint (~50KB for all definitions)

## Troubleshooting

### Common Issues

**Issue**: Stat not found
```python
# Check if stat exists
if fangraphs_ref.validate_stat("MY_STAT"):
    print("Stat found!")
else:
    print("Stat not found - check spelling or add to definitions")
```

**Issue**: Case sensitivity
```python
# FanGraphs preserves original case
get_fangraphs_abbreviation("k/9")  # Returns: "K/9"
get_fangraphs_abbreviation("K/9")  # Returns: "K/9"
```

**Issue**: Symbol handling
```python
# Symbols are preserved
get_fangraphs_abbreviation("BB%")  # Returns: "BB%"
get_fangraphs_abbreviation("wRC+")  # Returns: "wRC+"
```

### Debugging

```python
# Get detailed stat information
info = fangraphs_ref.get_stat_info("HR")
print(f"Stat: {info['stat']}")
print(f"Full name: {info['full_name']}")
print(f"Category: {info['category']}")
print(f"Description: {info['description']}")

# Search for similar stats
results = fangraphs_ref.search_stats("home")
print(f"Similar stats: {results}")
```

## Conclusion

The FanGraphs Reference System provides a robust, comprehensive solution for baseball statistics abbreviation. By using FanGraphs as the primary reference, we ensure consistency with industry standards while maintaining flexibility for custom applications.

The system is designed to be:
- **Comprehensive**: Covers all major baseball statistics
- **Flexible**: Supports custom and non-baseball stats
- **Consistent**: Maintains industry-standard abbreviations
- **Extensible**: Easy to add new stats and categories
- **Performant**: Fast lookups with minimal memory usage

This foundation enables consistent, professional table formatting across all our baseball analytics and DFS applications. 