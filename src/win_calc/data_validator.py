#!/usr/bin/env python3
"""
Data Validation Tool for Win Calc Adjustments

Validates rolling windows and statcast data against MLB API endpoints
to ensure data accuracy and identify potential issues.
"""

import json
import os
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import pandas as pd

# Data paths
ROLLING_ROOT = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/rolling_windows/data"
STATCAST_ROOT = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/statcast_adv_box/data"
ROSTERS_PATH = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/active_rosters/data/active_rosters.json"

# MLB API endpoints
MLB_STATS_BASE = "https://statsapi.mlb.com/api/v1"
MLB_PEOPLE_BASE = "https://statsapi.mlb.com/api/v1/people"

# Validation thresholds
XWOBA_TOLERANCE = 0.050  # 50 points difference
EV_TOLERANCE = 2.0  # 2 mph difference
FANTASY_TOLERANCE = 0.20  # 20% difference


@dataclass
class ValidationResult:
    """Result of a data validation check."""
    player_id: str
    player_name: str
    team: str
    check_type: str
    is_valid: bool
    expected_value: Optional[float]
    actual_value: Optional[float]
    difference: Optional[float]
    tolerance: Optional[float]
    message: str
    severity: str = "warning"  # info, warning, error


class MLBDataValidator:
    """Validates MLB data against official API endpoints."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RedOcean-DataValidator/1.0'
        })

    def validate_player_stats(self, player_id: str, player_name: str, team: str) -> List[ValidationResult]:
        """Validate player stats against MLB API."""
        results = []

        try:
            # Get current season stats from MLB API
            url = f"{MLB_PEOPLE_BASE}/{player_id}/stats"
            params = {
                'stats': 'season',
                'group': 'hitting,pitching',
                'season': '2025'
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Validate hitting stats
            hitting_stats = data.get('stats', [])
            for stat_group in hitting_stats:
                if stat_group.get('group', {}).get('displayName') == 'hitting':
                    splits = stat_group.get('splits', [])
                    if splits:
                        season_stats = splits[0].get('stat', {})
                        results.extend(self._validate_hitting_stats(
                            player_id, player_name, team, season_stats
                        ))

            # Validate pitching stats
            for stat_group in hitting_stats:
                if stat_group.get('group', {}).get('displayName') == 'pitching':
                    splits = stat_group.get('splits', [])
                    if splits:
                        season_stats = splits[0].get('stat', {})
                        results.extend(self._validate_pitching_stats(
                            player_id, player_name, team, season_stats
                        ))

        except Exception as e:
            results.append(ValidationResult(
                player_id=player_id,
                player_name=player_name,
                team=team,
                check_type="mlb_api_connection",
                is_valid=False,
                expected_value=None,
                actual_value=None,
                difference=None,
                tolerance=None,
                message=f"Failed to connect to MLB API: {str(e)}",
                severity="error"
            ))

        return results

    def _validate_hitting_stats(self, player_id: str, player_name: str, team: str,
                               mlb_stats: Dict[str, Any]) -> List[ValidationResult]:
        """Validate hitting statistics."""
        results = []

        # Load our rolling windows data
        rolling_path = os.path.join(ROLLING_ROOT, "hitters", f"{player_id}.json")
        if not os.path.exists(rolling_path):
            return [ValidationResult(
                player_id=player_id,
                player_name=player_name,
                team=team,
                check_type="rolling_data_exists",
                is_valid=False,
                expected_value=None,
                actual_value=None,
                difference=None,
                tolerance=None,
                message="No rolling windows data found",
                severity="error"
            )]

        with open(rolling_path, 'r') as f:
            rolling_data = json.load(f)

        # Validate xwOBA (if available in MLB API)
        mlb_xwoba = mlb_stats.get('xwoba')
        if mlb_xwoba:
            rolling_xwoba = self._get_latest_xwoba(rolling_data)
            if rolling_xwoba:
                diff = abs(mlb_xwoba - rolling_xwoba)
                is_valid = diff <= XWOBA_TOLERANCE
                results.append(ValidationResult(
                    player_id=player_id,
                    player_name=player_name,
                    team=team,
                    check_type="xwoba_validation",
                    is_valid=is_valid,
                    expected_value=mlb_xwoba,
                    actual_value=rolling_xwoba,
                    difference=diff,
                    tolerance=XWOBA_TOLERANCE,
                    message=f"xwOBA validation: MLB={mlb_xwoba:.3f}, Rolling={rolling_xwoba:.3f}, Diff={diff:.3f}",
                    severity="error" if not is_valid else "info"
                ))

        # Always validate that we have rolling data
        rolling_xwoba = self._get_latest_xwoba(rolling_data)
        if rolling_xwoba:
            results.append(ValidationResult(
                player_id=player_id,
                player_name=player_name,
                team=team,
                check_type="rolling_data_quality",
                is_valid=True,
                expected_value=None,
                actual_value=rolling_xwoba,
                difference=None,
                tolerance=None,
                message=f"Rolling windows data available: xwOBA={rolling_xwoba:.3f}",
                severity="info"
            ))
        else:
            results.append(ValidationResult(
                player_id=player_id,
                player_name=player_name,
                team=team,
                check_type="rolling_data_quality",
                is_valid=False,
                expected_value=None,
                actual_value=None,
                difference=None,
                tolerance=None,
                message="No xwOBA data found in rolling windows",
                severity="error"
            ))

        return results

    def _validate_pitching_stats(self, player_id: str, player_name: str, team: str,
                                mlb_stats: Dict[str, Any]) -> List[ValidationResult]:
        """Validate pitching statistics."""
        results = []

        # Load our rolling windows data
        rolling_path = os.path.join(ROLLING_ROOT, "pitchers", f"{player_id}.json")
        if not os.path.exists(rolling_path):
            return [ValidationResult(
                player_id=player_id,
                player_name=player_name,
                team=team,
                check_type="rolling_data_exists",
                is_valid=False,
                expected_value=None,
                actual_value=None,
                difference=None,
                tolerance=None,
                message="No rolling windows data found",
                severity="error"
            )]

        with open(rolling_path, 'r') as f:
            rolling_data = json.load(f)

        # Validate ERA
        mlb_era = mlb_stats.get('era')
        if mlb_era:
            rolling_era = self._get_latest_era(rolling_data)
            if rolling_era:
                diff = abs(mlb_era - rolling_era)
                is_valid = diff <= 0.5  # 0.5 ERA tolerance
                results.append(ValidationResult(
                    player_id=player_id,
                    player_name=player_name,
                    team=team,
                    check_type="era_validation",
                    is_valid=is_valid,
                    expected_value=mlb_era,
                    actual_value=rolling_era,
                    difference=diff,
                    tolerance=0.5,
                    message=f"ERA validation: MLB={mlb_era:.2f}, Rolling={rolling_era:.2f}, Diff={diff:.2f}",
                    severity="error" if not is_valid else "info"
                ))

        return results

    def _get_latest_xwoba(self, rolling_data: Dict[str, Any]) -> Optional[float]:
        """Get the latest xwOBA from rolling windows data."""
        rolling_windows = rolling_data.get('rolling_windows', {})
        for window in ['50', '100', '250']:
            window_data = rolling_windows.get(window, {})
            summary = window_data.get('summary', {})
            xwoba = summary.get('latest_xwoba')
            if xwoba is not None:
                return float(xwoba)
        return None

    def _get_latest_era(self, rolling_data: Dict[str, Any]) -> Optional[float]:
        """Get the latest ERA from rolling windows data."""
        rolling_windows = rolling_data.get('rolling_windows', {})
        for window in ['50', '100', '250']:
            window_data = rolling_windows.get(window, {})
            summary = window_data.get('summary', {})
            era = summary.get('latest_era')
            if era is not None:
                return float(era)
        return None

    def validate_statcast_data(self, player_id: str, player_name: str, team: str) -> List[ValidationResult]:
        """Validate Statcast data against Baseball Savant."""
        results = []

        # Load our statcast data - try both batter and pitcher directories
        statcast_path = os.path.join(STATCAST_ROOT, "batter", f"{player_id}.json")
        if not os.path.exists(statcast_path):
            statcast_path = os.path.join(STATCAST_ROOT, "pitcher", f"{player_id}.json")

        if not os.path.exists(statcast_path):
            return [ValidationResult(
                player_id=player_id,
                player_name=player_name,
                team=team,
                check_type="statcast_data_exists",
                is_valid=False,
                expected_value=None,
                actual_value=None,
                difference=None,
                tolerance=None,
                message="No Statcast data found",
                severity="error"
            )]

        with open(statcast_path, 'r') as f:
            statcast_data = json.load(f)

        # Validate exit velocity data (only for batters)
        if "batter" in statcast_path:
            results.extend(self._validate_exit_velocity(player_id, player_name, team, statcast_data))

        # Always validate that we have statcast data
        games = statcast_data.get('games', {})
        if games:
            game_count = len(games)
            results.append(ValidationResult(
                player_id=player_id,
                player_name=player_name,
                team=team,
                check_type="statcast_data_quality",
                is_valid=True,
                expected_value=None,
                actual_value=game_count,
                difference=None,
                tolerance=None,
                message=f"Statcast data available: {game_count} games",
                severity="info"
            ))
        else:
            results.append(ValidationResult(
                player_id=player_id,
                player_name=player_name,
                team=team,
                check_type="statcast_data_quality",
                is_valid=False,
                expected_value=None,
                actual_value=None,
                difference=None,
                tolerance=None,
                message="No games data found in Statcast file",
                severity="error"
            ))

        return results

    def _validate_exit_velocity(self, player_id: str, player_name: str, team: str,
                               statcast_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate exit velocity data."""
        results = []

        # Calculate average exit velocity from our data
        total_ev = 0
        total_events = 0

        games = statcast_data.get('games', {})
        for game_data in games.values():
            for at_bat in game_data.get('batter_at_bats', []):
                ev = at_bat.get('launch_speed')
                if ev and ev > 0:
                    total_ev += ev
                    total_events += 1

        if total_events > 0:
            avg_ev = total_ev / total_events

            # Compare with rolling windows data
            rolling_path = os.path.join(ROLLING_ROOT, "hitters", f"{player_id}.json")
            if os.path.exists(rolling_path):
                with open(rolling_path, 'r') as f:
                    rolling_data = json.load(f)

                rolling_ev = self._get_latest_avg_ev(rolling_data)
                if rolling_ev:
                    diff = abs(avg_ev - rolling_ev)
                    is_valid = diff <= EV_TOLERANCE
                    results.append(ValidationResult(
                        player_id=player_id,
                        player_name=player_name,
                        team=team,
                        check_type="exit_velocity_validation",
                        is_valid=is_valid,
                        expected_value=avg_ev,
                        actual_value=rolling_ev,
                        difference=diff,
                        tolerance=EV_TOLERANCE,
                        message=f"Exit velocity validation: Statcast={avg_ev:.1f}, Rolling={rolling_ev:.1f}, Diff={diff:.1f}",
                        severity="error" if not is_valid else "info"
                    ))

        return results

    def _get_latest_avg_ev(self, rolling_data: Dict[str, Any]) -> Optional[float]:
        """Get the latest average exit velocity from rolling windows data."""
        rolling_windows = rolling_data.get('rolling_windows', {})
        for window in ['50', '100', '250']:
            window_data = rolling_windows.get(window, {})
            summary = window_data.get('summary', {})
            avg_ev = summary.get('avg_ev')
            if avg_ev is not None:
                return float(avg_ev)
        return None


