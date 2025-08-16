#!/usr/bin/env python3
"""
Enhanced Rolling Windows Adjuster - Hybrid Approach

Implements multiple signal blending with moderate aggressiveness increase
to achieve ~5 point max adjustments while remaining statistically sound.
"""

import json
import os
import re
import requests
from unidecode import unidecode
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Enhanced parameters for hybrid approach
WEIGHTS = {"50": 0.5, "100": 0.3, "250": 0.2}

# Moderate aggressiveness increase (2.5x from original 0.22)
AGGRESSIVENESS_K = 0.55
MAX_ABS_TILT = 0.40  # Allow 40% adjustments (up from 20%)

LEAGUE_XWOBA_HITTER = 0.320
LEAGUE_XWOBA_PITCHER_ALLOWED = 0.320

# League baselines for enhanced metrics
LEAGUE_HARD_HIT_RATE = 0.38
LEAGUE_MEAN_EV = 88.5
LEAGUE_BARREL_RATE = 0.08
LEAGUE_FANTASY_EFFICIENCY = 2.5  # points per at-bat (batters)
LEAGUE_PITCHER_FANTASY_EFFICIENCY = 20.0  # points per game (pitchers) - adjusted based on actual data

# Enhanced signal blending weights
SIGNAL_BLEND = {
    "xwoba": 0.4,              # Reduce xwOBA weight
    "contact_quality": 0.25,    # Exit velocity trends
    "power": 0.2,              # Barrel rate, hard hit rate
    "fantasy_efficiency": 0.15  # Points per at-bat
}

ROLLING_ROOT = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/rolling_windows/data"
STATCAST_ROOT = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/statcast_adv_box/data"
ROSTERS_PATH = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/active_rosters/data/active_rosters.json"


def _normalize_name(name: str) -> str:
    """Normalize player names for matching."""
    name = unidecode(name or "").lower().strip()
    name = re.sub(r"[\.'`']", "", name)
    name = re.sub(r"\s+jr$", "", name)
    name = re.sub(r"\s+sr$", "", name)
    name = re.sub(r"\s+ii$|\s+iii$|\s+iv$", "", name)
    name = re.sub(r"\s+", " ", name)
    return name


