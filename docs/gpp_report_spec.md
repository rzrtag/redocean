# GPP Dynamic Report Specification

## Overview
Markdown-based reports for GPP dynamic analysis with optimized formatting for readability and concise presentation.

## File Naming Convention
- **Date Format**: `MMDD` (e.g., `0814` for August 14th)
- **Report Type**: `gpp_report_MMDD_HHMM.md`
- **Example**: `gpp_report_0814_1430.md`

## Codebase Organization
```
src/ml_agentic/
├── core/
│   ├── gpp_reporter.py      # Main reporter
│   └── stack_analyzer.py    # Stack analysis logic
├── reports/
│   ├── markdown.py          # Markdown generation
│   └── formatter.py         # Data formatting
└── utils/
    ├── dates.py             # Date utilities
    └── abbrev.py            # Abbreviation mapping
```

## Report Structure

### 1. Header Section
```markdown
# GPP Dynamic Report - 0814 14:30

**Contest**: FanDuel Main Slate
**Entries**: 2,400
**Last Update**: 2025-08-14 14:30:00
**Status**: Live Analysis
```

### 2. Executive Summary
```markdown
## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| Top Stacks | 5 identified |
| High Leverage | 3 opportunities |
| Avg Stack Adj | +22.5% |
| Top Pitchers | 3 recommended |
| Avg Pitcher Adj | +15.6% |
```

### 3. Stack Analysis (Primary Focus)

#### 3.1 Top Stack Opportunities
```markdown
## 🏆 Top Stack Opportunities

| Team | Size | Own% | Leverage | Adj% | Rec |
|------|------|------|----------|------|-----|
| MIA | 4 | 5.7 | 1.00 | +22.5 | ⭐⭐⭐ |
| WSH | 3 | 4.7 | 1.00 | +22.5 | ⭐⭐⭐ |
| ATL | 5 | 6.2 | 0.98 | +22.5 | ⭐⭐ |
| MIN | 4 | 7.1 | 0.89 | +22.5 | ⭐⭐ |
| CLE | 5 | 8.9 | 0.69 | +22.5 | ⭐ |
```

#### 3.2 Stack Details
```markdown
## 📋 Stack Details

### MIA Stack (4-man)
- **Players**: Edwards, Stowers, Pauley, +1
- **Ownership**: 5.7% avg
- **BBE Quality**: 0.85
- **Momentum**: +0.12
- **Leverage**: 1.00 (Perfect)
- **Adjustment**: +22.5%
- **Reasoning**: Low ownership with high BBE quality

### WSH Stack (3-man)
- **Players**: DeJong, Crews, Bell
- **Ownership**: 4.7% avg
- **BBE Quality**: 0.82
- **Momentum**: +0.08
- **Leverage**: 1.00 (Perfect)
- **Adjustment**: +22.5%
- **Reasoning**: Contrarian play with strong metrics
```

### 4. Pitcher Analysis (Secondary Focus)

#### 4.1 Top Pitcher Recommendations
```markdown
## ⚾ Top Pitcher Recommendations

| Name | Team | Opp | Own% | Adj% | Rec |
|------|------|-----|------|------|-----|
| Skubal | DET | MIN | 20.7 | +15.6 | ⭐⭐ |
| Luzardo | PHI | WSH | 19.0 | +15.6 | ⭐⭐ |
| Bibee | CLE | MIA | 18.0 | +15.6 | ⭐ |
| Senga | NYM | ATL | 14.7 | +15.6 | ⭐⭐⭐ |
| Cabrera | MIA | CLE | 10.9 | +15.6 | ⭐⭐⭐ |
```

#### 4.2 Pitcher Details
```markdown
## 📋 Pitcher Details

### Tarik Skubal (DET vs MIN)
- **Ownership**: 20.7%
- **BBE Quality**: 0.78
- **Momentum**: +0.05
- **Adjustment**: +15.6%
- **Recommendation**: QUALITY_PLAY
- **Reasoning**: High quality despite moderate ownership

### Kodai Senga (NYM vs ATL)
- **Ownership**: 14.7%
- **BBE Quality**: 0.82
- **Momentum**: +0.03
- **Adjustment**: +15.6%
- **Recommendation**: STRONG_PLAY
- **Reasoning**: Low ownership with high quality
```

