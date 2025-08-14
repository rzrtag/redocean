#!/usr/bin/env python3
"""
Generate a markdown analysis report of rolling adjustments applied to SaberSim projections.

Finds the latest slate for FanDuel and DraftKings, loads adj JSONs, computes
per-player deltas (adjusted - base), and writes a human-friendly report with
context and top movers.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import argparse
from typing import Any, Dict, List, Tuple

DATA_ROOT = Path("/mnt/storage_fast/workspaces/red_ocean/_data/sabersim_2025")
DEFAULT_OUT_ROOT = Path("/mnt/storage_fast/workspaces/red_ocean/docs")
ROLLING_ROOT = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/rolling_windows/data")
ROSTERS_PATH = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/active_rosters/data/active_rosters.json")

# Mirror adjustment parameters used in rolling_adjuster
WEIGHTS = {"50": 0.5, "100": 0.3, "250": 0.2}
AGGRESSIVENESS_K = 0.15
MAX_ABS_TILT = 0.20
LEAGUE_XWOBA_HITTER = 0.320
LEAGUE_XWOBA_PITCHER_ALLOWED = 0.320


def find_latest_slate(site: str) -> Path | None:
    site_dir = DATA_ROOT / site
    if not site_dir.exists():
        return None
    latest: Path | None = None
    for child in site_dir.iterdir():
        if child.is_dir():
            if latest is None or child.stat().st_mtime > latest.stat().st_mtime:
                latest = child
    return latest


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


@dataclass
class Record:
    site: str
    slate: str
    role: str  # batter|pitcher
    name: str
    dfs_id: str
    team: str
    position: str
    price: float | int | None
    ownership: float | None
    is_home: bool | None
    is_starter: bool | None
    confirmed: bool | None
    rolling_signal: float | None
    base_proj: float | None
    adj_proj: float | None

    @property
    def delta(self) -> float | None:
        if self.base_proj is None or self.adj_proj is None:
            return None
        return float(self.adj_proj) - float(self.base_proj)

    @property
    def pct_change(self) -> float | None:
        if self.base_proj is None or self.adj_proj is None or not self.base_proj:
            return None
        return (float(self.adj_proj) / float(self.base_proj)) - 1.0


def collect_records(site: str, latest: Path, role: str) -> List[Record]:
    site_prefix = "fd" if site == "fanduel" else "dk"
    fname = f"adj_{site_prefix}_{'batters' if role == 'batter' else 'pitchers'}.json"
    path = latest / "win_calc" / fname
    if not path.exists():
        return []
    payload = load_json(path)
    items = payload.get("batters" if role == "batter" else "pitchers", [])
    base_key = f"{site_prefix}Projection"

    out: List[Record] = []
    for p in items:
        out.append(
            Record(
                site=site,
                slate=payload.get("slate") or latest.name,
                role=role,
                name=p.get("name"),
                dfs_id=p.get("dfs_id"),
                team=p.get("team"),
                position=p.get("position"),
                price=p.get("price"),
                ownership=p.get("ownership"),
                is_home=p.get("is_home"),
                is_starter=p.get("is_starter"),
                confirmed=p.get("confirmed"),
                rolling_signal=p.get("rolling_signal"),
                base_proj=p.get(base_key),
                adj_proj=p.get("my_proj"),
            )
        )
    return out


def top_movers(recs: List[Record], n: int = 10) -> List[Record]:
    recs = [r for r in recs if r.delta is not None]
    recs.sort(key=lambda r: abs(r.delta or 0.0), reverse=True)
    return recs[:n]


def fmt_pct(x: float | None) -> str:
    if x is None:
        return "—"
    return f"{x*100:.1f}%"


def fmt_float(x: float | None) -> str:
    if x is None:
        return "—"
    return f"{x:.2f}"


def fmt_short_name(name: str | None) -> str:
    """Return first-initial.last in lowercase, e.g., 'p.alonso'."""
    if not name:
        return "?"
    parts = [p for p in name.strip().split() if p]
    if not parts:
        return "?"
    first = parts[0]
    last = parts[-1]
    first_initial = (first[0] if first else "?")
    return f"{first_initial}.{last}".lower()


def _normalize_name(name: str) -> str:
    import re
    name = name.lower().strip()
    name = re.sub(r"[\.'`’]", "", name)
    name = re.sub(r"\s+jr$", "", name)
    name = re.sub(r"\s+sr$", "", name)
    name = re.sub(r"\s+ii$|\s+iii$|\s+iv$", "", name)
    name = re.sub(r"\s+", " ", name)
    return name


def _load_active_rosters() -> Dict[str, Any]:
    try:
        with open(ROSTERS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _build_name_index(rosters: Dict[str, Any]) -> Dict[Tuple[str, str], str]:
    index: Dict[Tuple[str, str], str] = {}
    for team_abbr, team_data in rosters.get("rosters", {}).items():
        for p in team_data.get("roster", []):
            full = p.get("fullName") or ""
            pid = p.get("id")
            if not full or pid is None:
                continue
            index[(_normalize_name(full), team_abbr.upper())] = str(pid)
    return index


def _load_rolling_file(player_id: str, role: str) -> Dict[str, Any] | None:
    path = ROLLING_ROOT / ("hitters" if role == "batter" else "pitchers") / f"{player_id}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _latest_xwoba(rolling: Dict[str, Any], window: str) -> float | None:
    series = (rolling.get("rolling_windows", {}).get(window, {}) or {}).get("series", [])
    if not series:
        return None
    val = series[0].get("xwoba")
    return float(val) if isinstance(val, (int, float)) else None


def compute_breakdown(row: Record) -> Dict[str, Any] | None:
    rosters = _load_active_rosters()
    index = _build_name_index(rosters)
    mlb_id = index.get((_normalize_name(row.name or ""), (row.team or "").upper()))
    if not mlb_id:
        return None
    rolling = _load_rolling_file(mlb_id, row.role)
    if not rolling:
        return None
    # Extract latest xwOBA per window
    x50 = _latest_xwoba(rolling, "50")
    x100 = _latest_xwoba(rolling, "100")
    x250 = _latest_xwoba(rolling, "250")
    league = LEAGUE_XWOBA_HITTER if row.role == "batter" else LEAGUE_XWOBA_PITCHER_ALLOWED
    def dev(x: float | None) -> float | None:
        if x is None or not league:
            return None
        d = (x - league) / league
        if row.role == "pitcher":
            d = -d
        return d
    d50, d100, d250 = dev(x50), dev(x100), dev(x250)
    # Weighted signal
    acc = 0.0
    total_w = 0.0
    for key, w in WEIGHTS.items():
        val = {"50": d50, "100": d100, "250": d250}.get(key)
        if val is None:
            continue
        acc += w * val
        total_w += w
    signal = None if total_w == 0.0 else acc / total_w
    if signal is None:
        return None
    k = AGGRESSIVENESS_K
    cap = MAX_ABS_TILT
    factor = k * signal
    if factor > cap:
        factor = cap
    elif factor < -cap:
        factor = -cap
    base = row.base_proj
    adj = None if base is None else base * (1.0 + factor)
    return {
        "x50": x50, "x100": x100, "x250": x250,
        "d50": d50, "d100": d100, "d250": d250,
        "weights": WEIGHTS,
        "league": league,
        "signal": signal,
        "k": k,
        "cap": cap,
        "factor": factor,
        "base": base,
        "adj": adj,
    }


def section_for(site: str, role: str, movers: List[Record]) -> str:
    title = f"{site.title()} — {'Batters' if role=='batter' else 'Pitchers'} (Top Adjustments)"
    lines = [f"### {title}", "", "- **count**: {}".format(len(movers)), ""]
    # Table header
    lines.append("| Name | Team | Price | Own% | Base | Adj | Δ | Δ% | Signal |")
    # Alignment: text left, numbers right
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in movers:
        own = f"{(r.ownership or 0):.1f}" if r.ownership is not None else "—"
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                fmt_short_name(r.name),
                r.team or "?",
                r.price if r.price is not None else "—",
                own,
                fmt_float(r.base_proj),
                fmt_float(r.adj_proj),
                fmt_float(r.delta),
                fmt_pct(r.pct_change),
                fmt_float(r.rolling_signal),
            )
        )
    lines.append("")
    return "\n".join(lines)


def details_section_for(site: str, role: str, movers: List[Record]) -> str:
    title = f"{site.title()} — {'Batters' if role=='batter' else 'Pitchers'} (Detailed Breakdown)"
    lines: List[str] = [f"#### {title}", ""]
    # Explanation header for the first details section only will be added by caller
    for r in movers:
        b = compute_breakdown(r)
        name = fmt_short_name(r.name)
        if not b:
            lines.append(f"- {name} ({r.team or '?'}) — no rolling window data available")
            continue
        # Compose a compact multi-line bullet
        lines.append(f"- {name} ({r.team or '?'})")
        lines.append(f"  - base: {fmt_float(b['base'])}, signal: {fmt_float(b['signal'])}")
        # Windows line: show available values
        w_parts: List[str] = []
        for key in ("50", "100", "250"):
            x = b.get(f"x{key}")
            d = b.get(f"d{key}")
            if x is None:
                continue
            w_parts.append(f"{key}={x:.3f} ({fmt_pct(d)})")
        if w_parts:
            lines.append(f"  - windows: {'; '.join(w_parts)} | weights: 50={WEIGHTS['50']}, 100={WEIGHTS['100']}, 250={WEIGHTS['250']}")
        lines.append(f"  - params: k={AGGRESSIVENESS_K}, cap=±{int(MAX_ABS_TILT*100)}%, factor={fmt_float(b['factor'])} ({fmt_pct(b['factor'])} of base)")
        lines.append(f"  - adjusted: {fmt_float(b['adj'])}")
    lines.append("")
    return "\n".join(lines)


def _build_summary_content() -> List[str]:
    content: List[str] = []
    content.append("## Win Calc Adjustments Report")
    content.append("")
    content.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    content.append("")
    content.append("This report summarizes adjustments applied to SaberSim projections using rolling windows signals (xwOBA 50/100/250).")
    content.append("")

    for site in ("fanduel", "draftkings"):
        latest = find_latest_slate(site)
        if latest is None:
            content.append(f"### {site.title()} — No data found")
            continue
        bat = collect_records(site, latest, "batter")
        pit = collect_records(site, latest, "pitcher")
        # Include any players labeled as pitchers by position even if role tagged otherwise
        def is_pitcher_pos(pos: str | None) -> bool:
            if not pos:
                return False
            up = pos.upper()
            return up in ("P", "SP", "RP") or ("PITCH" in up)
        extra_pit = [r for r in bat if is_pitcher_pos(r.position)]
        if extra_pit:
            seen = {(r.name, r.team) for r in pit}
            for r in extra_pit:
                key = (r.name, r.team)
                if key not in seen:
                    pit.append(r)
                    seen.add(key)

        content.append(section_for(site, "batter", top_movers(bat, 10)))
        content.append(section_for(site, "pitcher", top_movers(pit, 10)))
    return content


def _build_calc_content() -> List[str]:
    content: List[str] = []
    content.append("## Win Calc Adjustment Calculation Details")
    content.append("")
    content.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    content.append("")
    content.append("Adjustment method: For each player, we pull the latest xwOBA in 50/100/250 PA windows, compute deviation from league average (pitchers inverted), take a weighted average (0.5/0.3/0.2) to form a signal, then apply k×signal to the base projection with a ±20% cap.")
    content.append("")

    for site in ("fanduel", "draftkings"):
        latest = find_latest_slate(site)
        if latest is None:
            content.append(f"### {site.title()} — No data found")
            continue
        bat = collect_records(site, latest, "batter")
        pit = collect_records(site, latest, "pitcher")
        content.append(details_section_for(site, "batter", top_movers(bat, 10)))
        content.append(details_section_for(site, "pitcher", top_movers(pit, 10)))
    return content


def generate_reports(out_root: Path | None = None, out_file: Path | None = None, split: bool = True) -> Tuple[Path, Path | None]:
    if out_root is None:
        out_root = DEFAULT_OUT_ROOT
    short_date = datetime.now().strftime("%m%d")

    if out_file is not None:
        summary_path = out_file
        calc_path = out_file.with_name(out_file.stem + "_calc.md") if split else None
    else:
        summary_path = out_root / f"{short_date}_adj.md"
        calc_path = (out_root / f"{short_date}_adj_calc.md") if split else None

    # Write summary
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        f.write("\n".join(_build_summary_content()))

    # Write calc details if requested
    if split and calc_path is not None:
        calc_path.parent.mkdir(parents=True, exist_ok=True)
        with open(calc_path, "w") as f:
            f.write("\n".join(_build_calc_content()))

    return summary_path, calc_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate win_calc adjustment report (markdown)")
    parser.add_argument("--out-dir", dest="out_dir", default=str(DEFAULT_OUT_ROOT), help="Output directory for reports")
    parser.add_argument("--out-file", dest="out_file", default=None, help="Optional explicit summary file path; calc file will use *_calc.md next to it if --split is on")
    parser.add_argument("--no-split", dest="split", action="store_false", help="Write only the summary report (no separate calc report)")
    args = parser.parse_args()

    summary_path, calc_path = generate_reports(Path(args.out_dir), Path(args.out_file) if args.out_file else None, split=bool(args.split))
    print(f"✅ Wrote report: {summary_path}")
    if calc_path is not None:
        print(f"✅ Wrote calc report: {calc_path}")


if __name__ == "__main__":
    main()
