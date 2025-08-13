#!/usr/bin/env python3
"""
Run HAR Extraction and Table Creation

Simple script to extract data from SaberSim HAR files and create tables.
Uses the working archived logic with proper site detection and slate detection.
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import re
from urllib.parse import urlparse, parse_qs

# Add the current directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from extractor import MLBAtomExtractor


def detect_slate_from_har(har_path: Path) -> str:
    """Detect slate from HAR file content."""
    try:
        with open(har_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
            entries = har_data.get('log', {}).get('entries', [])

            # Check first 100 entries for slate indicators
            for entry in entries[:100]:
                req = entry.get("request", {})
                url = (req.get("url") or "").lower()
                text = ""

                if req.get("method") == "POST":
                    post = req.get("postData", {})
                    if post.get("mimeType") == "application/json":
                        text = (post.get("text") or "").lower()

                blob = (url + "\n" + text).lower()

                # Check for slate indicators
                if "night_slate" in blob or "late-night" in blob or re.search(r"\\bnight\\b", blob):
                    return "night_slate"
                elif "main_slate" in blob or "main-slate" in blob:
                    return "main_slate"
                elif "early_slate" in blob or "early-slate" in blob:
                    return "early_slate"
                elif "afternoon_slate" in blob or "afternoon-slate" in blob:
                    return "afternoon_slate"
                elif "late_slate" in blob or "late-slate" in blob:
                    return "late_slate"

                # Check response content for slate indicators
                response = entry.get("response", {})
                if response.get("status") == 200:
                    content = response.get("content", {})
                    response_text = content.get("text", "").lower()
                    if "night_slate" in response_text or "late-night" in response_text:
                        return "night_slate"
                    elif "main_slate" in response_text or "main-slate" in response_text:
                        return "main_slate"
                    elif "early_slate" in response_text or "early-slate" in response_text:
                        return "early_slate"
                    elif "afternoon_slate" in response_text or "afternoon-slate" in response_text:
                        return "afternoon_slate"
                    elif "late_slate" in response_text or "late-slate" in response_text:
                        return "late_slate"
    except Exception:
        pass

    return "main_slate"  # Default to main_slate


def detect_site_from_har(har_path: Path) -> str:
    """Very simple detector, defaults to draftkings if unknown."""
    p = str(har_path).lower()
    if "/fd/" in p or "fanduel" in p:
        return "fanduel"
    if "/dk/" in p or "draftkings" in p:
        return "draftkings"

    # Try to sniff entries quickly (stream-first approach)
    try:
        with open(har_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
            entries = har_data.get('log', {}).get('entries', [])

            # Check first 100 entries for better coverage
            for entry in entries[:100]:
                req = entry.get("request", {})
                url = (req.get("url") or "").lower()

                # Check URL for site indicators
                if "fanduel" in url or "site=fd" in url:
                    return "fanduel"
                if "draftkings" in url or "site=dk" in url:
                    return "draftkings"

                # Check for site in URL parameters
                if "app.sabersim.com" in url:
                    parsed = urlparse(url)
                    query = parse_qs(parsed.query)
                    site_param = query.get('site', [None])[0]
                    if site_param == 'fd':
                        return "fanduel"
                    elif site_param == 'dk':
                        return "draftkings"

                # Check response content for site indicators
                response = entry.get("response", {})
                if response.get("status") == 200:
                    content = response.get("content", {})
                    response_text = content.get("text", "").lower()
                    if "fanduel" in response_text or '"site":"fd"' in response_text:
                        return "fanduel"
                    if "draftkings" in response_text or '"site":"dk"' in response_text:
                        return "draftkings"
    except Exception:
        pass

    return "draftkings"


def detect_site_from_entry(entry: dict) -> str | None:
    """Detect site for a single HAR entry via query params, body, or URL."""
    try:
        req = entry.get('request', {})
        url = (req.get('url') or '').lower()

        # Query params
        parsed = urlparse(url)
        q = parse_qs(parsed.query)
        site_q = (q.get('site') or [None])[0]
        if site_q:
            if site_q.lower() in ('dk', 'draftkings'):
                return 'draftkings'
            if site_q.lower() in ('fd', 'fanduel'):
                return 'fanduel'

        # Body
        if req.get('method') == 'POST':
            post = req.get('postData', {})
            if post.get('mimeType') == 'application/json':
                try:
                    body = json.loads(post.get('text', '{}'))
                    body_site = (body.get('site') or '').lower()
                    if body_site in ('dk', 'draftkings'):
                        return 'draftkings'
                    if body_site in ('fd', 'fanduel'):
                        return 'fanduel'
                except Exception:
                    pass

        # URL hints
        if "fanduel" in url or "site=fd" in url:
            return 'fanduel'
        if "draftkings" in url or "site=dk" in url:
            return 'draftkings'

    except Exception:
        return None
    return None


def detect_contest_bucket(entry: dict) -> str | None:
    """Extract a stable contest bucket identifier if present."""
    try:
        req = entry.get('request', {})
        # POST json
        if req.get('method') == 'POST':
            post = req.get('postData', {})
            if post.get('mimeType') == 'application/json':
                try:
                    body = json.loads(post.get('text', '{}'))
                    # Common keys observed
                    bucket = body.get("contest_bucket") or body.get("contestType") or body.get("contest_bucket_name")
                    if bucket:
                        # Normalize typical pattern 'uuid_flagship_mid_entry' → 'flagship_mid_entry'
                        b = str(bucket)
                        parts = b.split("_")
                        if len(parts) > 2:
                            return "_".join(parts[1:])
                        return b
                except Exception:
                    pass
    except Exception:
        return None
    return None


def detect_slate_from_entries(entries: list, site: str, bucket: str = None) -> str:
    """Detect slate from HAR entries."""
    slate_hints = {}

    for entry in entries:
        try:
            req = entry.get("request", {})
            url = (req.get("url") or "").lower()
            text = ""
            if req.get("method") == "POST":
                post = req.get("postData", {})
                if post.get("mimeType") == "application/json":
                    text = (post.get("text") or "").lower()

            blob = (url + "\n" + text).lower()

            # Prefer explicit night indicators; avoid matching 'latest'
            if ("night_slate" in blob) or ("late-night" in blob) or re.search(r"\bnight\b", blob):
                slate_hints[(site, bucket)] = "night_slate"
            elif "main_slate" in blob or "main-slate" in blob:
                slate_hints[(site, bucket)] = "main_slate"
            # Else leave unset; default later is main_slate
        except Exception:
            pass

    return slate_hints.get((site, bucket), "main_slate")


def main():
    """Main function to run HAR extraction."""

    # Check if HAR file path is provided
    if len(sys.argv) < 2:
        print("Usage: python run_har_extraction.py <path_to_har_file> [output_directory]")
        print("\nExample:")
        print("  python run_har_extraction.py ../../dfs/app.sabersim.com")
        print("  python run_har_extraction.py ../../dfs/app.sabersim.com ./output")
        sys.exit(1)

    har_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    # Validate HAR file
    har_path = Path(har_file)
    if not har_path.exists():
        print(f"❌ Error: HAR file not found: {har_file}")
        sys.exit(1)

    print(f"🚀 Starting HAR extraction...")
    print(f"📁 HAR file: {har_path}")

    # Load HAR entries for analysis
    try:
        with open(har_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        entries = har_data.get('log', {}).get('entries', [])
        print(f"📊 Found {len(entries)} entries in HAR file")
    except Exception as e:
        print(f"❌ Error loading HAR file: {e}")
        sys.exit(1)

    # Detect site
    site = detect_site_from_har(har_path)
    print(f"🏠 Detected site: {site}")

    # Determine output directory
    if output_dir is None:
        # Auto-generate output directory based on date, site, and detected slate
        today = datetime.now()
        date_str = today.strftime("%m%d")

        # Detect slate from HAR entries
        slate = detect_slate_from_har(har_path)
        slate_suffix = f"_{slate}"  # Always append slate

        output_dir = f"_data/sabersim_2025/{site}/{date_str}{slate_suffix}"

    print(f"📂 Output directory: {output_dir}")
    print(f"🎯 Detected slate: {slate}")

    # Group entries by site and contest bucket
    from collections import defaultdict
    groups = defaultdict(lambda: defaultdict(list))

    site_counts = {"draftkings": 0, "fanduel": 0, None: 0}
    bucket_counts = {}

    for entry in entries:
        # Only process successful responses
        status = entry.get("response", {}).get("status", 0)
        if status != 200:
            continue

        site_entry = detect_site_from_entry(entry)
        site_counts[site_entry if site_entry in ("draftkings", "fanduel") else None] += 1

        # Site override: if user passed a specific site, filter to it
        if site_entry and site_entry != site:
            continue

        # If we still don't know site, fall back to global detection
        if not site_entry:
            site_entry = site

        bucket = detect_contest_bucket(entry)
        groups[site_entry][bucket].append(entry)

        # Count buckets
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1

    print(f"📊 Site detection counts: {site_counts}")
    print(f"📊 Unique buckets: {sum(1 for _ in bucket_counts.keys())}")

    total_atoms = 0
    group_count = 0

    for site_entry, bucket_map in groups.items():
        for bucket, ents in bucket_map.items():
            group_count += 1

                                                            # Use the already-detected slate for data organization
            slate_suffix = f"_{slate}"  # Always append slate

            # Compute output dir - flat structure with slate
            base = Path("_data") / "sabersim_2025" / site_entry / f"{date_str}{slate_suffix}"
            out_dir = base / "atoms_output"
            out_dir.mkdir(parents=True, exist_ok=True)

            print(f"🔍 Processing group -> site={site_entry} bucket={bucket} slate={slate} entries={len(ents)} out={out_dir}")

            # Build a minimal temporary HAR with only grouped entries
            temp_har = {"log": {"version": "1.2", "creator": {"name": "red_ocean", "version": "1"}}}
            temp_har["log"]["entries"] = ents

            # Save temporary HAR
            import tempfile
            with tempfile.NamedTemporaryFile("w", suffix=".har", delete=False) as tf:
                json.dump(temp_har, tf, indent=2)
                tf.flush()
                temp_path = Path(tf.name)

            try:
                # Extract atoms
                extractor = MLBAtomExtractor(str(out_dir))
                extracted = extractor.extract_atoms_from_har(str(temp_path))
                group_atoms = sum(len(v) for v in extracted.values())
                total_atoms += group_atoms
                print(f"  ✅ Extracted {group_atoms} atoms")

            except Exception as e:
                print(f"  ❌ Extraction failed: {e}")
            finally:
                # Clean up temp file
                temp_path.unlink()

    print(f"\n✅ Extraction completed!")
    print(f"📊 Total atoms extracted: {total_atoms} across {group_count} group(s)")
    print(f"📁 Base output: _data/sabersim_2025/<site>/{date_str}_<slate>/atoms_output")

    # Check what was created
    output_path = Path(output_dir)
    if output_path.exists():
        print(f"\n📋 Generated files:")
        for item in output_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(output_path)
                print(f"  • {rel_path}")


if __name__ == '__main__':
    main()
