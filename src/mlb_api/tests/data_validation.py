#!/usr/bin/env python3
"""
MLB API Data Validation Test Suite

Validates data accuracy and consistency across all collectors:
- Roster data validation
- Statcast data validation  
- Rolling windows data validation
"""

import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from mlb_api.rosters.rosters_collector import ActiveRostersCollector
from mlb_api.statcast_adv_box.statcast_collector import StatcastAdvancedCollector
from mlb_api.rolling_windows.core.collector import EnhancedRollingCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a data validation test."""
    test_name: str
    passed: bool
    details: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    execution_time: float


class DataValidator:
    """Comprehensive data validation for MLB API collectors."""
    
    def __init__(self, output_dir: str = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/tests"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Test results storage
        self.results: List[ValidationResult] = []
        
        # Expected data patterns
        self.expected_patterns = {
            'teams_count': 30,
            'players_per_team_min': 20,
            'players_per_team_max': 30,
            'statcast_dates_min': 100,
            'rolling_players_min': 700
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("🧪 Starting MLB API Data Validation Tests...")
        print(f"📁 Output directory: {self.output_dir}")
        
        start_time = time.time()
        
        # Run individual test suites
        self._test_roster_data()
        self._test_statcast_data()
        self._test_rolling_data()
        self._test_cross_references()
        
        # Generate summary
        total_time = time.time() - start_time
        summary = self._generate_summary(total_time)
        
        # Save results
        self._save_results(summary)
        
        return summary
    
    def _test_roster_data(self):
        """Validate roster data accuracy."""
        print("\n🔍 Testing Roster Data...")
        start_time = time.time()
        
        try:
            # Load roster data
            roster_file = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/active_rosters/data/active_rosters.json")
            
            if not roster_file.exists():
                self.results.append(ValidationResult(
                    test_name="roster_data_exists",
                    passed=False,
                    details={},
                    errors=["Roster data file not found"],
                    warnings=[],
                    execution_time=time.time() - start_time
                ))
                return
            
            with open(roster_file, 'r') as f:
                roster_data = json.load(f)
            
            details = {}
            errors = []
            warnings = []
            
            # Test 1: Basic structure
            if 'teams' not in roster_data or 'rosters' not in roster_data:
                errors.append("Missing required top-level keys: teams, rosters")
            else:
                details['teams_count'] = len(roster_data['teams'])
                details['rosters_count'] = len(roster_data['rosters'])
            
            # Test 2: Team count validation
            if details.get('teams_count', 0) != self.expected_patterns['teams_count']:
                errors.append(f"Expected {self.expected_patterns['teams_count']} teams, got {details.get('teams_count', 0)}")
            
            # Test 3: Player count validation
            total_players = 0
            team_player_counts = []
            
            for team_abbr, team_roster in roster_data.get('rosters', {}).items():
                if 'roster' in team_roster:
                    player_count = len(team_roster['roster'])
                    team_player_counts.append(player_count)
                    total_players += player_count
                    
                    if player_count < self.expected_patterns['players_per_team_min']:
                        warnings.append(f"Team {team_abbr}: Only {player_count} players (expected 20+)")
                    elif player_count > self.expected_patterns['players_per_team_max']:
                        warnings.append(f"Team {team_abbr}: {player_count} players (expected 30 or fewer)")
            
            details['total_players'] = total_players
            details['avg_players_per_team'] = total_players / len(roster_data.get('rosters', {})) if roster_data.get('rosters') else 0
            
            # Test 4: Player data structure
            sample_player = None
            for team_roster in roster_data.get('rosters', {}).values():
                if 'roster' in team_roster and team_roster['roster']:
                    sample_player = team_roster['roster'][0]
                    break
            
            if sample_player:
                required_fields = ['id', 'fullName', 'primaryPosition']
                missing_fields = [field for field in required_fields if field not in sample_player]
                if missing_fields:
                    errors.append(f"Player missing required fields: {missing_fields}")
                else:
                    details['player_structure_valid'] = True
            
            # Test 5: Metadata validation
            if 'metadata' in roster_data:
                metadata = roster_data['metadata']
                details['collection_timestamp'] = metadata.get('collection_timestamp')
                details['total_teams'] = metadata.get('total_teams')
                details['total_players'] = metadata.get('total_players')
            else:
                warnings.append("No metadata found in roster data")
            
            passed = len(errors) == 0
            
            self.results.append(ValidationResult(
                test_name="roster_data_validation",
                passed=passed,
                details=details,
                errors=errors,
                warnings=warnings,
                execution_time=time.time() - start_time
            ))
            
            print(f"✅ Roster validation completed: {passed}")
            if errors:
                print(f"❌ Errors: {len(errors)}")
            if warnings:
                print(f"⚠️ Warnings: {len(warnings)}")
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="roster_data_validation",
                passed=False,
                details={},
                errors=[f"Exception during roster validation: {str(e)}"],
                warnings=[],
                execution_time=time.time() - start_time
            ))
    
    def _test_statcast_data(self):
        """Validate statcast data accuracy."""
        print("\n🔍 Testing Statcast Data...")
        start_time = time.time()
        
        try:
            # Load statcast data
            statcast_file = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/statcast_adv_box/data/statcast_adv_box.json")
            
            if not statcast_file.exists():
                self.results.append(ValidationResult(
                    test_name="statcast_data_exists",
                    passed=False,
                    details={},
                    errors=["Statcast data file not found"],
                    warnings=[],
                    execution_time=time.time() - start_time
                ))
                return
            
            with open(statcast_file, 'r') as f:
                statcast_data = json.load(f)
            
            details = {}
            errors = []
            warnings = []
            
            # Test 1: Basic structure
            if 'metadata' not in statcast_data:
                errors.append("Missing metadata in statcast data")
            else:
                metadata = statcast_data['metadata']
                details['collection_timestamp'] = metadata.get('collection_timestamp')
                details['total_dates'] = metadata.get('total_dates', 0)
                details['total_players'] = metadata.get('total_players', 0)
            
            # Test 2: Date files validation
            date_dir = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/statcast_adv_box/data/date")
            if date_dir.exists():
                date_files = list(date_dir.glob("advanced_statcast_*.json"))
                details['date_files_count'] = len(date_files)
                
                if len(date_files) < self.expected_patterns['statcast_dates_min']:
                    warnings.append(f"Only {len(date_files)} date files found (expected 100+)")
                
                # Check recent dates
                recent_dates = []
                for date_file in date_files[-5:]:  # Last 5 files
                    try:
                        date_str = date_file.stem.split('_')[-1]
                        date_obj = datetime.strptime(date_str, '%Y%m%d')
                        recent_dates.append(date_obj.date())
                    except:
                        pass
                
                if recent_dates:
                    latest_date = max(recent_dates)
                    days_behind = (datetime.now().date() - latest_date).days
                    details['latest_date'] = str(latest_date)
                    details['days_behind'] = days_behind
                    
                    if days_behind > 3:
                        warnings.append(f"Latest statcast data is {days_behind} days old")
            else:
                errors.append("Statcast date directory not found")
            
            # Test 3: Player data validation
            player_dir = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/statcast_adv_box/data/players")
            if player_dir.exists():
                batter_files = list(player_dir.glob("batters/*.json"))
                pitcher_files = list(player_dir.glob("pitchers/*.json"))
                
                details['batter_files_count'] = len(batter_files)
                details['pitcher_files_count'] = len(pitcher_files)
                details['total_player_files'] = len(batter_files) + len(pitcher_files)
                
                if len(batter_files) < 500:
                    warnings.append(f"Only {len(batter_files)} batter files found (expected 500+)")
                if len(pitcher_files) < 600:
                    warnings.append(f"Only {len(pitcher_files)} pitcher files found (expected 600+)")
            else:
                warnings.append("Statcast player directory not found")
            
            passed = len(errors) == 0
            
            self.results.append(ValidationResult(
                test_name="statcast_data_validation",
                passed=passed,
                details=details,
                errors=errors,
                warnings=warnings,
                execution_time=time.time() - start_time
            ))
            
            print(f"✅ Statcast validation completed: {passed}")
            if errors:
                print(f"❌ Errors: {len(errors)}")
            if warnings:
                print(f"⚠️ Warnings: {len(warnings)}")
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="statcast_data_validation",
                passed=False,
                details={},
                errors=[f"Exception during statcast validation: {str(e)}"],
                warnings=[],
                execution_time=time.time() - start_time
            ))
    
    def _test_rolling_data(self):
        """Validate rolling windows data accuracy."""
        print("\n🔍 Testing Rolling Windows Data...")
        start_time = time.time()
        
        try:
            # Load rolling data
            rolling_file = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/rolling_windows/data/rolling_windows.json")
            
            if not rolling_file.exists():
                self.results.append(ValidationResult(
                    test_name="rolling_data_exists",
                    passed=False,
                    details={},
                    errors=["Rolling windows data file not found"],
                    warnings=[],
                    execution_time=time.time() - start_time
                ))
                return
            
            with open(rolling_file, 'r') as f:
                rolling_data = json.load(f)
            
            details = {}
            errors = []
            warnings = []
            
            # Test 1: Basic structure
            if 'metadata' not in rolling_data:
                errors.append("Missing metadata in rolling data")
            else:
                metadata = rolling_data['metadata']
                details['collection_timestamp'] = metadata.get('collection_timestamp')
                details['total_players'] = metadata.get('total_players', 0)
                details['successful_collections'] = metadata.get('successful_collections', 0)
                details['failed_collections'] = metadata.get('failed_collections', 0)
            
            # Test 2: Player files validation
            hitters_dir = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/rolling_windows/data/hitters")
            pitchers_dir = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/rolling_windows/data/pitchers")
            
            if hitters_dir.exists():
                hitter_files = list(hitters_dir.glob("*.json"))
                details['hitter_files_count'] = len(hitter_files)
            else:
                details['hitter_files_count'] = 0
                errors.append("Hitters directory not found")
            
            if pitchers_dir.exists():
                pitcher_files = list(pitchers_dir.glob("*.json"))
                details['pitcher_files_count'] = len(pitcher_files)
            else:
                details['pitcher_files_count'] = 0
                errors.append("Pitchers directory not found")
            
            total_player_files = details.get('hitter_files_count', 0) + details.get('pitcher_files_count', 0)
            details['total_player_files'] = total_player_files
            
            if total_player_files < self.expected_patterns['rolling_players_min']:
                warnings.append(f"Only {total_player_files} player files found (expected 700+)")
            
            # Test 3: Sample player data structure
            sample_player_file = None
            if hitters_dir.exists() and list(hitters_dir.glob("*.json")):
                sample_player_file = list(hitters_dir.glob("*.json"))[0]
            elif pitchers_dir.exists() and list(pitchers_dir.glob("*.json")):
                sample_player_file = list(pitchers_dir.glob("*.json"))[0]
            
            if sample_player_file:
                try:
                    with open(sample_player_file, 'r') as f:
                        sample_data = json.load(f)
                    
                    required_fields = ['player_id', 'player_type', 'name', 'multi_window_data']
                    missing_fields = [field for field in required_fields if field not in sample_data]
                    
                    if missing_fields:
                        errors.append(f"Player data missing required fields: {missing_fields}")
                    else:
                        details['player_structure_valid'] = True
                        
                        # Check window data
                        window_data = sample_data.get('multi_window_data', {})
                        expected_windows = ['50', '100', '250']
                        missing_windows = [w for w in expected_windows if w not in window_data]
                        
                        if missing_windows:
                            warnings.append(f"Missing window sizes: {missing_windows}")
                        else:
                            details['window_sizes_valid'] = True
                            
                except Exception as e:
                    errors.append(f"Error reading sample player file: {str(e)}")
            else:
                warnings.append("No sample player files found for structure validation")
            
            # Test 4: Hash files validation
            hash_dir = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/rolling_windows/hash")
            if hash_dir.exists():
                hitter_hashes = list(hash_dir.glob("hitters/*.json"))
                pitcher_hashes = list(hash_dir.glob("pitchers/*.json"))
                
                details['hitter_hash_files'] = len(hitter_hashes)
                details['pitcher_hash_files'] = len(pitcher_hashes)
                details['total_hash_files'] = len(hitter_hashes) + len(pitcher_hashes)
                
                if len(hitter_hashes) + len(pitcher_hashes) < total_player_files * 0.8:
                    warnings.append("Hash files count significantly lower than player files")
            else:
                warnings.append("Hash directory not found")
            
            passed = len(errors) == 0
            
            self.results.append(ValidationResult(
                test_name="rolling_data_validation",
                passed=passed,
                details=details,
                errors=errors,
                warnings=warnings,
                execution_time=time.time() - start_time
            ))
            
            print(f"✅ Rolling validation completed: {passed}")
            if errors:
                print(f"❌ Errors: {len(errors)}")
            if warnings:
                print(f"⚠️ Warnings: {len(warnings)}")
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="rolling_data_validation",
                passed=False,
                details={},
                errors=[f"Exception during rolling validation: {str(e)}"],
                warnings=[],
                execution_time=time.time() - start_time
            ))
    
    def _test_cross_references(self):
        """Test cross-references between datasets."""
        print("\n🔍 Testing Cross-References...")
        start_time = time.time()
        
        try:
            details = {}
            errors = []
            warnings = []
            
            # Load all datasets
            roster_file = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/active_rosters/data/active_rosters.json")
            rolling_file = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/rolling_windows/data/rolling_windows.json")
            
            if not roster_file.exists() or not rolling_file.exists():
                errors.append("Required data files not found for cross-reference testing")
                self.results.append(ValidationResult(
                    test_name="cross_references",
                    passed=False,
                    details={},
                    errors=errors,
                    warnings=[],
                    execution_time=time.time() - start_time
                ))
                return
            
            with open(roster_file, 'r') as f:
                roster_data = json.load(f)
            
            with open(rolling_file, 'r') as f:
                rolling_data = json.load(f)
            
            # Test 1: Player count consistency
            roster_players = roster_data.get('metadata', {}).get('total_players', 0)
            rolling_players = rolling_data.get('metadata', {}).get('total_players', 0)
            
            details['roster_players'] = roster_players
            details['rolling_players'] = rolling_players
            
            if abs(roster_players - rolling_players) > 50:
                warnings.append(f"Player count mismatch: roster={roster_players}, rolling={rolling_players}")
            
            # Test 2: Team consistency
            roster_teams = len(roster_data.get('teams', []))
            details['roster_teams'] = roster_teams
            
            if roster_teams != self.expected_patterns['teams_count']:
                errors.append(f"Roster team count mismatch: {roster_teams} vs expected {self.expected_patterns['teams_count']}")
            
            # Test 3: Sample player ID consistency
            roster_player_ids = set()
            for team_roster in roster_data.get('rosters', {}).values():
                if 'roster' in team_roster:
                    for player in team_roster['roster']:
                        if 'id' in player:
                            roster_player_ids.add(str(player['id']))
            
            rolling_player_ids = set()
            hitters_dir = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/rolling_windows/data/hitters")
            pitchers_dir = Path("/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025/rolling_windows/data/pitchers")
            
            for player_dir in [hitters_dir, pitchers_dir]:
                if player_dir.exists():
                    for player_file in player_dir.glob("*.json"):
                        try:
                            with open(player_file, 'r') as f:
                                player_data = json.load(f)
                                if 'player_id' in player_data:
                                    rolling_player_ids.add(str(player_data['player_id']))
                        except:
                            pass
            
            details['roster_unique_players'] = len(roster_player_ids)
            details['rolling_unique_players'] = len(rolling_player_ids)
            
            # Check overlap
            overlap = roster_player_ids.intersection(rolling_player_ids)
            details['player_overlap'] = len(overlap)
            details['overlap_percentage'] = len(overlap) / len(roster_player_ids) * 100 if roster_player_ids else 0
            
            if details['overlap_percentage'] < 80:
                warnings.append(f"Low player overlap: {details['overlap_percentage']:.1f}%")
            
            # Test 4: Data freshness
            roster_timestamp = roster_data.get('metadata', {}).get('collection_timestamp')
            rolling_timestamp = rolling_data.get('metadata', {}).get('collection_timestamp')
            
            if roster_timestamp and rolling_timestamp:
                try:
                    roster_time = datetime.fromisoformat(roster_timestamp.replace('Z', '+00:00'))
                    rolling_time = datetime.fromisoformat(rolling_timestamp.replace('Z', '+00:00'))
                    
                    time_diff = abs((roster_time - rolling_time).total_seconds() / 3600)
                    details['time_difference_hours'] = time_diff
                    
                    if time_diff > 24:
                        warnings.append(f"Data collection times differ by {time_diff:.1f} hours")
                except:
                    warnings.append("Could not parse collection timestamps")
            
            passed = len(errors) == 0
            
            self.results.append(ValidationResult(
                test_name="cross_references",
                passed=passed,
                details=details,
                errors=errors,
                warnings=warnings,
                execution_time=time.time() - start_time
            ))
            
            print(f"✅ Cross-reference validation completed: {passed}")
            if errors:
                print(f"❌ Errors: {len(errors)}")
            if warnings:
                print(f"⚠️ Warnings: {len(warnings)}")
                
        except Exception as e:
            self.results.append(ValidationResult(
                test_name="cross_references",
                passed=False,
                details={},
                errors=[f"Exception during cross-reference validation: {str(e)}"],
                warnings=[],
                execution_time=time.time() - start_time
            ))
    
    def _generate_summary(self, total_time: float) -> Dict[str, Any]:
        """Generate test summary."""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result.passed)
        failed_tests = total_tests - passed_tests
        
        total_errors = sum(len(result.errors) for result in self.results)
        total_warnings = sum(len(result.warnings) for result in self.results)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_execution_time': total_time,
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            'issues_summary': {
                'total_errors': total_errors,
                'total_warnings': total_warnings
            },
            'detailed_results': [
                {
                    'test_name': result.test_name,
                    'passed': result.passed,
                    'execution_time': result.execution_time,
                    'errors': result.errors,
                    'warnings': result.warnings,
                    'details': result.details
                }
                for result in self.results
            ]
        }
        
        return summary
    
    def _save_results(self, summary: Dict[str, Any]):
        """Save test results to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.output_dir / f"validation_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n📁 Test results saved to: {results_file}")
        
        # Print summary
        print(f"\n📊 Validation Summary:")
        print(f"   Tests: {summary['test_summary']['passed_tests']}/{summary['test_summary']['total_tests']} passed")
        print(f"   Success Rate: {summary['test_summary']['success_rate']:.1f}%")
        print(f"   Errors: {summary['issues_summary']['total_errors']}")
        print(f"   Warnings: {summary['issues_summary']['total_warnings']}")
        print(f"   Total Time: {summary['total_execution_time']:.1f}s")


def main():
    """Run the data validation test suite."""
    validator = DataValidator()
    summary = validator.run_all_tests()
    
    # Exit with error code if any tests failed
    if summary['test_summary']['failed_tests'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
