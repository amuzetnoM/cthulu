#!/usr/bin/env python3
"""
Cthulu Metrics Pipeline
=======================
Master script to process metrics and generate all visualizations.

Usage:
    python run_metrics_pipeline.py
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - FAILED")
        print(f"Error: {e}")
        return False


def main():
    print("="*60)
    print("🐙 CTHULU METRICS PIPELINE")
    print("="*60)
    print("\nProcessing monitoring metrics and generating visualizations...")
    
    script_dir = Path(__file__).parent
    
    # Step 1: Update spreadsheet
    update_cmd = f"cd {script_dir} && python update_metrics_spreadsheet.py"
    if not run_command(update_cmd, "Processing metrics spreadsheet"):
        print("\n⚠️  Spreadsheet processing failed, continuing anyway...")
    
    # Step 2: Create visualizations
    viz_cmd = f"cd {script_dir} && python visualize_metrics.py"
    if not run_command(viz_cmd, "Creating visualizations"):
        print("\n⚠️  Visualization failed")
    
    # Summary
    print("\n" + "="*60)
    print("📊 PIPELINE COMPLETE")
    print("="*60)
    
    output_dir = script_dir.parent
    print(f"\n📁 Outputs saved to: {output_dir}")
    print("\n📄 Generated files:")
    print("   - metrics_clean.xlsx     (Excel spreadsheet)")
    print("   - metrics_clean.csv      (Clean CSV data)")
    print("   - metrics_summary.csv    (Summary statistics)")
    print("   - metrics_dashboard.html (Interactive dashboard)")
    print("   - metrics_charts.png     (Static charts)")
    
    dashboard = output_dir / "metrics_dashboard.html"
    if dashboard.exists():
        print(f"\n🌐 View dashboard: file://{dashboard.absolute()}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