def run_validation_report(player_ids: Optional[List[str]] = None,
                         output_path: Optional[str] = None) -> Dict[str, Any]:
    """Run comprehensive validation report."""

    # Load active rosters
    with open(ROSTERS_PATH, 'r') as f:
        rosters = json.load(f)

    # Get player list
    if player_ids is None:
        # Get all players from rosters
        player_ids = []
        for team_data in rosters.get('rosters', {}).values():
            for player in team_data.get('roster', []):
                player_ids.append(str(player.get('id')))

    validator = MLBDataValidator()
    all_results = []

    print(f"🔍 Validating data for {len(player_ids)} players...")

    for i, player_id in enumerate(player_ids):
        # Get player info
        player_name = "Unknown"
        team = "Unknown"
        for team_data in rosters.get('rosters', {}).values():
            for player in team_data.get('roster', []):
                if str(player.get('id')) == player_id:
                    player_name = player.get('fullName_ascii', player.get('fullName', 'Unknown'))
                    team = list(rosters.get('rosters', {}).keys())[
                        list(rosters.get('rosters', {}).values()).index(team_data)
                    ]
                    break

        print(f"  [{i+1}/{len(player_ids)}] Validating {player_name} ({team})...")

        # Run validations
        results = validator.validate_player_stats(player_id, player_name, team)
        results.extend(validator.validate_statcast_data(player_id, player_name, team))

        all_results.extend(results)

        # Rate limiting
        time.sleep(0.1)

    # Generate report
    report = generate_validation_report(all_results, output_path)

    return report


