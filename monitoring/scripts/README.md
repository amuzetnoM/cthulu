# Cthulu Monitoring Scripts

This directory contains automated scripts for processing, analyzing, and visualizing Cthulu trading system metrics.

## 📁 Contents

- **`update_metrics_spreadsheet.py`** - Processes raw metrics.csv and creates clean spreadsheets
- **`visualize_metrics.py`** - Generates interactive dashboards and static charts
- **`run_metrics_pipeline.py`** - Master script that runs the complete pipeline
- **`README.md`** - This file

## 🚀 Quick Start

### Run the Complete Pipeline

```bash
cd /home/runner/work/cthulu/cthulu/monitoring/scripts
python run_metrics_pipeline.py
```

This will:
1. Process raw metrics.csv
2. Generate clean spreadsheet (Excel + CSV)
3. Create interactive HTML dashboard
4. Generate static chart images

### Run Individual Scripts

#### Process Metrics Only
```bash
python update_metrics_spreadsheet.py
```

#### Create Visualizations Only
```bash
python visualize_metrics.py
```

## 📊 Output Files

All outputs are saved to the monitoring directory (`../`):

| File | Description |
|------|-------------|
| `metrics_clean.xlsx` | Excel workbook with cleaned data (Summary, Metrics, Events, Raw) |
| `metrics_clean.csv` | Clean CSV format of all metrics |
| `metrics_summary.csv` | Statistical summary of key metrics |
| `metrics_dashboard.html` | Interactive HTML dashboard with charts |
| `metrics_charts.png` | Static PNG image with 4-panel chart layout |

## 📈 Dashboard Features

The interactive HTML dashboard (`metrics_dashboard.html`) includes:

### Summary Cards
- Total Trades
- System Errors
- Average Memory Usage
- Max CPU Time
- Monitoring Duration
- Total Data Points

### Interactive Charts
1. **Trading Activity Timeline** - Cumulative and per-interval trades
2. **CPU Performance** - CPU usage over time
3. **Error Timeline** - Error accumulation and new error events
4. **System Resources** - Combined memory and CPU visualization

### Features
- **Dark theme** optimized for readability
- **Interactive tooltips** - Hover over data points for details
- **Zoom and pan** - Click and drag to explore data
- **Legend controls** - Click legend items to show/hide traces
- **Responsive design** - Adapts to different screen sizes

## 🔄 Continuous Data Handling

The visualization system is designed for never-ending chronological data:

### Rolling Window Mode
Use the `--window` parameter to focus on recent data:

```bash
python visualize_metrics.py --window 24  # Last 24 hours
python visualize_metrics.py --window 168  # Last week
```

### Full Historical View
Omit the window parameter or set it very high:

```bash
python visualize_metrics.py --window 8760  # Full year
```

### Auto-Update Workflow

For continuous monitoring, set up a cron job or scheduled task:

**Linux/macOS:**
```bash
# Add to crontab (runs every hour)
0 * * * * cd /path/to/monitoring/scripts && python run_metrics_pipeline.py
```

**Windows (Task Scheduler):**
- Create a scheduled task to run `run_metrics_pipeline.py` every hour

## 📦 Dependencies

### Required
- Python 3.7+
- pandas
- numpy

### Optional (for enhanced features)
- openpyxl - Excel file support
- matplotlib - Static charts
- plotly - Enhanced interactivity (included via CDN in HTML)

### Install Dependencies

```bash
# Minimal (CSV output only)
pip install pandas numpy

# Full features
pip install pandas numpy openpyxl matplotlib
```

## 🔧 Advanced Usage

### Custom Input/Output Paths

```bash
# Process different metrics file
python update_metrics_spreadsheet.py --input /path/to/metrics.csv --output-dir /path/to/output

# Visualize different clean data
python visualize_metrics.py --input /path/to/metrics_clean.csv --output-dir /path/to/output
```

### Programmatic Use

```python
from update_metrics_spreadsheet import MetricsProcessor

# Create processor
processor = MetricsProcessor('metrics.csv', 'output/')

# Process data
processor.load_metrics()
processor.parse_metrics()
processor.create_summary()
processor.save_excel('metrics_clean.xlsx')
processor.save_csv()
```

