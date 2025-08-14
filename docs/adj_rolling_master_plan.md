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

## Platform Adjustments (DK vs FD)
Platform differences must be respected end-to-end.

- Scoring systems: DK and FD award different fantasy points for events. Until we port scoring tables, we adjust the site-specific SaberSim median directly (already expressed in the site’s FP units). No cross-site mixing.
- CSV schemas: Upload column names and formats can differ by platform; we will maintain per-site exporters (`dk_upload.csv`, `fd_upload.csv`).
- Roster/constraints & salary caps: Used downstream for portfolio optimization; keep site metadata available alongside projections.
- Implementation plan:
  1) Centralize platform metadata in `win_calc` (site id, scoring version tag, CSV schema hints, salary cap, roster constraints).
  2) Ensure the adjustment path always uses site-scoped inputs and writes site-scoped outputs.
  3) Later, port exact scoring rules from `docs/old/fantasy_points_guide.md` and `docs/old/dk_vs_fd.md` into code to support statline-to-FP recalculation if needed for backtests.
  4) Validate export files with small test uploads on each platform.

References for porting (to be codified soon):
- `docs/old/fantasy_points_guide.md` — event scoring
- `docs/old/dk_vs_fd.md` — platform differences
- `docs/old/platform_adj.md` — prior platform adjustment notes

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

## SaberSim Dataset Layout (per site/slate)
Base directory example (FanDuel main slate on 08/13):
`_data/sabersim_2025/fanduel/0813_main_slate`

- `atoms_output/`
  - `atoms/`
    - `build_optimization.json`: Latest build optimization configuration/results snapshot.
    - `contest_information.json`: Contest listings, sizes, payouts, metadata.
    - `contest_simulations_<bucket>.json`: Contest-level simulation results for a specific bucket (e.g., `flagship_mid_entry`).
    - `field_lineups_<bucket>.json`: Field (opponent) lineup samples/flags for a contest bucket.
  - `metadata/`
    - `atom_registry.json`: Known atom IDs written during extraction.
    - `endpoint_mapping.json`: Map of endpoint types to atom IDs.
    - `extraction_summary.json`: When/what was extracted (mtime, counts, provenance).
  - `tables/`
    - `contest_summary.json`: Consolidated summary of contests on the slate.
    - `games.json`: Per-game slate context (start times, starters, team confirmations, win probs, etc.).
    - `map_docs.json`: Cross-reference map (players/teams/games) for convenience.
    - `master_summary.json`: High-level rollup across generated tables.
    - `players.json`: Player-level table (ids, names, teams, positions, salaries, projections).
    - `starters.json`: Starter-centric view derived from atoms/tables (batters with `bat_order_visible`, implied SPs).

- `tables_analysis/`
  - `contest_site_summary.json`: Summary of site/slate-level metrics (counts, coverage, timestamps).
  - `lineup_stats.json`: Aggregate lineup-level statistics derived from tables/atoms.
  - `pid_own_batters_<bucket>.json`: Batter ownership estimates per player id for a contest bucket.
  - `pid_own_pitchers_<bucket>.json`: Pitcher ownership estimates per player id for a contest bucket.
  - `stack_analysis.json`: Stack configuration analysis (team stacks, sizes, efficiency metrics).
  - `stack_own_<bucket>.json`: Stack ownership estimates for the given contest bucket.

Notes:
- Buckets (e.g., `flagship_mid_entry`) segment contest types/sizes; multiple bucket files may exist.
- Starters:
  - Batters are considered projected/confirmed starters if `bat_order_visible > 0`.
  - Pitchers are implied via `games.json` (`home_starter`/`away_starter`) and confirmation flags elsewhere; treat implied as starters until proven otherwise.
- These artifacts refresh as lineups confirm; ADJ should tolerate projected status and update when confirmations arrive.
