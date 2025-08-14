# MLB API Data Validation Tests

Comprehensive test suite for validating data accuracy across all MLB API collectors.

## Test Structure

```
src/mlb_api/tests/
├── __init__.py              # Package initialization
├── data_validation.py       # Main validation test suite
├── run_tests.py            # Simple test runner
├── summary.py              # Results summary display
└── README.md               # This file
```

## Test Output

Test results are saved to:
```
/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/tests/
└── validation_results_YYYYMMDD_HHMMSS.json
```

## Test Coverage

### 1. Roster Data Validation
- ✅ Team count validation (30 teams)
- ✅ Player count validation (20-30 players per team)
- ✅ Data structure validation
- ✅ Metadata validation

### 2. Statcast Data Validation
- ✅ Date files validation (100+ date files)
- ✅ Player data validation
- ✅ Data freshness validation
- ✅ Structure validation

### 3. Rolling Windows Data Validation
- ✅ Player files validation (700+ player files)
- ✅ Hash files validation
- ✅ Data structure validation
- ✅ Window sizes validation (50, 100, 250)

### 4. Cross-Reference Validation
- ✅ Player count consistency
- ✅ Team consistency
- ✅ Player ID overlap validation
- ✅ Data freshness comparison

## Usage

### Run All Tests
```bash
python src/mlb_api/tests/run_tests.py
```

### View Latest Results Summary
```bash
python src/mlb_api/tests/summary.py
```

### Run Individual Test
```python
from mlb_api.tests.data_validation import DataValidator

validator = DataValidator()
summary = validator.run_all_tests()
```

## Expected Data Patterns

- **Teams**: 30 MLB teams
- **Players per team**: 20-30 players
- **Statcast dates**: 100+ date files
- **Rolling players**: 700+ player files
- **Data overlap**: 80%+ consistency between datasets

## Test Results Interpretation

### Success Criteria
- ✅ **All tests pass** (0 errors)
- ✅ **High data consistency** (95%+ overlap)
- ✅ **Expected data volumes** met
- ✅ **Data structure** valid

### Warning Levels
- ⚠️ **Minor warnings**: Non-critical issues (e.g., missing directories)
- ⚠️ **Data freshness**: Data older than expected
- ⚠️ **Volume warnings**: Lower than expected data volumes

### Error Levels
- ❌ **Critical errors**: Missing required data or structure
- ❌ **Validation failures**: Data doesn't meet expected patterns
- ❌ **Consistency errors**: Major discrepancies between datasets

## Recent Test Results

**Latest Run**: 2025-08-13 17:16:06
- ✅ **4/4 tests passed** (100% success rate)
- ✅ **0 errors**
- ⚠️ **2 warnings** (non-critical)
- 🎉 **Excellent data consistency** (100% overlap)

### Data Quality Metrics
- 🏟️ **MLB Teams**: 30/30
- 👥 **Active Players**: 780
- 📊 **Rolling Data Files**: 791
- 🔗 **Data Consistency**: 100.0% overlap

## Continuous Integration

These tests can be integrated into CI/CD pipelines to ensure data quality:

```bash
# Exit with error code if tests fail
python src/mlb_api/tests/run_tests.py
if [ $? -eq 0 ]; then
    echo "✅ All tests passed"
else
    echo "❌ Tests failed"
    exit 1
fi
```

## Customization

You can customize test parameters by modifying the `expected_patterns` in `DataValidator`:

```python
self.expected_patterns = {
    'teams_count': 30,
    'players_per_team_min': 20,
    'players_per_team_max': 30,
    'statcast_dates_min': 100,
    'rolling_players_min': 700
}
```
