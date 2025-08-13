#!/usr/bin/env python3
"""
Fantasy Points Scoring Systems

Contains DraftKings and FanDuel scoring configurations and calculation logic.
"""

from typing import Dict

class FantasyScoring:
    """Base class for fantasy points scoring systems."""

    def __init__(self):
        self.draftkings_scoring = {
            # Hitting
            'single': 3,
            'double': 5,
            'triple': 8,
            'home_run': 10,
            'rbi': 2,
            'run': 2,
            'walk': 2,
            'hit_by_pitch': 2,
            'stolen_base': 5,
            'caught_stealing': -2,
            # Pitching
            'win': 4,
            'earned_run': -2,
            'inning_pitched': 2.25,
            'strikeout': 2,
            'walk_allowed': -0.6,
            'hit_allowed': -0.6,
            'no_hitter': 5,
            'perfect_game': 5,
            'complete_game': 2.5,
            'complete_game_shutout': 2.5
        }

        self.fanduel_scoring = {
            # Hitting
            'single': 3,
            'double': 6,
            'triple': 9,
            'home_run': 12,
            'rbi': 3.5,
            'run': 3.2,
            'walk': 3,
            'hit_by_pitch': 3,
            'stolen_base': 6,
            'caught_stealing': -3,
            # Pitching
            'win': 6,
            'quality_start': 4,
            'earned_run': -3,
            'inning_pitched': 3,
            'strikeout': 3,
            'walk_allowed': -3,
            'hit_allowed': -3,
            'complete_game': 3
        }

    def calculate_fantasy_points(self, player_stats: Dict, site: str = 'draftkings') -> Dict[str, float]:
        """
        Calculate fantasy points for both DraftKings and FanDuel from boxscore stats.

        Args:
            player_stats: Dictionary containing game stats
            site: 'draftkings' or 'fanduel'

        Returns:
            Dictionary with 'batting_points', 'pitching_points', and 'total_points'
        """
        scoring = self.draftkings_scoring if site == 'draftkings' else self.fanduel_scoring

        batting_points = 0.0
        pitching_points = 0.0

        # Calculate batting points
        if any(key.startswith('game_') for key in player_stats.keys()):
            # Extract hitting stats
            hits = player_stats.get('game_hits', 0)
            doubles = player_stats.get('game_doubles', 0)
            triples = player_stats.get('game_triples', 0)
            home_runs = player_stats.get('game_home_runs', 0)
            singles = hits - doubles - triples - home_runs

            # Calculate points for each stat type
            batting_points += singles * scoring['single']
            batting_points += doubles * scoring['double']
            batting_points += triples * scoring['triple']
            batting_points += home_runs * scoring['home_run']
            batting_points += player_stats.get('game_rbi', 0) * scoring['rbi']
            batting_points += player_stats.get('game_runs', 0) * scoring['run']
            batting_points += player_stats.get('game_walks', 0) * scoring['walk']
            batting_points += player_stats.get('game_hit_by_pitch', 0) * scoring['hit_by_pitch']
            batting_points += player_stats.get('game_stolen_bases', 0) * scoring['stolen_base']
            batting_points += player_stats.get('game_caught_stealing', 0) * scoring['caught_stealing']

        # Calculate pitching points
        if player_stats.get('game_innings_pitched', 0) > 0:
            innings_pitched = player_stats.get('game_innings_pitched', 0)
            earned_runs = player_stats.get('game_earned_runs', 0)
            strikeouts = player_stats.get('game_strikeouts_pitched', 0)
            walks_allowed = player_stats.get('game_walks_allowed', 0)
            hits_allowed = player_stats.get('game_hits_allowed', 0)

            # Basic pitching points
            pitching_points += innings_pitched * scoring['inning_pitched']
            pitching_points += earned_runs * scoring['earned_run']
            pitching_points += strikeouts * scoring['strikeout']
            pitching_points += walks_allowed * scoring['walk_allowed']

            # DraftKings specific penalties
            if site == 'draftkings':
                pitching_points += hits_allowed * scoring['hit_allowed']

            # FanDuel quality start bonus (6+ IP, ≤3 ER)
            if site == 'fanduel' and innings_pitched >= 6 and earned_runs <= 3:
                pitching_points += scoring['quality_start']

            # Complete game bonuses (if we can determine from innings)
            if innings_pitched >= 9:
                if site == 'draftkings':
                    pitching_points += scoring['complete_game']
                elif site == 'fanduel':
                    pitching_points += scoring['complete_game']

                # DraftKings complete game shutout bonus
                if site == 'draftkings' and earned_runs == 0:
                    pitching_points += scoring['complete_game_shutout']

        total_points = batting_points + pitching_points

        return {
            'batting_points': round(batting_points, 2),
            'pitching_points': round(pitching_points, 2),
            'total_points': round(total_points, 2)
        }

    def calculate_game_fantasy_points(self, player_stats: Dict[int, Dict]) -> Dict[int, Dict]:
        """
        Calculate fantasy points for all players in a game.

        Args:
            player_stats: Dictionary mapping player_id to their game stats

        Returns:
            Dictionary mapping player_id to their fantasy points for both sites
        """
        fantasy_points = {}

        for player_id, stats in player_stats.items():
            dk_points = self.calculate_fantasy_points(stats, 'draftkings')
            fd_points = self.calculate_fantasy_points(stats, 'fanduel')

            fantasy_points[player_id] = {
                'draftkings': dk_points,
                'fanduel': fd_points,
                'raw_stats': stats
            }

        return fantasy_points