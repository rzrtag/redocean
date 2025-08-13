# Complete SaberSim HAR Extraction System Documentation

## Overview

A comprehensive, intelligent HAR extraction system for SaberSim data with automatic site detection, dynamic slate detection, and clean data organization.

## What We Built

### 🎯 **Core Features**
- **Automatic Site Detection** - DraftKings vs FanDuel
- **Dynamic Slate Detection** - main_slate, night_slate, early_slate, etc.
- **Smart Data Organization** - Flat, logical directory structure
- **Comprehensive Extraction** - All major atom types
- **Clean Output** - JSON-only tables, no clutter

### 🏗️ **Architecture**
```
src/sabersim/atoms/extractors/     # All source code
├── extract.py                      # Main extraction script
├── tables.py                       # Table generation script
├── status.py                       # Status and summary script
├── extractor.py                    # Core extraction logic
└── __init__.py                     # Package initialization
```

## Evolution & Improvements

### **Phase 1: Initial Cleanup**
- ✅ Removed 7 antiquated files
- ✅ Consolidated working functionality
- ✅ Simplified file names (short, clear)
- ✅ Fixed data directory paths

**Before (Messy):**
```
src/sabersim/atoms/extractors/
├── mlb_atom_extractor.py          # Working but long name
├── ingest_har.py                  # Antiquated
├── process_har.py                 # Antiquated
├── process_har_auto.py            # Antiquated
├── process_fanduel_har.py         # Antiquated
├── fix_contest_mapping.py         # Antiquated
├── run_extraction.py              # Antiquated
├── site_atom_extractor.py         # Antiquated
└── __init__.py
```

**After (Clean):**
```
src/sabersim/atoms/extractors/
├── extract.py                     # Main extraction
├── tables.py                      # Table generation
├── status.py                      # Status check
├── extractor.py                   # Core logic
└── __init__.py                    # Package init
```

### **Phase 2: Site Detection Fixes**
- ✅ **Fixed site detection** - Now correctly identifies FanDuel vs DraftKings
- ✅ Enhanced detection to check response content for site indicators
- ✅ Increased coverage from 50 to 100 entries for better detection

**Result:**
- Before: `🏠 Detected site: draftkings` ❌
- After: `🏠 Detected site: fanduel` ✅

### **Phase 3: Output Cleanup**
- ✅ **Removed CSV output** - No more unnecessary CSV files
- ✅ **Removed archive functionality** - Simplified output structure
- ✅ **Removed pandas dependency** - Cleaner, faster table generation

**Result:**
- Before: Generated both `.csv` and `.json` files
- After: Only `.json` files generated (cleaner, faster)

### **Phase 4: Directory Structure Flattening**
- ✅ **Combined slate and date** - Single date directory instead of date/slate
- ✅ **Consolidated metadata** - Single metadata directory instead of duplicates
- ✅ **Simplified paths** - Much cleaner and easier to navigate

**Before (Too Nested):**
```
_data/sabersim_2025/
├── fanduel/
│   └── 0812/                          # Date
│       └── main_slate/                # Slate (unnecessary)
│           └── atoms_output/          # Too many levels
│               ├── atoms/             # Main atoms
│               ├── metadata/          # Main metadata
│               ├── tables/            # Tables
│               └── by_contest/        # Contest-specific (unnecessary)
│                   └── flagship_mid_entry/
│                       ├── atoms/     # Duplicate atoms dir
│                       └── metadata/  # Duplicate metadata dir
```

**After (Clean and Flat):**
```
_data/sabersim_2025/
├── fanduel/
│   └── 0812_main_slate/              # Date + Slate (MMDD_slate)
│       └── atoms_output/              # Single output directory
│           ├── atoms/                 # ALL atoms in one place
│           ├── metadata/              # Single metadata directory
│           └── tables/                # Generated tables
```

### **Phase 5: Dynamic Slate Detection**
- ✅ **Implemented dynamic slate detection** - Automatically detects slate from HAR content
- ✅ **Created slate-appended paths** - `/fanduel/0812_main_slate` format
- ✅ **Moved all source code** to `/src/sabersim/atoms/extractors/`

**Slate Detection:**
- Supports: `main_slate`, `night_slate`, `early_slate`, `afternoon_slate`, `late_slate`
- Checks URL, body content, and response content for slate indicators
- Creates descriptive paths: `0812_main_slate`, `0812_night_slate`, etc.

## Final System Structure

