#!/usr/bin/env python3
"""
SaberSim chunkers runner

Creates minimal chunked artifacts (players/games/starters) and a map doc from extracted atoms.
Looks in the atoms_output path created by the atoms step.
"""

import sys
import argparse
from pathlib import Path

# Ensure repository src is importable
sys.path.append(str(Path(__file__).parent.parent.parent))

from sabersim.atoms.chunkers.chunk_and_map_extracted_atoms import main as chunk_main


def find_required_atoms(atoms_dir: Path) -> tuple[Path | None, Path | None]:
    """Heuristically locate needed atom files for chunking."""
    if not atoms_dir.exists():
        return None, None

    # Prefer build_optimization and contest_simulations
    build_optm = None
    contest_sim = None

    for f in atoms_dir.glob("*.json"):
        name = f.name
        if name.startswith("build_optimization") and build_optm is None:
            build_optm = f
        if name.startswith("contest_simulations") and contest_sim is None:
            contest_sim = f

    return contest_sim, build_optm


def main():
    parser = argparse.ArgumentParser(description="Run chunkers on extracted atoms")
    parser.add_argument("--atoms-dir", required=True, help="Path to atoms directory (e.g., .../atoms_output/atoms)")
    parser.add_argument("--out-dir", required=False, help="Output directory for chunked artifacts (default: alongside atoms)")
    args = parser.parse_args()

    atoms_dir = Path(args.atoms_dir)
    if not atoms_dir.exists():
        print(f"❌ Atoms directory not found: {atoms_dir}")
        sys.exit(1)

    # Default tables path directly under atoms_output
    out_dir = Path(args.out_dir) if args.out_dir else atoms_dir.parent / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)

    contest_sim, build_optm = find_required_atoms(atoms_dir)
    if not contest_sim or not build_optm:
        print("⚠️ Could not locate required atoms (contest_simulations, build_optimization). Skipping chunkers.")
        print(f"   Atoms dir: {atoms_dir}")
        sys.exit(0)

    # Execute chunker module CLI
    sys.argv = [
        "chunk_and_map_extracted_atoms",
        "--contest_sim", str(contest_sim),
        "--build_optm", str(build_optm),
        "--out_dir", str(out_dir)
    ]
    chunk_main()


if __name__ == "__main__":
    main()
