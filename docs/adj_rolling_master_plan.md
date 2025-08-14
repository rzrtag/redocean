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
- Windows: 50-day, 100-day, 150-day (existing precomputed windows, e.g., xwOBA for hitters; analogous pitcher metrics if present).
- Compute z-scores vs seasonal baseline and apply sample-size-aware shrinkage.
- Recency-weighted blend:
  - S_recent = w50*z50 + w100*z100 + w150*z150
  - Initial weights (tunable): w50=0.6, w100=0.3, w150=0.1
- Apply to SaberSim median P_base:
  - P_adj = P_base * (1 + k * S_recent)
  - Cap |k * S_recent| to ≤ cap (default cap ±0.20)
- Minimum sample thresholds per window (e.g., hitters PA≥40; pitchers IP≥10). Below thresholds: down-weight or skip window.
- Skip adjustments if overall history insufficient.

Notes:
- Start with xwOBA for hitters; later include wOBA, Barrel%, HardHit%, K%, BB%, Contact%.
- For pitchers, aim for K-BB%, CSW%, GB%, Barrel% allowed, IP recency when available.

## Phase 2+ (Augmentations)
- Incorporate Statcast granular signals (EV/LA distributions, batted ball quality, pitch metrics).
- Context layers: opponent strength, park factors, handedness splits.
- Histogram-derived stability and upside indicators.
- Nonlinear/bounded transforms (e.g., exp(k*clip(S, -c, c))).

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

## Backtesting & Tuning
- Metrics: RMSE, calibration, contest ROI/profit metrics.
- Procedures: rolling-origin, OOS validation; grid/Bayesian tuning for (k, weights, caps, thresholds).
- Guard against overfitting via temporal splits and nested CV where practical.

## Milestones
1) Ship MVP: precomputed windows → S_recent → P_adj → JSON + CSV export.
2) Add stability: thresholds, shrinkage improvements, caps finalized.
3) Expand metric set; add pitcher pathway.
4) Add context (park/opponent/handedness) and histogram features.
5) Build backtesting harness; refine weights.
6) Optional automation: rerun SaberSim after uploads.

## FAQs
- What is MVP? Minimum Viable Product — the smallest end-to-end version that delivers value and lets us iterate safely.
- Why precomputed windows first? They’re already collected daily, enabling a fast path to a working pipeline.
- How do we treat projected vs confirmed lineups? Treat `bat_order_visible > 0` as starters (projected or confirmed). Update as confirmations roll in; adjustments apply in either case.
