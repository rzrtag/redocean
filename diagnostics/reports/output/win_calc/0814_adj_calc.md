## Win Calc Adjustment Calculation Details

Generated: 2025-08-14T11:29:40

Adjustment method: For each player, we pull the latest xwOBA in 50/100/250 PA windows, compute deviation from league average (pitchers inverted), take a weighted average (0.5/0.3/0.2) to form a signal, then apply k×signal to the base projection with a ±20% cap.

#### Fanduel — Batters (Detailed Breakdown)

- p.alonso (NYM)
  - base: 12.25, signal: 0.42
  - windows: 50=0.502 (56.9%); 100=0.413 (29.1%); 250=0.401 (25.2%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.06 (6.3% of base)
  - adjusted: 13.02
- m.ozuna (ATL)
  - base: 10.36, signal: 0.34
  - windows: 50=0.477 (49.1%); 100=0.400 (24.9%); 250=0.355 (10.9%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.05 (5.1% of base)
  - adjusted: 10.90
- j.soto (NYM)
  - base: 12.53, signal: 0.28
  - windows: 50=0.426 (33.1%); 100=0.356 (11.1%); 250=0.448 (40.1%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.04 (4.2% of base)
  - adjusted: 13.06
- b.buxton (MIN)
  - base: 8.83, signal: 0.34
  - windows: 50=0.461 (44.1%); 100=0.405 (26.4%); 250=0.390 (21.9%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.05 (5.2% of base)
  - adjusted: 9.29
- k.marte (ARI) — no rolling window data available
- g.perdomo (ARI) — no rolling window data available
- c.carroll (ARI) — no rolling window data available
- k.schwarber (PHI)
  - base: 12.60, signal: 0.21
  - windows: 50=0.353 (10.2%); 100=0.425 (32.8%); 250=0.414 (29.3%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.03 (3.1% of base)
  - adjusted: 12.99
- a.castillo (ARI) — no rolling window data available
- j.bell (WSH)
  - base: 8.95, signal: 0.27
  - windows: 50=0.423 (32.3%); 100=0.389 (21.4%); 250=0.396 (23.8%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.04 (4.1% of base)
  - adjusted: 9.31

#### Fanduel — Pitchers (Detailed Breakdown)

- k.senga (NYM)
  - base: 26.93, signal: -0.21
  - windows: 50=0.416 (-30.0%); 100=0.383 (-19.7%); 250=0.321 (-0.4%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=-0.03 (-3.2% of base)
  - adjusted: 26.08
- e.cabrera (MIA)
  - base: 26.61, signal: 0.19
  - windows: 50=0.241 (24.6%); 100=0.267 (16.5%); 250=0.292 (8.6%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.03 (2.8% of base)
  - adjusted: 27.37
- e.rodriguez (ARI) — no rolling window data available
- t.skubal (DET)
  - base: 36.30, signal: 0.13
  - windows: 50=0.273 (14.7%); 100=0.292 (8.7%); 250=0.266 (16.9%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.02 (2.0% of base)
  - adjusted: 37.03
- b.ober (MIN)
  - base: 27.55, signal: -0.15
  - windows: 50=0.368 (-15.1%); 100=0.366 (-14.4%); 250=0.368 (-14.9%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=-0.02 (-2.2% of base)
  - adjusted: 26.94
- b.blalock (COL)
  - base: 15.34, signal: -0.24
  - windows: 50=0.410 (-28.1%); 100=0.378 (-18.2%); 250=0.395 (-23.3%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=-0.04 (-3.6% of base)
  - adjusted: 14.78
- t.bibee (CLE)
  - base: 24.82, signal: -0.03
  - windows: 50=0.346 (-8.0%); 100=0.323 (-1.1%); 250=0.298 (6.9%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=-0.00 (-0.4% of base)
  - adjusted: 24.71
- b.elder (ATL)
  - base: 23.80, signal: 0.02
  - windows: 50=0.269 (16.0%); 100=0.348 (-8.6%); 250=0.376 (-17.6%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.00 (0.3% of base)
  - adjusted: 23.86
- b.lord (WSH)
  - base: 23.12, signal: 0.02
  - windows: 50=0.324 (-1.2%); 100=0.294 (8.2%); 250=0.321 (-0.2%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.00 (0.3% of base)
  - adjusted: 23.19

#### Draftkings — Batters (Detailed Breakdown)

- p.alonso (NYM)
  - base: 9.07, signal: 0.42
  - windows: 50=0.502 (56.9%); 100=0.413 (29.1%); 250=0.401 (25.2%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.06 (6.3% of base)
  - adjusted: 9.65
- m.ozuna (ATL)
  - base: 7.78, signal: 0.34
  - windows: 50=0.477 (49.1%); 100=0.400 (24.9%); 250=0.355 (10.9%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.05 (5.1% of base)
  - adjusted: 8.18
- j.soto (NYM)
  - base: 9.29, signal: 0.28
  - windows: 50=0.426 (33.1%); 100=0.356 (11.1%); 250=0.448 (40.1%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.04 (4.2% of base)
  - adjusted: 9.68
- b.buxton (MIN)
  - base: 6.78, signal: 0.34
  - windows: 50=0.461 (44.1%); 100=0.405 (26.4%); 250=0.390 (21.9%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.05 (5.2% of base)
  - adjusted: 7.13
- k.marte (ARI) — no rolling window data available
- g.perdomo (ARI) — no rolling window data available
- c.carroll (ARI) — no rolling window data available
- a.castillo (ARI) — no rolling window data available
- k.schwarber (PHI)
  - base: 9.28, signal: 0.21
  - windows: 50=0.353 (10.2%); 100=0.425 (32.8%); 250=0.414 (29.3%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.03 (3.1% of base)
  - adjusted: 9.57
- s.kwan (CLE)
  - base: 7.61, signal: -0.25
  - windows: 50=0.196 (-38.7%); 100=0.286 (-10.5%); 250=0.285 (-11.0%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=-0.04 (-3.7% of base)
  - adjusted: 7.33

#### Draftkings — Pitchers (Detailed Breakdown)

- k.senga (NYM)
  - base: 14.21, signal: -0.21
  - windows: 50=0.416 (-30.0%); 100=0.383 (-19.7%); 250=0.321 (-0.4%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=-0.03 (-3.2% of base)
  - adjusted: 13.76
- t.skubal (DET)
  - base: 20.79, signal: 0.13
  - windows: 50=0.273 (14.7%); 100=0.292 (8.7%); 250=0.266 (16.9%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.02 (2.0% of base)
  - adjusted: 21.20
- e.cabrera (MIA)
  - base: 14.21, signal: 0.19
  - windows: 50=0.241 (24.6%); 100=0.267 (16.5%); 250=0.292 (8.6%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.03 (2.8% of base)
  - adjusted: 14.62
- e.rodriguez (ARI) — no rolling window data available
- b.ober (MIN)
  - base: 14.83, signal: -0.15
  - windows: 50=0.368 (-15.1%); 100=0.366 (-14.4%); 250=0.368 (-14.9%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=-0.02 (-2.2% of base)
  - adjusted: 14.50
- b.blalock (COL)
  - base: 7.44, signal: -0.24
  - windows: 50=0.410 (-28.1%); 100=0.378 (-18.2%); 250=0.395 (-23.3%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=-0.04 (-3.6% of base)
  - adjusted: 7.17
- t.bibee (CLE)
  - base: 12.83, signal: -0.03
  - windows: 50=0.346 (-8.0%); 100=0.323 (-1.1%); 250=0.298 (6.9%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=-0.00 (-0.4% of base)
  - adjusted: 12.77
- b.lord (WSH)
  - base: 11.86, signal: 0.02
  - windows: 50=0.324 (-1.2%); 100=0.294 (8.2%); 250=0.321 (-0.2%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.00 (0.3% of base)
  - adjusted: 11.89
- b.elder (ATL)
  - base: 11.47, signal: 0.02
  - windows: 50=0.269 (16.0%); 100=0.348 (-8.6%); 250=0.376 (-17.6%) | weights: 50=0.5, 100=0.3, 250=0.2
  - params: k=0.15, cap=±20%, factor=0.00 (0.3% of base)
  - adjusted: 11.51
