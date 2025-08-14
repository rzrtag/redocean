#!/usr/bin/env python3
"""
SaberSim Master Pipeline Runner

Handles frequent SaberSim updates throughout the day for breaking analysis.
Typically runs up to 10 times per day depending on live roster updates.

Usage:
    python run_ss.py                    # Process latest HAR files
    python run_ss.py --har /path/to/har # Process specific HAR file
    python run_ss.py --force            # Force reprocess all data
    python run_ss.py --status           # Check pipeline status
"""

import sys
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime


def run_step(cmd: list[str], title: str, timeout: int = 1800) -> bool:
    """Run a pipeline step with monitoring."""
    print(f"\n🚀 {title}")
    print(f"📄 Running: {' '.join(cmd)}")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {title} completed in {execution_time:.1f}s")
            if result.stdout.strip():
                print("📋 Output:")
                for line in result.stdout.strip().split('\n'):
                    print(f"   {line}")
            return True
        else:
            print(f"❌ {title} failed after {execution_time:.1f}s")
            if result.stderr.strip():
                print("🔴 Error:")
                for line in result.stderr.strip().split('\n'):
                    print(f"   {line}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {title} timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"💥 {title} crashed: {e}")
        return False


def check_pipeline_status():
    """Check status of SaberSim pipeline components."""
    print("🔍 SaberSim Pipeline Status Check")
    print("=" * 50)
    
    # Check for recent HAR files
    har_root = Path("/mnt/storage_fast/workspaces/red_ocean/dfs_1")
    if har_root.exists():
        har_files = list(har_root.glob("*.har"))
        if har_files:
            latest_har = max(har_files, key=lambda p: p.stat().st_mtime)
            har_age = time.time() - latest_har.stat().st_mtime
            print(f"📁 Latest HAR: {latest_har.name}")
            print(f"⏰ Age: {har_age/3600:.1f} hours")
        else:
            print("⚠️ No HAR files found")
    
    # Check for recent data
    data_root = Path("/mnt/storage_fast/workspaces/red_ocean/_data/sabersim_2025")
    if data_root.exists():
        sites = ["draftkings", "fanduel"]
        for site in sites:
            site_dir = data_root / site
            if site_dir.exists():
                latest_slate = None
                for slate_dir in site_dir.iterdir():
                    if slate_dir.is_dir():
                        if latest_slate is None or slate_dir.stat().st_mtime > latest_slate.stat().st_mtime:
                            latest_slate = slate_dir
                
                if latest_slate:
                    data_age = time.time() - latest_slate.stat().st_mtime
                    print(f"📊 {site.title()}: {latest_slate.name} ({data_age/3600:.1f}h old)")
                else:
                    print(f"📊 {site.title()}: No data")
            else:
                print(f"📊 {site.title()}: No directory")


def run_sabersim_pipeline(har_file: str = None, force: bool = False):
    """Run the complete SaberSim pipeline."""
    start_time = time.time()
    
    print("🚀 SaberSim Master Pipeline")
    print("=" * 50)
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔄 Mode: {'FORCED UPDATE' if force else 'SMART INCREMENTAL'}")
    
    # Build SaberSim pipeline command
    ss_cmd = ["python3", "src/sabersim/pipeline/run_all_sabersim.py"]
    
    if har_file:
        ss_cmd.extend(["--har", har_file])
    if force:
        # Note: SaberSim doesn't have a --force flag yet, but we could add one
        print("⚠️ Force mode not yet implemented for SaberSim")
    
    # Run SaberSim pipeline
    success = run_step(ss_cmd, "SaberSim Pipeline")
    
    # Summary
    total_time = time.time() - start_time
    print(f"\n📊 Pipeline Summary")
    print("=" * 50)
    print(f"⏱️ Total Time: {total_time:.1f}s")
    
    if success:
        print("✅ SaberSim pipeline completed successfully!")
        return True
    else:
        print("❌ SaberSim pipeline failed")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='SaberSim Master Pipeline')
    parser.add_argument('--har', type=str, help='Specific HAR file to process')
    parser.add_argument('--force', action='store_true', help='Force reprocess all data')
    parser.add_argument('--status', action='store_true', help='Check pipeline status')
    
    args = parser.parse_args()
    
    if args.status:
        check_pipeline_status()
        sys.exit(0)
    else:
        success = run_sabersim_pipeline(
            har_file=args.har,
            force=args.force
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
