#!/usr/bin/env python3
"""
Export latest metrics from comprehensive_metrics.csv to a JSON file for the dashboard.
Also pushes to GitHub Gist for the live GitHub Pages dashboard.

Setup for Gist publishing:
1. Create a GitHub Personal Access Token with 'gist' scope
2. Create a new Gist at https://gist.github.com with a file named 'cthulu_metrics.json'
3. Set environment variables:
   - GITHUB_GIST_TOKEN: Your personal access token
   - GITHUB_GIST_ID: The Gist ID (from the URL)
"""
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib import request, error

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CSV_PATH = PROJECT_ROOT / "observability" / "reporting" / "comprehensive_metrics.csv"
JSON_OUTPUT_PATH = PROJECT_ROOT / "docs" / "logs" / "dashboard_metrics.json"

# GitHub Gist config (set via environment variables)
GIST_TOKEN = os.environ.get("GITHUB_GIST_TOKEN", "")
GIST_ID = os.environ.get("GITHUB_GIST_ID", "")
GIST_FILENAME = "cthulu_metrics.json"

# Track when exporter started for live uptime calculation
EXPORTER_START_TIME = datetime.now(timezone.utc)

# Fields we care about for the dashboard
REQUIRED_FIELDS = [
    "timestamp",
    "account_balance",
    "account_equity", 
    "account_margin_level",
    "total_trades",
    "win_rate",
    "max_drawdown_pct",
    "peak_equity",
    "drawdown_state",
    "current_symbol",
    "current_price",
    "system_uptime_seconds",
    "mt5_connected",
    "memory_usage_mb",
    "cpu_usage_pct",
    "active_positions",
    "unrealized_pnl",
    "realized_pnl",
    "daily_pnl",
]


def parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO timestamp string to datetime."""
    try:
        # Handle various ISO formats
        if ts_str.endswith('Z'):
            ts_str = ts_str[:-1] + '+00:00'
        return datetime.fromisoformat(ts_str)
    except:
        return None


def get_latest_metrics() -> dict:
    """Read the CSV and return the latest row as a dict with only required fields."""
    if not CSV_PATH.exists():
        return {"error": "CSV file not found", "timestamp": datetime.now().isoformat()}
    
    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        if not rows:
            return {"error": "No data in CSV", "timestamp": datetime.now().isoformat()}
        
        latest = rows[-1]
        first = rows[0]
        
        # Extract only required fields
        metrics = {}
        for field in REQUIRED_FIELDS:
            value = latest.get(field, "")
            # Try to convert numeric strings to numbers
            if value and field != "timestamp" and field != "drawdown_state" and field != "current_symbol":
                try:
                    if "." in str(value):
                        metrics[field] = float(value)
                    else:
                        metrics[field] = int(value) if value.isdigit() else value
                except (ValueError, AttributeError):
                    metrics[field] = value
            else:
                metrics[field] = value
        
        # Calculate real uptime from CSV data span
        first_ts = parse_timestamp(first.get("timestamp", ""))
        latest_ts = parse_timestamp(latest.get("timestamp", ""))
        now = datetime.now(timezone.utc)
        
        if first_ts and latest_ts:
            # Calculate how long the CSV data spans (session duration)
            csv_session_duration = (latest_ts - first_ts).total_seconds()
            
            # Check if data is fresh (less than 60 seconds old)
            data_age = (now - latest_ts).total_seconds() if latest_ts.tzinfo else 0
            
            if data_age < 60:
                # Data is fresh - use the CSV's system_uptime_seconds
                metrics["_data_status"] = "live"
            else:
                # Data is stale - calculate exporter uptime instead
                exporter_uptime = (now - EXPORTER_START_TIME).total_seconds()
                metrics["system_uptime_seconds"] = exporter_uptime
                metrics["_data_status"] = "stale"
                metrics["_data_age_seconds"] = data_age
                metrics["_csv_session_duration"] = csv_session_duration
        
        # Add export metadata
        metrics["_exported_at"] = now.isoformat()
        metrics["_source"] = "cthulu"
        metrics["_status"] = "live"
        metrics["_exporter_uptime"] = (now - EXPORTER_START_TIME).total_seconds()
        
        return metrics
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "_status": "error"
        }


def push_to_gist(metrics: dict) -> bool:
    """Push metrics to GitHub Gist for the live dashboard."""
    if not GIST_TOKEN or not GIST_ID:
        return False
    
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        data = json.dumps({
            "files": {
                GIST_FILENAME: {
                    "content": json.dumps(metrics, indent=2)
                }
            }
        }).encode("utf-8")
        
        req = request.Request(url, data=data, method="PATCH")
        req.add_header("Authorization", f"token {GIST_TOKEN}")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/vnd.github.v3+json")
        
        with request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print(f"  → Pushed to Gist {GIST_ID}")
                return True
    except error.URLError as e:
        print(f"  ⚠ Gist push failed: {e.reason}")
    except Exception as e:
        print(f"  ⚠ Gist push failed: {e}")
    
    return False


def export_metrics(push_gist: bool = True):
    """Export metrics to JSON file and optionally push to Gist."""
    metrics = get_latest_metrics()
    
    # Ensure output directory exists
    JSON_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(JSON_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    
    print(f"[{datetime.now().isoformat()}] Exported to {JSON_OUTPUT_PATH.name}")
    
    # Push to Gist for GitHub Pages
    if push_gist and GIST_TOKEN and GIST_ID:
        push_to_gist(metrics)
    
    return metrics


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        import time
        print(f"Watching {CSV_PATH} and exporting every 10 seconds...")
        while True:
            try:
                export_metrics()
            except Exception as e:
                print(f"Error: {e}")
            time.sleep(10)
    else:
        result = export_metrics()
        print(json.dumps(result, indent=2))
