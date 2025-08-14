# ADJ Rolling Master Plan

Single source of truth for adjusting SaberSim median projections using MLB
rolling/Statcast signals, exporting upload CSVs, and iterating safely.

## Goals
- **Extract & Analyze**: Extract SaberSim simulation data (build optimizations,
  contest simulations, field lineups) for advanced ownership and stacking
  insights
- **Adjust & Enhance**: Blend SaberSim simulation-based projections (likely
  ~50th percentile from thousands of play-by-play simulations) with
  recent-performance signals (statistically responsible)
- **Re-optimize**: Re-upload adjusted projections to SaberSim for portfolio-level
  re-optimization across contest buckets
- **Portfolio Analysis**: Analyze lineup sets as a whole for optimal contest
  entry strategies and risk management
- **Platform Optimization**: Respect DK/FD scoring differences and
  contest-specific dynamics
- **Iterative Improvement**: Keep parameters tunable; enable rapid iteration
  and backtesting

## Inputs & Optimized Data Infrastructure

### Core Data Sources
- **SaberSim tables**:
  `_data/sabersim_2025/<site>/<mmdd>_<slate>/atoms_output/tables/*.json`
  (simulation-based projections, likely ~50th percentile)
- **SaberSim analysis**:
  `_data/sabersim_2025/<site>/<mmdd>_<slate>/tables_analysis/*.json`
  (ownership, stacking, contest insights)
- **MLB rolling windows**:
  `_data/mlb_api_2025/rolling_windows/data/<role>/<mlb_id>.json`
- **Statcast BBE**:
  `_data/mlb_api_2025/statcast_adv_box/data/<role>/<mlb_id>.json`
- **BBE-derived windows (middle dataset)**:
  `_data/mlb_api_2025/rolling_windows/cache/bbe_windows/<role>/<mlb_id>.json`
  (see `docs/bbe_windows.md`)

### Revolutionary Data Collection Infrastructure
**Super Aggressive Collection (16 workers, 0.1s delay):**
- **Rolling Windows**: 796 players with actual data (415 hitters + 381 pitchers)
- **Statcast BBE**: 1,426 players with game data (626 batters + 800 pitchers)
- **Collection Speed**: ~1560 players in seconds, not hours
- **Exit Handling**: Proper pipeline-ready exit codes (0=success, 1=needs update)

**Data Quality Assurance:**
- **Event-based filtering**: Only players with recent batted ball events
- **Empty file cleanup**: Removed 764 empty files, kept 796 with actual data
- **Pre-calculated histograms**: No need for complex calculations
- **Real-time updates**: Hash-based change detection with simple date-based fallback

**Collection Optimization:**
- **Rolling Windows**: Uses active rosters + cleanup (includes recently activated players)
- **Statcast BBE**: Date-based collection with super aggressive parallel processing
- **Pipeline Ready**: Both collectors exit properly for automation

### Data Validation
- **Rolling Windows**: 50/100/250 event-based windows with 2-4 week recency
- **Statcast BBE**: Comprehensive game-by-game data with player classification
- **Histogram Data**: Pre-calculated exit velocity, launch angle, pitch speed distributions
- **Quality Metrics**: xwOBA, hard hit rates, barrel rates, contact quality trends

Useful historical docs (reference only): `docs/old/fantasy_points_guide.md`, `docs/old/dk_vs_fd.md`, `docs/old/platform_adj.md`.

## Starter/Eligibility Logic
- Rookies/Call-ups: No adjustment for now (insufficient history).
- Batters to adjust: players with `bat_order_visible > 0` in SaberSim tables (treated as projected or confirmed starters until proven otherwise).
- Pitchers to adjust: implied starters from SaberSim slate context (e.g., `games.json` `home_starter`/`away_starter`); once confirmed, continue to adjust. If not confirmed, still adjust if implied.

## MVP Adjustment Method (Event-Based Rolling Windows)

### SaberSim Projection Characteristics
**Important Distinction**: SaberSim projections are **simulation-based percentiles** from thousands of play-by-play simulations, not traditional season-long projections:

