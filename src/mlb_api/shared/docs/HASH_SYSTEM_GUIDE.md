# MLB API Hash System Guide

## Overview

The MLB API Hash System provides intelligent incremental updates for data collectors. It ensures that:
- **Only changed data is downloaded** - No unnecessary API calls
- **Efficient caching** - Hash-based change detection
- **Clean file management** - Single output files, automatic cleanup
- **Pipeline ready** - Consistent interface across all collectors

## How It Works

### 1. Hash Computation
The system computes SHA-256 hashes of collected data, but intelligently excludes timestamp-dependent fields:

```python
def _compute_hash(self, data: Union[str, bytes, Dict, List]) -> str:
    if isinstance(data, dict):
        stable_data = data.copy()
        # Remove timestamp-dependent fields for stable hashing
        if 'metadata' in stable_data:
            metadata = stable_data['metadata'].copy()
            metadata.pop('collection_timestamp', None)
            metadata.pop('performance', None)
            stable_data['metadata'] = metadata

        # Special handling for roster data
        if 'rosters' in stable_data and 'teams' in stable_data:
            # Focus on essential, stable identifiers
            stable_data = self._create_stable_roster_hash(stable_data)

    return hashlib.sha256(json.dumps(stable_data, sort_keys=True).encode()).hexdigest()
```

### 2. Change Detection
The system compares current hash with previous hash to determine if updates are needed:

```python
def check_for_updates(self, data: Union[Dict, List], data_key: str = "data") -> Tuple[bool, Optional[str]]:
    current_hash = self._compute_hash(data)
    previous_hash = self._load_previous_hash()

    if previous_hash is None:
        return True, "No previous hash found - first run"

    if current_hash == previous_hash:
        return False, "Hash unchanged - no updates needed"

    return True, f"Hash changed: {previous_hash[:8]} -> {current_hash[:8]}"
```

### 3. File Management
- **Single output file**: `{collector_name}.json` (no timestamps)
- **Automatic cleanup**: Old timestamped files are removed
- **Hash tracking**: `current_hash.json`, `previous_hash.json`, `update_log.json`

## Implementation Guide

### Step 1: Extend MLBAPICollector

```python
from ..shared.incremental_updater import MLBAPICollector

class YourCollector(MLBAPICollector):
    def __init__(self, max_workers: int = 5, request_delay: float = 0.05):
        super().__init__("your_collector_name", str(self.config.base_data_path))
        self.set_performance_settings(max_workers, request_delay)

    def collect_data(self) -> Union[Dict, List]:
        """Implement this method to collect your data."""
        # Your data collection logic here
        data = self._collect_your_data()

        # Add metadata (timestamps will be excluded from hash)
        data['metadata'] = {
            'collection_timestamp': datetime.now().isoformat(),
            'collector_name': 'your_collector_name',
            'version': '1.0.0',
            # Add other metadata as needed
        }

        return data
```

### Step 2: Create Runner Script

```python
#!/usr/bin/env python3
"""Your Collector Runner"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from your_collector import YourCollector

def main():
    collector = YourCollector()

    # Run collection
    was_updated, data, reason = collector.run_collection()

    if was_updated:
        print(f"✅ Data updated: {reason}")
    else:
        print(f"ℹ️  No update needed: {reason}")

if __name__ == "__main__":
    main()
```

### Step 3: Directory Structure

```
src/mlb_api/your_collector/
├── __init__.py
├── your_collector.py      # Main collector class
└── run_your_collector.py  # Runner script

_data/mlb_api_2025/your_collector/
├── data/
│   └── your_collector.json    # Single output file
├── hash/
│   ├── current_hash.json      # Current hash
│   ├── previous_hash.json     # Previous hash
│   └── update_log.json        # Update history
└── cache/                     # Temporary files
```

## Hash Optimization Best Practices

### 1. Exclude Timestamp Fields
Always exclude these fields from hash computation:
- `collection_timestamp`
- `performance` metrics
- `request_id` or `session_id`
- Any other time-dependent fields

