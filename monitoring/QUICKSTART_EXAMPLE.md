# Cthulu Monitoring System - Quick Start Example

## Overview

This guide demonstrates how to use the monitoring system to analyze Cthulu's trading performance.

## Generated Files

After running the pipeline, you'll have these files in the `monitoring/` directory:

```
monitoring/
├── metrics.csv                    # Original raw data (674 rows)
├── metrics_clean.csv              # Cleaned metrics (672 rows)
├── metrics_clean.xlsx             # Excel workbook with 4 sheets
├── metrics_summary.csv            # Summary statistics (11 metrics)
├── metrics_dashboard.html         # Interactive HTML dashboard
└── metrics_charts.png             # Static 4-panel chart image
```

## What You Get

### 1. Clean Spreadsheet (Excel)

**File:** `metrics_clean.xlsx`

Contains 4 sheets:
- **Summary** - Key metrics at a glance
- **Metrics** - Time-series numerical data
- **Events** - Session events and milestones
- **Raw Data** - Original data (first 1000 rows)

**Example Summary Statistics:**
```
Metric                  | Value    | Unit          | Description
------------------------|----------|---------------|----------------------------
Total Duration          | 34.43    | hours         | Total monitoring period
Total Trades            | 4,404    | trades        | Cumulative trades executed
Total Errors            | 581      | errors        | Cumulative errors
Avg Memory Usage        | 211.86   | MB            | Average memory footprint
Max Memory Usage        | 787.22   | MB            | Peak memory usage
System Restarts         | 4        | restarts      | Number of restarts
```

### 2. Interactive Dashboard (HTML)

**File:** `metrics_dashboard.html`

Features:
- ⚡ Dark theme with neon accents
- 📊 6 Summary cards with live metrics
- 📈 4 Interactive Plotly charts:
  1. **Trading Activity** - Cumulative and per-interval trades
  2. **CPU Performance** - Resource usage over time
  3. **Error Timeline** - Error accumulation tracking
  4. **System Resources** - Combined memory/CPU view

**Interactivity:**
- Hover over data points for details
- Click and drag to zoom
- Double-click to reset zoom
- Click legend items to show/hide traces

### 3. Static Charts (PNG)

**File:** `metrics_charts.png`

4-panel layout:
- Top-left: Trading Activity
- Top-right: Memory Usage
- Bottom-left: CPU Performance
- Bottom-right: Error Timeline

Perfect for:
- Reports and presentations
- Email attachments
- Documentation

## Real Data Example

From the actual Cthulu metrics:

### System Performance
```
Time Range: Dec 29 11:27 - Dec 30 16:53 (34.43 hours)
Total Trades: 4,404 executions
Trade Rate: 18.54 trades/interval average
Peak Activity: 940 CPU seconds recorded
Memory Usage: 86-787 MB range
System Stability: 4 restarts over 34+ hours
```

### Key Insights
1. **High Volume**: System executed 4,404+ trades over monitoring period
2. **Resource Efficient**: Average 211 MB memory usage
3. **Error Rate**: 581 errors total (~16 errors/hour)
4. **Uptime**: Ran continuously for 34+ hours with only 4 restarts

## Usage Examples

### Daily Monitoring
```bash
# Run every morning to see yesterday's activity
cd /path/to/monitoring/scripts
python run_metrics_pipeline.py

# Open dashboard in browser
xdg-open ../metrics_dashboard.html  # Linux
open ../metrics_dashboard.html      # macOS
start ../metrics_dashboard.html     # Windows
```

### Troubleshooting
```bash
# Check recent activity
python update_metrics_spreadsheet.py
grep "error" ../metrics_clean.csv | tail -20

# View specific time window
python visualize_metrics.py --window 1  # Last hour
python visualize_metrics.py --window 24  # Last day
```

### Performance Analysis
```bash
# Generate reports
python run_metrics_pipeline.py

# Export to PDF (requires additional tools)
wkhtmltopdf ../metrics_dashboard.html ../report.pdf

# Email the charts
mail -s "Cthulu Daily Report" team@example.com < ../metrics_charts.png
```

## Continuous Monitoring

The system is designed for never-ending data:

### How It Handles Continuous Data

