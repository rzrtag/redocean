# Fangraphs API Data Collection System

Scalable data collection from Fangraphs API endpoints with team-based organization and hash-based incremental updates.

## 🏗️ **Architecture Overview**

### **Data Organization**
```
_data/fg_api_2025/
├── collectors/
│   └── roster/
│       ├── 2025_TEX_MLB.json
│       ├── 2025_SEA_MLB.json
│       └── 2025_HOU_MLB.json
├── hash/
│   └── roster/
│       ├── 2025_TEX_MLB_hash.json
│       ├── 2025_SEA_MLB_hash.json
│       └── 2025_HOU_MLB_hash.json
└── tests/
```

### **File Naming Convention**
- **Data Files**: `{YEAR}_{TEAM}_{LEVEL}.json`
- **Hash Files**: `{YEAR}_{TEAM}_{LEVEL}_hash.json`
- **Example**: `2025_TEX_MLB.json` (Texas Rangers MLB roster)

## 🚀 **Current Collectors**

### **1. Roster Collector** ✅
- **Endpoint**: `https://www.fangraphs.com/api/depth-charts/roster`
- **Data**: Complete roster with stats, projections, fantasy points
- **Organization**: Team-based files with all players (MLB + minors)
- **Features**: Hash-based incremental updates, progress monitoring

## 📊 **Data Structure**

### **Roster Data Includes:**
- **Player Info**: Name, position, age, handedness
- **Team Info**: Service time, options, acquisition details
- **Stats**: Batting (AVG, OBP, SLG, wRC+, WAR) and Pitching (ERA, K/9, WAR)
- **Projections**: Current year and future projections
- **Fantasy**: Daily fantasy points and rankings
- **Advanced**: Barrel%, HardHit%, pitch mix data

## 🛠️ **Usage**

### **Run Collection**
```bash
# Collect all MLB teams
python src/fg_api/pipeline/run_roster_collector.py --workers 12

# Collect specific teams
python src/fg_api/pipeline/run_roster_collector.py --teams TEX SEA HOU

# Force update (ignore hash checks)
python src/fg_api/pipeline/run_roster_collector.py --force
```

### **Check Status**
```bash
# Show collection status
python src/fg_api/pipeline/run_roster_collector.py --status

# Show team summary
python src/fg_api/pipeline/run_roster_collector.py --team-summary TEX
```

## ⚙️ **Performance Profiles**

- **conservative**: 3 workers, 0.5s delay
- **balanced**: 6 workers, 0.2s delay
- **aggressive**: 10 workers, 0.1s delay
- **ultra_aggressive**: 15 workers, 0.05s delay

## 🔄 **Incremental Updates**

- **Hash-based**: Compares data content to detect changes
- **Team-level**: Each team updated independently
- **Smart**: Only updates when data actually changes
- **Progress tracking**: Real-time ETA and status updates

## 📈 **Validation & Monitoring**

- **Data integrity**: Hash verification for each team
- **Progress monitoring**: Real-time collection status
- **Error handling**: Graceful failure recovery
- **Performance metrics**: Collection speed and success rates

## 🎯 **Future Endpoints**

The system is designed to easily add more Fangraphs endpoints:

- **Projections API**: Season-long projections
- **Leaderboards API**: Statistical leaderboards
- **Game Logs API**: Individual game performance
- **Advanced Stats API**: Detailed advanced metrics

## 🔧 **Configuration**

Team mappings, performance settings, and API configuration in `src/fg_api/shared/config.py`.

## 📝 **Notes**

- **Rate limiting**: Built-in delays to respect Fangraphs servers
- **Error recovery**: Automatic retry logic for failed requests
- **Data consistency**: Hash-based validation ensures data integrity
- **Scalability**: Thread pool execution for concurrent collection