### 2. Focus on Stable Identifiers
For data that should trigger updates, focus on:
- **IDs**: Player IDs, team IDs, game IDs
- **Core data**: Names, positions, statistics
- **Structure**: Number of items, relationships

### 3. Avoid Hash Changes For:
- **Order changes**: Player order in roster, team order
- **Formatting**: Whitespace, field order
- **Metadata**: Collection time, performance metrics

## Example: Roster Collector Implementation

The `ActiveRostersCollector` demonstrates optimal implementation:

```python
class ActiveRostersCollector(MLBAPICollector):
    def collect_data(self) -> Union[Dict, List]:
        # Collect roster data
        roster_data = self._collect_all_rosters()

        # Add metadata (timestamps excluded from hash)
        roster_data['metadata'] = {
            'collection_timestamp': datetime.now().isoformat(),  # Excluded from hash
            'season': 2025,                                     # Included in hash
            'total_teams': 30,                                  # Included in hash
            'total_players': 780,                               # Included in hash
            'collector_version': '1.0.0',                       # Included in hash
            'collector_name': 'active_rosters'                  # Included in hash
        }

        return roster_data
```

## Hash File Formats

### current_hash.json
```json
{
  "data": "9fba5c06849374ddaafa973ceea779a707df6d2248282f4712855f7de1d0c353",
  "timestamp": "2025-08-12T21:50:12.628111",
  "collector": "active_rosters",
  "data_size": 324522
}
```

### update_log.json
```json
{
  "updates": [
    {
      "timestamp": "2025-08-12T21:50:12.628111",
      "action": "hash_updated",
      "collector": "active_rosters",
      "data_key": "data",
      "hash": "9fba5c06849374ddaafa973ceea779a707df6d2248282f4712855f7de1d0c353"
    }
  ]
}
```

## Performance Tuning

### Worker Configuration
```python
collector = YourCollector(
    max_workers=8,        # Concurrent API calls
    request_delay=0.02    # Delay between requests (seconds)
)
```

### Rate Limiting
- **Default**: 5 workers, 0.05s delay
- **Aggressive**: 8 workers, 0.02s delay
- **Conservative**: 3 workers, 0.1s delay

## Troubleshooting

### Hash Always Changes
1. Check if timestamp fields are included in data
2. Verify API isn't returning different data each time
3. Ensure stable field ordering in JSON serialization

### No Updates Detected
1. Verify hash files exist and are readable
2. Check if data structure matches expected format
3. Ensure `collect_data()` method is implemented correctly

### Performance Issues
1. Reduce `max_workers` if API rate limits are hit
2. Increase `request_delay` for more conservative API usage
3. Monitor API response times and adjust accordingly

## Testing Your Collector

### 1. First Run
```bash
python run_your_collector.py
# Should show: "First run for your_collector: No previous hash found"
```

### 2. Second Run (No Changes)
```bash
python run_your_collector.py
# Should show: "No updates needed for your_collector: Hash unchanged"
```

### 3. Force Update
```bash
python run_your_collector.py --force
# Should force collection regardless of hash
```

## Integration with Pipeline

### Command Line Usage
```bash
# From project root
python src/mlb_api/your_collector/run_your_collector.py

# With custom settings
python src/mlb_api/your_collector/run_your_collector.py --workers 8 --delay 0.02
```

### Pipeline Script
```bash
#!/bin/bash
# Update active rosters
python src/mlb_api/rosters/run_active_rosters.py

# Update your data
python src/mlb_api/your_collector/run_your_collector.py

# Continue with rest of pipeline...
```

## Summary

The hash system provides:
- ✅ **Efficient updates** - Only when data actually changes
- ✅ **Clean file management** - Single output files, no clutter
- ✅ **Performance optimization** - Configurable workers and rate limiting
- ✅ **Pipeline integration** - Consistent interface across collectors
- ✅ **Hash verification** - Ensures data integrity

Follow this guide to implement efficient, hash-based incremental updates for your MLB API collectors! 🚀
