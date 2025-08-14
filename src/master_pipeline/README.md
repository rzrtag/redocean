# Red Ocean Master Pipeline

The master pipeline orchestrates the core data collection processes for Red Ocean with different update frequencies.

## Pipeline Overview

### Daily Pipelines (MLB & FG)
- **`run_mlb_fg.py`** - MLB API and Fangraphs data collection (once daily)
- Updates: MLB Rosters, Fangraphs Rosters, MLB Statcast, MLB Rolling Windows

### Frequent Pipelines (SaberSim)
- **`run_ss.py`** - SaberSim data processing (up to 10x daily)
- Updates: Contest data, lineup projections, portfolio optimization

## Usage

### Daily Data Collection (MLB & FG)
```bash
# Run complete MLB and Fangraphs pipeline
python src/master_pipeline/run_mlb_fg.py

# Force update all data
python src/master_pipeline/run_mlb_fg.py --force

# Check status
python src/master_pipeline/run_mlb_fg.py --status
```

### Frequent SaberSim Updates
```bash
# Process latest HAR files
python src/master_pipeline/run_ss.py

# Process specific HAR file
python src/master_pipeline/run_ss.py --har /path/to/har

# Check SaberSim status
python src/master_pipeline/run_ss.py --status
```

## Data Flow

### Daily Pipeline (MLB & FG)
1. **MLB Rosters** → Active player rosters from MLB API
2. **Fangraphs Rosters** → Cross-reference and verification data
3. **MLB Statcast** → Comprehensive event-level data
4. **MLB Rolling Windows** → Aggregated statistics for analysis

### Frequent Pipeline (SaberSim)
1. **Atoms Extraction** → Extract data from HAR files
2. **Chunkers** → Process player/game data
3. **Tables** → Generate structured data tables
4. **Analysis** → Create analysis summaries

## Update Frequency

- **MLB & FG**: Once daily (stable data, infrequent changes)
- **SaberSim**: Up to 10x daily (breaking news, roster updates, live analysis)

## Notes

- MLB and FG data is stable and only needs daily updates
- SaberSim data changes frequently throughout the day
- Each pipeline can be run independently based on needs
