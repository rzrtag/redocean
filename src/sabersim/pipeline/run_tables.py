#!/usr/bin/env python3
"""
SaberSim tables runner

Generates tables from extracted atoms: contest summary, lineup summary, portfolio/progress summaries, and a master summary.
"""

import sys
import argparse
from pathlib import Path

# Ensure repository src is importable
sys.path.append(str(Path(__file__).parent.parent.parent))

from sabersim.atoms.extractors.tables import main as tables_main


def main():
    parser = argparse.ArgumentParser(description="Create tables from extracted atoms")
    parser.add_argument("--atoms-dir", required=True, help="Path to atoms directory (e.g., .../atoms_output/atoms)")
    parser.add_argument("--out-dir", required=False, help="Output directory for tables (default: atoms_output/tables)")
    args = parser.parse_args()

    atoms_dir = Path(args.atoms_dir)
    if not atoms_dir.exists():
        print(f"❌ Atoms directory not found: {atoms_dir}")
        sys.exit(1)

    out_dir = Path(args.out_dir) if args.out_dir else atoms_dir.parent / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Execute tables module CLI. Let the module compute a Path output_dir to avoid string Path issues.
    sys.argv = [
        "tables",
        str(atoms_dir)
    ]
    tables_main()


if __name__ == "__main__":
    main()