### **Source Code Organization**
```
src/sabersim/atoms/extractors/
├── extract.py              # Main extraction script
├── tables.py               # Table generation script
├── status.py               # Status and summary script
├── extractor.py            # Core extraction logic
└── __init__.py             # Package initialization
```

### **Data Output Structure**
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

## Key Features

### 1. **Dynamic Slate Detection** 🎯
- Automatically detects slate from HAR content
- Supports: `main_slate`, `night_slate`, `early_slate`, `afternoon_slate`, `late_slate`
- Creates descriptive paths: `0812_main_slate`, `0812_night_slate`, etc.

### 2. **Smart Site Detection** 🏠
- Automatically identifies DraftKings vs FanDuel
- Checks URL parameters, body content, and response content
- Handles both explicit and implicit site indicators

### 3. **Clean Data Organization** 📁
- All atoms in single `atoms/` directory
- Single metadata directory (no duplicates)
- JSON-only tables (no CSV clutter)
- Flat, logical structure

### 4. **Comprehensive Extraction** 🔍
- Multiple atom types: contests, lineups, portfolios, progress
- Contest bucket detection and grouping
- Automatic metadata tracking and lineage

## Usage Examples

### **Basic Extraction**
```bash
# Extract from HAR file (auto-detects site and slate)
python src/sabersim/atoms/extractors/extract.py /path/to/app.sabersim.com
```

### **Generate Tables**
```bash
# Generate tables from extracted data
python src/sabersim/atoms/extractors/tables.py _data/sabersim_2025/fanduel/0812_main_slate/atoms_output/atoms
```

### **Check Status**
```bash
# Check system status and latest extraction
python src/sabersim/atoms/extractors/status.py
```

### **Custom Output Directory**
```bash
# Extract to custom output directory
python src/sabersim/atoms/extractors/extract.py /path/to/app.sabersim.com ./custom_output
```

## Example Output Paths

### **FanDuel Main Slate**
```
_data/sabersim_2025/fanduel/0812_main_slate/atoms_output/
├── atoms/
│   ├── build_optimization.json
│   ├── lineup_data.json
│   ├── contest_information.json
│   ├── portfolio_optimization_latest.json
│   ├── progress_tracking.json
│   ├── contest_simulations_flagship_mid_entry.json
│   └── field_lineups_flagship_mid_entry.json
├── metadata/
│   ├── atom_registry.json
│   ├── endpoint_mapping.json
│   └── extraction_summary.json
└── tables/
    ├── contest_summary.json
    ├── lineup_summary.json
    ├── portfolio_data.json
    ├── portfolio_summary.json
    ├── progress_data.json
    └── master_summary.json
```

### **DraftKings Night Slate**
```
_data/sabersim_2025/draftkings/0812_night_slate/atoms_output/
├── atoms/
├── metadata/
└── tables/
```

## What Makes This System Great

🚀 **Automatic Detection** - No manual configuration needed
📁 **Clean Organization** - Logical, flat structure
🔍 **Comprehensive Coverage** - All major atom types
💾 **Efficient Storage** - No duplicate data or unnecessary files
📊 **Rich Metadata** - Full extraction history and lineage
🎯 **Smart Grouping** - Contest buckets and site separation

## Benefits of the New Structure

### **For Developers**
- **Clean codebase** - No antiquated files
- **Logical organization** - All extractor code in one place
- **Easy maintenance** - Simple, focused scripts

### **For Users**
- **Simple commands** - Easy to remember and use
- **Automatic detection** - No manual configuration
- **Clear output** - Logical directory structure

### **For Data Analysis**
- **Organized data** - Easy to find and analyze
- **Rich metadata** - Full extraction history
- **Clean tables** - JSON format for programmatic use

## Result

**Perfect extraction system** that:
- ✅ **Automatically detects** site and slate
- ✅ **Creates descriptive paths** like `0812_main_slate`
- ✅ **Organizes data logically** without over-nesting
- ✅ **Maintains all functionality** while being cleaner
- ✅ **Is easy to use** with simple commands
- ✅ **Scales well** for different sites and slates

## Next Steps

1. **Analyze contest data** for GPP vs Cash game strategies
2. **Review lineup projections** and stack compositions
3. **Export data to Excel** for further analysis
4. **Run additional HAR files** for different dates/sites
5. **Extend slate detection** for more slate types if needed

---

The system now provides **intelligent, automatic data organization** that's both powerful and easy to use! 🎉

*Last Updated: August 12, 2025*