- **Projection Type**: Likely ~50th percentile from simulation distributions
- **Methodology**: Play-by-play simulations incorporating game theory, matchups, park factors
- **Conservatism**: More conservative than Vegas lines or traditional models (by design)
- **Team Totals**: Projected run totals differ from Vegas lines due to simulation methodology
- **Market Impact**: Widely used by DFS community, creating market inefficiencies to exploit

**Why This Matters for Adjustments:**
- Base projections are already "smart" but may be too conservative
- Recent performance signals can identify players trending above/below simulation expectations
- Rolling adjustments help capture form changes that simulations may not fully reflect

### Revolutionary Data Discovery
Our Statcast rolling windows data is **transformational** - it provides pre-calculated quality metrics that eliminate the need for complex calculations:

**Event-Based Windows (Not Game-Based):**
- **50 events**: Most recent 50 batted ball events (~2-4 weeks)
- **100 events**: Most recent 100 batted ball events (~4-6 weeks)
- **250 events**: Most recent 250 batted ball events (~8-12 weeks)

**Pre-Calculated Quality Metrics:**
- **xwOBA**: Expected weighted on-base average (primary adjustment metric)
- **Exit Velocity Histograms**: Distribution of batted ball speeds (10-120+ mph bins)
- **Launch Angle Histograms**: Distribution of launch angles (-85° to +85° bins)
- **Pitch Speed Histograms**: For pitchers (85-100+ mph bins)

### Adjustment Calculation Method
```python
# Recency-weighted blend of event-based windows
S_recent = w50*z50 + w100*z100 + w250*z250

# Initial weights (tunable): Recent performance weighted more heavily
w50 = 0.5   # Most recent 50 events (highest weight)
w100 = 0.3  # Recent 100 events (medium weight)
w250 = 0.2  # Recent 250 events (baseline weight)

# Apply to SaberSim simulation-based projections (likely ~50th percentile)
P_adj = P_base * (1 + k * S_recent)
Cap |k * S_recent| ≤ 0.20  # Maximum 20% adjustment
```

### Quality Metrics Available (No Calculation Needed!)
**Hitters:**
- **Hard Hit Rate**: Sum events >95 mph exit velocity
- **Barrel Rate**: Optimal exit velocity + launch angle combinations
- **Ground Ball Rate**: Negative launch angles
- **Fly Ball Rate**: Positive launch angles
- **Line Drive Rate**: Launch angles 0-15°
- **Contact Quality Trends**: Exit velocity distribution shifts

**Pitchers:**
- **Pitch Speed Distribution**: Velocity trends and consistency
- **Spin Rate Data**: When available in histograms
- **Contact Quality Allowed**: Exit velocity against pitcher

### Data Quality Validation
- **796 players** with actual rolling windows data (415 hitters + 381 pitchers)
- **1,426 players** with Statcast BBE data (626 batters + 800 pitchers)
- **Event-based filtering** ensures only players with recent activity
- **Pre-calculated histograms** eliminate computational overhead

## Platform Adjustments & Contest Strategy

### DraftKings vs FanDuel Scoring Differences

**DraftKings (Power-Heavy Scoring):**
- **Home Runs**: 14 points (massive value)
- **RBIs**: 2 points
- **Runs**: 2 points
- **Stolen Bases**: 5 points
- **Pitcher Strikeouts**: 2.25 points
- **Pitcher Innings**: 2.25 points
- **Pitcher Wins**: 4 points
- **Pitcher Earned Runs**: -2 points

**FanDuel (Stack Correlation Focus):**
- **Home Runs**: 6 points (moderate value)
- **RBIs**: 3.5 points (higher than DK)
- **Runs**: 3.2 points (higher than DK)
- **Stolen Bases**: 6 points
- **Pitcher Strikeouts**: 4 points
- **Pitcher Innings**: 3 points
- **Pitcher Wins**: 6 points
- **Pitcher Earned Runs**: -3 points

### Contest Bucket Strategy

