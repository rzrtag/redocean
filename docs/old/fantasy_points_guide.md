# Fantasy Points Integration Guide

## Overview

The enhanced Statcast collector now includes comprehensive fantasy points calculation for both **DraftKings** and **FanDuel** MLB contests. This integration provides:

- **Real-time fantasy points calculation** from boxscore data
- **Dual-platform scoring** (DraftKings and FanDuel)
- **Comprehensive game summaries** with player performance metrics
- **Multiple export formats** for analysis and integration

## Key Features

### 🎯 **Dual Platform Scoring**
- **DraftKings**: Complete scoring system including bonuses for complete games, no-hitters, etc.
- **FanDuel**: Enhanced scoring with quality start bonuses and higher point values

### 📊 **Comprehensive Boxscore Integration**
- Traditional batting and pitching statistics
- Derived statistics (singles, slugging %, OBP)
- Advanced pitching metrics (first-pitch strikes, ground/air outs)

### 🚀 **Automated Collection & Export**
- Fantasy points calculated automatically during data collection
- Multiple export formats (JSON, CSV, Summary)
- Integration with existing Statcast collection pipeline

## Scoring Systems

### DraftKings Scoring

| Statistic | Points | Notes |
|-----------|--------|-------|
| **Single** | +3 | Base hit |
| **Double** | +5 | Extra-base hit |
| **Triple** | +8 | Extra-base hit |
| **Home Run** | +10 | Maximum batting points |
| **RBI** | +2 | Run batted in |
| **Run** | +2 | Run scored |
| **Walk** | +2 | Base on balls |
| **Hit By Pitch** | +2 | Hit by pitch |
| **Stolen Base** | +5 | Base stolen |
| **Caught Stealing** | -2 | Penalty |
| **Inning Pitched** | +2.25 | Per inning (0.75 per out) |
| **Strikeout** | +2 | Per strikeout |
| **Win** | +4 | Game win |
| **Earned Run** | -2 | Per earned run |
| **Complete Game** | +2.5 | Bonus for 9+ innings |
| **Complete Game Shutout** | +2.5 | Bonus for 9+ IP, 0 ER |

### FanDuel Scoring

| Statistic | Points | Notes |
|-----------|--------|-------|
| **Single** | +3 | Base hit |
| **Double** | +6 | Higher value than DK |
| **Triple** | +9 | Higher value than DK |
| **Home Run** | +12 | **Highest value** |
| **RBI** | +3.5 | **Premium value** |
| **Run** | +3.2 | **Premium value** |
| **Walk** | +3 | Higher value than DK |
| **Hit By Pitch** | +3 | Higher value than DK |
| **Stolen Base** | +6 | Higher value than DK |
| **Caught Stealing** | -3 | Higher penalty |
| **Inning Pitched** | +3 | Per inning (1.0 per out) |
| **Strikeout** | +3 | Higher value than DK |
| **Win** | +6 | Higher value than DK |
| **Earned Run** | -3 | Higher penalty |
| **Quality Start** | +4 | **FD Exclusive** (6+ IP, ≤3 ER) |
| **Complete Game** | +3 | Bonus for 9+ innings |

## Usage Examples

### 1. **Basic Fantasy Points Calculation**

```python
from statcast.collector import DailyStatcastCollector

# Create collector instance
collector = DailyStatcastCollector()

# Sample player stats from boxscore
player_stats = {
    'game_at_bats': 4,
    'game_hits': 2,
    'game_doubles': 1,
    'game_home_runs': 1,
    'game_rbi': 3,
    'game_runs': 2,
    'game_walks': 1,
    'game_stolen_bases': 1
}

# Calculate DraftKings points
dk_points = collector.calculate_fantasy_points(player_stats, 'draftkings')
print(f"DraftKings: {dk_points['total_points']} pts")
print(f"  Batting: {dk_points['batting_points']} pts")
print(f"  Pitching: {dk_points['pitching_points']} pts")

# Calculate FanDuel points
fd_points = collector.calculate_fantasy_points(player_stats, 'fanduel')
print(f"FanDuel: {fd_points['total_points']} pts")
print(f"  Batting: {fd_points['batting_points']} pts")
print(f"  Pitching: {fd_points['pitching_points']} pts")
```

### 2. **Game Summary Generation**

```python
# Generate comprehensive game summary with fantasy points
game_summary = collector.generate_game_summary(game_data)

# Access fantasy points summary
dk_summary = game_summary['fantasy_points_summary']['draftkings']
fd_summary = game_summary['fantasy_points_summary']['fanduel']

print(f"DraftKings Total Points: {dk_summary['total_points']}")
print(f"FanDuel Total Points: {fd_summary['total_points']}")

# Get top performers
top_dk = dk_summary['top_scorers'][0]
print(f"Top DK Scorer: Player {top_dk['player_id']} with {top_dk['points']} pts")
```

### 3. **Command Line Usage**

#### Collect data and export fantasy points automatically:
```bash
# Collect today's games and export fantasy points
python src/statcast/collector.py --auto-export

# Collect specific date with fantasy points export
python src/statcast/collector.py --date 2025-08-10 --auto-export

# Collect date range with fantasy points export
python src/statcast/collector.py --start-date 2025-08-01 --end-date 2025-08-10 --auto-export
```

