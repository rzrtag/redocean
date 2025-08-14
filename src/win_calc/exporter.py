from __future__ import annotations

from pathlib import Path
import csv
from typing import Iterable, Dict, Any

from .platforms import get_platform

BASE_DATA = Path("/mnt/storage_fast/workspaces/red_ocean/_data")
WIN_BASE = BASE_DATA / "win_calc"


def export_csv(site: str, date_mmdd: str, slate: str, rows: Iterable[Dict[str, Any]]) -> Path:
    meta = get_platform(site)
    export_dir = WIN_BASE / "export" / site / f"{date_mmdd}_{slate}"
    export_dir.mkdir(parents=True, exist_ok=True)
    out_path = export_dir / meta.upload_filename

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=meta.csv_headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in meta.csv_headers})

    return out_path
