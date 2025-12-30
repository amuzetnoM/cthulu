#!/usr/bin/env python3
"""
Cthulu Metrics Spreadsheet Updater
===================================
Automatically processes raw metrics.csv and creates/updates a clean, human-readable
spreadsheet with comprehensive analytics and visualization support.

Usage:
    python update_metrics_spreadsheet.py [--input metrics.csv] [--output metrics_clean.xlsx]
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import sys
import re


class MetricsProcessor:
    """Process and clean Cthulu monitoring metrics"""
    
    def __init__(self, input_file, output_dir):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.raw_df = None
        self.clean_df = None
        self.summary_df = None
        self.trading_sessions = []
        
    def load_metrics(self):
        """Load and parse the raw metrics CSV"""
        print(f"Loading metrics from {self.input_file}...")
        
        try:
            # Read CSV with flexible parsing - handle inconsistent columns
            self.raw_df = pd.read_csv(
                self.input_file, 
                header=0,
                on_bad_lines='skip',  # Skip problematic lines
                engine='python'  # More flexible parser
            )
            print(f"Loaded {len(self.raw_df)} rows")
            return True
        except Exception as e:
            print(f"Error loading metrics: {e}")
            # Try without header
            try:
                self.raw_df = pd.read_csv(
                    self.input_file,
                    header=None,
                    on_bad_lines='skip',
                    engine='python'
                )
                print(f"Loaded {len(self.raw_df)} rows (no header)")
                return True
            except Exception as e2:
                print(f"Error loading metrics (retry): {e2}")
                return False
    
    def parse_metrics(self):
        """Parse and structure the metrics data"""
        print("Parsing metrics data...")
        
        records = []
        
        for idx, row in self.raw_df.iterrows():
            try:
                # Get the first column (timestamp or event)
                first_col = str(row.iloc[0]) if len(row) > 0 else ""
                
                # Skip header row
                if 'timestamp' in first_col.lower():
                    continue
                
                # Parse timestamp
                timestamp = self._parse_timestamp(first_col)
                
                # Determine row type - be more inclusive
                is_event = self._is_session_event(row)
                has_numbers = self._has_numeric_data(row)
                
                if is_event:
                    record = self._parse_session_event(row, timestamp)
                elif has_numbers or timestamp:
                    record = self._parse_metrics_row(row, timestamp)
                else:
                    continue
                
                if record:
                    records.append(record)
                    
            except Exception as e:
                # Silently continue on parse errors
                continue
        
        self.clean_df = pd.DataFrame(records)
        print(f"Parsed {len(self.clean_df)} valid records")
        return True
    
    def _parse_timestamp(self, timestamp_str):
        """Parse various timestamp formats"""
        if pd.isna(timestamp_str):
            return None
            
        # Try different formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dZ",
        ]
        
        for fmt in formats:
            try:
                return pd.to_datetime(timestamp_str, format=fmt)
            except:
                continue
        
        # Try pandas auto-parsing
        try:
            return pd.to_datetime(timestamp_str)
        except:
            return None
    
    def _has_numeric_data(self, row):
        """Check if row has any numeric data"""
        numeric_count = 0
        for val in row:
            try:
                if pd.notna(val) and (isinstance(val, (int, float)) or str(val).replace('.', '').replace('-', '').isdigit()):
                    numeric_count += 1
            except:
                continue
        return numeric_count >= 2
    
    def _is_session_event(self, row):
        """Check if row is a session event"""
        row_str = ' '.join(str(val) for val in row if pd.notna(val)).lower()
        keywords = ['restart', 'session', 'phase', 'complete', 'start', 'test', 'stress', 'rpc']
        return any(kw in row_str for kw in keywords)
    
    def _is_metrics_row(self, row):
        """Check if row contains numerical metrics"""
        # Check if row has numerical data
        numeric_count = sum(1 for val in row if isinstance(val, (int, float)) and not pd.isna(val))
        return numeric_count >= 3
    
    def _parse_session_event(self, row, timestamp):
        """Parse session/event rows"""
        values = [str(val) for val in row if pd.notna(val)]
        
        return {
            'timestamp': timestamp,
            'type': 'event',
            'event_type': values[1] if len(values) > 1 else 'unknown',
            'description': ' '.join(values[1:]) if len(values) > 1 else '',
            'strategy': self._extract_strategy(values),
            'symbol': self._extract_symbol(values),
        }
    
    def _parse_metrics_row(self, row, timestamp):
        """Parse numerical metrics rows"""
        return {
            'timestamp': timestamp,
            'type': 'metrics',
            'pid': self._safe_int(row.iloc[1]) if len(row) > 1 else None,
            'cpu_seconds': self._safe_float(row.iloc[2]) if len(row) > 2 else 0.0,
            'memory_mb': self._safe_float(row.iloc[3]) if len(row) > 3 else 0.0,
            'errors_delta': self._safe_int(row.iloc[4]) if len(row) > 4 else 0,
            'errors_total': self._safe_int(row.iloc[5]) if len(row) > 5 else 0,
            'trades_delta': self._safe_int(row.iloc[6]) if len(row) > 6 else 0,
            'trades_total': self._safe_int(row.iloc[7]) if len(row) > 7 else 0,
            'restarts': self._safe_int(row.iloc[8]) if len(row) > 8 else 0,
            'log_bytes': self._safe_int(row.iloc[9]) if len(row) > 9 else 0,
        }
    
    def _extract_strategy(self, values):
        """Extract strategy from values"""
        strategies = ['conservative', 'balanced', 'aggressive', 'ultra_aggressive']
        for val in values:
            val_lower = str(val).lower()
            for strat in strategies:
                if strat in val_lower:
                    return strat
        return None
    
    def _extract_symbol(self, values):
        """Extract trading symbol"""
        for val in values:
            val_str = str(val).upper()
            if 'BTCUSD' in val_str or 'BTC' in val_str:
                return 'BTCUSD#'
        return None
    
    def _safe_int(self, val):
        """Safely convert to int"""
        try:
            if pd.isna(val):
                return 0
            return int(float(val))
        except:
            return 0
    
    def _safe_float(self, val):
        """Safely convert to float"""
        try:
            if pd.isna(val):
                return 0.0
            return float(val)
        except:
            return 0.0
    
    def create_summary(self):
        """Create summary statistics"""
        print("Creating summary statistics...")
        
        if self.clean_df is None or len(self.clean_df) == 0:
            print("No data to summarize")
            return False
        
        metrics_df = self.clean_df[self.clean_df['type'] == 'metrics'].copy()
        
        if len(metrics_df) == 0:
            print("No metrics data found")
            return False
        
        summary = {
            'Metric': [],
            'Value': [],
            'Unit': [],
            'Description': []
        }
        
        # Time range
        if 'timestamp' in metrics_df.columns:
            timestamps = metrics_df['timestamp'].dropna()
            # Remove timezone info for comparison
            timestamps = pd.to_datetime(timestamps, utc=True).dt.tz_localize(None)
            if len(timestamps) > 0:
                summary['Metric'].append('Time Range Start')
                summary['Value'].append(timestamps.min())
                summary['Unit'].append('')
                summary['Description'].append('First recorded timestamp')
                
                summary['Metric'].append('Time Range End')
                summary['Value'].append(timestamps.max())
                summary['Unit'].append('')
                summary['Description'].append('Last recorded timestamp')
                
                duration = timestamps.max() - timestamps.min()
                summary['Metric'].append('Total Duration')
                summary['Value'].append(f"{duration.total_seconds() / 3600:.2f}")
                summary['Unit'].append('hours')
                summary['Description'].append('Total monitoring period')
        
        # Trade statistics
        if 'trades_total' in metrics_df.columns:
            total_trades = metrics_df['trades_total'].max()
            summary['Metric'].append('Total Trades')
            summary['Value'].append(total_trades)
            summary['Unit'].append('trades')
            summary['Description'].append('Cumulative trades executed')
        
        if 'trades_delta' in metrics_df.columns:
            avg_trades_per_period = metrics_df['trades_delta'].mean()
            summary['Metric'].append('Avg Trades Per Period')
            summary['Value'].append(f"{avg_trades_per_period:.2f}")
            summary['Unit'].append('trades/interval')
            summary['Description'].append('Average trade rate')
        
        # Error statistics
        if 'errors_total' in metrics_df.columns:
            total_errors = metrics_df['errors_total'].max()
            summary['Metric'].append('Total Errors')
            summary['Value'].append(total_errors)
            summary['Unit'].append('errors')
            summary['Description'].append('Cumulative errors encountered')
        
        # System performance
        if 'cpu_seconds' in metrics_df.columns:
            avg_cpu = metrics_df['cpu_seconds'].mean()
            max_cpu = metrics_df['cpu_seconds'].max()
            summary['Metric'].append('Avg CPU Usage')
            summary['Value'].append(f"{avg_cpu:.2f}")
            summary['Unit'].append('seconds')
            summary['Description'].append('Average CPU time per interval')
            
            summary['Metric'].append('Max CPU Usage')
            summary['Value'].append(f"{max_cpu:.2f}")
            summary['Unit'].append('seconds')
            summary['Description'].append('Peak CPU time')
        
        if 'memory_mb' in metrics_df.columns:
            avg_mem = metrics_df[metrics_df['memory_mb'] > 0]['memory_mb'].mean()
            max_mem = metrics_df['memory_mb'].max()
            summary['Metric'].append('Avg Memory Usage')
            summary['Value'].append(f"{avg_mem:.2f}")
            summary['Unit'].append('MB')
            summary['Description'].append('Average memory footprint')
            
            summary['Metric'].append('Max Memory Usage')
            summary['Value'].append(f"{max_mem:.2f}")
            summary['Unit'].append('MB')
            summary['Description'].append('Peak memory usage')
        
        # System stability
        if 'restarts' in metrics_df.columns:
            total_restarts = metrics_df['restarts'].max()
            summary['Metric'].append('System Restarts')
            summary['Value'].append(total_restarts)
            summary['Unit'].append('restarts')
            summary['Description'].append('Number of system restarts')
        
        self.summary_df = pd.DataFrame(summary)
        print(f"Created summary with {len(self.summary_df)} metrics")
        return True
    
    def save_excel(self, output_file):
        """Save processed data to Excel"""
        print(f"Saving to {output_file}...")
        
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Summary sheet
                if self.summary_df is not None:
                    summary_copy = self.summary_df.copy()
                    # Convert timestamp columns to timezone-naive
                    for col in summary_copy.columns:
                        if summary_copy[col].dtype == 'datetime64[ns, UTC]':
                            summary_copy[col] = summary_copy[col].dt.tz_localize(None)
                    summary_copy.to_excel(writer, sheet_name='Summary', index=False)
                
                # Clean metrics
                if self.clean_df is not None:
                    # Separate metrics and events
                    metrics = self.clean_df[self.clean_df['type'] == 'metrics'].copy()
                    events = self.clean_df[self.clean_df['type'] == 'event'].copy()
                    
                    # Remove timezone from timestamp columns
                    for df in [metrics, events]:
                        if len(df) > 0 and 'timestamp' in df.columns:
                            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.tz_localize(None)
                    
                    if len(metrics) > 0:
                        metrics.to_excel(writer, sheet_name='Metrics', index=False)
                    
                    if len(events) > 0:
                        events.to_excel(writer, sheet_name='Events', index=False)
                
                # Raw data (first 1000 rows)
                if self.raw_df is not None:
                    self.raw_df.head(1000).to_excel(writer, sheet_name='Raw Data', index=False)
            
            print(f"Successfully saved to {output_file}")
            return True
            
        except Exception as e:
            print(f"Error saving Excel: {e}")
            return False
    
    def save_csv(self):
        """Save cleaned data to CSV"""
        print("Saving cleaned CSV files...")
        
        try:
            # Save clean metrics
            if self.clean_df is not None:
                metrics_csv = self.output_dir / 'metrics_clean.csv'
                self.clean_df.to_csv(metrics_csv, index=False)
                print(f"Saved clean metrics to {metrics_csv}")
            
            # Save summary
            if self.summary_df is not None:
                summary_csv = self.output_dir / 'metrics_summary.csv'
                self.summary_df.to_csv(summary_csv, index=False)
                print(f"Saved summary to {summary_csv}")
            
            return True
            
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Process Cthulu metrics and create clean spreadsheet'
    )
    parser.add_argument(
        '--input', 
        default='../metrics.csv',
        help='Input metrics CSV file (default: ../metrics.csv)'
    )
    parser.add_argument(
        '--output-dir',
        default='..',
        help='Output directory (default: ..)'
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to script location
    script_dir = Path(__file__).parent
    input_file = (script_dir / args.input).resolve()
    output_dir = (script_dir / args.output_dir).resolve()
    
    print("="*60)
    print("Cthulu Metrics Spreadsheet Updater")
    print("="*60)
    print(f"Input file: {input_file}")
    print(f"Output dir: {output_dir}")
    print()
    
    # Check input file exists
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return 1
    
    # Create processor
    processor = MetricsProcessor(input_file, output_dir)
    
    # Load and process
    if not processor.load_metrics():
        return 1
    
    if not processor.parse_metrics():
        return 1
    
    if not processor.create_summary():
        return 1
    
    # Save outputs
    output_excel = output_dir / 'metrics_clean.xlsx'
    
    # Try to save Excel (requires openpyxl)
    try:
        import openpyxl
        processor.save_excel(output_excel)
    except ImportError:
        print("Warning: openpyxl not installed, skipping Excel output")
        print("Install with: pip install openpyxl")
    
    # Always save CSV
    processor.save_csv()
    
    print()
    print("="*60)
    print("Processing complete!")
    print("="*60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