#### Export fantasy points for existing data:
```bash
# Export fantasy points for specific date
python src/statcast/collector.py --export-fantasy 2025-08-10

# Export in different formats
python src/statcast/collector.py --export-fantasy 2025-08-10 --export-format csv
python src/statcast/collector.py --export-fantasy 2025-08-10 --export-format summary
```

## Output Formats

### 1. **JSON Export** (`--export-format json`)
Comprehensive export with all game data and fantasy points:
```json
{
  "date": "2025-08-10",
  "exported_at": "2025-08-10T22:00:33.852014",
  "total_games": 15,
  "games": [
    {
      "game_metadata": {...},
      "fantasy_points_summary": {...},
      "player_performance": {...}
    }
  ]
}
```

### 2. **CSV Export** (`--export-format csv`)
Tabular format for easy analysis in Excel/Google Sheets:
```csv
game_pk,game_date,player_id,player_name,team,position,dk_total_points,dk_batting_points,dk_pitching_points,fd_total_points,fd_batting_points,fd_pitching_points,at_bats,hits,home_runs,rbi,runs,stolen_bases
123456,2025-08-10,641386,Player Name,NYM,OF,15.5,15.5,0.0,18.2,18.2,0.0,4,2,1,3,2,1
```

### 3. **Summary Export** (`--export-format summary`)
Aggregated statistics and top performers:
```json
{
  "date": "2025-08-10",
  "total_games": 15,
  "total_players": 450,
  "fantasy_points_summary": {
    "draftkings": {
      "total_points": 6750.5,
      "average_points_per_game": 450.0
    },
    "fanduel": {
      "total_points": 8234.8,
      "average_points_per_game": 549.0
    }
  },
  "top_performers": {
    "draftkings": [...],
    "fanduel": [...]
  }
}
```

## Integration with Existing Pipeline

### **Automatic Integration**
- Fantasy points are calculated automatically during data collection
- No changes needed to existing collection scripts
- Game summaries are included in the main output files

### **File Structure**
```
_data/statcast/
├── advanced_statcast_20250810.json          # Main data file
├── fantasy_points/                          # Fantasy points exports
│   ├── fantasy_points_20250810.json        # Comprehensive export
│   ├── fantasy_points_20250810.csv         # CSV export
│   └── fantasy_points_summary_20250810.json # Summary export
```

### **Data Flow**
1. **Collection**: Statcast data + boxscore data collected
2. **Processing**: Fantasy points calculated for all players
3. **Integration**: Points added to at-bat records and game summaries
4. **Export**: Optional export in multiple formats
5. **Storage**: All data saved with fantasy points included

## Testing

### **Run Test Suite**
```bash
cd test
python test_fantasy_points.py
```

### **Test Specific Functionality**
```python
# Test scoring systems
collector = DailyStatcastCollector()
print("DraftKings scoring:", collector.draftkings_scoring)
print("FanDuel scoring:", collector.fanduel_scoring)

# Test with sample data
sample_stats = {'game_hits': 2, 'game_home_runs': 1, 'game_rbi': 2}
points = collector.calculate_fantasy_points(sample_stats, 'draftkings')
print(f"Sample points: {points}")
```

## Advanced Features

### **Quality Start Detection**
FanDuel quality start bonus (+4 pts) automatically calculated for:
- 6+ innings pitched
- ≤3 earned runs

### **Complete Game Bonuses**
- DraftKings: +2.5 pts for 9+ IP
- FanDuel: +3 pts for 9+ IP
- DraftKings: Additional +2.5 pts for shutout

### **Derived Statistics**
- **Singles**: Automatically calculated (hits - doubles - triples - home runs)
- **Slugging %**: Total bases / at bats
- **OBP**: (Hits + Walks + HBP) / plate appearances

## Troubleshooting

### **Common Issues**

1. **No fantasy points in output**
   - Ensure boxscore data is available in game data
   - Check that `extract_boxscore_stats()` is working correctly

2. **Incorrect point calculations**
   - Verify scoring system configuration
   - Check that all required stats are present

3. **Export failures**
   - Ensure data exists for the specified date
   - Check file permissions for export directory

### **Debug Mode**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

collector = DailyStatcastCollector()
# Detailed logging will show calculation steps
```

## Performance Considerations

- **Fantasy points calculation** adds minimal overhead to collection
- **Game summaries** are generated once per game, not per at-bat
- **Export functions** can be run independently of collection
- **Memory usage** scales linearly with number of players per game

## Future Enhancements

- **Win probability added (WPA)** integration
- **Advanced metrics** (wOBA, xFIP) for enhanced projections
- **Historical fantasy points** analysis and trends
- **Real-time fantasy points** streaming during live games
- **Custom scoring systems** for other DFS platforms

---

## Quick Start Checklist

- [ ] Install enhanced Statcast collector
- [ ] Run test suite: `python test/test_fantasy_points.py`
- [ ] Collect sample data: `python src/statcast/collector.py --date 2025-08-10 --auto-export`
- [ ] Verify fantasy points in output files
- [ ] Export in preferred format: `--export-format csv`
- [ ] Integrate with existing analysis pipeline

For questions or issues, check the test output and ensure all dependencies are properly installed.