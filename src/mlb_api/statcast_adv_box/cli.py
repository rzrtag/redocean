#!/usr/bin/env python3
"""
Command Line Interface

Simple CLI for the Statcast collector - outputs one clean file per date.
"""

import argparse
import logging
from datetime import datetime, timedelta

from .core import StatcastCollector

def main():
    """CLI interface for the Statcast collector - clean output per date."""
    parser = argparse.ArgumentParser(description='Collect advanced Statcast data with fantasy points')
    parser.add_argument('--yesterday', action='store_true', help='Collect yesterday\'s games only')
    parser.add_argument('--last-days', type=int, default=30, help='Collect last N days (default: 30)')
    parser.add_argument('--date', type=str, help='Collect specific date (YYYY-MM-DD)')
    parser.add_argument('--start-date', type=str, help='Start date for range (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date for range (YYYY-MM-DD)')
    parser.add_argument('--full-season', type=int, help='Collect full regular season for year (e.g. 2025)')
    parser.add_argument('--current-season', action='store_true', help='Collect full current regular season')
    parser.add_argument('--workers', type=int, default=3, help='Concurrent workers (default: 3)')
    parser.add_argument('--output-dir', type=str, default='_data/statcast', help='Output directory')

    args = parser.parse_args()

    collector = StatcastCollector(args.output_dir)

    logging.info("🚀 Starting Daily Statcast Collection")
    logging.info(f"📂 Output directory: {args.output_dir}")

    results = {}

    if args.yesterday:
        count = collector.collect_yesterday()
        if count is not None:
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            results[yesterday] = count

    elif args.date:
        count = collector.collect_date(args.date, args.workers)
        if count is not None:
            results[args.date] = count

    elif args.start_date and args.end_date:
        results = collector.collect_date_range(args.start_date, args.end_date, args.workers)

    elif args.full_season:
        results = collector.collect_full_regular_season(args.full_season, args.workers)

    elif args.current_season:
        results = collector.collect_full_regular_season(None, args.workers)

    else:
        # Default: collect last N days
        results = collector.collect_last_n_days(args.last_days)

    # Summary
    total_at_bats = sum(results.values())
    logging.info("✅ Collection Complete!")
    logging.info(f"📊 Total at-bats collected: {total_at_bats}")

    for date, count in sorted(results.items()):
        logging.info(f"  {date}: {count} at-bats")
        logging.info(f"    📁 File: advanced_statcast_{date.replace('-', '')}.json")

if __name__ == "__main__":
    main()