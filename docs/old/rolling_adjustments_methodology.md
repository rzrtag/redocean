# Rolling Windows Adjustments — Methodology

This document describes, in detail, how the enhanced rolling-window adjustments and projections are calculated and operationalized in the `cosmic_grid` system. It covers data sources, extraction, weighting, confidence scoring, adjustment formulas, safety caps, operational rules (non-qualifiers, hashing/incremental refresh), and validation notes.

## 1) Overview

Goal: produce short-term DFS projections that (a) react to recent form and (b) remain robust to small-sample noise. The system combines multiple rolling-window series per player, applies intra-window (series) weighting, cross-window weighting, recency boosts, and confidence scoring to produce a single, bounded adjustment that modifies base projections.

Key components:
- Multi-window series extraction (5, 10, 15, 20, 30, 50 games)
- Intra-window series weighting (exponential decay inside each window)
- Cross-window weighting (favor more recent / smaller windows moderately)
- Confidence metrics (effective sample size, weighted CV, variance components)
- Adjustment formulas (hitters: weighted xwOBA + OPS + Barrel/HardHit; pitchers: K%, BB%, ERA, WHIP)
- Dynamic caps based on confidence
- Operational rules for non-qualifiers and incremental refresh (hash-based)

## 2) Data sources

- MLB Savant `player-services/rolling-thumb` (multi-window rolling series) — primary multi-window time series. Each window (e.g., `plate5`, `plate10`, ...) returns a short series ordered most-recent-first.
- MLB Savant `player-services/histogram` endpoints — additional stats used for pitcher/hitter extra features (pitch-type dist, velocity, launch angle proxies). These are optional and used when available.
- MLB Stats API (statsapi.mlb.com) — used as a lightweight authoritative feed for seasonal totals (PA, AB, innings, pitch counts) to determine qualification.
- Local roster feed (/_data/rosters/YYYY/active_players.json) — drives which players are active and role preference.

## 3) Rolling-window extraction

For each player we extract the multi-window data for windows: 5, 10, 15, 20, 30, 50 (games). For each window we store:
- `games` — games covered in the most-recent observation (rn)
- `xwoba` — the instant metric per-window (or similar metric depending on entity)
- `series` — the list of per-game or per-entry items ordered most-recent-first
- `max_game_date` — most recent date in that series (for freshness checks)

If a window has no data, it is omitted. The `_extract_multi_window_data` builds a `multi_window_data` dict keyed by window size.

## 4) Series (intra-window) weighting

Given a `series` for a window, we compute an exponentially decayed weighted mean and variance to summarize intra-window behavior:

- Decay factor: `series_decay_factor` (default 0.90)
- We assign raw weight for series entry at index `i` (0 = most recent): w_i = decay ** i
- Normalize weights to sum to 1 and compute weighted mean and weighted variance (biased; stable proxy).
- Effective points: sum(norm_weights) * len(series) — used to measure intra-window depth for confidence.

This yields per-window `series_stats`: {weighted_mean, weighted_std, effective_points}.

## 5) Cross-window weighting (inter-window)

We compute a cross-window weight for each window size that balances recency, sample size and window preference:

- Recency base weight: base_decay_factor ** (index_order), where smaller windows (more recent) get larger base weights.
- Sample-size factor: `min(1.0, games / min_games_threshold)` (limits very small windows)
- Window size preference: 1 + (window_size_preference * (1.0 / window_size)) (gives small-window boost)
- Volume penalty: max(0.1, 1.0 - (volume_penalty * (1.0 - sample_size_factor)))

Final raw weight per window = recency_weight * sample_size_factor * window_size_factor * volume_penalty. Normalize weights across windows so they sum to 1.

## 6) Weighted averages and combined stats

Using normalized cross-window weights and per-window series stats we compute:
- `weighted_xwoba` = sum(per-window-weight * per-window-mean)
- `weighted_games` = sum(per-window-weight * per-window-games)

We also compute a `confidence_metrics` bundle using the law of total variance:
- per-window means and within-window variances (from series_stats)
- overall mean = E[per-window mean]
- within_component = E[Var | window]
- between_component = Var(E[.|window])
- total_variance = within_component + between_component
- weighted_xwoba_std = sqrt(total_variance)
- weighted_xwoba_cv = weighted_xwoba_std / overall_mean if overall_mean > 0
- effective_sample_size = sum(weight * max(1.0, per-window-effective_points))

These drive a combined confidence score.

## 7) Confidence scoring

Confidence score in [0.1, 1.0] is computed as a blend:
- `sample_size_score` = min(1.0, effective_sample_size / 10.0)
- `variance_score` = max(0.1, 1.0 - min(1.0, weighted_xwoba_cv))
- `confidence` = max(0.1, min(1.0, 0.6 * sample_size_score + 0.4 * variance_score))

This yields a confidence multiplier used to scale adjustment magnitude. Low effective sample size and high CV reduces confidence.