### 5. Leverage Insights

```markdown
## 🚀 Leverage Insights

### High Leverage Stacks
- **MIA (4/5-man)**: Perfect leverage (1.00) with 5.7% ownership
- **WSH (3/4/5-man)**: Perfect leverage (1.00) with 4.7% ownership
- **ATL (5-man)**: Near perfect leverage (0.98) with 6.2% ownership

### High Adjustment Pitchers
- **9 pitchers** with >10% adjustments
- **Top 3**: Skubal, Luzardo, Bibee
- **Average adjustment**: +15.6%

### Stack Opportunities
- **10 identified** opportunities
- **Average leverage**: 0.85
- **Average adjustment**: +22.5%
```

### 6. Contest Analysis

```markdown
## 🏆 Contest Analysis

| Metric | Value |
|--------|-------|
| Total Entries | 2,400 |
| Prize Pool | $10,000 |
| Cash Rate | 23.1% |
| Field Status | Live |
| Top Stack Type | 4|3 (2,007 lineups) |
| Avg Stack Size | 4.2 |

### Field Composition
- **4-man stacks**: 5,393 total
- **3-man stacks**: 2,623 total
- **2-man stacks**: 3,341 total
```

### 7. Data Quality

```markdown
## 📈 Data Quality

| Source | Records | Status |
|--------|---------|--------|
| SaberSim Players | 689 | ✅ |
| Batter Ownership | 90 | ✅ |
| Pitcher Ownership | 9 | ✅ |
| Contest Sims | Live | ✅ |
| Field Lineups | Live | ✅ |
| Last Update | 14:30:00 | ✅ |
```

### 8. Recommendations

```markdown
## 💡 Actionable Recommendations

### Primary Plays
1. **MIA 4-man stack** - Perfect leverage, low ownership
2. **WSH 3-man stack** - Contrarian with strong metrics
3. **Kodai Senga** - Low ownership, high quality

### Secondary Plays
1. **ATL 5-man stack** - Near perfect leverage
2. **Tarik Skubal** - Quality play despite ownership
3. **MIN 4-man stack** - Good leverage opportunity

### Avoid
- High ownership stacks (>15%)
- Low BBE quality players
- Over-exposed pitchers
```

## Formatting Rules

### 1. Abbreviations
- **Team Names**: Use 3-letter codes (MIA, WSH, ATL)
- **Positions**: P (Pitcher), STACK (Stack)
- **Recommendations**: ⭐⭐⭐ (STRONG), ⭐⭐ (GOOD), ⭐ (AVOID)

### 2. Number Formatting
- **Percentages**: Round to 2 decimals (22.50%)
- **Decimals**: Round to 2 places (0.85)
- **Large Numbers**: Use commas (2,400)

### 3. Table Optimization
- **Max Width**: 6 columns per table
- **Split Large Tables**: Use multiple smaller tables
- **Key Metrics**: Bold important values
- **Alignment**: Right-align numbers, left-align text

### 4. Section Organization
- **Primary Focus**: Stack analysis first
- **Secondary Focus**: Pitcher analysis second
- **Supporting Data**: Leverage, contest, quality last
- **Action Items**: Recommendations at end

### 5. Visual Hierarchy
- **H1**: Report title
- **H2**: Major sections
- **H3**: Subsections
- **Bold**: Key metrics and recommendations
- **Emojis**: Section indicators

## Implementation Notes

### Functional Programming
- **Pure functions** for data transformation
- **Immutable data structures** where possible
- **Composition over inheritance**
- **Short, focused functions**

### File Organization
- **Short filenames** preferred
- **Functional organization** by capability
- **Minimal folder depth** (max 3 levels)
- **Clear separation** of concerns

### Output Organization
- **Date-based folders**: `reports/0814/`
- **Time-stamped files**: `gpp_report_0814_1430.md`
- **Version control**: Git-friendly naming
- **Archive structure**: `reports/archive/MMDD/`

### Performance Considerations
- **Lazy evaluation** for large datasets
- **Caching** for repeated calculations
- **Streaming** for real-time updates
- **Efficient data structures** for lookups
