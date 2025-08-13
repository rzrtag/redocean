#!/usr/bin/env python3
"""
SaberSim tables analysis runner (run_tbl_analysis)

Writes consolidated analysis artifacts to:
  _data/sabersim_2025/<site>/<mmdd>_<slate>/tables_analysis

Currently produces:
  - contest_site_summary.json (counts, paths)

Extensible to add more analyses (top inclusion, stacks, ownership) later.
"""

import sys
import argparse
from pathlib import Path
import json

# Ensure repository src is importable
sys.path.append(str(Path(__file__).parent.parent.parent))

from sabersim.tables.manifest import SaberSimLayout
from sabersim.tables.summary.compute_contest_summary import write_summary
from sabersim.tables.analysis.generate_analysis import write_analysis
from sabersim.tables.ownership.compute_field_ownership import compute_ownership_from_atom as compute_field_own_from_atom
from sabersim.tables.ownership.compute_pid_ownership import compute_pid_ownership as compute_pid_ownership_from_atom
from sabersim.tables.stacks.compute_stack_ownership import compute_stack_ownership_from_atom


def infer_from_atoms_dir(atoms_dir: Path) -> tuple[Path, str, str]:
    # atoms_dir: /.../_data/sabersim_2025/<site>/<date_slate>/atoms_output/atoms
    site = atoms_dir.parents[2].name
    date_slate = atoms_dir.parents[1].name
    base = atoms_dir.parents[3]
    return base, site, date_slate


def main():
    parser = argparse.ArgumentParser(description="Run SaberSim tables analysis")
    parser.add_argument("--site", type=str, help="Site (fanduel|draftkings)")
    parser.add_argument("--date-slate", type=str, help="Date and slate, e.g., 0812_main_slate")
    parser.add_argument("--atoms-dir", type=str, help="Path to atoms dir (…/atoms_output/atoms)")
    args = parser.parse_args()

    if args.atoms_dir:
        base, site, date_slate = infer_from_atoms_dir(Path(args.atoms_dir))
    else:
        if not args.site or not args.date_slate:
            print("❌ Provide either --atoms-dir or both --site and --date-slate")
            sys.exit(1)
        # Default base to _data/sabersim_2025 if not atoms-dir
        base = Path("/mnt/storage_fast/workspaces/red_ocean/_data/sabersim_2025")
        site = args.site
        date_slate = args.date_slate

    layout = SaberSimLayout(base=base, site=site, date_slate=date_slate)
    out = write_summary(layout)
    # Also generate additional analysis tables from atoms_output/tables
    write_analysis(layout.tables_dir, layout.analysis_dir)

    # Try to derive a contest bucket from atoms names (best effort)
    bucket = None
    for f in layout.atoms_dir.glob('field_lineups_*.json'):
        name = f.stem
        if name.startswith('field_lineups_'):
            bucket = name.replace('field_lineups_', '')
            break

    # Ownership tables per bucket (if available)
    if bucket:
        atom_file = layout.atoms_dir / f"field_lineups_{bucket}.json"
        if atom_file.exists():
            # Build PID meta by scanning sabersim atoms for richer metadata
            def build_pid_meta_from_sabersim() -> dict[str, dict]:
                import json as _json
                meta: dict[str, dict] = {}
                def scan_file(p: Path):
                    try:
                        d = _json.loads(p.read_text(encoding='utf-8'))
                    except Exception:
                        return
                    stack = [d]
                    def richness(m: dict) -> int:
                        score = 0
                        if any(isinstance(m.get(k), str) and m.get(k) for k in ('name','displayName','fullName','playerName')):
                            score += 2
                        if any(isinstance(m.get(k), str) and m.get(k) for k in ('team','teamAbbr','team_abbr','teamAbbreviation','mlbTeamAbbrev')):
                            score += 1
                        posv = m.get('position') or m.get('pos') or m.get('pos_str')
                        if isinstance(posv, (str, dict, list)):
                            score += 1
                        return score
                    while stack:
                        x = stack.pop()
                        if isinstance(x, dict):
                            pid = x.get('pid') or x.get('playerId') or x.get('id')
                            if isinstance(pid, (str, int)):
                                pid_str = str(pid)
                                new_meta = dict(x)
                                old_meta = meta.get(pid_str, {})
                                if old_meta:
                                    if richness(new_meta) >= richness(old_meta):
                                        merged = dict(old_meta)
                                        merged.update(new_meta)
                                        meta[pid_str] = merged
                                else:
                                    meta[pid_str] = new_meta
                            for v in x.values():
                                if isinstance(v, (dict, list)):
                                    stack.append(v)
                        elif isinstance(x, list):
                            for v in x:
                                if isinstance(v, (dict, list)):
                                    stack.append(v)
                # Candidate atoms for metadata
                for name in (
                    'portfolio_optimization_latest.json',
                    'build_optimization.json',
                    'lineup_data.json',
                    f'contest_simulations_{bucket}.json',
                    f'field_lineups_{bucket}.json',
                ):
                    p = layout.atoms_dir / name
                    if p.exists():
                        scan_file(p)
                return meta

            pid_meta = build_pid_meta_from_sabersim()

            # Note: field_own (name-based) is redundant with PID ownership; omitted to reduce clutter

            # PID ownership split batters/pitchers
            pid_bat = compute_pid_ownership_from_atom(atom_file, 'batter', pid_meta)
            pid_pit = compute_pid_ownership_from_atom(atom_file, 'pitcher', pid_meta)
            bat_path = layout.analysis_dir / f"pid_own_batters_{bucket}.json"
            pit_path = layout.analysis_dir / f"pid_own_pitchers_{bucket}.json"
            with open(bat_path, 'w', encoding='utf-8') as f:
                json.dump({'bucket': bucket, **pid_bat}, f, indent=2)
            with open(pit_path, 'w', encoding='utf-8') as f:
                json.dump({'bucket': bucket, **pid_pit}, f, indent=2)

            # Team stack ownership (e.g., MIA 4-man %, 3-man %)
            # Derive site and date components
            site = layout.site
            date_mmdd = layout.date_slate[:4]
            slate = layout.date_slate.split('_', 1)[1]
            stacks = compute_stack_ownership_from_atom(atom_file, site, date_mmdd, slate)
            stack_path = layout.analysis_dir / f"stack_own_{bucket}.json"
            with open(stack_path, 'w', encoding='utf-8') as f:
                json.dump({'bucket': bucket, **stacks}, f, indent=2)

    print(f"✅ Wrote analysis summary: {out}")


if __name__ == "__main__":
    main()