**Contest Types & Optimization:**
- **Low Stakes**: High-volume, low-entry-fee contests ($0.25-$1) - focus on volume and ownership leverage
- **Mid Entry**: Medium-volume contests ($2-$10) - balance of upside and risk management
- **Flagship**: High-stakes contests ($20+) - maximum upside with careful risk control
- **Single Entry**: Unique structures requiring single lineup - precision optimization

**Portfolio-Level Considerations:**
- **Cross-Contest Optimization**: Coordinate lineup selection across contest buckets
- **Ownership Leverage**: Vary contrarian plays across different contest types
- **Stack Diversification**: Different stack constructions for different contest profiles
- **Risk Distribution**: Balance exposure across contest payout structures

### Strategic Implications

**DraftKings Strategy:**
- **Power hitters** get massive boost (HR = 14 points)
- **Stack correlation** less important due to balanced R/RBI scoring
- **Pitchers** need K/IP efficiency (2.25 points each)
- **Focus**: Individual power upside over team correlation
- **Contest Strategy**: Leverage power upside in flagship contests, volume in low stakes

**FanDuel Strategy:**
- **Stack correlation** critical (R/RBI worth more than HR)
- **Power hitters** less dominant (HR = 6 points)
- **Pitchers** need volume (IP = 3, K = 4 points)
- **Focus**: Team offensive production over individual power
- **Contest Strategy**: Optimize stack construction across contest buckets for maximum correlation value

### Implementation Plan

1. **Platform-Specific Adjustments:**
   - DK: Boost power hitters (high barrel%, exit velocity)
   - FD: Boost stack correlation (R/RBI production)
   - Pitchers: DK favors efficiency, FD favors volume


3. **Scoring Multipliers:**
   ```python
   DK_MULTIPLIERS = {
       "hr": 14, "rbi": 2, "r": 2, "sb": 5,
       "k": 2.25, "ip": 2.25, "w": 4, "er": -2
   }
   FD_MULTIPLIERS = {
       "hr": 6, "rbi": 3.5, "r": 3.2, "sb": 6,
       "k": 4, "ip": 3, "w": 6, "er": -3
   }
   ```

4. **Adjustment Logic:**
   - Apply rolling window adjustments first
   - Then apply platform-specific scoring adjustments
   - DK: Emphasize power metrics in final projection
   - FD: Emphasize run production metrics in final projection
   - Re-upload to SaberSim for portfolio-level re-optimization

## SaberSim Dataset Layout

### Directory Structure
```
_data/sabersim_2025/<site>/<mmdd>_<slate>/atoms_output/
├── atoms/           # Raw extracted atoms
├── metadata/        # HAR metadata and extraction info
├── tables/          # Processed tables
│   ├── players.json     # Player projections and info (simulation-based, likely ~50th percentile)
│   ├── games.json       # Game info and starters
│   ├── starters.json    # DEPRECATED - will be removed
│   └── ...
└── tables_analysis/ # Analysis outputs
```

### Key Files for Starter Identification

**`players.json`** - Main player data:
- `bat_order_visible > 0`: Indicates projected starter (batter)
- `confirmed: true/false`: Lineup confirmation status
- `position`: Player position
- `team`: Team abbreviation

**`games.json`** - Game and pitcher data:
- `home_starter`: Home team starting pitcher
- `away_starter`: Away team starting pitcher
- `game_id`: Unique game identifier

**`starters.json`** - DEPRECATED:
- Will be removed from SaberSim source code
- Starter info now derived from `games.json` and `players.json`

### Starter Inference Rules

**Batters (Starters):**
- `bat_order_visible > 0` in `players.json`
- `confirmed: true` indicates lineup is confirmed
- Exclude bench players (`bat_order_visible = 0`)

**Pitchers (Starters):**
- Listed in `games.json` as `home_starter` or `away_starter`
- Projected starters even if not confirmed
- Focus on daily contests only

**Note:** Extraction code is still being improved, so some tables may not be perfect yet.

## Project Architecture: Three-Component System

### 1. Data Collector and Extractor (`src/sabersim/`)
- **Purpose**: Extract SaberSim simulation data for both adjustments and analysis
- **Key Endpoints**: Build optimizations, contest simulations, field lineups
- **Output**: Organized data by site/slate with tables and analysis

