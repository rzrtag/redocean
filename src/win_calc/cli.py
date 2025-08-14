import argparse
import json
from typing import Dict

from .adj_builder import build_adj_from_build_optimization, load_json, write_json


def main() -> None:
	parser = argparse.ArgumentParser(description="Build adj batters/pitchers tables from build_optimization.json")
	parser.add_argument("--site", required=True, choices=["fanduel", "draftkings"], help="DFS site")
	parser.add_argument("--build-json", required=True, help="Path to atoms_output/atoms/build_optimization.json")
	parser.add_argument("--out-batters", required=True, help="Output path for adj batters JSON")
	parser.add_argument("--out-pitchers", required=True, help="Output path for adj pitchers JSON")
	args = parser.parse_args()

	build_payload: Dict = load_json(args.build_json)
	batters, pitchers = build_adj_from_build_optimization(build_payload, site=args.site)

	# Compute metadata
	site = args.site
	date = build_payload.get("metadata", {}).get("request_data", {}).get("date")
	slate = None
	# Derive slate directory from the build-json path if possible
	path_parts = args.build_json.split("/")
	try:
		if site in ("fanduel", "draftkings"):
			i = path_parts.index(site)
			slate = path_parts[i + 1]
	except Exception:
		slate = None

	out_batters_obj = {"site": site, "date": date, "slate": slate, "batters": batters}
	out_pitchers_obj = {"site": site, "date": date, "slate": slate, "pitchers": pitchers}

	write_json(args.out_batters, out_batters_obj)
	write_json(args.out_pitchers, out_pitchers_obj)


if __name__ == "__main__":
	main()
