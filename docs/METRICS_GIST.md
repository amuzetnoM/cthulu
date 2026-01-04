# Live Metrics Dashboard Setup Guide

> This guide explains how the Cthulu trading system is configured to display **live metrics** on the GitHub Pages website.
> NOTE: This module is still in early development and may change in future releases.


## Overview

The live dashboard system works by:
1. **Cthulu** writes metrics to `comprehensive_metrics.csv` every second
2. **Export script** reads the CSV and pushes to a GitHub Gist every 10 seconds
3. **GitHub Pages** website fetches from the Gist and displays live data

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐     ┌─────────────────┐
│   Cthulu    │ --> │ CSV Metrics File │ --> │ Export      │ --> │ GitHub Gist     │
│  (Trading)  │     │                  │     │ Script      │     │ (Public JSON)   │
└─────────────┘     └──────────────────┘     └─────────────┘     └─────────────────┘
                                                                          │
                                                                          ▼
                                                                 ┌─────────────────┐
                                                                 │ GitHub Pages    │
                                                                 │ Dashboard       │
                                                                 └─────────────────┘
```

---

## Prerequisites

- **GitHub CLI** (`gh`) installed and authenticated
- **Python 3.8+** installed
- **Git** configured with push access to the repository
- **Cthulu** running and writing metrics

### Verify GitHub CLI Authentication

```powershell
gh auth status
```

Expected output should show:
- ✓ Logged in to github.com
- Token scopes include: `gist`

If not authenticated:
```powershell
gh auth login
```

---

## Step 1: Create the GitHub Gist

The Gist serves as a public JSON endpoint that GitHub Pages can fetch.

### Option A: Automatic (Recommended)

```powershell
cd C:\workspace\cthulu

# Create initial JSON content
echo '{"_status": "initializing"}' | gh gist create --public --filename "cthulu_metrics.json" --desc "Cthulu Trading System - Live Metrics Dashboard"
```

This will output a URL like:
```
https://gist.github.com/YOUR_USERNAME/GIST_ID_HERE
```

**Copy the Gist ID** (the long string after your username).

### Option B: Manual

1. Go to https://gist.github.com
2. Create a new **public** gist
3. Set filename: `cthulu_metrics.json`
4. Set content: `{}`
5. Click "Create public gist"
6. Copy the Gist ID from the URL

---

## Step 2: Configure the Website

Update `docs/index.html` to use your Gist ID.

Find this section (around line 2038):
```javascript
// Live Metrics Dashboard - Fetch from Gist (GitHub Pages) or local JSON
const GIST_ID = '';  // <-- UPDATE THIS
const GIST_FILENAME = 'cthulu_metrics.json';
```

Replace with your Gist ID:
```javascript
const GIST_ID = '0e860218dbdf40ab4019970b1e035cab';  // Your actual Gist ID
const GIST_FILENAME = 'cthulu_metrics.json';
```

Commit and push:
```powershell
git add docs/index.html
git commit -m "feat: Configure live dashboard Gist ID"
git push origin main
```

---

## Step 3: Run the Metrics Exporter

The exporter script reads from the CSV and pushes to the Gist.

### Set Environment Variables

```powershell
# Get token from GitHub CLI
$env:GITHUB_GIST_TOKEN = (gh auth token)

# Set your Gist ID
$env:GITHUB_GIST_ID = "0e860218dbdf40ab4019970b1e035cab"  # Replace with your ID
```

### Run Once (Test)

```powershell
cd C:\workspace\cthulu
python scripts/export_dashboard_metrics.py
```

Expected output:
```
[2026-01-02T15:51:26.763448] Exported to dashboard_metrics.json
  → Pushed to Gist 0e860218dbdf40ab4019970b1e035cab
{
  "timestamp": "...",
  "account_balance": 1127.99,
  ...
}
```

### Run in Watch Mode (Production)

```powershell
cd C:\workspace\cthulu
$env:GITHUB_GIST_TOKEN = (gh auth token)
$env:GITHUB_GIST_ID = "0e860218dbdf40ab4019970b1e035cab"
python scripts/export_dashboard_metrics.py --watch
```

This will:
- Update every **10 seconds**
- Push to Gist automatically
- Also save locally to `docs/logs/dashboard_metrics.json`

---

## Step 4: Verify Live Dashboard

### Check the Gist

```powershell
gh gist view YOUR_GIST_ID --raw
```

Or visit: `https://gist.githubusercontent.com/YOUR_USERNAME/YOUR_GIST_ID/raw/cthulu_metrics.json`

### Check GitHub Pages

Visit your GitHub Pages URL:
```
https://YOUR_USERNAME.github.io/cthulu/docs/
```

The dashboard should show:
- **LIVE** status (green indicator)
- Real-time metrics: Equity, Balance, Margin Level, etc.
- Timestamp showing when data was last updated

---

## Automation Options

### Option 1: PowerShell Script (Windows)

Create `start_metrics_exporter.ps1`:

