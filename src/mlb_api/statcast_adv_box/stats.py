#!/usr/bin/env python3
"""
Boxscore Stats Extraction

Handles extraction and processing of traditional boxscore statistics from MLB game data.
"""

from typing import Dict

def extract_boxscore_stats(game_data: Dict) -> Dict[int, Dict]:
    """Extract traditional game log stats from boxscore with enhanced fantasy-relevant data."""
    player_stats = {}

    boxscore = game_data.get('boxscore', {})
    teams = boxscore.get('teams', {})

    for team_key, team_data in teams.items():
        players = team_data.get('players', {})

        for player_key, player_data in players.items():
            # Extract player ID from key like "ID123456"
            player_id = int(player_key.replace('ID', '')) if player_key.startswith('ID') else None
            if not player_id:
                continue

            # Get player info
            player_info = player_data.get('person', {})
            position_info = player_data.get('position', {})

            # Get batting and pitching stats
            batting_stats = player_data.get('stats', {}).get('batting', {})
            pitching_stats = player_data.get('stats', {}).get('pitching', {})

                        # Compile comprehensive stats for fantasy points calculation
            stats = {
                # Player identification
                'player_name': player_info.get('fullName', 'Unknown'),
                'team': team_key,
                'position': position_info.get('abbreviation', 'Unknown'),

                # Batting stats (essential for fantasy points) - ensure numeric types
                'game_at_bats': int(batting_stats.get('atBats', 0) or 0),
                'game_runs': int(batting_stats.get('runs', 0) or 0),
                'game_hits': int(batting_stats.get('hits', 0) or 0),
                'game_doubles': int(batting_stats.get('doubles', 0) or 0),
                'game_triples': int(batting_stats.get('triples', 0) or 0),
                'game_home_runs': int(batting_stats.get('homeRuns', 0) or 0),
                'game_rbi': int(batting_stats.get('rbi', 0) or 0),
                'game_walks': int(batting_stats.get('baseOnBalls', 0) or 0),
                'game_strikeouts': int(batting_stats.get('strikeOuts', 0) or 0),
                'game_stolen_bases': int(batting_stats.get('stolenBases', 0) or 0),
                'game_caught_stealing': int(batting_stats.get('caughtStealing', 0) or 0),
                'game_hit_by_pitch': int(batting_stats.get('hitByPitch', 0) or 0),
                'game_sac_flies': int(batting_stats.get('sacFlies', 0) or 0),
                'game_sac_bunts': int(batting_stats.get('sacBunts', 0) or 0),
                'game_left_on_base': int(batting_stats.get('leftOnBase', 0) or 0),
                'game_total_bases': int(batting_stats.get('totalBases', 0) or 0),
                'game_plate_appearances': int(batting_stats.get('plateAppearances', 0) or 0),

                # Additional batting context
                'game_ground_into_double_plays': int(batting_stats.get('groundIntoDoublePlays', 0) or 0),
                'game_intentional_walks': int(batting_stats.get('intentionalWalks', 0) or 0),

                # Pitching stats (essential for fantasy points) - ensure numeric types
                'game_innings_pitched': float(pitching_stats.get('inningsPitched', 0) or 0),
                'game_hits_allowed': int(pitching_stats.get('hits', 0) or 0),
                'game_runs_allowed': int(pitching_stats.get('runs', 0) or 0),
                'game_earned_runs': int(pitching_stats.get('earnedRuns', 0) or 0),
                'game_walks_allowed': int(pitching_stats.get('baseOnBalls', 0) or 0),
                'game_strikeouts_pitched': int(pitching_stats.get('strikeOuts', 0) or 0),
                'game_home_runs_allowed': int(pitching_stats.get('homeRuns', 0) or 0),
                'game_pitch_count': int(pitching_stats.get('numberOfPitches', 0) or 0),

                # Additional pitching context
                'game_wild_pitches': int(pitching_stats.get('wildPitches', 0) or 0),
                'game_balk': int(pitching_stats.get('balk', 0) or 0),
                'game_batters_faced': int(pitching_stats.get('battersFaced', 0) or 0),
                'game_ground_outs': int(pitching_stats.get('groundOuts', 0) or 0),
                'game_air_outs': int(pitching_stats.get('airOuts', 0) or 0),
                'game_pitches_thrown': int(pitching_stats.get('pitchesThrown', 0) or 0),
                'game_strikes': int(pitching_stats.get('strikes', 0) or 0),
                'game_first_pitch_strikes': int(pitching_stats.get('firstPitchStrikes', 0) or 0),
            }

            # Calculate derived stats for fantasy points
            if stats['game_hits'] > 0:
                # Calculate singles (hits - doubles - triples - home runs)
                stats['game_singles'] = stats['game_hits'] - stats['game_doubles'] - stats['game_triples'] - stats['game_home_runs']
            else:
                stats['game_singles'] = 0

            # Calculate slugging percentage
            if stats['game_at_bats'] > 0:
                stats['game_slugging'] = round(stats['game_total_bases'] / stats['game_at_bats'], 3)
            else:
                stats['game_slugging'] = 0.0

            # Calculate on-base percentage
            if stats['game_plate_appearances'] > 0:
                on_base = stats['game_hits'] + stats['game_walks'] + stats['game_hit_by_pitch']
                stats['game_on_base_pct'] = round(on_base / stats['game_plate_appearances'], 3)
            else:
                stats['game_on_base_pct'] = 0.0

            player_stats[player_id] = stats

    return player_stats