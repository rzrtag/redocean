#!/usr/bin/env python3
"""
Create Tables from Extracted Atoms

Generate useful tables from the extracted SaberSim atoms data.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def load_atom_data(atom_file: Path) -> Dict[str, Any]:
    """Load atom data from JSON file."""
    try:
        with open(atom_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {atom_file}: {e}")
        return {}

def create_contest_summary_table(contest_atom: Dict[str, Any], output_dir: Path) -> None:
    """Create contest summary table."""
    if not contest_atom or 'response_data' not in contest_atom:
        return

    contests = contest_atom['response_data'].get('contests', [])
    if not contests:
        return

    # Extract contest data
    contest_data = []
    for contest in contests:
        contest_data.append({
            'contest_id': contest.get('contest_id'),
            'name': contest.get('name'),
            'contest_bucket': contest.get('contest_bucket'),
            'entry_fee': contest.get('entry_fee'),
            'entries': contest.get('entries'),
            'max_per_user': contest.get('max_per_user'),
            'prize_pool': contest.get('prize_pool'),
            'pct_cash': contest.get('pct_cash'),
            'game_type': contest.get('game_type'),
            'is_qualifier': contest.get('is_qualifier'),
            'is_final': contest.get('is_final')
        })

        # Save as JSON for easy consumption
    json_file = output_dir / 'contest_summary.json'
    with open(json_file, 'w') as f:
        json.dump(contest_data, f, indent=2)
    print(f"✅ Created contest summary table: {json_file}")
    print(f"   📊 {len(contest_data)} contests")

def create_lineup_summary_table(lineup_atom: Dict[str, Any], output_dir: Path) -> None:
    """Create lineup summary table."""
    if not lineup_atom or 'response_data' not in lineup_atom:
        return

    lineups = lineup_atom['response_data'].get('lineups', [])
    if not lineups:
        return

    # Extract lineup data
    lineup_data = []
    for lineup in lineups:
        lineup_data.append({
            'lineup_id': lineup.get('id'),
            'salary': lineup.get('salary'),
            'projection': lineup.get('projection'),
            'stack': lineup.get('stack'),
            'stack_types': '|'.join(lineup.get('stack_types', [])),
            'sim_optimals': lineup.get('sim_optimals'),
            'pct_25': lineup.get('percentiles', {}).get('25'),
            'pct_50': lineup.get('percentiles', {}).get('50'),
            'pct_75': lineup.get('percentiles', {}).get('75'),
            'pct_85': lineup.get('percentiles', {}).get('85'),
            'pct_95': lineup.get('percentiles', {}).get('95'),
            'pct_99': lineup.get('percentiles', {}).get('99')
        })

        # Save as JSON for easy consumption
    json_file = output_dir / 'lineup_summary.json'
    with open(json_file, 'w') as f:
        json.dump(lineup_data, f, indent=2)
    print(f"✅ Created lineup summary table: {json_file}")
    print(f"   📊 {len(lineup_data)} lineups")

def create_portfolio_summary_table(portfolio_atom: Dict[str, Any], output_dir: Path) -> None:
    """Create portfolio optimization summary table."""
    if not portfolio_atom or 'response_data' not in portfolio_atom:
        return

    # Extract portfolio data (structure may vary)
    portfolio_data = portfolio_atom['response_data']

    # Save raw portfolio data as JSON
    json_file = output_dir / 'portfolio_data.json'
    with open(json_file, 'w') as f:
        json.dump(portfolio_data, f, indent=2)
    print(f"✅ Saved portfolio data: {json_file}")

    # Try to extract any structured data
    if isinstance(portfolio_data, dict):
        summary = {
            'extraction_timestamp': datetime.now().isoformat(),
            'data_keys': list(portfolio_data.keys()),
            'data_size': len(json.dumps(portfolio_data))
        }

        summary_file = output_dir / 'portfolio_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"   📄 Summary: {summary_file}")

def create_progress_summary_table(progress_atom: Dict[str, Any], output_dir: Path) -> None:
    """Create progress tracking summary table."""
    if not progress_atom or 'response_data' not in progress_atom:
        return

    # Save raw progress data as JSON
    progress_data = progress_atom['response_data']
    json_file = output_dir / 'progress_data.json'
    with open(json_file, 'w') as f:
        json.dump(progress_data, f, indent=2)
    print(f"✅ Saved progress data: {json_file}")

    # Try to extract any structured data
    if isinstance(progress_data, dict):
        summary = {
            'extraction_timestamp': datetime.now().isoformat(),
            'data_keys': list(progress_data.keys()),
            'data_size': len(json.dumps(progress_data))
        }

        summary_file = output_dir / 'progress_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"   📄 Summary: {summary_file}")

def create_master_summary_table(atoms_dir: Path, output_dir: Path) -> None:
    """Create a master summary of all extracted data."""
    summary = {
        'extraction_timestamp': datetime.now().isoformat(),
        'atoms_directory': str(atoms_dir),
        'tables_directory': str(output_dir),
        'available_atoms': [],
        'summary_stats': {}
    }

    # Scan for available atoms
    for atom_file in atoms_dir.glob('*.json'):
        atom_data = load_atom_data(atom_file)
        if atom_data:
            endpoint_type = atom_data.get('endpoint_type', 'unknown')
            summary['available_atoms'].append({
                'file': atom_file.name,
                'endpoint_type': endpoint_type,
                'url': atom_data.get('url', ''),
                'data_size': atom_file.stat().st_size
            })

    # Save master summary
    summary_file = output_dir / 'master_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Created master summary: {summary_file}")

def main():
    """Main function to create tables from extracted atoms."""
    if len(sys.argv) < 2:
        print("Usage: python tables.py <atoms_directory> [output_directory]")
        print("\nExample:")
        print("  python tables.py _data/sabersim_2025/fanduel/0812/atoms")
        sys.exit(1)

    atoms_dir = Path(sys.argv[1])
    output_dir = sys.argv[2] if len(sys.argv) > 2 else atoms_dir.parent / 'tables'

    if not atoms_dir.exists():
        print(f"❌ Error: Atoms directory not found: {atoms_dir}")
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🚀 Creating tables from extracted atoms...")
    print(f"📁 Atoms directory: {atoms_dir}")
    print(f"📂 Output directory: {output_dir}")

    # Load all available atoms
    atoms = {}
    for atom_file in atoms_dir.glob('*.json'):
        atom_data = load_atom_data(atom_file)
        if atom_data:
            endpoint_type = atom_data.get('endpoint_type', 'unknown')
            atoms[endpoint_type] = atom_data

    print(f"\n📊 Found {len(atoms)} atom types:")
    for endpoint_type in atoms.keys():
        print(f"  • {endpoint_type}")

    # Create tables for each atom type
    if 'contest_information' in atoms:
        print(f"\n🏆 Processing contest information...")
        create_contest_summary_table(atoms['contest_information'], output_dir)

    if 'lineup_data' in atoms:
        print(f"\n📋 Processing lineup data...")
        create_lineup_summary_table(atoms['lineup_data'], output_dir)

    if 'portfolio_optimization' in atoms:
        print(f"\n💼 Processing portfolio optimization...")
        create_portfolio_summary_table(atoms['portfolio_optimization'], output_dir)

    if 'progress_tracking' in atoms:
        print(f"\n📈 Processing progress tracking...")
        create_progress_summary_table(atoms['progress_tracking'], output_dir)

    # Create master summary
    print(f"\n📊 Creating master summary...")
    create_master_summary_table(atoms_dir, output_dir)

    print(f"\n✅ Table creation completed!")
    print(f"📁 Tables saved to: {output_dir}")

    # List created files
    if output_dir.exists():
        print(f"\n📋 Generated tables:")
        for item in output_dir.glob("*"):
            if item.is_file():
                print(f"  • {item.name}")


if __name__ == '__main__':
    main()
