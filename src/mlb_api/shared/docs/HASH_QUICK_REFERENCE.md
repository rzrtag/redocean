# Hash System Quick Reference

## 🚀 Quick Start

### 1. Create Your Collector
```python
from ..shared.incremental_updater import MLBAPICollector

class YourCollector(MLBAPICollector):
    def __init__(self, max_workers: int = 5, request_delay: float = 0.05):
        super().__init__("your_collector_name", str(self.config.base_data_path))
        self.set_performance_settings(max_workers, request_delay)

    def collect_data(self) -> Union[Dict, List]:
        # Your data collection logic here
        data = self._collect_your_data()

        # Add metadata (timestamps auto-excluded from hash)
        data['metadata'] = {
            'collection_timestamp': datetime.now().isoformat(),  # ✅ Excluded from hash
            'collector_name': 'your_collector_name',             # ✅ Included in hash
            'version': '1.0.0'                                   # ✅ Included in hash
        }

        return data
```

### 2. Create Runner
```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from your_collector import YourCollector

def main():
    collector = YourCollector()
    was_updated, data, reason = collector.run_collection()

    if was_updated:
        print(f"✅ Updated: {reason}")
    else:
        print(f"ℹ️  No update: {reason}")

if __name__ == "__main__":
    main()
```

## 📁 Directory Structure
```
src/mlb_api/your_collector/
├── __init__.py
├── your_collector.py
└── run_your_collector.py

_data/mlb_api_2025/your_collector/
├── data/your_collector.json    # Single output file
├── hash/                       # Hash tracking
└── cache/                      # Temporary files
```

## ⚡ Performance Settings
```python
# Conservative (respectful to API)
collector = YourCollector(max_workers=3, request_delay=0.1)

# Default (balanced)
collector = YourCollector(max_workers=5, request_delay=0.05)

# Aggressive (fast collection)
collector = YourCollector(max_workers=8, request_delay=0.02)
```

## 🔍 Hash Behavior

### ✅ What Triggers Updates
- Player ID changes
- Team roster changes
- Game data changes
- Structure changes (count, relationships)

### ❌ What Doesn't Trigger Updates
- Collection timestamps
- Performance metrics
- Player order changes
- Formatting differences

## 🧪 Testing Commands
```bash
# First run
python run_your_collector.py

# Check status
python run_your_collector.py --status

# Force update
python run_your_collector.py --force

# Custom performance
python run_your_collector.py --workers 8 --delay 0.02
```

## 🚨 Common Issues

### Hash Always Changes
- Check for timestamp fields in data
- Verify API isn't returning different data
- Ensure stable JSON serialization

### No Updates Detected
- Verify hash files exist
- Check data structure format
- Ensure `collect_data()` implemented

## 📋 Checklist
- [ ] Extend `MLBAPICollector`
- [ ] Implement `collect_data()` method
- [ ] Add metadata (timestamps will be auto-excluded)
- [ ] Create runner script
- [ ] Test first run (should collect data)
- [ ] Test second run (should skip if no changes)
- [ ] Test force update (should always collect)

## 🎯 Best Practices
1. **Focus on stable identifiers** (IDs, names, core data)
2. **Exclude timestamps** (handled automatically)
3. **Use consistent data structure** (same fields, same order)
4. **Test hash behavior** (verify incremental updates work)
5. **Monitor performance** (adjust workers/delay as needed)

---
**Need more details?** See `HASH_SYSTEM_GUIDE.md` for comprehensive documentation.
