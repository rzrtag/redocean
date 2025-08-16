# Agentic Directory Structure & Organization

## Overview
Flat directory structure with longer filenames for optimal organization and easy navigation.

## Directory Structure

```
/mnt/storage_fast/workspaces/red_ocean/
├── _data/
│   ├── agentic_2025/                    # Agentic data directory
│   │   ├── 0814/                        # August 14th reports
│   │   │   ├── gpp_report_0814_1430.md  # 2:30 PM report
│   │   │   ├── gpp_report_0814_1500.md  # 3:00 PM report
│   │   │   └── gpp_report_0814_1530.md  # 3:30 PM report
│   │   ├── 0815/                        # August 15th reports
│   │   │   ├── gpp_report_0815_0051.md  # 12:51 AM report
│   │   │   └── gpp_report_0815_0100.md  # 1:00 AM report
│   │   └── 0816/                        # August 16th reports
│   │       └── gpp_report_0816_0900.md  # 9:00 AM report
│   ├── sabersim_2025/                   # SaberSim data (existing)
│   └── mlb_api_2025/                    # MLB API data (existing)
├── src/
│   └── ml_agentic/                      # Agentic source code
│       ├── core/
│       │   ├── gpp_reporter.py          # Main reporter
│       │   └── gpp_dynamic_reporter.py  # Dynamic analysis
│       ├── reports/
│       │   └── markdown.py              # Markdown generation
│       ├── utils/
│       │   ├── dates.py                 # Date utilities
│       │   └── abbrev.py                # Abbreviation utilities
│       └── markdown_demo.py             # Demo script
└── docs/
    ├── gpp_report_spec.md               # Report specification
    └── agentic_directory_structure.md   # This file
```

## File Naming Convention

### Report Files
- **Format**: `gpp_report_MMDD_HHMM.md`
- **Example**: `gpp_report_0815_0051.md`
- **Meaning**: GPP report for August 15th at 00:51

### Date Format
- **MMDD**: Month and day (0815 = August 15th)
- **HHMM**: Hour and minute in 24-hour format (0051 = 12:51 AM)

### Benefits
- **Chronological**: Natural sorting by date/time
- **Descriptive**: Clear indication of content and timing
- **Git-friendly**: No special characters or spaces
- **Scalable**: Can handle thousands of reports efficiently

## Organization Principles

### 1. Flat Structure
- **No deep nesting**: Maximum 2-3 levels deep
- **Easy navigation**: Quick access to any report
- **Clear hierarchy**: Date-based organization

### 2. Longer Filenames
- **Descriptive names**: Include date, time, and type
- **Self-documenting**: No need for additional metadata files
- **Searchable**: Easy to find specific reports

### 3. Date-Based Organization
- **Daily folders**: One folder per day (0814, 0815, 0816)
- **Chronological order**: Natural time progression
- **Easy archiving**: Can archive entire days

## Report Content Structure

### File Size
- **Typical size**: 5-10 KB per report
- **Content**: ~150-200 lines of markdown
- **Compression**: Can be gzipped for storage efficiency

### Report Sections
1. **Header**: Title, contest info, timestamp
2. **Executive Summary**: Key metrics table
3. **Stack Analysis**: Top opportunities and details
4. **Pitcher Analysis**: Recommendations and details
5. **Leverage Insights**: High-leverage opportunities
6. **Contest Analysis**: Field composition and stats
7. **Data Quality**: Source status and validation
8. **Recommendations**: Actionable insights

## Management Features

### Report Listing
```python
reporter.list_reports()
# Returns: List of all reports with metadata
```

### Report Reading
```python
reporter.read_report("gpp_report_0815_0051.md")
# Returns: Full markdown content
```

### Cleanup
```python
reporter.cleanup_old_reports(days_to_keep=7)
# Deletes reports older than 7 days
```

### Summary
```python
reporter.get_report_summary()
# Returns: Key metrics without full content
```

## Scalability Considerations

### Storage
- **Daily volume**: ~24-48 reports per day
- **Monthly volume**: ~720-1440 reports per month
- **Storage per report**: ~5-10 KB
- **Monthly storage**: ~3.5-14 MB

### Performance
- **Fast access**: No deep folder traversal
- **Efficient listing**: Direct file enumeration
- **Quick search**: Filename-based filtering
- **Easy backup**: Simple directory copying

### Archiving
- **Daily archives**: Compress entire day folders
- **Monthly archives**: Archive older months
- **Retention policy**: Configurable cleanup schedules

## Integration Points

### SaberSim Integration
- **Data source**: `_data/sabersim_2025/`
- **Real-time updates**: Dynamic report generation
- **CSV export**: For SaberSim upload

### MLB API Integration
- **Rolling windows**: `_data/mlb_api_2025/`
- **BBE data**: Statcast integration
- **Player data**: Active rosters

### Version Control
- **Git-friendly**: No binary files or deep nesting
- **Diff-friendly**: Text-based markdown files
- **Merge-friendly**: No complex conflicts

## Best Practices

### 1. File Management
- **Regular cleanup**: Remove old reports automatically
- **Backup strategy**: Archive important reports
- **Monitoring**: Track disk usage and file counts

### 2. Naming Consistency
- **Strict format**: Always use MMDD_HHMM format
- **No variations**: Consistent naming across all reports
- **Validation**: Check filename format before saving

### 3. Content Quality
- **Validation**: Ensure all required sections are present
- **Formatting**: Consistent markdown formatting
- **Data integrity**: Validate all metrics and calculations

### 4. Performance
- **Caching**: Cache recent reports for quick access
- **Lazy loading**: Load content only when needed
- **Efficient queries**: Use filename patterns for filtering

## Future Enhancements

### 1. Indexing
- **Search index**: Full-text search across reports
- **Metadata database**: Store key metrics for quick queries
- **Tagging system**: Add tags for specific analysis types

### 2. Analytics
- **Trend analysis**: Track metrics over time
- **Performance tracking**: Monitor system performance
- **Usage statistics**: Track report access patterns

### 3. Automation
- **Scheduled generation**: Automatic report creation
- **Notification system**: Alert on important findings
- **Integration APIs**: Connect with external systems

### 4. Visualization
- **Charts and graphs**: Visual representation of data
- **Interactive reports**: Web-based report viewing
- **Dashboard**: Real-time monitoring interface
