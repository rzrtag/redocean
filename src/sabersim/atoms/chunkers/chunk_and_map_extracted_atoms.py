import json
import os
from pathlib import Path
import argparse

def extract_players(contest_sim_file, out_dir):
    with open(contest_sim_file) as f:
        data = json.load(f)
    # Try to find players in common locations
    players = []
    for key in ["players", "batters", "pitchers"]:
        if key in data:
            players = data[key]
            break
    if not players:
        # Try nested in metadata.request_data.players
        players = data.get("metadata", {}).get("request_data", {}).get("players", [])
    out_path = Path(out_dir) / "players.json"
    with open(out_path, "w") as f:
        json.dump({"players": players}, f, indent=2)
    return str(out_path), len(players)

def extract_games_and_starters(build_optm_file, out_dir):
    with open(build_optm_file) as f:
        data = json.load(f)
    games = data.get("metadata", {}).get("request_data", {}).get("games", [])
    out_games = Path(out_dir) / "games.json"
    with open(out_games, "w") as f:
        json.dump({"games": games}, f, indent=2)
    # Extract starters
    starters = set()
    for game in games:
        for key in ["home_starter", "away_starter"]:
            name = game.get(key)
            if name:
                starters.add(name.strip())
    out_starters = Path(out_dir) / "starters.json"
    with open(out_starters, "w") as f:
        json.dump(sorted(list(starters)), f, indent=2)
    return str(out_games), str(out_starters), len(games), len(starters)

def create_map_doc(out_dir, players_path, games_path, starters_path):
    map_doc = {
        "players": players_path,
        "games": games_path,
        "starters": starters_path
    }
    out_map = Path(out_dir) / "map_docs.json"
    with open(out_map, "w") as f:
        json.dump(map_doc, f, indent=2)
    return str(out_map)

def main():
    parser = argparse.ArgumentParser(description="Chunk extracted atom files and create a reference map.")
    parser.add_argument('--contest_sim', required=True, help='Path to contest_sim_flag_mid.json or similar')
    parser.add_argument('--build_optm', required=True, help='Path to build_optm.json')
    parser.add_argument('--out_dir', required=True, help='Directory to write chunked files and map_docs')
    args = parser.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    players_path, n_players = extract_players(args.contest_sim, args.out_dir)
    games_path, starters_path, n_games, n_starters = extract_games_and_starters(args.build_optm, args.out_dir)
    map_doc_path = create_map_doc(args.out_dir, players_path, games_path, starters_path)
    print(f"Chunked {n_players} players, {n_games} games, {n_starters} starters.")
    print(f"Reference map written to {map_doc_path}")

if __name__ == "__main__":
    main() 