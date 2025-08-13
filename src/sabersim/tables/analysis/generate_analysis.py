#!/usr/bin/env python3
from __future__ import annotations

"""
Generate basic analysis tables from atoms_output tables.

Inputs (atoms_output/tables):
  - lineup_summary.json
  - contest_summary.json (optional)

Outputs (tables_analysis):
  - stack_analysis.json
  - lineup_stats.json
"""

import json
from pathlib import Path
from typing import Dict, Any, List


def _load_json(path: Path):
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _percentiles(values: List[float], cuts: List[float]) -> Dict[str, float]:
    if not values:
        return {str(int(c*100)): 0.0 for c in cuts}
    vs = sorted(values)
    n = len(vs)
    out: Dict[str, float] = {}
    for c in cuts:
        if n == 1:
            out[str(int(c*100))] = float(vs[0])
            continue
        idx = min(n-1, max(0, int(round(c*(n-1)))))
        out[str(int(c*100))] = float(vs[idx])
    return out


def generate_stack_analysis(lineups: List[Dict[str, Any]]) -> Dict[str, Any]:
    stack_types_counts: Dict[str, int] = {}
    stack_size_counts: Dict[str, int] = {}
    for rec in lineups:
        st = str(rec.get('stack_types') or rec.get('stack') or '').strip()
        if not st:
            continue
        stack_types_counts[st] = stack_types_counts.get(st, 0) + 1
        # accumulate per size token
        for token in st.split('|'):
            token = token.strip()
            if not token:
                continue
            stack_size_counts[token] = stack_size_counts.get(token, 0) + 1
    # Top 20 by count
    top_stack_types = sorted(stack_types_counts.items(), key=lambda x: (-x[1], x[0]))[:20]
    top_sizes = sorted(stack_size_counts.items(), key=lambda x: (-x[1], x[0]))
    return {
        'total_lineups': len(lineups),
        'stack_types_top': [{'stack': k, 'count': v} for k, v in top_stack_types],
        'stack_size_counts': [{'size': k, 'count': v} for k, v in top_sizes],
    }


def generate_lineup_stats(lineups: List[Dict[str, Any]]) -> Dict[str, Any]:
    projs = [float(rec.get('projection') or 0.0) for rec in lineups]
    salaries = [int(rec.get('salary') or 0) for rec in lineups]
    stats = {
        'count': len(lineups),
        'projection': {
            'min': float(min(projs)) if projs else 0.0,
            'max': float(max(projs)) if projs else 0.0,
            'avg': float(sum(projs)/len(projs)) if projs else 0.0,
            'pct': _percentiles(projs, [0.25, 0.5, 0.75, 0.85, 0.95, 0.99])
        },
        'salary': {
            'min': int(min(salaries)) if salaries else 0,
            'max': int(max(salaries)) if salaries else 0,
            'avg': float(sum(salaries)/len(salaries)) if salaries else 0.0,
            'pct': _percentiles([float(s) for s in salaries], [0.25, 0.5, 0.75, 0.85, 0.95, 0.99])
        }
    }
    # Top 100 lineups by projection
    top = sorted(lineups, key=lambda r: float(r.get('projection') or 0.0), reverse=True)[:100]
    stats['top_lineups'] = [
        {
            'lineup_id': rec.get('lineup_id'),
            'projection': float(rec.get('projection') or 0.0),
            'salary': int(rec.get('salary') or 0),
            'stack_types': rec.get('stack_types') or rec.get('stack')
        }
        for rec in top
    ]
    return stats


def write_analysis(tables_dir: Path, analysis_dir: Path) -> Dict[str, Path]:
    analysis_dir.mkdir(parents=True, exist_ok=True)
    lineups = _load_json(tables_dir / 'lineup_summary.json') or []
    out_paths: Dict[str, Path] = {}
    stack = generate_stack_analysis(lineups)
    p = analysis_dir / 'stack_analysis.json'
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(stack, f, indent=2)
    out_paths['stack_analysis'] = p

    stats = generate_lineup_stats(lineups)
    p2 = analysis_dir / 'lineup_stats.json'
    with open(p2, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    out_paths['lineup_stats'] = p2
    return out_paths


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate SaberSim analysis tables')
    parser.add_argument('--tables-dir', required=True, help='Path to atoms_output/tables')
    parser.add_argument('--analysis-dir', required=True, help='Path to write tables_analysis outputs')
    args = parser.parse_args()
    tables_dir = Path(args.tables_dir)
    analysis_dir = Path(args.analysis_dir)
    write_analysis(tables_dir, analysis_dir)
    print(f"✅ Analysis written to: {analysis_dir}")


if __name__ == '__main__':
    main()
