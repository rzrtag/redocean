import argparse
import csv
import json
from typing import Any, Dict, List


def load_json(path: str) -> Dict[str, Any]:
	with open(path, "r") as f:
		return json.load(f)


def to_rows(objs: List[Dict[str, Any]]) -> List[List[Any]]:
	rows: List[List[Any]] = []
	for p in objs:
		dfs_id = p.get("dfs_id")
		name = p.get("name")
		my_proj = p.get("my_proj")
		if dfs_id is None or name is None or my_proj is None:
			continue
		rows.append([dfs_id, name, my_proj])
	return rows


def main() -> None:
	parser = argparse.ArgumentParser(description="Export adj JSONs to SaberSim upload CSV (DFS ID, Name, My Proj)")
	parser.add_argument("--in-batters", required=True, help="Path to adj_*_batters.json")
	parser.add_argument("--in-pitchers", required=True, help="Path to adj_*_pitchers.json")
	parser.add_argument("--out-csv", required=True, help="Output CSV path")
	args = parser.parse_args()

	batters_obj = load_json(args.in_batters)
	pitchers_obj = load_json(args.in_pitchers)
	batters = batters_obj.get("batters", [])
	pitchers = pitchers_obj.get("pitchers", [])

	rows = to_rows(batters) + to_rows(pitchers)
	# Write CSV with exact header casing required by SaberSim
	with open(args.out_csv, "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(["DFS ID", "Name", "My Proj"])
		writer.writerows(rows)


if __name__ == "__main__":
	main()