### 2. Analysis Engine (`src/sabersim/tables/analysis/`)
- **Purpose**: Analyze extracted data for ownership, stacking, and contest insights
- **Key Capabilities**: Contest simulation analysis, ownership leverage, stack ownership analysis
- **Strategic Value**: Identify contrarian plays, optimize stack construction, understand contest dynamics

### 3. Adjustments Engine (`src/win_calc/`)
- **Purpose**: Apply rolling window adjustments and re-optimize lineups
- **Process**: Load projections → Apply adjustments → Re-upload to SaberSim → Re-optimize → Analyze portfolio
- **Key Features**: Event-based rolling windows, platform-specific adjustments, quality metrics integration

## Data Flow and Directories
- **SaberSim Code**: `src/sabersim/`
- **Win Calc Code**: `src/win_calc/`
- **Working Data**: `_data/win_calc/`
- **Outputs**: `_data/win_calc/output/<site>/<mmdd>_<slate>/projections_adj.json`
- **Exports**: `_data/win_calc/export/<site>/<mmdd>_<slate>/<site>_upload.csv`

**Complete Flow**: SaberSim Original → Extract Data → Apply Adjustments → Re-upload to SaberSim → Re-optimize → Analyze Portfolio

## CLI (win_calc)
- Script: `src/win_calc/run_adj.py`
- Example:
  - `python src/win_calc/run_adj.py --site fanduel --date 0813 --slate main_slate --export`
- Key args:
  - `--site {draftkings,fanduel}`
  - `--date MMDD`
  - `--slate <name>` (default `main_slate`)
  - `--k <float>` aggressiveness (default 0.15)
  - `--cap <float>` max fractional tilt (default 0.20)
  - `--export` write upload CSV

## Output Contracts & Workflow Integration

### Primary Outputs
- **JSON**: adjusted projections with metadata, for auditing and downstream use
- **CSV (upload-ready)**: columns initially include
  - `site, slate, player_id, player_name, team, pos, salary, projection_adj`
  - Future: exposure controls, lock/fade flags
- **Upload paths (conventional)**:
  - DK: `/mnt/storage_fast/workspaces/red_ocean/dfs_1/entries/dk_upload.csv`
  - FD: `/mnt/storage_fast/workspaces/red_ocean/dfs_1/entries/fd_upload.csv`

### SaberSim Re-Integration
- **Re-upload adjusted projections** to SaberSim for re-simulation
- **Portfolio re-optimization** across contest buckets (low stakes, mid entry, flagship, single entry)
- **Contest-specific analysis** using SaberSim's contest simulation capabilities
- **Ownership leverage optimization** based on updated projections and field analysis

### Analysis Integration
- **Ownership insights**: Leverage SaberSim's field lineup analysis for contrarian plays
- **Stack optimization**: Use contest simulation data to optimize stack construction
- **Portfolio analysis**: Evaluate lineup sets as a whole for optimal contest entry strategies
- **Risk management**: Coordinate exposure across different contest types and payout structures

## Phase 2+ (Histogram-Based Quality Analysis)

### Pre-Calculated Histogram Data Structure
Our rolling windows data includes **pre-calculated histograms** that eliminate the need for complex Statcast calculations:

**Exit Velocity Histograms:**
```json
"exit_velocity": [
  {"histogram_value": "60", "pitch_count": "217"},
  {"histogram_value": "65", "pitch_count": "156"},
  {"histogram_value": "70", "pitch_count": "89"}
]
```
- **histogram_value**: Speed in mph (10-120+ mph bins)
- **pitch_count**: Number of batted ball events at that speed

**Launch Angle Histograms:**
```json
"launch_angle": [
  {"histogram_value": "-40", "pitch_count": "142"},
  {"histogram_value": "-35", "pitch_count": "117"},
  {"histogram_value": "-30", "pitch_count": "89"}
]
```
- **histogram_value**: Angle in degrees (-85° to +85° bins)
- **pitch_count**: Number of batted ball events at that angle

