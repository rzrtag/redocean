# SaberSim HAR Extraction - Simplified

Clean, focused HAR extraction for SaberSim data with automatic site detection and table generation.

## Quick Start

```bash
# Extract from HAR file
python src/sabersim/atoms/extractors/extract.py /path/to/app.sabersim.com

# Create tables from extracted data
python src/sabersim/atoms/extractors/tables.py _data/sabersim_2025/fanduel/0812_main_slate/atoms_output/atoms

# Check status
python src/sabersim/atoms/extractors/status.py
```

## File Structure

```
src/sabersim/
├── extract.py              # Main extraction script
├── tables.py               # Table generation script
├── status.py               # Status and summary script
├── atoms/
│   └── extractors/
│       ├── extractor.py    # Core extraction logic
│       └── __init__.py     # Package initialization
└── tables/                 # Table analysis modules
```

## Data Output

All extracted data goes to `_data/sabersim_2025/` with this clean structure:

```
_data/sabersim_2025/
├── draftkings/
│   └── 0812_main_slate/   # Date + Slate (MMDD_slate)
│       └── atoms_output/
│           ├── atoms/      # All extracted atoms
│           ├── metadata/   # Extraction metadata
│           └── tables/     # Generated tables
└── fanduel/
    └── ...                 # Same structure for FanDuel
```

## Features

- ✅ **Automatic site detection** (DraftKings/FanDuel)
- ✅ **Dynamic slate detection** (main_slate, night_slate)
- ✅ **Contest bucket grouping** for organized data
- ✅ **Multiple atom types** (contests, lineups, portfolios)
- ✅ **JSON tables** for easy analysis
- ✅ **Metadata tracking** and lineage

## Atom Types

- `contest_information` - Contest details and settings
- `lineup_data` - Lineup projections and stacks
- `portfolio_optimization` - Portfolio data
- `progress_tracking` - Progress information

## Usage Examples

### Extract from specific HAR file
```bash
python src/sabersim/atoms/extractors/extract.py ../../dfs/app.sabersim.com
```

### Extract to custom output directory
```bash
python src/sabersim/atoms/extractors/extract.py ../../dfs/app.sabersim.com ./custom_output
```

### Generate tables from existing extraction
```bash
python src/sabersim/atoms/extractors/tables.py _data/sabersim_2025/fanduel/0812_main_slate/atoms_output/atoms
```

### Check system status
```bash
python src/sabersim/status.py
```

## Output Files

After extraction and table generation, you'll have:

- **Raw atoms**: JSON files with extracted data
- **JSON tables**: Structured data for programmatic use
- **Metadata**: Extraction history and lineage tracking

## Next Steps

1. **Analyze contest data** for GPP vs Cash strategies
2. **Review lineup projections** and stack compositions
3. **Export to Excel** for further analysis
4. **Run additional HAR files** for different dates/sites
