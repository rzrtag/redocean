# Master Pipeline Runner with Data Validation

A comprehensive pipeline system that runs all data collection, processing, and validation steps with integrated data quality checks.

## 🚀 Quick Start

### Using the Shell Script (Recommended)
```bash
# Run full pipeline with validation
./run_master_pipeline.sh

# Run only validation (skip data pipelines)
./run_master_pipeline.sh --validate-only

# Run pipelines without validation
./run_master_pipeline.sh --skip-validation

# Quick validation (sample players only)
./run_master_pipeline.sh --quick
```

### Using Python Directly
```bash
# Run full pipeline
python3 src/master_pipeline/run_validator.py

# Validate only
python3 src/master_pipeline/run_validator.py --validate-only

# Skip validation
python3 src/master_pipeline/run_validator.py --skip-validation
```

## 📋 Pipeline Components

The master pipeline runs the following components in sequence:

### 1. **Pre-Validation** 🔍
- Validates existing data quality before running pipelines
- Checks rolling windows and statcast data availability
- Identifies potential issues early

### 2. **SaberSim Data Extraction** 📊
- Extracts contest data from HAR files
- Processes multiple sites (DraftKings, FanDuel)
- Generates structured "atoms" for analysis

### 3. **Post-SaberSim Validation** 🔍
- Validates extracted contest data
- Checks for missing endpoints or incomplete extractions
- Ensures data integrity

### 4. **MLB Data Collection** ⚾
- Collects Statcast advanced metrics
- Updates rolling windows data (50, 100, 250 BBE)
- Gathers player performance data

### 5. **Post-MLB Validation** 🔍
- Validates collected MLB data against official APIs
- Checks data completeness and accuracy
- Identifies any collection issues

### 6. **Win Calc Adjustments** 🧮
- Applies enhanced rolling window adjustments
- Uses hybrid signal blending (xwOBA, contact quality, power, fantasy efficiency)
- Generates adjusted projections

### 7. **Post-Win-Calc Validation** 🔍
- Validates adjustment calculations
- Checks for reasonable adjustment ranges
- Ensures no systematic biases

### 8. **Final Validation** 🔍
- Comprehensive final data quality check
- Validates all components together
- Ensures pipeline integrity

## 📊 Output Structure

All reports are saved to: `/mnt/storage_fast/workspaces/red_ocean/_data/reports/validator/`

### Directory Structure
```
_data/reports/validator/
├── YYYYMMDD_HHMMSS/                    # Timestamped run directory
│   ├── pipeline_report_YYYYMMDD_HHMMSS.json    # Main pipeline report
│   ├── validation_pre_pipeline_YYYYMMDD_HHMMSS.json
│   ├── validation_post_sabersim_YYYYMMDD_HHMMSS.json
│   ├── validation_post_mlb_YYYYMMDD_HHMMSS.json
│   ├── validation_post_win_calc_YYYYMMDD_HHMMSS.json
│   └── validation_final_YYYYMMDD_HHMMSS.json
└── ...
```

### Report Contents

#### Pipeline Report (`pipeline_report_*.json`)
```json
{
  "timestamp": "2025-08-16T01:32:49.266628",
  "pipeline_version": "1.0",
  "steps": [
    {
      "step": "SaberSim Pipeline",
      "success": true,
      "message": "Completed successfully",
      "duration": 45.2,
      "timestamp": "2025-08-16T01:32:49.266683"
    }
  ],
  "validation_reports": [
    {
      "stage": "post_sabersim",
      "report_path": "...",
      "summary": {
        "total_checks": 1,
        "valid_checks": 1,
        "error_count": 0,
        "success_rate": 100.0
      }
    }
  ],
  "summary": {
    "total_steps": 7,
    "successful_steps": 7,
    "failed_steps": 0,
    "validation_errors": 0,
    "validation_warnings": 0,
    "success_rate": 100.0,
    "pipeline_status": "SUCCESS"
  }
}
```