```powershell
#!/usr/bin/env pwsh
# Start Cthulu Metrics Exporter

$env:GITHUB_GIST_TOKEN = (gh auth token)
$env:GITHUB_GIST_ID = "0e860218dbdf40ab4019970b1e035cab"

cd C:\workspace\cthulu
python scripts/export_dashboard_metrics.py --watch
```

### Option 2: Batch File (Windows)

Create `start_metrics_exporter.bat`:

```batch
@echo off
cd /d C:\workspace\cthulu

for /f "tokens=*" %%i in ('gh auth token') do set GITHUB_GIST_TOKEN=%%i
set GITHUB_GIST_ID=0e860218dbdf40ab4019970b1e035cab

python scripts/export_dashboard_metrics.py --watch
```

### Option 3: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task: "Cthulu Metrics Exporter"
3. Trigger: At log on (or At startup)
4. Action: Start a program
   - Program: `powershell.exe`
   - Arguments: `-ExecutionPolicy Bypass -File "C:\workspace\cthulu\start_metrics_exporter.ps1"`
5. Finish

### Option 4: Run with Cthulu Startup

Add to your Cthulu startup script or `docker-compose.yml`:

```yaml
services:
  cthulu:
    # ... existing config ...
    
  metrics-exporter:
    image: python:3.11-slim
    volumes:
      - ./scripts:/app/scripts
      - ./observability:/app/observability
    environment:
      - GITHUB_GIST_TOKEN=${GITHUB_GIST_TOKEN}
      - GITHUB_GIST_ID=0e860218dbdf40ab4019970b1e035cab
    command: python /app/scripts/export_dashboard_metrics.py --watch
    depends_on:
      - cthulu
```

---

## Troubleshooting

### Dashboard shows "OFFLINE"

1. **Check Gist ID** is correct in `index.html`
2. **Check exporter is running**: `python scripts/export_dashboard_metrics.py`
3. **Check Gist is public**: Visit the Gist URL in incognito mode
4. **Check CORS**: Gist must be public for browser fetch to work

### Exporter fails to push to Gist

1. **Check token has gist scope**:
   ```powershell
   gh auth status
   ```
   Should show `'gist'` in token scopes.

2. **Refresh token**:
   ```powershell
   gh auth refresh -s gist
   ```

3. **Check Gist ID is correct**:
   ```powershell
   gh gist view YOUR_GIST_ID
   ```

### CSV file not found

Ensure Cthulu is running and writing to:
```
C:\workspace\cthulu\observability\reporting\comprehensive_metrics.csv
```

Check the path in `scripts/export_dashboard_metrics.py`:
```python
CSV_PATH = PROJECT_ROOT / "observability" / "reporting" / "comprehensive_metrics.csv"
```

### Metrics are stale (not updating)

1. Check CSV is being updated:
   ```powershell
   Get-Content observability\reporting\comprehensive_metrics.csv -Tail 3
   ```

2. Check exporter is running in watch mode (`--watch` flag)

3. Check for Python errors in the terminal

---

## Metrics Reference

The dashboard displays these fields from `comprehensive_metrics.csv`:

| Field | Dashboard Label | Description |
|-------|----------------|-------------|
| `account_equity` | EQUITY | Current account equity |
| `account_balance` | BALANCE | Account balance |
| `account_margin_level` | MARGIN LEVEL | Margin level percentage |
| `_exporter_uptime` | UPTIME | How long the metrics exporter has been running |
| `total_trades` | TOTAL TRADES | Number of trades executed |
| `win_rate` | Win Rate | Percentage of winning trades |
| `max_drawdown_pct` | MAX DRAWDOWN | Maximum drawdown percentage |
| `peak_equity` | PEAK EQUITY | Highest equity reached |
| `drawdown_state` | SYSTEM STATE | Current risk state (normal/warning/critical) |
| `current_symbol` | Symbol | Currently traded symbol |
| `current_price` | Price | Current market price |
| `memory_usage_mb` | Memory | RAM usage in MB |

### Additional Metadata Fields

| Field | Description |
|-------|-------------|
| `_exported_at` | ISO timestamp when data was exported |
| `_exporter_uptime` | Seconds since exporter started (real-time uptime) |
| `_data_status` | `live` if CSV data is fresh (<60s), `stale` otherwise |
| `_data_age_seconds` | How old the CSV data is (when stale) |
| `_status` | Overall export status |

---

## Security Notes

1. **Never commit tokens** to the repository
2. **Use environment variables** for sensitive data
3. **Gist must be public** for GitHub Pages to fetch (only contains non-sensitive trading stats)
4. **Token only needs `gist` scope** - use minimal permissions

---

## Quick Reference

```powershell
# One-liner to start the exporter
cd C:\workspace\cthulu; $env:GITHUB_GIST_TOKEN=(gh auth token); $env:GITHUB_GIST_ID="YOUR_GIST_ID"; python scripts/export_dashboard_metrics.py --watch
```

**Your Gist ID**: `0e860218dbdf40ab4019970b1e035cab`

**Gist URL**: https://gist.github.com/amuzetnoM/0e860218dbdf40ab4019970b1e035cab

**Dashboard URL**: https://amuzetnom.github.io/cthulu/docs/
