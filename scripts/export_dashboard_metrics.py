#!/usr/bin/env python3
"""
Export latest metrics from comprehensive_metrics.csv to a JSON file for the dashboard.
This script should be run periodically (e.g., every 30 seconds) or triggered by cthulu.
"""
import csv
import json
import os
from datetime import datetime
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CSV_PATH = PROJECT_ROOT / "observability" / "reporting" / "comprehensive_metrics.csv"
JSON_OUTPUT_PATH = PROJECT_ROOT / "docs" / "logs" / "dashboard_metrics.json"

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
        
        # Add export metadata
        metrics["_exported_at"] = datetime.now().isoformat()
        metrics["_source"] = str(CSV_PATH)
        metrics["_status"] = "live"
        
        return metrics
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "_status": "error"
        }


def export_metrics():
    """Export metrics to JSON file."""
    metrics = get_latest_metrics()
    
    # Ensure output directory exists
    JSON_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(JSON_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    
    print(f"[{datetime.now().isoformat()}] Exported metrics to {JSON_OUTPUT_PATH}")
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
