import subprocess
import sys
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Run all chunkers in sequence.")
    parser.add_argument('--contest_sim', nargs='+', required=True, help='Paths to contest_sim_[bucket].json files')
    parser.add_argument('--field_lineups', nargs='+', required=True, help='Paths to field_lineups_[bucket].json files')
    parser.add_argument('--build_optm', required=True, help='Path to build_optm.json')
    parser.add_argument('--players', required=True, help='Path to players.json (for stack chunker)')
    parser.add_argument('--out_dir', required=True, help='Directory to write chunked files and map_docs')
    parser.add_argument('--stacks_output', required=False, help='Path to output stacks_ownership.json (optional, defaults to out_dir/stacks_ownership.json)')
    args = parser.parse_args()

    # Run data_chunker
    print("\n=== Running data_chunker ===")
    data_chunker_cmd = [
        sys.executable, '-m', 'src.star_cannon.core.chunkers.data_chunker',
        '--contest_sim', *args.contest_sim,
        '--field_lineups', *args.field_lineups,
        '--build_optm', args.build_optm,
        '--out_dir', args.out_dir
    ]
    subprocess.run(data_chunker_cmd, check=True)

    # Run stack_ownership_chunker
    print("\n=== Running stack_ownership_chunker ===")
    stacks_output = args.stacks_output or str(Path(args.out_dir) / 'stacks_ownership.json')
    stack_chunker_cmd = [
        sys.executable, '-m', 'src.star_cannon.core.chunkers.stack_ownership_chunker',
        '--field_lineups', *args.field_lineups,
        '--players', args.players,
        '--output', stacks_output
    ]
    subprocess.run(stack_chunker_cmd, check=True)

    print("\nAll chunkers completed successfully.")

if __name__ == "__main__":
    main() 