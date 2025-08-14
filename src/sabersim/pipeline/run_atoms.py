#!/usr/bin/env python3
"""
SaberSim HAR → Atoms runner

Discovers HAR files and extracts MLB atoms for all detected sites and contest buckets.
Defaults to reading from the workspace symlink at `/mnt/storage_fast/workspaces/red_ocean/dfs_1`.
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Ensure repository src is importable
sys.path.append(str(Path(__file__).parent.parent.parent))

from sabersim.atoms.extractors.extract import (
    detect_site_from_har,
    detect_slate_from_har,
)


DEFAULT_HAR_ROOT = Path("/mnt/storage_fast/workspaces/red_ocean/dfs_1")
DEFAULT_OUTPUT_BASE = Path("/mnt/storage_fast/workspaces/red_ocean/_data/sabersim_2025")


def find_har_files(har_path: Path) -> list[Path]:
    """Find candidate HAR files under a path (file or directory)."""
    if har_path.is_file():
        return [har_path]

    if har_path.is_dir():
        candidates: list[Path] = []
        for child in har_path.iterdir():
            if child.is_file():
                # Accept typical names or any JSON/HAR-like files
                name = child.name.lower()
                if name.endswith(".har") or name.endswith(".json") or "app.sabersim" in name:
                    candidates.append(child)
        # Sort newest first
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates

    return []


def compute_output_dir(har_file: Path) -> Path:
    """Compute dynamic output directory site/date_slate under DEFAULT_OUTPUT_BASE."""
    # Prefer date from HAR mtime
    dt = datetime.fromtimestamp(har_file.stat().st_mtime)
    date_str = dt.strftime("%m%d")

    site = detect_site_from_har(har_file)
    slate = detect_slate_from_har(har_file)
    slate_suffix = f"_{slate}"

    return DEFAULT_OUTPUT_BASE / site / f"{date_str}{slate_suffix}" / "atoms_output"


def extract_from_har(har_file: Path, output_dir: Path) -> bool:
    """Run extraction from a single HAR file into the specified output directory."""
    print(f"🚀 Extracting atoms from HAR: {har_file}")
    print(f"📂 Output: {output_dir}")

    try:
        # Use our new extraction script with proper site detection
        import subprocess
        cmd = [
            "python3",
            str(Path(__file__).parent.parent / "atoms" / "extractors" / "extract.py"),
            str(har_file)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)

        if result.returncode == 0:
            print("✅ Extraction completed successfully")
            return True
        else:
            print(f"❌ Extraction failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Extraction failed for {har_file}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run HAR → atoms extraction for SaberSim")
    parser.add_argument("--har", dest="har", type=str, default=None, help="Path to a HAR file to process")
    parser.add_argument("--har-dir", dest="har_dir", type=str, default=None, help="Directory to search for HAR files")
    parser.add_argument("--limit", dest="limit", type=int, default=1, help="Max number of HAR files to process (default: 1)")
    args = parser.parse_args()

    # Resolve discovery root
    if args.har:
        root = Path(args.har)
    elif args.har_dir:
        root = Path(args.har_dir)
    else:
        root = DEFAULT_HAR_ROOT

    print(f"🔎 Discovering HAR files under: {root}")
    har_files = find_har_files(root)
    if not har_files:
        print("❌ No HAR files found")
        sys.exit(1)

    processed = 0
    successes = 0
    for har_file in har_files:
        out_dir = compute_output_dir(har_file)
        ok = extract_from_har(har_file, out_dir)
        successes += int(ok)
        processed += 1
        if processed >= args.limit:
            break

    print(f"\n📊 Extraction complete: {successes}/{processed} succeeded")
    sys.exit(0 if successes > 0 else 1)


if __name__ == "__main__":
    main()
