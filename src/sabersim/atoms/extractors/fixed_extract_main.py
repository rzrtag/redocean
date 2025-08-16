#!/usr/bin/env python3
"""
Fixed SaberSim HAR Extraction - Main Logic

This fixes the grouping issue by processing all entries for a site together,
rather than splitting by contest buckets which was causing endpoint loss.
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import re
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

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


def main():
    """Main function to run HAR extraction with FIXED grouping logic."""
    
    # Check if HAR file path is provided
    if len(sys.argv) < 2:
        print("Usage: python fixed_extract_main.py <path_to_har_file> [output_directory]")
        print("\nExample:")
        print("  python fixed_extract_main.py ../../dfs/app.sabersim.com")
        print("  python fixed_extract_main.py ../../dfs/app.sabersim.com ./output")
        sys.exit(1)

    har_file = sys.argv[1]
    output_dir = None

    # Handle additional arguments
    if len(sys.argv) > 2:
        if sys.argv[2].startswith('--'):
            # Skip flag arguments
            pass
        else:
            output_dir = sys.argv[2]

    # Validate HAR file
    har_path = Path(har_file)
    if not har_path.exists():
        print(f"❌ Error: HAR file not found: {har_file}")
        sys.exit(1)

    print(f"🚀 Starting FIXED HAR extraction...")
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

    # Detect site and slate
    site = detect_site_from_har(har_path)
    print(f"🏠 Detected site: {site}")

    # Detect slate from HAR entries
    slate = detect_slate_from_har(har_path)
    print(f"🎯 Detected slate: {slate}")

    # Determine output directory
    if output_dir is None:
        # Auto-generate output directory based on date, site, and detected slate
        today = datetime.now()
        date_str = today.strftime("%m%d")
        slate_suffix = f"_{slate}"  # Always append slate
        output_dir = f"_data/sabersim_2025/{site}/{date_str}{slate_suffix}"

    print(f"📂 Output directory: {output_dir}")

    # FIXED: Group entries by site only (not by site + bucket)
    from collections import defaultdict
    site_groups = defaultdict(list)

    site_counts = {"draftkings": 0, "fanduel": 0, None: 0}
    endpoint_counts = defaultdict(int)

    for entry in entries:
        # Only process successful responses
        status = entry.get("response", {}).get("status", 0)
        if status != 200:
            continue

        site_entry = detect_site_from_entry(entry)
        site_counts[site_entry if site_entry in ("draftkings", "fanduel") else None] += 1

        # If we can't detect site from entry, skip it (don't fall back to global)
        if not site_entry:
            continue

        # FIXED: Group by site only, not by site + bucket
        site_groups[site_entry].append(entry)

        # Count endpoint types for analysis
        url = entry.get("request", {}).get("url", "")
        if "contest_simulations" in url:
            endpoint_counts["contest_simulations"] += 1
        elif "contest_information" in url:
            endpoint_counts["contest_information"] += 1
        elif "field_lineups" in url:
            endpoint_counts["field_lineups"] += 1
        elif "build_optimization" in url:
            endpoint_counts["build_optimization"] += 1
        elif "portfolio_optimization" in url:
            endpoint_counts["portfolio_optimization"] += 1
        elif "progress_tracking" in url:
            endpoint_counts["progress_tracking"] += 1
        elif "lineup_data" in url:
            endpoint_counts["lineup_data"] += 1

    print(f"📊 Site detection counts: {site_counts}")
    print(f"📊 Endpoint counts: {dict(endpoint_counts)}")

    total_atoms = 0
    site_count = 0

    # FIXED: Process each site as a single group
    for site_entry, entries in site_groups.items():
        site_count += 1

        # Use the already-detected slate for data organization
        slate_suffix = f"_{slate}"  # Always append slate

        # Compute output dir - flat structure with slate
        base = Path("_data") / "sabersim_2025" / site_entry / f"{date_str}{slate_suffix}"
        out_dir = base / "atoms_output"
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"🔍 Processing site -> site={site_entry} slate={slate} entries={len(entries)} out={out_dir}")

        # Build a minimal temporary HAR with all entries for this site
        temp_har = {"log": {"version": "1.2", "creator": {"name": "red_ocean", "version": "1"}}}
        temp_har["log"]["entries"] = entries

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
            site_atoms = sum(len(v) for v in extracted.values())
            total_atoms += site_atoms
            print(f"  ✅ Extracted {site_atoms} atoms")

        except Exception as e:
            print(f"  ❌ Extraction failed: {e}")
        finally:
            # Clean up temp file
            temp_path.unlink()

    print(f"\n✅ FIXED Extraction completed!")
    print(f"📊 Total atoms extracted: {total_atoms} across {site_count} site(s)")
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
