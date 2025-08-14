#!/usr/bin/env python3
"""
Integrated Statcast Advanced Box Score Collector

Extends MLBAPICollector for hash-based incremental updates while preserving
all sophisticated Statcast data collection logic.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
import logging
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import handling for both direct execution and package import
try:
    from ..shared.incremental_updater import MLBAPICollector
except ImportError:
    # Direct execution - add parent to path
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from shared.incremental_updater import MLBAPICollector
# Import handling for both direct execution and package import
try:
    from .stats import extract_boxscore_stats
    from .scoring import FantasyScoring
except ImportError:
    # Direct execution - add current directory to path
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from stats import extract_boxscore_stats
    from scoring import FantasyScoring

# Configure logging
logger = logging.getLogger(__name__)

class StatcastAdvancedCollector(MLBAPICollector):
    """
    Integrated Statcast Advanced Box Score Collector with hash-based incremental updates.

    Preserves all sophisticated data collection while adding intelligent update detection.
    """

    def __init__(self, performance_profile: str = 'super_aggressive', max_workers: int = None, request_delay: float = None):
        super().__init__("statcast_adv_box")

        # Use shared config for performance settings
        try:
            from ..shared.config import MLBConfig
        except ImportError:
            # Direct execution - add parent to path
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent.parent))
            from shared.config import MLBConfig

        self.config = MLBConfig()

        # Get performance settings from shared config
        if max_workers is None or request_delay is None:
            perf_settings = self.config.get_performance_settings(performance_profile)
            max_workers = max_workers or perf_settings['max_workers']
            request_delay = request_delay or perf_settings['request_delay']

        self.set_performance_settings(max_workers, request_delay)
        logger.info(f"🚀 Statcast collector initialized with {performance_profile} profile: {max_workers} workers, {request_delay}s delay")

        # Initialize fantasy scoring
        self.scoring = FantasyScoring()

        # MLB Stats API base URL for getting game PKs
        self.mlb_api_base = "https://statsapi.mlb.com/api/v1"
                # Baseball Savant game feed endpoint
        self.savant_base = "https://baseballsavant.mlb.com/gf"

        # Initialize session for API calls with larger connection pool for ultra-aggressive settings
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
        })

        # Increase connection pool size for super-aggressive performance
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=30,  # Increased for super-aggressive
            pool_maxsize=30,      # Increased for super-aggressive
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # Create organized output directories
        self._setup_output_directories()

    def _setup_output_directories(self):
        """Create organized output directory structure."""
        # Main data directory (accessed through updater)
        self.updater.data_dir.mkdir(parents=True, exist_ok=True)

        # Date-based directory (like cosmic_grid) - for efficient collection and date analysis
        self.date_dir = self.updater.data_dir / "date"
        self.date_dir.mkdir(exist_ok=True)

        # Player-based directories - for player-centric analysis
        self.batter_dir = self.updater.data_dir / "batter"
        self.pitcher_dir = self.updater.data_dir / "pitcher"
        self.batter_dir.mkdir(exist_ok=True)
        self.pitcher_dir.mkdir(exist_ok=True)

        # Track which players we have data for
        self.known_players = self._load_known_players()

    def _load_known_players(self) -> Dict[str, Set[str]]:
        """Load list of known dates and players from existing files."""
        known_dates = set()
        known_players = {'batter': set(), 'pitcher': set()}

        # Load date-based files (advanced_statcast_YYYYMMDD.json)
        for file_path in self.date_dir.glob("advanced_statcast_*.json"):
            # Extract date from filename like "advanced_statcast_20250812.json"
            if file_path.stem.startswith("advanced_statcast_"):
                date_str = file_path.stem.replace("advanced_statcast_", "")
                if len(date_str) == 8 and date_str.isdigit():  # YYYYMMDD format
                    known_dates.add(date_str)

        # Load player-based files
        for file_path in self.batter_dir.glob("*.json"):
            if file_path.stem.isdigit():  # Only numeric player IDs
                known_players['batter'].add(file_path.stem)

        for file_path in self.pitcher_dir.glob("*.json"):
            if file_path.stem.isdigit():  # Only numeric player IDs
                known_players['pitcher'].add(file_path.stem)

        logger.info(f"Loaded {len(known_dates)} known dates and {len(known_players['batter'])} batters, {len(known_players['pitcher'])} pitchers")
        return {'dates': known_dates, 'players': known_players}

    def collect_data(self) -> Union[Dict, List]:
        """
        Main data collection method required by MLBAPICollector.

        Creates a comprehensive data structure representing the current state
        of all date-based statcast files. The hash system will detect changes in this data.
        """
        logger.info("🔄 Collecting comprehensive date-based statcast data for hash-based updates...")

        # Get the current season dates
        season_start, season_end = self._get_regular_season_dates()
        if not season_start or not season_end:
            logger.error("Could not determine season dates")
            return {"status": "error", "message": "Could not determine season dates"}

        logger.info(f"📅 Season range: {season_start} to {season_end}")

        # Create comprehensive data structure representing both date-based and player-based files
        comprehensive_data = {
            'metadata': {
                'collection_timestamp': datetime.now().isoformat(),  # Will be excluded from hash
                'collector_name': 'statcast_adv_box',
                'collector_version': '2.0.0',
                'data_type': 'advanced_statcast',
                'source': 'baseball_savant_game_feed',
                'season': {
                    'start_date': season_start,
                    'end_date': season_end,
                    'current_date': datetime.now().strftime('%Y-%m-%d')
                }
            },
            'dates': {},
            'players': {
                'batter': {},
                'pitcher': {}
            }
        }

        # Load existing date-based data to create the comprehensive structure
        total_at_bats = 0
        total_games = 0

        # Process date-based files (advanced_statcast_YYYYMMDD.json)
        for file_path in self.date_dir.glob("advanced_statcast_*.json"):
            if file_path.stem.startswith("advanced_statcast_"):
                date_str = file_path.stem.replace("advanced_statcast_", "")
                if len(date_str) == 8 and date_str.isdigit():  # YYYYMMDD format
                    try:
                        with open(file_path, 'r') as f:
                            date_data = json.load(f)

                        # Add to comprehensive data (exclude timestamps for stable hashing)
                        clean_date_data = self._create_stable_date_data(date_data)
                        comprehensive_data['dates'][date_str] = clean_date_data

                        total_at_bats += date_data.get('summary', {}).get('total_at_bats', 0)
                        total_games += date_data.get('summary', {}).get('total_games', 0)

                    except Exception as e:
                        logger.warning(f"Error loading date {date_str}: {e}")

        # Load player-based data
        total_players = 0

        # Process batter files
        for file_path in self.batter_dir.glob("*.json"):
            if file_path.stem.isdigit():  # Only numeric player IDs
                player_id = file_path.stem
                try:
                    with open(file_path, 'r') as f:
                        player_data = json.load(f)

                    # Add to comprehensive data (exclude timestamps for stable hashing)
                    clean_player_data = self._create_stable_player_data(player_data)
                    comprehensive_data['players']['batter'][player_id] = clean_player_data

                    total_players += 1

                except Exception as e:
                    logger.warning(f"Error loading batter {player_id}: {e}")

        # Process pitcher files
        for file_path in self.pitcher_dir.glob("*.json"):
            if file_path.stem.isdigit():  # Only numeric player IDs
                player_id = file_path.stem
                try:
                    with open(file_path, 'r') as f:
                        player_data = json.load(f)

                    # Add to comprehensive data (exclude timestamps for stable hashing)
                    clean_player_data = self._create_stable_player_data(player_data)
                    comprehensive_data['players']['pitcher'][player_id] = clean_player_data

                    total_players += 1

                except Exception as e:
                    logger.warning(f"Error loading pitcher {player_id}: {e}")

        # Add summary statistics
        comprehensive_data['summary'] = {
            'total_dates': len(comprehensive_data['dates']),
            'total_players': total_players,
            'total_at_bats': total_at_bats,
            'total_games': total_games
        }

        logger.info(f"✅ Comprehensive data collected: {len(comprehensive_data['dates'])} dates, {total_players} players, {total_at_bats} at-bats, {total_games} games")
        return comprehensive_data

    def run_collection(self, force_update: bool = False) -> Tuple[bool, Union[Dict, List], str]:
        """
        Override the base run_collection method to directly collect data without hash system.
        """
        logger.info("🚀 Starting direct Statcast data collection...")

        # Always collect new data (bypass hash system)
        self.update_date_files()

        # Create a summary data structure for compatibility
        summary_data = {
            'status': 'success',
            'collection_timestamp': datetime.now().isoformat(),
            'collector_name': 'statcast_adv_box',
            'data_type': 'advanced_statcast'
        }

        logger.info("✅ Statcast data collection completed")
        return True, summary_data, "Direct collection completed"

    def update_date_files(self):
        """
        Update all date-based statcast files and player-based files when hash system detects changes.
        This method is called after the hash system determines updates are needed.
        """
        logger.info("🔄 Hash system detected changes - updating date-based and player-based statcast files...")

        # Get the current season dates - but only process recent dates for efficiency
        season_start, season_end = self._get_regular_season_dates()
        if not season_start or not season_end:
            logger.error("Could not determine season dates")
            return

        # Only process last 3 days to avoid long loops
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        day_before = today - timedelta(days=2)

        dates_to_process = [day_before, yesterday, today]

        logger.info(f"🔄 Processing dates: {day_before}, {yesterday}, {today}")

        # Process each date in the recent range
        total_at_bats = 0
        dates_updated = 0
        games_processed = 0

        for date_to_process in dates_to_process:
            date_str = date_to_process.strftime('%Y-%m-%d')

            # Check if we already have data for this date
            if self._date_exists(date_str):
                logger.info(f"📁 Data already exists for {date_str}, skipping")
                continue

            # Check if we have games for this date
            try:
                games = self._fetch_games_for_date(date_str, game_types=['R'])  # Regular season only
                if games:
                    logger.info(f"🎯 Processing {date_str}: {len(games)} games")
                    count = self._collect_single_date(date_str)
                    if count > 0:
                        total_at_bats += count
                        dates_updated += 1
                        games_processed += len(games)
                else:
                    logger.info(f"📭 No games found for {date_str}")
            except Exception as e:
                logger.error(f"❌ Error processing {date_str}: {e}")
                continue

        logger.info(f"✅ Both date-based and player-based statcast files updated: {total_at_bats} at-bats, {dates_updated} dates, {games_processed} games")

        # Ensure we return properly
        return

    def _create_stable_date_data(self, date_data: Dict) -> Dict:
        """
        Create a stable version of date data for hashing.
        Excludes timestamps and other volatile fields.
        """
        stable_data = {
            'date': date_data.get('date'),
            'total_at_bats': date_data.get('summary', {}).get('total_at_bats', 0),
            'total_games': date_data.get('summary', {}).get('total_games', 0),
            'at_bats_with_xBA': date_data.get('summary', {}).get('at_bats_with_xBA', 0),
            'at_bats_with_exit_velo': date_data.get('summary', {}).get('at_bats_with_exit_velo', 0),
            'at_bats_with_launch_angle': date_data.get('summary', {}).get('at_bats_with_launch_angle', 0),
            'barrels': date_data.get('summary', {}).get('barrels', 0)
        }

        return stable_data

    def _create_stable_player_data(self, player_data: Dict) -> Dict:
        """
        Create a stable version of player data for hashing.
        Excludes timestamps and other volatile fields.
        """
        stable_data = {
            'player_id': player_data.get('player_id'),
            'total_games': player_data.get('total_games', 0),
            'total_at_bats': player_data.get('total_at_bats', 0),
            'games': {}
        }

        # Add game data without timestamps
        for date_str, game_data in player_data.get('games', {}).items():
            stable_data['games'][date_str] = {
                'batter_at_bats_count': len(game_data.get('batter_at_bats', [])),
                'pitcher_at_bats_count': len(game_data.get('pitcher_at_bats', [])),
                'total_at_bats': len(game_data.get('batter_at_bats', [])) + len(game_data.get('pitcher_at_bats', []))
            }

        return stable_data

    def _get_regular_season_dates(self, season: int = None) -> tuple:
        """Get start and end dates for regular season dynamically from MLB API."""
        if season is None:
            season = datetime.now().year

        url = f"{self.mlb_api_base}/seasons"
        params = {
            'sportId': 1,
            'season': season
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            for season_info in data.get('seasons', []):
                if season_info.get('seasonId') == str(season):
                    # Get regular season dates
                    regular_season_start = season_info.get('regularSeasonStartDate')
                    regular_season_end = season_info.get('regularSeasonEndDate')

                    if regular_season_start and regular_season_end:
                        # Convert from YYYY-MM-DD format
                        start_date = regular_season_start[:10]
                        end_date = regular_season_end[:10]

                        logger.info(f"🗓️  {season} Regular Season: {start_date} to {end_date}")
                        return start_date, end_date

            logger.error(f"Could not find regular season dates for {season}")
            return None, None

        except Exception as e:
            logger.error(f"Error fetching season info: {e}")
            return None, None

    # _process_date_games and _process_single_game methods removed - no longer needed
    # All data collection is now handled by _collect_single_date method

    # All player-based file methods removed - using date-based structure instead

    def _get_dates_to_collect(self) -> List[str]:
        """
        Determine which dates need to be collected based on:
        1. What we already have
        2. What games are available
        3. Hash-based change detection
        """
        # Start with yesterday (most common daily update)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # Check if we already have yesterday
        if self._date_exists(yesterday):
            logger.info(f"📁 Data already exists for {yesterday}")

            # Check if we need to update (maybe games were added later)
            if self._should_update_date(yesterday):
                logger.info(f"🔄 Updates detected for {yesterday}")
                return [yesterday]
            else:
                logger.info(f"✅ {yesterday} is up to date")
                return []
        else:
            logger.info(f"🆕 No data exists for {yesterday}, will collect")
            return [yesterday]

    def _date_exists(self, date_str: str) -> bool:
        """Check if we have data for a specific date."""
        # Check for the date file in the date directory
        date_file = self.date_dir / f"advanced_statcast_{date_str.replace('-', '')}.json"
        return date_file.exists()

    def _should_update_date(self, date_str: str) -> bool:
        """
        Check if a date needs updating by comparing hash of existing data
        with what would be collected now.
        """
        # This is a simplified check - in practice, you might want to
        # compare game counts, at-bat counts, or other metrics
        return False  # For now, assume existing data is complete

    def _collect_single_date(self, date_str: str) -> Optional[int]:
        """Collect advanced Statcast data for a single date."""
        logger.info(f"🎯 Collecting {date_str}...")

        # Get games for this date
        games = self._fetch_games_for_date(date_str)
        if not games:
            logger.info(f"No completed games found for {date_str}")
            return 0

        # Collect advanced data for each game
        date_at_bats = []
        game_summaries = []

        # Use threading for concurrent game fetching
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_game = {
                executor.submit(self._fetch_advanced_game_data, game['game_pk']): game
                for game in games
            }

            for future in as_completed(future_to_game):
                game = future_to_game[future]
                try:
                    game_data = future.result()
                    if game_data:
                        at_bats, game_summary = self._extract_advanced_at_bats(game_data)
                        date_at_bats.extend(at_bats)

                        # Generate game summary with fantasy points
                        game_summaries.append(game_summary)

                        logger.debug(f"  Game {game['game_pk']}: {len(at_bats)} at-bats, fantasy points calculated")
                except Exception as e:
                    logger.error(f"  Game {game['game_pk']} failed: {e}")

        # Save data for this date in organized structure
        if date_at_bats:
            self._save_organized_data(date_str, date_at_bats, game_summaries)
            logger.info(f"💾 Saved {len(date_at_bats)} advanced at-bats for {date_str}")
            return len(date_at_bats)

        return 0

    def _fetch_games_for_date(self, game_date: str, game_types: List[str] = ['R']) -> List[Dict]:
        """Fetch game PKs for a specific date from MLB Stats API."""
        url = f"{self.mlb_api_base}/schedule"
        params = {
            'date': game_date,
            'sportId': 1,  # MLB
            'gameType': ','.join(game_types)  # Regular season by default
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            games = []
            for date_info in data.get('dates', []):
                for game in date_info.get('games', []):
                    if game.get('status', {}).get('detailedState') == 'Final':
                        games.append({
                            'game_pk': game['gamePk'],
                            'away_team': game['teams']['away']['team'].get('abbreviation', 'Unknown'),
                            'home_team': game['teams']['home']['team'].get('abbreviation', 'Unknown'),
                            'game_date': game_date
                        })

            logger.info(f"Found {len(games)} completed games for {game_date}")
            return games

        except Exception as e:
            logger.error(f"Error fetching games for {game_date}: {e}")
            return []

    def _fetch_advanced_game_data(self, game_pk: int) -> Optional[Dict]:
        """Fetch advanced Statcast data for a specific game from Baseball Savant."""
        url = f"{self.savant_base}?game_pk={game_pk}"

        try:
            response = self.session.get(url, timeout=45)
            response.raise_for_status()

            data = response.json()
            logger.debug(f"✅ Fetched advanced data for game {game_pk}")
            return data

        except Exception as e:
            logger.error(f"❌ Error fetching game {game_pk}: {e}")
            return None

    def _extract_advanced_at_bats(self, game_data: Dict) -> tuple[List[Dict], Dict]:
        """Extract and process advanced at-bat data with expected stats."""
        if not game_data or 'exit_velocity' not in game_data:
            return [], {}

        at_bats = []
        # Get game_pk from scoreboard section first, fallback to top level
        game_pk = game_data.get('scoreboard', {}).get('gamePk')
        if not game_pk:
            game_pk = game_data.get('game_pk', 'Unknown')
        game_date = game_data.get('gameDate', 'Unknown')

        # Get boxscore stats for all players
        player_boxscore_stats = extract_boxscore_stats(game_data)

        # Generate comprehensive game summary with fantasy points
        game_summary = self._generate_game_summary(game_data)

        for ab_data in game_data['exit_velocity']:
            try:
                # Core at-bat record with essential Statcast metrics
                at_bat = {
                    'game_pk': game_pk,
                    'game_date': game_date,
                    'inning': ab_data.get('inning'),
                    'ab_number': ab_data.get('ab_number'),
                    'outs': ab_data.get('outs'),

                    # Player info with handedness
                    'batter_id': ab_data.get('batter'),
                    'batter_name': ab_data.get('batter_name'),
                    'batter_stand': ab_data.get('stand'),
                    'pitcher_id': ab_data.get('pitcher'),
                    'pitcher_name': ab_data.get('pitcher_name'),
                    'pitcher_throws': ab_data.get('p_throws'),

                    # Teams
                    'batting_team': ab_data.get('team_batting'),
                    'fielding_team': ab_data.get('team_fielding'),

                    # At-bat outcome
                    'result': ab_data.get('result'),
                    'events': ab_data.get('events'),

                    # Count
                    'balls': ab_data.get('balls'),
                    'strikes': ab_data.get('strikes'),

                    # CRITICAL: Expected Stats & Contact Quality
                    'exit_velocity': ab_data.get('hit_speed'),
                    'launch_angle': ab_data.get('hit_angle'),
                    'hit_distance': ab_data.get('hit_distance'),
                    'xBA': ab_data.get('xba'),
                    'is_barrel': ab_data.get('is_barrel', 0),
                    'bat_speed': ab_data.get('batSpeed'),

                    # Essential Pitch Context
                    'pitch_type': ab_data.get('pitch_type'),
                    'pitch_name': ab_data.get('pitch_name'),
                    'start_speed': ab_data.get('start_speed'),
                    'end_speed': ab_data.get('end_speed'),
                    'spin_rate': ab_data.get('spin_rate'),
                    'zone': ab_data.get('zone'),

                    # Strike Zone & Location
                    'plate_x': ab_data.get('px'),
                    'plate_z': ab_data.get('pz'),
                    'sz_top': ab_data.get('sz_top'),
                    'sz_bot': ab_data.get('sz_bot'),

                    # Pitch Movement & Physics
                    'pfx_x': ab_data.get('pfxX'),
                    'pfx_z': ab_data.get('pfxZ'),
                    'break_x': ab_data.get('breakX'),
                    'break_z': ab_data.get('breakZ'),
                    'induced_break_z': ab_data.get('inducedBreakZ'),
                    'extension': ab_data.get('extension'),
                    'plate_time': ab_data.get('plateTime'),

                    # Velocity Components (for advanced physics)
                    'vx0': ab_data.get('vx0'),
                    'vy0': ab_data.get('vy0'),
                    'vz0': ab_data.get('vz0'),

                    # Acceleration Components
                    'ax': ab_data.get('ax'),
                    'ay': ab_data.get('ay'),
                    'az': ab_data.get('az'),

                    # Release Point
                    'x0': ab_data.get('x0'),
                    'y0': ab_data.get('y0'),
                    'z0': ab_data.get('z0'),

                    # Count Context
                    'pre_balls': ab_data.get('pre_balls'),
                    'pre_strikes': ab_data.get('pre_strikes'),
                    'pitch_number': ab_data.get('pitch_number'),

                    # Advanced Context
                    'context_metrics': ab_data.get('contextMetrics', {}),
                    'is_sword': ab_data.get('isSword', False),
                    'call': ab_data.get('call'),
                    'call_name': ab_data.get('call_name'),
                    'description': ab_data.get('description'),
                }

                # Add boxscore game log stats for both batter and pitcher
                batter_id = at_bat.get('batter_id')
                pitcher_id = at_bat.get('pitcher_id')

                if batter_id in player_boxscore_stats:
                    batter_stats = player_boxscore_stats[batter_id]
                    # Add batter's game stats with 'batter_' prefix
                    for stat_key, stat_value in batter_stats.items():
                        if stat_key.startswith('game_'):
                            at_bat[f'batter_{stat_key}'] = stat_value

                    # Calculate and add fantasy points for batter
                    batter_fantasy_points = self.scoring.calculate_fantasy_points(batter_stats, 'draftkings')
                    at_bat['batter_dk_points'] = batter_fantasy_points['total_points']
                    at_bat['batter_dk_batting_points'] = batter_fantasy_points['batting_points']
                    at_bat['batter_dk_pitching_points'] = batter_fantasy_points['pitching_points']

                    batter_fantasy_points_fd = self.scoring.calculate_fantasy_points(batter_stats, 'fanduel')
                    at_bat['batter_fd_points'] = batter_fantasy_points_fd['total_points']
                    at_bat['batter_fd_batting_points'] = batter_fantasy_points_fd['batting_points']
                    at_bat['batter_fd_pitching_points'] = batter_fantasy_points_fd['pitching_points']

                if pitcher_id in player_boxscore_stats:
                    pitcher_stats = player_boxscore_stats[pitcher_id]
                    # Add pitcher's game stats with 'pitcher_' prefix
                    for stat_key, stat_value in pitcher_stats.items():
                        if stat_key.startswith('game_'):
                            at_bat[f'pitcher_{stat_key}'] = stat_value

                    # Calculate and add fantasy points for pitcher
                    pitcher_fantasy_points = self.scoring.calculate_fantasy_points(pitcher_stats, 'draftkings')
                    at_bat['pitcher_dk_points'] = pitcher_fantasy_points['total_points']
                    at_bat['pitcher_dk_batting_points'] = pitcher_fantasy_points['batting_points']
                    at_bat['pitcher_dk_pitching_points'] = pitcher_fantasy_points['pitching_points']

                    pitcher_fantasy_points_fd = self.scoring.calculate_fantasy_points(pitcher_stats, 'fanduel')
                    at_bat['pitcher_fd_points'] = pitcher_fantasy_points_fd['total_points']
                    at_bat['pitcher_fd_batting_points'] = pitcher_fantasy_points_fd['batting_points']
                    at_bat['pitcher_fd_pitching_points'] = pitcher_fantasy_points_fd['pitching_points']

                at_bats.append(at_bat)

            except Exception as e:
                logger.warning(f"Error processing at-bat in game {game_pk}: {e}")
                continue

        return at_bats, game_summary

    def _generate_game_summary(self, game_data: Dict) -> Dict:
        """Generate a clean game summary with boxscore stats and fantasy points."""
        # Extract boxscore stats
        player_stats = extract_boxscore_stats(game_data)

        # Calculate fantasy points for all players
        fantasy_points = self.scoring.calculate_game_fantasy_points(player_stats)

        # Get game metadata
        game_pk = game_data.get('scoreboard', {}).get('gamePk', 'Unknown')
        game_date = game_data.get('gameDate', 'Unknown')

        # Create clean game summary
        game_summary = {
            'game_pk': game_pk,
            'game_date': game_date,
            'total_players': len(player_stats),
            'players': {}
        }

        # Process each player's performance
        for player_id, stats in player_stats.items():
            player_name = stats.get('player_name', f'Player_{player_id}')
            team = stats.get('team', 'Unknown')
            position = stats.get('position', 'Unknown')

            # Get fantasy points
            dk_points = fantasy_points[player_id]['draftkings']['total_points']
            fd_points = fantasy_points[player_id]['fanduel']['total_points']

            # Create clean player record
            game_summary['players'][player_id] = {
                'player_id': player_id,
                'player_name': player_name,
                'team': team,
                'position': position,
                'boxscore_stats': stats,
                'fantasy_points': {
                    'draftkings': dk_points,
                    'fanduel': fd_points
                }
            }

        return game_summary

    def _save_organized_data(self, date_str: str, at_bats: List[Dict], game_summaries: List[Dict]):
        """Save data in both date-based AND player-based structures."""

        # 1. SAVE DATE-BASED FILE (like cosmic_grid) - for efficient collection and date analysis
        date_file = self.date_dir / f"advanced_statcast_{date_str.replace('-', '')}.json"

        # Calculate summary statistics
        at_bats_with_xba = len([ab for ab in at_bats if ab.get('xBA')])
        at_bats_with_exit_velo = len([ab for ab in at_bats if ab.get('exit_velocity')])
        at_bats_with_launch_angle = len([ab for ab in at_bats if ab.get('launch_angle')])
        barrels = len([ab for ab in at_bats if ab.get('is_barrel')])

        date_data = {
            'metadata': {
                'collected_at': datetime.now().isoformat(),
                'data_type': 'advanced_statcast',
                'date': date_str,
                'source': 'baseball_savant_game_feed',
                'summary': {
                    'total_games': len(game_summaries),
                    'total_at_bats': len(at_bats),
                    'at_bats_with_xBA': at_bats_with_xba,
                    'at_bats_with_exit_velo': at_bats_with_exit_velo,
                    'at_bats_with_launch_angle': at_bats_with_launch_angle,
                    'barrels': barrels
                }
            },
            'at_bats': at_bats
        }

        with open(date_file, 'w') as f:
            json.dump(date_data, f, indent=2)

        logger.info(f"💾 Saved date-based data for {date_str}: {len(at_bats)} at-bats to {date_file.name}")

        # 2. UPDATE PLAYER-BASED FILES - for player-centric analysis
        self._update_player_files_from_date_data(date_str, at_bats)

        logger.info(f"✅ Data saved in both structures: date-based ({date_file.name}) and player-based (batter/pitcher)")

    def _update_player_files_from_date_data(self, date_str: str, at_bats: List[Dict]):
        """Update player-based files with new at-bat data from a specific date."""
        # Group at-bats by player
        player_at_bats = {}

        for at_bat in at_bats:
            batter_id = at_bat.get('batter_id')
            pitcher_id = at_bat.get('pitcher_id')

            if batter_id:
                if batter_id not in player_at_bats:
                    player_at_bats[batter_id] = {'batter': [], 'pitcher': []}
                player_at_bats[batter_id]['batter'].append(at_bat)

            if pitcher_id:
                if pitcher_id not in player_at_bats:
                    player_at_bats[pitcher_id] = {'batter': [], 'pitcher': []}
                player_at_bats[pitcher_id]['pitcher'].append(at_bat)

        # Update each player's file
        for player_id, data in player_at_bats.items():
            self._update_single_player_file(player_id, data, date_str)

    def _update_single_player_file(self, player_id: str, data: Dict, date_str: str):
        """Update a single player's file with new data."""
        # Load existing player data
        player_file = self._get_player_file_path(player_id, data)
        existing_data = self._load_player_data(player_file)

        # Add new at-bats for this date
        if 'games' not in existing_data:
            existing_data['games'] = {}

        # Only add if we don't already have this date
        if date_str not in existing_data['games']:
            existing_data['games'][date_str] = {
                'batter_at_bats': data.get('batter', []),
                'pitcher_at_bats': data.get('pitcher', [])
            }

            # Update metadata
            existing_data['last_updated'] = datetime.now().isoformat()
            existing_data['total_games'] = len(existing_data['games'])
            existing_data['total_at_bats'] = sum(
                len(game_data.get('batter_at_bats', [])) + len(game_data.get('pitcher_at_bats', []))
                for game_data in existing_data['games'].values()
            )

            # Save updated player file
            with open(player_file, 'w') as f:
                json.dump(existing_data, f, indent=2)

            logger.debug(f"Updated player {player_id} with {date_str} data")

    def _get_player_file_path(self, player_id: str, data: Dict) -> Path:
        """Determine the file path for a player based on their primary role."""
        # If they have more batter at-bats, they're primarily a batter
        if len(data.get('batter', [])) >= len(data.get('pitcher', [])):
            return self.batter_dir / f"{player_id}.json"
        else:
            return self.pitcher_dir / f"{player_id}.json"

    def _load_player_data(self, player_file: Path) -> Dict:
        """Load existing player data or create new structure."""
        if player_file.exists():
            try:
                with open(player_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading {player_file}: {e}")

        # Create new player data structure
        return {
            'player_id': player_file.stem,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'total_games': 0,
            'total_at_bats': 0,
            'games': {}
        }

    def collect_yesterday(self) -> Optional[int]:
        """Collect data for yesterday's games."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        logger.info(f"🕐 Collecting yesterday's games ({yesterday})")

        # Use the main collection method
        data = self.collect_data()
        if data and 'collection_results' in data:
            return data['collection_results'].get(yesterday, 0)
        return 0

    def collect_date_range(self, start_date: str, end_date: str) -> Dict[str, int]:
        """Collect data for a range of dates."""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        today = datetime.now().date()

        # Don't go beyond today
        if end.date() > today:
            end = datetime.combine(today, datetime.min.time())
            logger.info(f"🛑 Adjusting end date to today: {end.strftime('%Y-%m-%d')}")

        results = {}
        current_date = start

        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')

            # Check if we need to collect this date
            if not self._date_exists(date_str):
                count = self._collect_single_date(date_str)
                if count is not None:
                    results[date_str] = count
            else:
                logger.info(f"📁 Data already exists for {date_str}, skipping")

            current_date += timedelta(days=1)

            # Small delay to be respectful to APIs
            time.sleep(self.request_delay)

        return results
