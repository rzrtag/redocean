from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PlatformMeta:
    site: str
    upload_filename: str
    salary_cap: int | None
    roster_slots: List[str]
    csv_headers: List[str]


PLATFORMS: Dict[str, PlatformMeta] = {
    "draftkings": PlatformMeta(
        site="draftkings",
        upload_filename="dk_upload.csv",
        salary_cap=50000,
        roster_slots=["P", "P", "C", "1B", "2B", "3B", "SS", "OF", "OF", "OF"],
        csv_headers=[
            "site", "slate", "player_id", "player_name", "team", "pos", "salary", "projection_adj"
        ],
    ),
    "fanduel": PlatformMeta(
        site="fanduel",
        upload_filename="fd_upload.csv",
        salary_cap=35000,
        roster_slots=["P", "C/1B", "2B", "3B", "SS", "OF", "OF", "OF", "UTIL"],
        csv_headers=[
            "site", "slate", "player_id", "player_name", "team", "pos", "salary", "projection_adj"
        ],
    ),
}


def get_platform(site: str) -> PlatformMeta:
    s = site.lower()
    if s not in PLATFORMS:
        raise ValueError(f"Unknown platform site: {site}")
    return PLATFORMS[s]
