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
    scoring_multipliers: Dict[str, float]
    strategic_focus: str


PLATFORMS: Dict[str, PlatformMeta] = {
    "draftkings": PlatformMeta(
        site="draftkings",
        upload_filename="dk_upload.csv",
        salary_cap=50000,
        roster_slots=["P", "P", "C", "1B", "2B", "3B", "SS", "OF", "OF", "OF"],
        csv_headers=[
            "site", "slate", "player_id", "player_name", "team", "pos", "salary", "projection_adj"
        ],
        scoring_multipliers={
            "hr": 14.0,      # Massive power value
            "rbi": 2.0,      # Balanced
            "r": 2.0,        # Balanced
            "sb": 5.0,       # Good value
            "k": 2.25,       # Pitcher efficiency
            "ip": 2.25,      # Pitcher efficiency
            "w": 4.0,        # Win bonus
            "er": -2.0       # ERA penalty
        },
        strategic_focus="Power hitters get massive boost (HR=14). Individual upside over team correlation."
    ),
    "fanduel": PlatformMeta(
        site="fanduel",
        upload_filename="fd_upload.csv",
        salary_cap=35000,
        roster_slots=["P", "C/1B", "2B", "3B", "SS", "OF", "OF", "OF", "UTIL"],
        csv_headers=[
            "site", "slate", "player_id", "player_name", "team", "pos", "salary", "projection_adj"
        ],
        scoring_multipliers={
            "hr": 6.0,       # Moderate power value
            "rbi": 3.5,      # Higher than DK
            "r": 3.2,        # Higher than DK
            "sb": 6.0,       # Good value
            "k": 4.0,        # Pitcher volume
            "ip": 3.0,       # Pitcher volume
            "w": 6.0,        # Win bonus
            "er": -3.0       # ERA penalty
        },
        strategic_focus="Stack correlation critical (R/RBI > HR). Team production over individual power."
    ),
}


def get_platform(site: str) -> PlatformMeta:
    s = site.lower()
    if s not in PLATFORMS:
        raise ValueError(f"Unknown platform site: {site}")
    return PLATFORMS[s]
