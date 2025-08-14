# win_calc Module

Site-agnostic adjustment engine that blends SaberSim median projections with MLB rolling/Statcast signals to produce adjusted projections and upload CSVs.

## Scope
- Load SaberSim base projections per site/slate
- Load MLB rolling windows/Statcast metrics
- Compute recent-performance signal with decay and shrinkage
- Apply tilt to base projections with caps
- Output adjusted projections and export CSVs for DK/FD

## Inputs
- `_data/sabersim_2025/<site>/<mmdd>_<slate>/atoms_output/tables/*.json`
- `_data/mlb_api_2025/rolling_windows/...`

## Outputs
- `_data/win_calc/output/<site>/<mmdd>_<slate>/projections_adj.json`
- `_data/win_calc/export/<site>/<mmdd>_<slate>/<site>_upload.csv`

## CLI (planned)
- `python src/win_calc/run_adj.py --site draftkings --date 0813 --slate main_slate --export`

## Utilities
- `starters.py`: load starter pitchers and batter starters (bat_order_visible > 0) for a site/slate.
- `platforms.py`: DK/FD metadata (salary cap, roster slots, CSV headers, upload filename).
- `exporter.py`: write per-site upload CSVs using platform metadata.

This module is designed to be parameterized so we can iterate on weights and caps quickly.