## 8) Adjustment formulas (how we turn metrics into a % adjustment)

All adjustments are designed to be multiplicative on base projections: final = base * (1 + rolling_adj) + platform_adj.

Pitchers (examples and rationale):
- K% centered at 20%: k_z = (k_pct - 20)/10 → k_adj = 0.03 * k_z * conf_mult
- BB% centered at 8%: bb_z = (bb_pct - 8)/5 → bb_adj = -0.02 * bb_z * conf_mult
- ERA centered at 4.0: era_z = (era - 4.0)/2 → era_adj = -0.02 * era_z * conf_mult
- WHIP centered at 1.30: whip_z = (whip - 1.30)/0.5 → whip_adj = -0.02 * whip_z * conf_mult
- Total pitcher adjustment = sum of the above, then clipped to ±dynamic_cap(confidence)

Hitters:
- Weighted xwOBA (preferred): center 0.320; z = (weighted_xwoba - 0.320) / 0.080 → xwoba_adj = 0.04 * z * conf_mult * recency_boost
- OPS fallback: ops_z = (ops - 0.750) / 0.200 → ops_adj = 0.03 * ops_z * conf_mult
- Barrel% and HardHit% small positive contributions
- Total hitter adjustment = sum(...), clipped to ±dynamic_cap(confidence)

Dynamic cap: `max_adjustment_low_conf` (e.g., 0.20) at low confidence up to `max_adjustment_high_conf` (e.g., 0.35) at high confidence.

Platform adjustments: applied after rolling adjustment, small additive offsets tuned per site.

## 9) Rookies / small-sample protection

- We detect rookies or small seasonal totals via `rolling_hashes.json` / roster seasonal stats.
- Default rookie thresholds: PA < 100 or IP < 20 use a `rookie_scale` to shrink adjustments (e.g., multiply adjustment by 0.5).
- Additionally we have `volume_penalty` in cross-window weights to lower contributions from tiny windows.

## 10) Non-qualifiers & incremental refresh (operational)

- Players with insufficient season-level sample (primary criterion: pitch count or plate appearances < 50) are marked `non_qualifier` and skipped from daily Savant collection. These are recorded in `rolling_hashes.json` and `non_qualifiers.json` with: player_id, name, position, stats (per MLB API), fail_count and timestamps.
- Re-evaluation: on each run we check non-qualifiers via MLB Stats API; if the primary stat (pitches) crosses the 50 threshold (or PA >= 50 for hitters if pitch count missing), the player is unmarked and re-included immediately.
- Hash-based incremental refresh: when a player is fetched we compute SHA256 of their rolling metrics JSON blob and store it in `rolling_hashes.json`. Daily runs only fetch missing players or those explicitly forced.

## 11) Logging, checkpoints, performance

- Collector writes `collect.log` with structured timestamps, info, warning, and error levels.
- Checkpointing: metrics and hashes are checkpointed in batches (`--save-every`) to reduce I/O overhead.
- Parallel collection: optional `--concurrency` worker threads with polite `--rate-limit` delay per worker; safe defaults are `concurrency=1` and `rate-limit=0.5s`.

## 12) Tuning and validation plan

- Backtest: run a rolling historical backtest comparing base projections vs enhanced projections across slates. Key metrics: calibrated error (MAE), lineup value uplift, optimizer score.
- Grid search: tune `recency_boost_factor`, `base_decay_factor`, `max_adjustment_*` and `volume_penalty` to maximize predictive value on holdout sets.
- Robustness checks: confirm adjustments are not dominated by single tiny windows (inspect effective sample size and series_stats). Use `rookie_scale` to reduce volatility.

## 13) Repro & operational checklist

- Data freshness: ensure `_data/rosters/YYYY/active_players.json` is refreshed daily before collector run.
- One-time non-qual build: run `collect_rolling_once.py --build-nonqual-list --year <year>` offline to seed `non_qualifiers.json`.
- Daily job: run collector (incremental), then run `projection` generator to emit enhanced projections and reports. Use `--concurrency` if candidate set is larger but be cautious with Savant rate limits.

## Appendix — default parameter values

- Window sizes: [5, 10, 15, 20, 30, 50]
- Series decay factor: 0.90
- Base decay factor (cross-window): 0.85
- Series min length for intra-window weighting: 2
- Volume penalty: 0.1
- Recency boost factor: 1.2
- Confidence thresholds: low cap = 0.20, high cap = 0.35; high_conf_threshold = 0.8
- Qualification: primary `numberOfPitches >= 50`; fallback `plateAppearances >= 50` for hitters; fallback innings >= 3.0 for pitchers when pitch count missing

---

If you want, I can:
- Add this file to `docs/` (done) and create a summarized `docs/quick_reference.md` for ops.
- Generate a short validation recipe (scripts + sample datasets) to reproduce historical checks.

Which follow-up would you like?