def generate_validation_report(results: List[ValidationResult],
                              output_path: Optional[str] = None) -> Dict[str, Any]:
    """Generate validation report."""

    # Summary statistics
    total_checks = len(results)
    valid_checks = sum(1 for r in results if r.is_valid)
    error_checks = sum(1 for r in results if r.severity == "error")
    warning_checks = sum(1 for r in results if r.severity == "warning")

    # Group by check type
    check_types = {}
    for result in results:
        check_type = result.check_type
        if check_type not in check_types:
            check_types[check_type] = []
        check_types[check_type].append(result)

    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_checks": total_checks,
            "valid_checks": valid_checks,
            "invalid_checks": total_checks - valid_checks,
            "error_count": error_checks,
            "warning_count": warning_checks,
            "success_rate": (valid_checks / total_checks * 100) if total_checks > 0 else 0
        },
        "check_types": {},
        "errors": [r for r in results if r.severity == "error"],
        "warnings": [r for r in results if r.severity == "warning"]
    }

    # Add check type summaries
    for check_type, type_results in check_types.items():
        valid_count = sum(1 for r in type_results if r.is_valid)
        report["check_types"][check_type] = {
            "total": len(type_results),
            "valid": valid_count,
            "invalid": len(type_results) - valid_count,
            "success_rate": (valid_count / len(type_results) * 100) if type_results else 0
        }

    # Save report
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

    # Print summary
    print(f"\n📊 VALIDATION REPORT SUMMARY:")
    print(f"   Total checks: {total_checks}")
    print(f"   Valid: {valid_checks} ({report['summary']['success_rate']:.1f}%)")
    print(f"   Errors: {error_checks}")
    print(f"   Warnings: {warning_checks}")

    if error_checks > 0:
        print(f"\n❌ ERRORS FOUND:")
        for error in report["errors"][:5]:  # Show first 5 errors
            print(f"   {error.player_name} ({error.team}): {error.message}")

    return report


if __name__ == "__main__":
    # Run validation on a sample of players
    sample_players = [
        "664040",  # Brandon Lowe
        "664285",  # Framber Valdez
        "622491",  # Luis Castillo
    ]

    report = run_validation_report(
        player_ids=sample_players,
        output_path="diagnostics/reports/output/win_calc/validation_report.json"
    )
