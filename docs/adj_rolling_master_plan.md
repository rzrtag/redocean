# ADJ Rolling Master Plan

Single source of truth for adjusting SaberSim median projections using MLB rolling/Statcast signals, exporting upload CSVs, and iterating safely.

## Goals
- Blend SaberSim median projections with recent-performance signals (statistically responsible).
- Start with precomputed rolling windows; expand to granular Statcast later.
- Respect DK/FD scoring and platform nuances.
- Export adjusted projections to CSVs for upload; optionally re-run simulations.
- Keep parameters tunable; enable rapid iteration and backtesting.

## Inputs
- SaberSim tables per site/slate: `_data/sabersim_2025/<site>/<mmdd>_<slate>/atoms_output/tables/*.json`
- MLB rolling windows: `_data/mlb_api_2025/rolling_windows/data/<role>/<mlb_id>.json`
- (Later) Statcast granular: `_data/mlb_api_2025/statcast_adv_box/...`

Useful historical docs (reference only): `docs/old/fantasy_points_guide.md`, `docs/old/dk_vs_fd.md`, `docs/old/platform_adj.md`.

## Starter/Eligibility Logic
- Rookies/Call-ups: No adjustment for now (insufficient history).
- Batters to adjust: players with `bat_order_visible > 0` in SaberSim tables (treated as projected or confirmed starters until proven otherwise).
- Pitchers to adjust: implied starters from SaberSim slate context (e.g., `games.json` `home_starter`/`away_starter`); once confirmed, continue to adjust. If not confirmed, still adjust if implied.

## MVP Adjustment Method (precomputed windows first)
- Windows: 50 events, 100 events, 250 events (existing precomputed windows, e.g., xwOBA for hitters; analogous pitcher metrics if present).
- Compute z-scores vs seasonal baseline and apply sample-size-aware shrinkage.
- Recency-weighted blend:
  - S_recent = w50*z50 + w100*z100 + w250*z250
  - Initial weights (tunable): w50=0.5, w100=0.3, w250=0.2
- Apply to SaberSim median P_base:
  - P_adj = P_base * (1 + k * S_recent)
  - Cap |k * S_recent| to ≤ cap (default cap ±0.05 for MVP)
- Minimum sample thresholds per window (e.g., hitters PA≥40; pitchers IP≥10). Below thresholds: down-weight or skip window.
- Skip adjustments if overall history insufficient.

Notes:
- Start with xwOBA for hitters; later include wOBA, Barrel%, HardHit%, K%, BB%, Contact%.
- For pitchers, aim for K-BB%, CSW%, GB%, Barrel% allowed, IP recency when available.

## Platform Adjustments

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

### Strategic Implications

**DraftKings Strategy:**
- **Power hitters** get massive boost (HR = 14 points)
- **Stack correlation** less important due to balanced R/RBI scoring
- **Pitchers** need K/IP efficiency (2.25 points each)
- **Focus**: Individual power upside over team correlation

**FanDuel Strategy:**
- **Stack correlation** critical (R/RBI worth more than HR)
- **Power hitters** less dominant (HR = 6 points)
- **Pitchers** need volume (IP = 3, K = 4 points)
- **Focus**: Team offensive production over individual power

### Implementation Plan

1. **Platform-Specific Adjustments:**
   - DK: Boost power hitters (high barrel%, exit velocity)
   - FD: Boost stack correlation (R/RBI production)
   - Pitchers: DK favors efficiency, FD favors volume

2. **Scoring Multipliers:**
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

3. **Adjustment Logic:**
   - Apply rolling window adjustments first
   - Then apply platform-specific scoring adjustments
   - DK: Emphasize power metrics in final projection
   - FD: Emphasize run production metrics in final projection

## SaberSim Dataset Layout

### Directory Structure
```
_data/sabersim_2025/<site>/<mmdd>_<slate>/atoms_output/
├── atoms/           # Raw extracted atoms
├── metadata/        # HAR metadata and extraction info
├── tables/          # Processed tables
│   ├── players.json     # Player projections and info
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

## Data Flow and Directories
- Code: `src/win_calc/`
- Working data: `_data/win_calc/`
- Outputs: `_data/win_calc/output/<site>/<mmdd>_<slate>/projections_adj.json`
- Exports: `_data/win_calc/export/<site>/<mmdd>_<slate>/<site>_upload.csv`

Inputs → win_calc → Outputs → Exports

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

## Output Contracts
- JSON: adjusted projections with metadata, for auditing and downstream use.
- CSV (upload-ready): columns initially include
  - `site, slate, player_id, player_name, team, pos, salary, projection_adj`
  - Future: exposure controls, lock/fade flags.
- Upload paths (conventional):
  - DK: `/mnt/storage_fast/workspaces/red_ocean/dfs_1/entries/dk_upload.csv`
  - FD: `/mnt/storage_fast/workspaces/red_ocean/dfs_1/entries/fd_upload.csv`

## Phase 2+ (Augmentations)
- Incorporate Statcast granular signals (EV/LA distributions, batted ball quality, pitch metrics).
- Context layers: opponent strength, park factors, handedness splits.
- Histogram-derived stability and upside indicators.
- Nonlinear/bounded transforms (e.g., exp(k*clip(S, -c, c))).

## Backtesting & Tuning
- Metrics: RMSE, calibration, contest ROI/profit metrics.
- Procedures: rolling-origin, OOS validation; grid/Bayesian tuning for (k, weights, caps, thresholds).
- Guard against overfitting via temporal splits and nested CV where practical.

## Utilities
- `starters.py`: load starter pitchers and batter starters (bat_order_visible > 0) for a site/slate.
- `platforms.py`: DK/FD metadata (salary cap, roster slots, CSV headers, upload filename, scoring multipliers).
- `exporter.py`: write per-site upload CSVs using platform metadata.
- `rolling_adjuster.py`: calculate event-based rolling window adjustments.

## Milestones
1) Ship MVP: precomputed windows → S_recent → P_adj → JSON + CSV export.
2) Add stability: thresholds, shrinkage improvements, caps finalized.
3) Expand metric set; add pitcher pathway.
4) Platform-specific adjustments based on scoring differences.

This module is designed to be parameterized so we can iterate on weights and caps quickly.