def _load_active_rosters() -> Dict[str, Any]:
    """Load active rosters for player matching."""
    try:
        with open(ROSTERS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _build_name_index(rosters: Dict[str, Any]) -> Dict[Tuple[str, str], str]:
    """Build name-to-MLB-ID index."""
    index: Dict[Tuple[str, str], str] = {}
    for team_abbr, team_data in rosters.get("rosters", {}).items():
        for p in team_data.get("roster", []):
            full = p.get("fullName_ascii") or p.get("fullName") or ""
            pid = p.get("id")
            if not full or pid is None:
                continue
            index[(_normalize_name(full), team_abbr.upper())] = str(pid)
    return index


def _load_rolling_file(player_id: str, role: str) -> Optional[Dict[str, Any]]:
    """Load rolling windows data for a player."""
    path = os.path.join(ROLLING_ROOT, "hitters" if role == "batter" else "pitchers", f"{player_id}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _load_statcast_player_data(player_id: str, role: str) -> Optional[Dict[str, Any]]:
    """Load statcast data for a player."""
    path = os.path.join(STATCAST_ROOT, "batter" if role == "batter" else "pitcher", f"{player_id}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _latest_xwoba(rolling: Dict[str, Any], window: str) -> Optional[float]:
    """Get latest xwOBA for a window."""
    series = (rolling.get("rolling_windows", {}).get(window, {}) or {}).get("series", [])
    if not series:
        return None
    val = series[0].get("xwoba")
    return float(val) if isinstance(val, (int, float)) else None


def _compute_contact_quality_signal(rolling: Dict[str, Any], window: str) -> Optional[float]:
    """Compute contact quality signal from exit velocity trends."""
    # Use histogram data for exit velocity
    histogram_data = rolling.get("histogram_data", {})
    ev_histogram = histogram_data.get("exit_velocity", [])

    if not ev_histogram:
        return None

    # Calculate weighted average exit velocity
    total_events = 0
    weighted_ev = 0

    for bin_data in ev_histogram:
        ev_value = float(bin_data.get("histogram_value", 0))
        bbe_raw = bin_data.get("bbe")
        event_count = int(bbe_raw) if bbe_raw is not None else 0

        if event_count > 0:
            weighted_ev += ev_value * event_count
            total_events += event_count

    if total_events == 0:
        return None

    avg_ev = weighted_ev / total_events

    # Compare to league average
    league_deviation = (avg_ev - LEAGUE_MEAN_EV) / LEAGUE_MEAN_EV
    return league_deviation


def _compute_power_signal(rolling: Dict[str, Any], window: str) -> Optional[float]:
    """Compute power signal from barrel rate and hard hit rate."""
    histogram_data = rolling.get("histogram_data", {})

    # Calculate barrel rate (hard hit + optimal launch angle)
    ev_histogram = histogram_data.get("exit_velocity", [])
    la_histogram = histogram_data.get("launch_angle", [])

    if not ev_histogram or not la_histogram:
        return None

    # Count hard hit balls (≥95 mph)
    hard_hit_count = 0
    total_bbe = 0

    for bin_data in ev_histogram:
        ev_value = float(bin_data.get("histogram_value", 0))
        bbe_raw = bin_data.get("bbe")
        bbe_count = int(bbe_raw) if bbe_raw is not None else 0

        if ev_value >= 95:
            hard_hit_count += bbe_count
        total_bbe += bbe_count

    if total_bbe == 0:
        return None

    hard_hit_rate = hard_hit_count / total_bbe

    # Compare to league average
    hard_hit_deviation = (hard_hit_rate - LEAGUE_HARD_HIT_RATE) / LEAGUE_HARD_HIT_RATE

    return hard_hit_deviation


def _compute_fantasy_efficiency_signal(statcast_data: Optional[Dict[str, Any]], role: str) -> Optional[float]:
    """Compute fantasy efficiency signal from statcast data."""
    if not statcast_data:
        return None

    games = statcast_data.get("games", {})
    if not games:
        return None

    if role == "pitcher":
        # For pitchers: calculate per-game fantasy efficiency
        total_game_points = 0
        total_games = 0

        for game_data in games.values():
            # Each at-bat entry contains the TOTAL game fantasy points, not per-at-bat
            # So we just take the first at-bat's points as the game total
            pitcher_at_bats = game_data.get("pitcher_at_bats", [])
            if pitcher_at_bats:
                first_at_bat = pitcher_at_bats[0]
                game_dk_points = float(first_at_bat.get("pitcher_dk_points", 0))
                game_fd_points = float(first_at_bat.get("pitcher_fd_points", 0))

                # Average points per game
                avg_game_points = (game_dk_points + game_fd_points) / 2
                total_game_points += avg_game_points
                total_games += 1

        if total_games == 0:
            return None

        fantasy_efficiency = total_game_points / total_games

        # Compare to league average for pitchers
        efficiency_deviation = (fantasy_efficiency - LEAGUE_PITCHER_FANTASY_EFFICIENCY) / LEAGUE_PITCHER_FANTASY_EFFICIENCY

        return efficiency_deviation

    else:
        # For batters: calculate per-at-bat fantasy efficiency (existing logic)
        total_points = 0
        total_at_bats = 0

        for game_data in games.values():
            # Sum fantasy points from all at-bats in this game
            for at_bat in game_data.get("batter_at_bats", []):
                dk_points = float(at_bat.get("batter_dk_points", 0))
                fd_points = float(at_bat.get("batter_fd_points", 0))
                # Use average of DK and FD points
                avg_points = (dk_points + fd_points) / 2
                total_points += avg_points
                total_at_bats += 1

        if total_at_bats == 0:
            return None

        fantasy_efficiency = total_points / total_at_bats

        # Compare to league average for batters
        efficiency_deviation = (fantasy_efficiency - LEAGUE_FANTASY_EFFICIENCY) / LEAGUE_FANTASY_EFFICIENCY

        return efficiency_deviation


def _compute_enhanced_signal(rolling: Dict[str, Any], statcast_data: Optional[Dict[str, Any]],
                           role: str, weights: Dict[str, float], league_h: float, league_p: float) -> Optional[float]:
    """Compute enhanced signal blending multiple metrics."""

    # 1. xwOBA component (existing)
    xwoba_acc = 0.0
    xwoba_wsum = 0.0
    for w_key, w in weights.items():
        x = _latest_xwoba(rolling, w_key)
        if x is None:
            continue
        league = league_h if role == "batter" else league_p
        d = (x - league) / league if league else 0.0
        if role == "pitcher":
            d = -d
        xwoba_acc += w * d
        xwoba_wsum += w

    xwoba_component = None if xwoba_wsum == 0.0 else xwoba_acc / xwoba_wsum

    # 2. Contact quality component (new)
    contact_acc = 0.0
    contact_wsum = 0.0
    for w_key, w in weights.items():
        contact_signal = _compute_contact_quality_signal(rolling, w_key)
        if contact_signal is None:
            continue
        if role == "pitcher":
            contact_signal = -contact_signal  # Invert for pitchers
        contact_acc += w * contact_signal
        contact_wsum += w

    contact_component = None if contact_wsum == 0.0 else contact_acc / contact_wsum

    # 3. Power component (new)
    power_acc = 0.0
    power_wsum = 0.0
    for w_key, w in weights.items():
        power_signal = _compute_power_signal(rolling, w_key)
        if power_signal is None:
            continue
        if role == "pitcher":
            power_signal = -power_signal  # Invert for pitchers
        power_acc += w * power_signal
        power_wsum += w

    power_component = None if power_wsum == 0.0 else power_acc / power_wsum

    # 4. Fantasy efficiency component (new)
    fantasy_component = _compute_fantasy_efficiency_signal(statcast_data, role)
    if role == "pitcher" and fantasy_component is not None:
        fantasy_component = -fantasy_component  # Invert for pitchers

    # Blend all available components
    parts = []
    weights_blend = []

    if xwoba_component is not None:
        parts.append(xwoba_component)
        weights_blend.append(SIGNAL_BLEND["xwoba"])

    if contact_component is not None:
        parts.append(contact_component)
        weights_blend.append(SIGNAL_BLEND["contact_quality"])

    if power_component is not None:
        parts.append(power_component)
        weights_blend.append(SIGNAL_BLEND["power"])

    if fantasy_component is not None:
        parts.append(fantasy_component)
        weights_blend.append(SIGNAL_BLEND["fantasy_efficiency"])

    if not parts:
        return None

    # Weighted average of all components
    blend_sum = 0.0
    blend_wsum = 0.0
    for val, w in zip(parts, weights_blend):
        blend_sum += val * w
        blend_wsum += w

    return blend_sum / blend_wsum if blend_wsum > 0 else None


def _apply_enhanced_adjustment(base_proj: Optional[float], signal: float, k: float, cap: float) -> Optional[float]:
    """Apply enhanced adjustment with new parameters."""
    if base_proj is None:
        return None

    # Capped multiplier
    factor = k * signal
    if factor > cap:
        factor = cap
    elif factor < -cap:
        factor = -cap

    return base_proj * (1.0 + factor)


def adjust_records_enhanced(
    site: str,
    batters: List[Dict[str, Any]],
    pitchers: List[Dict[str, Any]],
    w50: Optional[float] = None,
    w100: Optional[float] = None,
    w250: Optional[float] = None,
    k: Optional[float] = None,
    cap: Optional[float] = None,
    league_xwoba_hitter: Optional[float] = None,
    league_xwoba_pitcher: Optional[float] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Enhanced adjustment function with hybrid signal blending.

    Adds fields per record:
    - enhanced_signal: multi-metric signal used
    - my_proj_adj: adjusted projection
    - my_proj: overwritten with adjusted value for CSV export convenience
    """
    # Use provided overrides or defaults
    weights = {
        "50": WEIGHTS.get("50") if w50 is None else float(w50),
        "100": WEIGHTS.get("100") if w100 is None else float(w100),
        "250": WEIGHTS.get("250") if w250 is None else float(w250),
    }
    use_k = AGGRESSIVENESS_K if k is None else float(k)
    use_cap = MAX_ABS_TILT if cap is None else float(cap)
    league_h = LEAGUE_XWOBA_HITTER if league_xwoba_hitter is None else float(league_xwoba_hitter)
    league_p = LEAGUE_XWOBA_PITCHER_ALLOWED if league_xwoba_pitcher is None else float(league_xwoba_pitcher)

    rosters = _load_active_rosters()
    name_index = _build_name_index(rosters)

    def _adjust_list_enhanced(records: List[Dict[str, Any]], role: str) -> List[Dict[str, Any]]:
        adjusted = []

        for r in records:
            name = _normalize_name(str(r.get("name") or ""))
            team = _normalize_team_abbr(str(r.get("team") or "").upper())
            mlb_id = name_index.get((name, team))

            if not mlb_id:
                # fallback: try any team for this normalized name
                candidates = [pid for (n, _t), pid in name_index.items() if n == name]
                if candidates:
                    mlb_id = candidates[0]
                else:
                    # final fallback: query MLB Stats search
                    mlb_id = _search_mlb_id_by_name(name, team)
                    if not mlb_id:
                        adjusted.append(r)
                        continue

            # Load both rolling windows and statcast data
            rolling = _load_rolling_file(mlb_id, role)
            statcast = _load_statcast_player_data(mlb_id, role)

            if not rolling:
                adjusted.append(r)
                continue

            # Compute enhanced signal
            signal = _compute_enhanced_signal(rolling, statcast, role, weights, league_h, league_p)
            if signal is None:
                adjusted.append(r)
                continue

            base_proj = r.get("my_proj")
            adj = _apply_enhanced_adjustment(base_proj, signal, use_k, use_cap)
            if adj is None:
                adjusted.append(r)
                continue

            new_r = dict(r)
            new_r["enhanced_signal"] = signal
            new_r["my_proj_adj"] = adj
            new_r["my_proj"] = adj
            adjusted.append(new_r)

        return adjusted

    return _adjust_list_enhanced(batters, "batter"), _adjust_list_enhanced(pitchers, "pitcher")


def _normalize_team_abbr(abbr: str) -> str:
    """Normalize team abbreviations."""
    mapping = {
        "LAA": "ANA", "LAD": "LAD", "ARI": "ARI", "ATL": "ATL", "BAL": "BAL",
        "BOS": "BOS", "CHC": "CHC", "CWS": "CWS", "CIN": "CIN", "CLE": "CLE",
        "COL": "COL", "DET": "DET", "HOU": "HOU", "KC": "KCR", "MIA": "MIA",
        "MIL": "MIL", "MIN": "MIN", "NYM": "NYM", "NYY": "NYY", "OAK": "OAK",
        "PHI": "PHI", "PIT": "PIT", "SD": "SDP", "SF": "SFG", "SEA": "SEA",
        "STL": "STL", "TB": "TBR", "TEX": "TEX", "TOR": "TOR", "WSH": "WSN"
    }
    return mapping.get(abbr.upper(), abbr.upper())


def _search_mlb_id_by_name(name_query: str, team_abbr: str) -> Optional[str]:
    """Search MLB Stats API for player ID by name."""
    try:
        url = "https://statsapi.mlb.com/api/v1/people/search"
        params = {
            'q': name_query,
            'sportIds': 1,
            'active': True
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        people = data.get('people', [])

        for person in people:
            if person.get('currentTeam', {}).get('abbreviation') == team_abbr:
                return str(person.get('id'))

        return None
    except Exception:
        return None