#### Validation Reports (`validation_*.json`)
```json
{
  "timestamp": "2025-08-16T01:32:50.450555",
  "summary": {
    "total_checks": 1,
    "valid_checks": 1,
    "invalid_checks": 0,
    "error_count": 0,
    "warning_count": 0,
    "success_rate": 100.0
  },
  "check_types": {
    "rolling_data_quality": {
      "total": 1,
      "valid": 1,
      "invalid": 0,
      "success_rate": 100.0
    }
  },
  "errors": [],
  "warnings": []
}
```

## 🔧 Configuration

### Validation Thresholds
Located in `src/win_calc/data_validator.py`:
```python
XWOBA_TOLERANCE = 0.050  # 50 points difference
EV_TOLERANCE = 2.0       # 2 mph difference
FANTASY_TOLERANCE = 0.20 # 20% difference
```

### Pipeline Paths
Located in `src/master_pipeline/run_validator.py`:
```python
SABERSIM_PIPELINE = "src/master_pipeline/run_ss.py"
MLB_PIPELINE = "src/master_pipeline/run_mlb_fg.py"
WIN_CALC_PIPELINE = "src/win_calc/pipeline/run_win_calc.py"
VALIDATION_TOOL = "src/win_calc/validate_data.py"
```

## 🚨 Error Handling

### Pipeline Status Codes
- **SUCCESS**: All steps completed successfully (100% success rate)
- **PARTIAL**: Some steps succeeded, some failed (>0% success rate)
- **FAILED**: All steps failed (0% success rate)

### Exit Codes
- **0**: Pipeline completed successfully
- **1**: Pipeline failed or completed with errors

### Common Issues
1. **MLB API Connection**: Network issues or API rate limits
2. **Missing Data**: Rolling windows or statcast data not found
3. **Validation Errors**: Data quality issues detected
4. **Pipeline Failures**: Individual pipeline component failures

## 📈 Monitoring

### Success Metrics
- **Pipeline Success Rate**: Percentage of successful steps
- **Validation Success Rate**: Percentage of passed validation checks
- **Error Count**: Number of validation errors
- **Warning Count**: Number of validation warnings

### Performance Metrics
- **Step Duration**: Time taken for each pipeline step
- **Total Duration**: Overall pipeline execution time
- **Validation Coverage**: Number of players validated

## 🔄 Automation

### Cron Job Example
```bash
# Run daily at 6 AM
0 6 * * * cd /mnt/storage_fast/workspaces/red_ocean && ./run_master_pipeline.sh

# Run validation only every hour
0 * * * * cd /mnt/storage_fast/workspaces/red_ocean && ./run_master_pipeline.sh --validate-only
```

### Integration with CI/CD
```yaml
# Example GitHub Actions workflow
- name: Run Master Pipeline
  run: |
    cd /mnt/storage_fast/workspaces/red_ocean
    ./run_master_pipeline.sh --validate-only
```

## 🛠️ Troubleshooting

### Check Pipeline Status
```bash
# View latest pipeline report
ls -la /mnt/storage_fast/workspaces/red_ocean/_data/reports/validator/
cat /mnt/storage_fast/workspaces/red_ocean/_data/reports/validator/LATEST/pipeline_report_*.json
```

### Validate Data Manually
```bash
# Run validation on specific players
python3 src/win_calc/validate_data.py --players 664040 664285

# Run validation on all players
python3 src/win_calc/validate_data.py --all
```

### Debug Pipeline Issues
```bash
# Run with verbose output
python3 src/master_pipeline/run_validator.py --validate-only

# Check individual components
python3 src/master_pipeline/run_ss.py
python3 src/master_pipeline/run_mlb_fg.py
python3 src/win_calc/pipeline/run_win_calc.py
```

## 📚 Related Documentation

- [Data Validation Tool](../win_calc/data_validator.py)
- [Enhanced Rolling Adjuster](../win_calc/enhanced_rolling_adjuster.py)
- [SaberSim Pipeline](run_ss.py)
- [MLB Pipeline](run_mlb_fg.py)
- [Win Calc Pipeline](../win_calc/pipeline/run_win_calc.py)
