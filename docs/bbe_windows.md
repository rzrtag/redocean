## BBE-Derived Rolling Windows (Middle Dataset)

### Why a Middle Dataset?
- Ensure consistency with event-based window definitions (last N batted ball events)
- Decouple raw Statcast BBE from adjustment logic (speed, reproducibility)
- Provide a traceable, cacheable artifact for audits and rapid iteration

### Sources
- Raw BBE: `_data/mlb_api_2025/statcast_adv_box/data/<role>/<mlb_id>.json`
  - Expected to contain event-level records or an `events` array with keys like
    `ts`/`timestamp`, `exit_velocity`, `launch_angle`, optional `xwoba_value`

### Window Definition
- Event-based windows, not games:
  - 50 events: Last 50 BBE events (≈ 2–4 weeks)
  - 100 events: Last 100 BBE events (≈ 4–6 weeks)
  - 250 events: Last 250 BBE events (≈ 8–12 weeks)
- Always take the chronological tail of the event stream
- If events available < N, compute with what is available and record coverage

### Metrics per Window
- `xwoba`: mean of `xwoba_value` if present; 0.0 if absent
- `hard_hit`: share of events with exit velocity ≥ 95 mph
- `barrel`: proxy via EV in [95,105] mph and LA in [8,32] degrees
- `optimal_contact`: share of events with EV ≥ 90 mph

### Cache Path
- Cache JSON: `_data/mlb_api_2025/rolling_windows/cache/bbe_windows/<role>/<mlb_id>.json`

### Cache File Schema
```json
{
  "metadata": {
    "mlb_id": "681481",
    "role": "batter",
    "as_of_utc": "2025-08-14T04:32:00+00:00",
    "source": "bbe_recompute",
    "events_available": 423,
    "last_event_ts": 1723600000
  },
  "coverage": { "50": 50, "100": 100, "250": 229 },
  "windows": {
    "50": {
      "xwoba": 0.372,
      "hard_hit": 0.44,
      "barrel": 0.16,
      "optimal_contact": 0.52
    },
    "100": { "xwoba": 0.351, "hard_hit": 0.41, "barrel": 0.14, "optimal_contact": 0.49 },
    "250": { "xwoba": 0.335, "hard_hit": 0.38, "barrel": 0.11, "optimal_contact": 0.47 }
  }
}
```

### Invalidation Policy (Date-Based)
- We do not use content hashes for Statcast BBE invalidation.
- To decide whether to reuse cache or recompute:
  1. Read the source BBE file; get the latest event timestamp (`last_ts`).
  2. Read the cache metadata `last_event_ts`.
  3. If equal, use cache; if different, recompute and overwrite cache.
- This aligns with the collection process, which is date-based.

### Selection & Blending Policy (win_calc)
- Preference order:
  1. Use BBE-derived windows from cache if `last_event_ts` matches source
  2. If no cache or mismatch, recompute from BBE and write cache
  3. If BBE unavailable, synthesize from precomputed rolling windows
- Optional blending with precomputed windows when coverage/staleness is weak:
  - `alpha` toward precomputed grows when coverage ratio (coverage/N) is low
  - `alpha` may also grow when staleness (days since last BBE) is high
  - Blended metric `m = alpha * pre + (1 - alpha) * bbe`

### Configuration (src/win_calc/config.py)
- `BBE_CONFIG`:
  - `enable_cache`: toggle cache read/write
  - `min_events`: minimum events considered reasonable for N in {50,100,250}
  - `staleness_days_threshold`: consider stale beyond this age
  - `blend_with_precomputed`: enable blending with precomputed windows
  - `blend_coverage_floor`: below this coverage ratio, increase alpha
  - `blend_staleness_days`: days where staleness starts to influence alpha
  - `decay_lambda`: optional exponential decay hyperparameter (future use)
- `FEATURE_WEIGHTS`:
  - Initial linear blend weights for `{xwoba, hard_hit, barrel, optimal_contact}`

### Adjustment Signal
- For each window (50/100/250), compute a feature-blended score:
  - `score_N = w_x * xwoba + w_hh * hard_hit + w_b * barrel + w_oc * optimal_contact`
- Recency-weighted combination:
  - `S_recent = w50 * score_50 + w100 * score_100 + w250 * score_250`
- Apply adjustment with cap:
  - `P_adj = P_base * (1 + k * S_recent)`, with `|k * S_recent| ≤ cap`

### Confidence & Shrinkage
- Record coverage (events used) to derive a confidence scalar
- Optionally shrink S_recent toward 0 for low-coverage windows
- Optionally incorporate staleness penalty (future step)

### Future Enhancements
- Incremental updates: append newly observed BBE, drop earliest to keep N
- Volatility-aware down-weighting (IQR of EV/LA distributions)
- Bayesian or grid optimization of feature weights (see weight refinement doc)
- Separate hitter/pitcher models and features