### Quality Metrics Calculation (No Raw Data Needed!)
**Hitter Quality Indicators:**
- **Hard Hit Rate**: `sum(events > 95 mph) / total_events`
- **Barrel Rate**: Optimal exit velocity + launch angle combinations
- **Ground Ball Rate**: `sum(negative_angles) / total_events`
- **Fly Ball Rate**: `sum(positive_angles) / total_events`
- **Line Drive Rate**: `sum(0-15° angles) / total_events`
- **Contact Quality Trends**: Exit velocity distribution shifts over time

**Pitcher Quality Indicators:**
- **Pitch Speed Distribution**: Velocity consistency and trends
- **Contact Quality Allowed**: Exit velocity against pitcher
- **Spin Rate Trends**: When available in histogram data

### Advanced Analysis Opportunities
- **Stability Indicators**: Histogram distribution consistency
- **Upside Indicators**: Recent quality metric improvements
- **Context Layers**: Opponent strength, park factors, handedness splits
- **Nonlinear Transforms**: Quality-based adjustment multipliers
- **Trend Analysis**: Rolling histogram changes over time

### Implementation Strategy
1. **Phase 1**: xwOBA-based adjustments (current MVP)
2. **Phase 2**: Add histogram-derived quality metrics
3. **Phase 3**: Quality-weighted adjustments
4. **Phase 4**: Advanced trend analysis and stability indicators

## Backtesting & Tuning
- Metrics: RMSE, calibration, contest ROI/profit metrics.
- Procedures: rolling-origin, OOS validation; grid/Bayesian tuning for (k, weights, caps, thresholds).
- Guard against overfitting via temporal splits and nested CV where practical.

## Utilities
- `starters.py`: load starter pitchers and batter starters (bat_order_visible > 0) for a site/slate.
- `platforms.py`: DK/FD metadata (salary cap, roster slots, CSV headers, upload filename, scoring multipliers).
- `exporter.py`: write per-site upload CSVs using platform metadata.
- `rolling_adjuster.py`: calculate event-based rolling window adjustments.

## Milestones & Current Progress

### ✅ COMPLETED (Infrastructure)
1. **Data Collection Infrastructure**: Super aggressive collectors with proper exit handling
2. **Data Quality Assurance**: 796 players with rolling windows, 1,426 with Statcast BBE
3. **Event-Based Windows**: 50/100/250 event windows with 2-4 week recency
4. **Pre-Calculated Histograms**: Exit velocity, launch angle, pitch speed distributions
5. **Platform Scoring**: DK vs FD scoring differences documented and implemented

### 🚧 IN PROGRESS (MVP Implementation)
1. **Data Extraction & Analysis**: Complete SaberSim pipeline for ownership and stacking insights
2. **Rolling Windows Adjustments**: xwOBA-based adjustments with recency weighting
3. **SaberSim Re-Integration**: Re-upload adjusted projections for portfolio re-optimization
4. **Contest-Specific Optimization**: Platform and contest bucket-specific strategies
5. **Portfolio Analysis**: Lineup set evaluation for optimal contest entry strategies
6. **Parameter Tuning**: Weights, caps, and thresholds optimization

### 📋 UPCOMING (Phase 2+)
1. **Histogram Quality Metrics**: Hard hit rate, barrel rate, contact quality trends
2. **Advanced Analysis**: Stability indicators, upside indicators, trend analysis
3. **Platform-Specific Adjustments**: Quality-based multipliers for DK vs FD
4. **Backtesting Framework**: Rolling origin validation and performance metrics

### 🎯 IMMEDIATE NEXT STEPS
1. **Complete SaberSim Pipeline**: Ensure extraction and analysis components are fully operational
2. **Implement MVP Adjustment Logic**: `src/win_calc/rolling_adjuster.py`
3. **Test with Real Data**: Apply to actual SaberSim simulation-based projections
4. **SaberSim Re-Integration Testing**: Validate re-upload and re-optimization workflow
5. **Contest-Specific Analysis**: Test platform and contest bucket optimization strategies
6. **Generate Sample Outputs**: DK/FD CSV files for validation
7. **Parameter Optimization**: Tune weights and caps based on results

This module is designed to be parameterized so we can iterate on weights and caps quickly.
