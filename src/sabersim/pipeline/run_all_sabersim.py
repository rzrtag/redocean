#!/usr/bin/env python3
"""
SaberSim full pipeline runner

Flow: discover HAR(s) → extract atoms → chunkers → tables.
Supports dynamic sites/contests.
Default HAR discovery root: /mnt/storage_fast/workspaces/red_ocean/dfs_1
(symlink-friendly).
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_step(cmd: list[str], title: str) -> bool:
    print(f"\n🚀 {title}")
    print(f"📄 Running: {' '.join(cmd)}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        if r.returncode == 0:
            if r.stdout.strip():
                print("📋 Output:")
                for line in r.stdout.splitlines():
                    print(f"   {line}")
            return True
        else:
            print("🔴 Error:")
            for line in r.stderr.splitlines():
                print(f"   {line}")
            return False
    except Exception as e:
        print(f"💥 {title} crashed: {e}")
        return False


def process_atoms_directory(atoms_dir: Path, project_src: Path) -> bool:
    """Process a single atoms directory through chunkers, tables, and analysis."""
    print(f"\n📁 Processing atoms directory: {atoms_dir}")

    # 1) Chunkers
    chunk_cmd = [
        "python3", str(Path(__file__).parent / "run_chunkers.py"),
        "--atoms-dir", str(atoms_dir)
    ]
    ok_chunk = run_step(chunk_cmd, "Run Chunkers")
    if not ok_chunk:
        print("⚠️ Chunkers failed or skipped; continuing to tables where "
              "possible")

    # 2) Tables
    tables_cmd = [
        "python3", str(Path(__file__).parent / "run_tables.py"),
        "--atoms-dir", str(atoms_dir)
    ]
    ok_tables = run_step(tables_cmd, "Create Tables")

    # 3) Analysis: write consolidated summary under tables_analysis via
    # dedicated runner
    try:
        analysis_runner = Path(__file__).parent / "run_tbl_analysis.py"
        # Ensure PYTHONPATH includes src so `import sabersim` works reliably
        cmd = [
            "bash", "-lc",
            f"PYTHONPATH={str(project_src)} python3 {str(analysis_runner)} "
            f"--atoms-dir {str(atoms_dir)}"
        ]
        run_step(cmd, "Write Analysis Summary")
    except Exception as e:
        print(f"⚠️ Analysis summary step skipped: {e}")

    return ok_tables  # Return success if tables were created


def main():
    parser = argparse.ArgumentParser(description="Run SaberSim HAR→atoms→chunkers→tables pipeline")
    parser.add_argument("--har", type=str, default=None, help="Specific HAR file to process")
    parser.add_argument("--har-dir", type=str, default=None, help="Directory to scan for HAR files")
    parser.add_argument("--limit", type=int, default=1, help="Max HAR files to process (default: 1)")
    args = parser.parse_args()

    # 1) Atoms
    atoms_cmd = [
        "python3", str(Path(__file__).parent / "run_atoms.py")
    ]
    if args.har:
        atoms_cmd += ["--har", args.har]
    if args.har_dir:
        atoms_cmd += ["--har-dir", args.har_dir]
    if args.limit is not None:
        atoms_cmd += ["--limit", str(args.limit)]
    ok_atoms = run_step(atoms_cmd, "Extract Atoms")
    if not ok_atoms:
        sys.exit(1)

        # Find ALL atoms_output paths (not just the newest)
    base_out = Path("/mnt/storage_fast/workspaces/red_ocean/_data/sabersim_2025")
    candidates: list[Path] = []
    if base_out.exists():
        for site_dir in base_out.iterdir():
            if not site_dir.is_dir():
                continue
            for slate_dir in site_dir.iterdir():
                out_atoms = slate_dir / "atoms_output" / "atoms"
                if out_atoms.exists():
                    candidates.append(out_atoms)

    if not candidates:
        print("⚠️ No atoms directory found after extraction; "
              "skipping chunkers/tables")
        sys.exit(0)

    # Sort by modification time (newest first) for consistent processing order
    candidates.sort(key=lambda p: p.parent.stat().st_mtime
                   if p.parent.exists() else 0, reverse=True)

    print(f"🔍 Found {len(candidates)} atoms directories to process:")
    for i, atoms_dir in enumerate(candidates):
        print(f"  {i+1}. {atoms_dir}")

    # Process each atoms directory
    project_src = Path(__file__).parent.parent.parent
    successes = 0
    total = len(candidates)

    for atoms_dir in candidates:
        if process_atoms_directory(atoms_dir, project_src):
            successes += 1

    print(f"\n📊 Pipeline complete: {successes}/{total} atoms directories "
          f"processed successfully")
    sys.exit(0 if successes > 0 else 1)


if __name__ == "__main__":
    main()
