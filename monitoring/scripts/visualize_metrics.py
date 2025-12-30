#!/usr/bin/env python3
"""
Cthulu Metrics Visualizer
==========================
Creates interactive and static visualizations of continuous monitoring data.
Designed to handle never-ending chronological data with multiple viewing modes.

Features:
- Rolling window views for continuous data
- Interactive HTML dashboards
- Time-series analysis
- Performance heatmaps
- 3D trajectory plots (optional)

Usage:
    python visualize_metrics.py [--input metrics_clean.csv] [--window 24h]
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import sys
import json


class MetricsVisualizer:
    """Visualize Cthulu metrics with support for continuous data"""
    
    def __init__(self, input_file, output_dir, window_hours=24):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.window_hours = window_hours
        self.df = None
        self.charts = []
        
    def load_data(self):
        """Load processed metrics data"""
        print(f"Loading data from {self.input_file}...")
        
        try:
            self.df = pd.read_csv(self.input_file)
            
            # Convert timestamp with flexible parsing
            if 'timestamp' in self.df.columns:
                # Parse timestamps with UTC awareness first, then normalize
                self.df['timestamp'] = pd.to_datetime(
                    self.df['timestamp'], 
                    errors='coerce',  # Invalid dates become NaT
                    utc=True  # Treat as UTC
                )
                # Remove timezone info for plotting compatibility
                self.df['timestamp'] = self.df['timestamp'].dt.tz_localize(None)
                self.df = self.df.sort_values('timestamp')
            
            print(f"Loaded {len(self.df)} records")
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def create_html_dashboard(self):
        """Create interactive HTML dashboard"""
        print("Creating HTML dashboard...")
        
        html_parts = []
        
        # Header
        html_parts.append(self._html_header())
        
        # Summary section
        html_parts.append(self._html_summary())
        
        # Charts
        html_parts.append(self._html_trades_chart())
        html_parts.append(self._html_system_performance())
        html_parts.append(self._html_error_timeline())
        html_parts.append(self._html_memory_cpu_chart())
        
        # Footer
        html_parts.append(self._html_footer())
        
        # Combine
        html_content = '\n'.join(html_parts)
        
        # Save
        output_file = self.output_dir / 'metrics_dashboard.html'
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"Saved dashboard to {output_file}")
        return output_file
    
    def _html_header(self):
        """HTML header with styling"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Cthulu Metrics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js" 
            integrity="sha384-placeholder" 
            crossorigin="anonymous"></script>
    <!-- Note: Replace placeholder with actual SRI hash if available, or use local copy -->
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0a0e27;
            color: #e0e0e0;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: #00d4ff;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }
        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 30px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .summary-card {
            background: linear-gradient(135deg, #1a1f3a 0%, #2a2f4a 100%);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #00d4ff33;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            color: #00d4ff;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .summary-value {
            font-size: 2em;
            font-weight: bold;
            color: #fff;
        }
        .summary-unit {
            color: #888;
            font-size: 0.8em;
            margin-left: 5px;
        }
        .chart-container {
            background: linear-gradient(135deg, #1a1f3a 0%, #2a2f4a 100%);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            border: 1px solid #00d4ff33;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .chart-title {
            color: #00d4ff;
            margin: 0 0 20px 0;
            font-size: 1.5em;
        }
        .chart {
            width: 100%;
            height: 400px;
        }
        .footer {
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #333;
        }
        .status-good { color: #00ff88; }
        .status-warning { color: #ffaa00; }
        .status-critical { color: #ff3344; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ CTHULU METRICS DASHBOARD ⚡</h1>
        <div class="subtitle">Real-time Trading System Analytics</div>
"""
    
    def _html_summary(self):
        """Generate summary cards"""
        metrics_df = self.df[self.df['type'] == 'metrics'].copy() if 'type' in self.df.columns else self.df
        
        # Calculate summary stats
        total_trades = metrics_df['trades_total'].max() if 'trades_total' in metrics_df.columns else 0
        total_errors = metrics_df['errors_total'].max() if 'errors_total' in metrics_df.columns else 0
        avg_memory = metrics_df[metrics_df['memory_mb'] > 0]['memory_mb'].mean() if 'memory_mb' in metrics_df.columns else 0
        max_cpu = metrics_df['cpu_seconds'].max() if 'cpu_seconds' in metrics_df.columns else 0
        
        # Time range
        duration_hours = 0
        if 'timestamp' in metrics_df.columns:
            timestamps = metrics_df['timestamp'].dropna()
            if len(timestamps) > 0:
                duration = timestamps.max() - timestamps.min()
                duration_hours = duration.total_seconds() / 3600
        
        # Status determination
        error_status = 'status-good' if total_errors < 50 else ('status-warning' if total_errors < 200 else 'status-critical')
        memory_status = 'status-good' if avg_memory < 100 else ('status-warning' if avg_memory < 150 else 'status-critical')
        
        return f"""
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Trades</h3>
                <div class="summary-value">{total_trades:,}</div>
                <div class="summary-unit">executions</div>
            </div>
            <div class="summary-card">
                <h3>System Errors</h3>
                <div class="summary-value {error_status}">{total_errors:,}</div>
                <div class="summary-unit">incidents</div>
            </div>
            <div class="summary-card">
                <h3>Avg Memory</h3>
                <div class="summary-value {memory_status}">{avg_memory:.1f}</div>
                <div class="summary-unit">MB</div>
            </div>
            <div class="summary-card">
                <h3>Max CPU Time</h3>
                <div class="summary-value">{max_cpu:.1f}</div>
                <div class="summary-unit">seconds</div>
            </div>
            <div class="summary-card">
                <h3>Monitoring Duration</h3>
                <div class="summary-value">{duration_hours:.1f}</div>
                <div class="summary-unit">hours</div>
            </div>
            <div class="summary-card">
                <h3>Data Points</h3>
                <div class="summary-value">{len(metrics_df):,}</div>
                <div class="summary-unit">samples</div>
            </div>
        </div>
"""
    
    def _html_trades_chart(self):
        """Create trades timeline chart"""
        metrics_df = self.df[self.df['type'] == 'metrics'].copy() if 'type' in self.df.columns else self.df
        
        if 'trades_total' not in metrics_df.columns or 'timestamp' not in metrics_df.columns:
            return ""
        
        # Prepare data
        chart_df = metrics_df[['timestamp', 'trades_total', 'trades_delta']].dropna()
        
        if len(chart_df) == 0:
            return ""
        
        # Create JSON data for Plotly
        timestamps = chart_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
        trades_total = chart_df['trades_total'].tolist()
        trades_delta = chart_df['trades_delta'].tolist()
        
        return f"""
        <div class="chart-container">
            <h2 class="chart-title">📈 Trading Activity Timeline</h2>
            <div id="tradesChart" class="chart"></div>
            <script>
                var trace1 = {{
                    x: {json.dumps(timestamps)},
                    y: {json.dumps(trades_total)},
                    name: 'Cumulative Trades',
                    type: 'scatter',
                    mode: 'lines',
                    line: {{color: '#00ff88', width: 2}},
                    yaxis: 'y1'
                }};
                
                var trace2 = {{
                    x: {json.dumps(timestamps)},
                    y: {json.dumps(trades_delta)},
                    name: 'Trades per Interval',
                    type: 'bar',
                    marker: {{color: '#00d4ff'}},
                    yaxis: 'y2'
                }};
                
                var layout = {{
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: {{color: '#e0e0e0'}},
                    xaxis: {{
                        gridcolor: '#333',
                        title: 'Time'
                    }},
                    yaxis: {{
                        gridcolor: '#333',
                        title: 'Cumulative Trades',
                        side: 'left'
                    }},
                    yaxis2: {{
                        gridcolor: '#333',
                        title: 'Trades per Interval',
                        overlaying: 'y',
                        side: 'right'
                    }},
                    legend: {{x: 0.02, y: 0.98}},
                    hovermode: 'x unified'
                }};
                
                Plotly.newPlot('tradesChart', [trace1, trace2], layout, {{responsive: true}});
            </script>
        </div>
"""
    
    def _html_system_performance(self):
        """Create system performance chart"""
        metrics_df = self.df[self.df['type'] == 'metrics'].copy() if 'type' in self.df.columns else self.df
        
        if 'cpu_seconds' not in metrics_df.columns or 'timestamp' not in metrics_df.columns:
            return ""
        
        chart_df = metrics_df[['timestamp', 'cpu_seconds']].dropna()
        chart_df = chart_df[chart_df['cpu_seconds'] > 0]
        
        if len(chart_df) == 0:
            return ""
        
        timestamps = chart_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
        cpu_values = chart_df['cpu_seconds'].tolist()
        
        return f"""
        <div class="chart-container">
            <h2 class="chart-title">⚙️ CPU Performance</h2>
            <div id="cpuChart" class="chart"></div>
            <script>
                var trace = {{
                    x: {json.dumps(timestamps)},
                    y: {json.dumps(cpu_values)},
                    name: 'CPU Time',
                    type: 'scatter',
                    mode: 'lines',
                    fill: 'tozeroy',
                    line: {{color: '#ff6b35', width: 2}},
                    fillcolor: 'rgba(255, 107, 53, 0.3)'
                }};
                
                var layout = {{
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: {{color: '#e0e0e0'}},
                    xaxis: {{
                        gridcolor: '#333',
                        title: 'Time'
                    }},
                    yaxis: {{
                        gridcolor: '#333',
                        title: 'CPU Seconds'
                    }},
                    hovermode: 'x unified'
                }};
                
                Plotly.newPlot('cpuChart', [trace], layout, {{responsive: true}});
            </script>
        </div>
"""
    
    def _html_error_timeline(self):
        """Create error timeline"""
        metrics_df = self.df[self.df['type'] == 'metrics'].copy() if 'type' in self.df.columns else self.df
        
        if 'errors_total' not in metrics_df.columns or 'timestamp' not in metrics_df.columns:
            return ""
        
        chart_df = metrics_df[['timestamp', 'errors_total', 'errors_delta']].dropna()
        
        if len(chart_df) == 0:
            return ""
        
        timestamps = chart_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
        errors_total = chart_df['errors_total'].tolist()
        errors_delta = chart_df['errors_delta'].tolist()
        
        return f"""
        <div class="chart-container">
            <h2 class="chart-title">⚠️ Error Timeline</h2>
            <div id="errorChart" class="chart"></div>
            <script>
                var trace1 = {{
                    x: {json.dumps(timestamps)},
                    y: {json.dumps(errors_total)},
                    name: 'Total Errors',
                    type: 'scatter',
                    mode: 'lines',
                    line: {{color: '#ff3344', width: 2}}
                }};
                
                var trace2 = {{
                    x: {json.dumps(timestamps)},
                    y: {json.dumps(errors_delta)},
                    name: 'New Errors',
                    type: 'bar',
                    marker: {{color: '#ffaa00'}}
                }};
                
                var layout = {{
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: {{color: '#e0e0e0'}},
                    xaxis: {{
                        gridcolor: '#333',
                        title: 'Time'
                    }},
                    yaxis: {{
                        gridcolor: '#333',
                        title: 'Error Count'
                    }},
                    legend: {{x: 0.02, y: 0.98}},
                    hovermode: 'x unified'
                }};
                
                Plotly.newPlot('errorChart', [trace1, trace2], layout, {{responsive: true}});
            </script>
        </div>
"""
    
    def _html_memory_cpu_chart(self):
        """Create memory and CPU combined chart"""
        metrics_df = self.df[self.df['type'] == 'metrics'].copy() if 'type' in self.df.columns else self.df
        
        if 'memory_mb' not in metrics_df.columns or 'timestamp' not in metrics_df.columns:
            return ""
        
        chart_df = metrics_df[['timestamp', 'memory_mb', 'cpu_seconds']].dropna()
        chart_df = chart_df[chart_df['memory_mb'] > 0]
        
        if len(chart_df) == 0:
            return ""
        
        timestamps = chart_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
        memory_values = chart_df['memory_mb'].tolist()
        cpu_values = chart_df['cpu_seconds'].tolist()
        
        return f"""
        <div class="chart-container">
            <h2 class="chart-title">💾 System Resources</h2>
            <div id="resourceChart" class="chart"></div>
            <script>
                var trace1 = {{
                    x: {json.dumps(timestamps)},
                    y: {json.dumps(memory_values)},
                    name: 'Memory (MB)',
                    type: 'scatter',
                    mode: 'lines',
                    line: {{color: '#00d4ff', width: 2}},
                    yaxis: 'y1'
                }};
                
                var trace2 = {{
                    x: {json.dumps(timestamps)},
                    y: {json.dumps(cpu_values)},
                    name: 'CPU (seconds)',
                    type: 'scatter',
                    mode: 'lines',
                    line: {{color: '#ff6b35', width: 2}},
                    yaxis: 'y2'
                }};
                
                var layout = {{
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: {{color: '#e0e0e0'}},
                    xaxis: {{
                        gridcolor: '#333',
                        title: 'Time'
                    }},
                    yaxis: {{
                        gridcolor: '#333',
                        title: 'Memory (MB)',
                        side: 'left'
                    }},
                    yaxis2: {{
                        gridcolor: '#333',
                        title: 'CPU (seconds)',
                        overlaying: 'y',
                        side: 'right'
                    }},
                    legend: {{x: 0.02, y: 0.98}},
                    hovermode: 'x unified'
                }};
                
                Plotly.newPlot('resourceChart', [trace1, trace2], layout, {{responsive: true}});
            </script>
        </div>
"""
    
    def _html_footer(self):
        """HTML footer"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f"""
        <div class="footer">
            <p>Cthulu Metrics Dashboard | Generated: {now}</p>
            <p>Monitoring data visualization for continuous trading operations</p>
        </div>
    </div>
</body>
</html>
"""
    
    def create_static_charts(self):
        """Create static chart images (PNG)"""
        print("Creating static charts...")
        
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            from matplotlib.dates import DateFormatter
            import matplotlib.dates as mdates
            
        except ImportError:
            print("matplotlib not available, skipping static charts")
            return False
        
        metrics_df = self.df[self.df['type'] == 'metrics'].copy() if 'type' in self.df.columns else self.df
        
        if len(metrics_df) == 0:
            print("No metrics data to visualize")
            return False
        
        # Set dark theme
        plt.style.use('dark_background')
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.patch.set_facecolor('#0a0e27')
        
        # Trades timeline
        if 'trades_total' in metrics_df.columns and 'timestamp' in metrics_df.columns:
            ax = axes[0, 0]
            trade_data = metrics_df[['timestamp', 'trades_total']].dropna()
            ax.plot(trade_data['timestamp'], trade_data['trades_total'], 
                   color='#00ff88', linewidth=2, label='Total Trades')
            ax.set_title('Trading Activity', fontsize=14, color='#00d4ff', pad=10)
            ax.set_xlabel('Time', color='#888')
            ax.set_ylabel('Total Trades', color='#888')
            ax.grid(True, alpha=0.2, color='#333')
            ax.legend()
            ax.tick_params(colors='#888')
        
        # Memory usage
        if 'memory_mb' in metrics_df.columns and 'timestamp' in metrics_df.columns:
            ax = axes[0, 1]
            mem_data = metrics_df[metrics_df['memory_mb'] > 0][['timestamp', 'memory_mb']].dropna()
            ax.plot(mem_data['timestamp'], mem_data['memory_mb'], 
                   color='#00d4ff', linewidth=2, label='Memory')
            ax.fill_between(mem_data['timestamp'], mem_data['memory_mb'], 
                           alpha=0.3, color='#00d4ff')
            ax.set_title('Memory Usage', fontsize=14, color='#00d4ff', pad=10)
            ax.set_xlabel('Time', color='#888')
            ax.set_ylabel('Memory (MB)', color='#888')
            ax.grid(True, alpha=0.2, color='#333')
            ax.legend()
            ax.tick_params(colors='#888')
        
        # CPU usage
        if 'cpu_seconds' in metrics_df.columns and 'timestamp' in metrics_df.columns:
            ax = axes[1, 0]
            cpu_data = metrics_df[metrics_df['cpu_seconds'] > 0][['timestamp', 'cpu_seconds']].dropna()
            ax.plot(cpu_data['timestamp'], cpu_data['cpu_seconds'], 
                   color='#ff6b35', linewidth=2, label='CPU Time')
            ax.fill_between(cpu_data['timestamp'], cpu_data['cpu_seconds'], 
                           alpha=0.3, color='#ff6b35')
            ax.set_title('CPU Performance', fontsize=14, color='#00d4ff', pad=10)
            ax.set_xlabel('Time', color='#888')
            ax.set_ylabel('CPU Seconds', color='#888')
            ax.grid(True, alpha=0.2, color='#333')
            ax.legend()
            ax.tick_params(colors='#888')
        
        # Errors timeline
        if 'errors_total' in metrics_df.columns and 'timestamp' in metrics_df.columns:
            ax = axes[1, 1]
            error_data = metrics_df[['timestamp', 'errors_total']].dropna()
            ax.plot(error_data['timestamp'], error_data['errors_total'], 
                   color='#ff3344', linewidth=2, label='Total Errors')
            ax.set_title('Error Timeline', fontsize=14, color='#00d4ff', pad=10)
            ax.set_xlabel('Time', color='#888')
            ax.set_ylabel('Total Errors', color='#888')
            ax.grid(True, alpha=0.2, color='#333')
            ax.legend()
            ax.tick_params(colors='#888')
        
        # Adjust layout and save
        plt.tight_layout(pad=3)
        
        output_file = self.output_dir / 'metrics_charts.png'
        plt.savefig(output_file, dpi=150, facecolor='#0a0e27', edgecolor='none')
        plt.close()
        
        print(f"Saved static charts to {output_file}")
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Visualize Cthulu metrics with interactive dashboard'
    )
    parser.add_argument(
        '--input',
        default='../metrics_clean.csv',
        help='Input clean metrics CSV (default: ../metrics_clean.csv)'
    )
    parser.add_argument(
        '--output-dir',
        default='..',
        help='Output directory (default: ..)'
    )
    parser.add_argument(
        '--window',
        type=float,
        default=24,
        help='Rolling window in hours for visualization (default: 24)'
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    input_file = (script_dir / args.input).resolve()
    output_dir = (script_dir / args.output_dir).resolve()
    
    print("="*60)
    print("Cthulu Metrics Visualizer")
    print("="*60)
    print(f"Input file: {input_file}")
    print(f"Output dir: {output_dir}")
    print(f"Window: {args.window} hours")
    print()
    
    # Check input exists
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        print("Run update_metrics_spreadsheet.py first to generate clean data")
        return 1
    
    # Create visualizer
    visualizer = MetricsVisualizer(input_file, output_dir, args.window)
    
    # Load data
    if not visualizer.load_data():
        return 1
    
    # Create visualizations
    dashboard_file = visualizer.create_html_dashboard()
    visualizer.create_static_charts()
    
    print()
    print("="*60)
    print("Visualization complete!")
    print("="*60)
    print(f"\n📊 Open dashboard: {dashboard_file}")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