## 📐 Data Structure

### Input Format (metrics.csv)
The raw metrics.csv can contain:
- Timestamp-based metrics rows
- Session event markers
- Trading activity logs
- System performance data

### Output Format (metrics_clean.csv)

**Metrics Rows:**
```csv
timestamp,type,pid,cpu_seconds,memory_mb,errors_delta,errors_total,trades_delta,trades_total,restarts,log_bytes
2025-12-29T13:22:58,metrics,12900,0.0,85.89,13,13,2619,2619,0,762678
```

**Event Rows:**
```csv
timestamp,type,event_type,description,strategy,symbol
2025-12-29T13:02:06,event,restart,restart ultra_aggressive BTCUSD#,ultra_aggressive,BTCUSD#
```

## 🎨 Visualization Concepts

### Chronological Never-Ending Data

The system handles continuous data through:

1. **Time-series focus** - X-axis always represents time
2. **Incremental loading** - Can append new data without regeneration
3. **Rolling windows** - View recent activity without losing historical context
4. **Cumulative metrics** - Track totals over entire history
5. **Delta metrics** - Show rate of change in each interval

### Chart Design Philosophy

- **Coherent**: Each chart has a clear purpose
- **Accurate**: Data is never interpolated or estimated
- **Scalable**: Performance remains good with large datasets
- **Informative**: Multiple data dimensions shown together where relevant

### 3D/4D Visualization Options

While the current implementation focuses on 2D time-series for clarity, the data structure supports advanced visualizations:

**3D Options:**
- X: Time
- Y: Metric Value
- Z: System State / Phase / Strategy

**4D Options (3D + color/size):**
- X, Y, Z: Time, Trades, Memory
- Color: Error rate
- Size: CPU usage

To implement 3D charts, extend `visualize_metrics.py` with plotly's 3D scatter/surface plots.

## 🤖 Automation Ideas

### Scheduled Updates
```bash
#!/bin/bash
# update_dashboard.sh
cd /path/to/monitoring/scripts
python run_metrics_pipeline.py

# Optional: Deploy to web server
cp ../metrics_dashboard.html /var/www/html/cthulu/
```

### Watch Mode
```python
# watch_metrics.py
import time
from pathlib import Path
from subprocess import run

metrics_file = Path("../metrics.csv")
last_modified = 0

while True:
    current_modified = metrics_file.stat().st_mtime
    if current_modified > last_modified:
        print("Metrics updated, regenerating dashboard...")
        run(["python", "run_metrics_pipeline.py"])
        last_modified = current_modified
    time.sleep(60)  # Check every minute
```

## 📝 Notes

- **Non-destructive**: Original metrics.csv is never modified
- **Idempotent**: Safe to run multiple times
- **Fast**: Processing typical datasets takes seconds
- **Extensible**: Easy to add new metrics or chart types

## 🐛 Troubleshooting

### Error: "Input file not found"
- Ensure metrics.csv exists in the monitoring directory
- Check the `--input` path is correct

### Error: "openpyxl not installed"
- Install with: `pip install openpyxl`
- Or use CSV output instead

### Dashboard not showing data
- Check browser console for JavaScript errors
- Ensure metrics_clean.csv has valid data
- Try regenerating with `python update_metrics_spreadsheet.py`

### Charts appear empty
- Verify timestamp column is properly parsed
- Check that metric columns contain numeric data
- Review console output for parsing warnings

## 📚 Related Documentation

- `../observability_guide.md` - How to instrument Cthulu for monitoring
- `../monitoring_report.md` - Analysis of monitoring data
- `../TRADING_REPORT.md` - Trading performance metrics

## 🔮 Future Enhancements

Potential improvements:
- Real-time WebSocket streaming
- 3D trajectory visualizations
- Machine learning anomaly detection
- Comparative analysis across sessions
- Export to Grafana/Prometheus
- PDF report generation

---

**Version:** 1.0.0  
**Last Updated:** 2025-12-30  
**Author:** Cthulu Development Team
