# ADJ Projections System: Master Plan

This document outlines the design for the ADJ projection system that blends SaberSim median projections with recent-performance adjustments derived from MLB Statcast and rolling windows. The goal is to tilt toward recent form in a statistically responsible way, export adjusted projections for upload, and re-run SaberSim simulations to gain unique edges.

### Objectives
- Combine robust SaberSim median projections with signal from recent rolling windows
- Emphasize recency while controlling for sample size and noise
- Preserve site-specific scoring and constraints for DK and FD
- Export adjusted projections to CSV for upload, then re-run contest simulations
- Keep the system tunable: weights, windows, shrinkage, filters

### Inputs and Sources
- SaberSim
  - Median projections per player per slate from contest simulations
  - Provided via extracted atoms/tables under `_data/sabersim_2025/<site>/<mmdd>_<slate>/atoms_output/tables/`
- MLB API
  - Rolling windows data (hitters/pitchers) under `_data/mlb_api_2025/rolling_windows/...`
  - Statcast advanced data for validating/engineering recency signals

References to prior docs for methodology and scoring details:
- `docs/old/rolling_adjustments_methodology.md`
- `docs/old/weight_refinement_methodology.md`
- `docs/old/fantasy_points_guide.md`
- `docs/old/platform_adj.md`
- `docs/old/dk_vs_fd.md`

---

### Adjustment Methodology (initial proposal)

We define a recent-performance signal S per player that blends multiple rolling windows with decay and shrinkage to long-term baseline:

- Windows: 7-day, 14-day, 30-day (configurable), optionally 60-day as a stability anchor
- Metrics for batters: xwOBA, wOBA, Barrel%, HardHit%, K%, BB%, Contact%, recent playing time
- Metrics for pitchers: K-BB%, CSW%, xERA components, GB%, FB%, Barrel% allowed, recent IP
- Opponent/context optional layers (later): opposing SP/lineup strength, park, handedness

Signal construction (per metric m):

1) Z-score vs player’s seasonal baseline with sample-size-aware shrinkage:
   - z_m = (recent_m - season_m) / max(epsilon, std_m)
   - shrunken_z_m = z_m * shrinkage_factor(recent_sample_size)

2) Decayed blend across windows:
   - S_m = w7 * shrunken_z_m(7d) + w14 * shrunken_z_m(14d) + w30 * shrunken_z_m(30d)
   - Sum of w7, w14, w30 = 1; e.g., w7=0.5, w14=0.3, w30=0.2 (tunable)

3) Aggregate across metrics with metric weights a_m:
   - S = Σ_m a_m * S_m,  with Σ_m a_m = 1 (per role: batter/pitcher)

Adjustment application on SaberSim median projection P_base (site-specific points):
- Linear tilt: P_adj = P_base * (1 + k * S), k>0 controls aggressiveness
- Or bounded transform: P_adj = P_base * exp(k * clip(S, -c, c)) to reduce extreme tails

Stability controls:
- Minimum sample thresholds per window (PA/IP). If below, reduce weight for that window
- Global shrinkage toward season/team/league baseline if volatility > threshold
- Cap final adjustment to ±X% (e.g., ±20%)

We’ll iterate on k, window weights, metric weights, and caps using backtests.

---

### Site and Scoring Specifics
- Respect DK vs FD scoring per `docs/old/fantasy_points_guide.md`
- Maintain platform-specific nuances per `docs/old/platform_adj.md` and `docs/old/dk_vs_fd.md`
- Export per-site upload files:
  - DK: `/mnt/storage_fast/workspaces/red_ocean/dfs_1/entries/dk_upload.csv`
  - FD: `/mnt/storage_fast/workspaces/red_ocean/dfs_1/entries/fd_upload.csv`

CSV export columns (initial):
- site, slate, contest_bucket, player_id, player_name, team, pos, salary, projection_adj, exposure (optional)
- Additional columns we can support: min/max exposure, lock/fade flags, notes

---

### Data Flow and Directory Layout

Code module:
- `src/win_calc/` — site-agnostic adjustment engine consuming MLB + SaberSim data

Runtime data:
- `_data/win_calc/` — working data for intermediate artifacts
- `_data/win_calc/output/` — per-site per-slate adjusted projection JSON/CSV
- `_data/win_calc/export/` — upload-ready CSVs for SaberSim/platforms

Inputs → win_calc → Outputs → Exports

- Inputs: `_data/sabersim_2025/<site>/<mmdd>_<slate>/atoms_output/tables/*.json`, `_data/mlb_api_2025/rolling_windows/...`
- Outputs: `_data/win_calc/output/<site>/<mmdd>_<slate>/projections_adj.json`
- Exports: `_data/win_calc/export/<site>/<mmdd>_<slate>/<site>_upload.csv`

---

### CLI Plan
- `src/win_calc/run_adj.py` (to be implemented)
  - Args: `--site {draftkings,fanduel}`, `--date MMDD`, `--slate`, `--bucket`, `--aggr K`, `--cap PCT`, `--export`
  - Optional: `--force`, `--status`, `--players-file` overrides
  - Behavior: load base projections + rolling windows, compute S, produce P_adj, write outputs, optional CSV export

### Integration Touchpoints
- After writing adjusted projections, optionally re-run SaberSim analyses to reflect new projections (manual upload step or future automation)
- Keep logs and progress output consistent with other pipelines (percent, ETA), per user preference

---

### Backtesting and Weight Refinement
- Use historical slates to evaluate metrics (RMSE, calibration, profit metrics)
- Grid search or Bayesian optimization for (k, window weights, metric weights, caps)
- Out-of-sample validation across date ranges and slate types
- Track overfitting via nested CV and rolling-origin evaluation

---

### Milestones
1) Scaffolding: module + data dirs + export format contract
2) MVP: implement S from a small metric set; linear tilt; per-site CSV export
3) Add stability: shrinkage by sample, caps, min thresholds
4) Expand metrics and windows; incorporate opponent/park splits
5) Backtesting harness; weight refinement workflow
6) Optional automation: trigger SaberSim refresh after uploads

---

### Open Questions
- Which exact metrics per role for MVP?
- Final cap percent and default k?
- How to handle players with missing rolling windows (call-ups, injuries)?
- Exposure rules in CSV or defer to SaberSim UI?

This plan will evolve as we iterate on parameters and validation results.
