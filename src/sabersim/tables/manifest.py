#!/usr/bin/env python3
from __future__ import annotations

"""
Flat API wrapper for table layout manifest utilities.
Inlined logic so callers can import from sabersim.tables.manifest and we can
retire tables/utils.
"""

from pathlib import Path
from dataclasses import dataclass
import json
from typing import Dict


@dataclass
class SaberSimLayout:
    base: Path  # e.g., /mnt/.../_data/sabersim_2025
    site: str   # 'fanduel' | 'draftkings'
    date_slate: str  # '0812_main_slate'

    @property
    def atoms_output(self) -> Path:
        return self.base / self.site / self.date_slate / "atoms_output"

    @property
    def atoms_dir(self) -> Path:
        return self.atoms_output / "atoms"

    @property
    def tables_dir(self) -> Path:
        return self.atoms_output / "tables"

    @property
    def analysis_dir(self) -> Path:
        return self.base / self.site / self.date_slate / "tables_analysis"


def load_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

__all__ = [
    'SaberSimLayout',
    'load_json',
]