1. **Append-Only**: New data is added without modifying history
2. **Rolling Windows**: View recent activity without losing historical context
3. **Cumulative Metrics**: Total trades, errors tracked from start
4. **Delta Metrics**: See rate of change in each interval

### Example: Viewing Last 7 Days
```bash
# Process all data
python update_metrics_spreadsheet.py

# Visualize last week only
python visualize_metrics.py --window 168  # 7 days × 24 hours
```

### Automation Setup

**Linux/macOS Cron:**
```bash
# Update dashboard hourly
0 * * * * cd /path/to/monitoring/scripts && python run_metrics_pipeline.py

# Email daily summary at 9 AM
0 9 * * * cd /path/to/monitoring && mail -s "Cthulu Report" you@email.com -a metrics_charts.png < metrics_summary.csv
```

**Windows Task Scheduler:**
1. Create new task
2. Trigger: Daily at startup + repeat every 1 hour
3. Action: `python C:\path\to\monitoring\scripts\run_metrics_pipeline.py`

## Advanced Features

### Custom Time Windows
```bash
# Last hour only
python visualize_metrics.py --window 1

# Last 3 days
python visualize_metrics.py --window 72

# Full history
python visualize_metrics.py --window 8760  # 1 year
```

### Multiple Data Sources
```bash
# Compare different sessions
python update_metrics_spreadsheet.py --input session1_metrics.csv --output-dir ./session1
python update_metrics_spreadsheet.py --input session2_metrics.csv --output-dir ./session2
```

### Programmatic Access
```python
import pandas as pd

# Load clean data
df = pd.read_csv('monitoring/metrics_clean.csv')

# Filter to specific time range
df['timestamp'] = pd.to_datetime(df['timestamp'])
recent = df[df['timestamp'] > '2025-12-30']

# Calculate custom metrics
avg_trades_per_hour = recent.groupby(recent['timestamp'].dt.hour)['trades_delta'].mean()
print(f"Best trading hour: {avg_trades_per_hour.idxmax()}")
```

## Interpreting Results

### Health Indicators

**🟢 Healthy System:**
- Memory usage stable < 150 MB
- Error rate < 10/hour
- No sudden crashes (restarts)
- Consistent trade execution

**🟡 Warning Signs:**
- Memory creeping upward (possible leak)
- Error rate 10-50/hour
- Frequent restarts (> 1/hour)
- Variable trade execution

**🔴 Critical Issues:**
- Memory > 500 MB sustained
- Error rate > 50/hour
- Crashes every few minutes
- Trade execution stopped

### Performance Benchmarks

From actual Cthulu data:

```
Metric               | Observed   | Good      | Excellent
---------------------|------------|-----------|----------
Trades/hour          | ~128       | > 50      | > 100
Memory (MB)          | 211 avg    | < 200     | < 150
Errors/hour          | ~16        | < 10      | < 5
Uptime (hours)       | 34+        | > 24      | > 48
CPU seconds/interval | 10.9 avg   | < 15      | < 10
```

## Next Steps

1. **Review Dashboard**: Open `metrics_dashboard.html` and explore the data
2. **Analyze Patterns**: Look for trends in trading activity and errors
3. **Set Up Automation**: Configure cron/Task Scheduler for regular updates
4. **Monitor Health**: Check summary stats daily
5. **Implement Subprograms**: See `SUBPROGRAM_RECOMMENDATIONS.md` for enhancement ideas

## Troubleshooting

### "Input file not found"
- Ensure `metrics.csv` exists in monitoring directory
- Check you're running from the scripts directory

### "No data to visualize"
- Run `update_metrics_spreadsheet.py` first
- Verify `metrics_clean.csv` was created and has data

### Charts look empty
- Check timestamp parsing in metrics.csv
- Verify numeric columns contain data
- Review console output for warnings

### Dashboard won't open
- Check browser console for JavaScript errors
- Ensure Plotly CDN is accessible
- Try different browser

## Support

For issues or questions:
1. Check `monitoring/scripts/README.md` for detailed documentation
2. Review `SUBPROGRAM_RECOMMENDATIONS.md` for enhancement ideas
3. Examine script output for error messages

---

**Generated:** 2025-12-30  
**System:** Cthulu Trading Bot  
**Version:** 1.0.0
