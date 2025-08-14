# ADJ System: Rolling Windows Plan

This document details how we will use rolling window data in the MVP and expand later.

## MVP (Precomputed Windows First)

- Source: `_data/mlb_api_2025/rolling_windows/data/<role>/<mlb_id>.json`
- Use precomputed windows present (e.g., xwOBA for hitters, K-BB% for pitchers if available).
- Windows prioritized by recency: 50-day, 100-day, 150-day
- Compute a recency-weighted signal:
  - `S_recent = w50 * z50 + w100 * z100 + w150 * z150`
  - Initial weights (tunable): `w50=0.6, w100=0.3, w150=0.1`
- Z-scores computed vs season baseline with sample-size-aware shrinkage
- Minimum sample size thresholds per window (e.g., PA>=40 for hitters)
- Cap final adjustment multiplier at ±20%
- Skip rookies/call-ups with insufficient history

## Players to Adjust

- Batters: those with `bat_order_visible > 0` in SaberSim tables for the slate
- Pitchers: implied starters from `games.json` (`home_starter` / `away_starter`) until confirmed; when confirmed, continue to adjust

## Output

- Adjusted projections JSON:
  - `_data/win_calc/output/<site>/<mmdd>_<slate>/projections_adj.json`
- Upload CSV:
  - `_data/win_calc/export/<site>/<mmdd>_<slate>/<site>_upload.csv`
  - Columns: `site, slate, player_id, player_name, team, pos, salary, projection_adj`

## Phase 2: Augmentations

- Incorporate Statcast granular metrics from event-level files
- Add more metrics: Barrel%, HardHit%, Contact%, CSW%, GB%, etc.
- Opponent/park/handedness context blending
- Histogram-derived stability and upside risk indicators
- Backtesting to tune weights and caps

## Notes

- We will iterate on the exact metric set and thresholds once MVP is functional end-to-end.
- Histograms present in rolling datasets will be used later once methodology is finalized.
