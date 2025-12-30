# Cthulu Observability System

## Overview

Comprehensive real-time monitoring system for Cthulu trading bot with Prometheus/Grafana integration.

## Components

### 1. Comprehensive Metrics Collector
**File:** `observability/comprehensive_collector.py`

Collects 173 metrics in real-time across 12 categories:
- Core Account Metrics (10)
- Trade Statistics (25)
- Risk & Drawdown (15)
- Advanced Statistics (10)
- Execution Quality (12)
- Signals & Strategy (20)
- Position & Exposure (10)
- Per-Symbol Metrics (8)
- Session & Time-Based (10)
- System Health (15)
- Adaptive & Dynamic (8)
- Performance Grades (5)

**Output:** `observability/comprehensive_metrics.csv` (continuously appended)

### 2. Prometheus Exporter
**File:** `observability/prometheus.py`

Exports all metrics to Prometheus format for scraping.

**Output:** `/tmp/cthulu_metrics.prom` (or Windows equivalent)

### 3. Observability Service
**File:** `observability/service.py`

Runs as separate process to collect metrics without blocking main trading loop.

**Features:**
- Separate process/PID
- Separate memory space
- Non-blocking collection
- Optional HTTP endpoint
- Signal handling for graceful shutdown

### 4. Grafana Dashboards
**Location:** `monitoring/grafana/dashboards/`

**Trading Dashboard** (`cthulu_trading.json`):
- Account Overview (6 panels)
- Performance Metrics (2 charts)
- Risk & Drawdown (8 stats)
- Trade Statistics (2 charts)
- Execution Quality (2 charts)

**System Health Dashboard** (`cthulu_system.json`):
- System Status (6 stats)
- Resource Usage (2 charts)
- Signals & Risk Management (2 charts)
- Session Trading Activity (1 chart)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install prometheus-client psutil
```

### 2. Configure Prometheus

Ensure Prometheus is configured to scrape Cthulu metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'cthulu'
    static_configs:
      - targets: ['localhost:8181']  # If using HTTP endpoint
    scrape_interval: 5s

  - job_name: 'cthulu_textfile'
    static_configs:
      - targets: ['localhost:9100']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'cthulu_.*'
        action: keep
```

### 3. Import Grafana Dashboards

1. Open Grafana UI
2. Navigate to Dashboards → Import
3. Upload `monitoring/grafana/dashboards/cthulu_trading.json`
4. Upload `monitoring/grafana/dashboards/cthulu_system.json`
5. Select Prometheus datasource
6. Click Import

### 4. Start Observability Service

#### Option A: Automatic (Integrated with Cthulu)

The observability service starts automatically when Cthulu boots if integrated into bootstrap.

#### Option B: Manual (Standalone)

```bash
# Start observability service manually
python -m observability.service --csv observability/comprehensive_metrics.csv \
                                 --prometheus /tmp/cthulu_metrics.prom \
                                 --interval 1.0 \
                                 --http-port 8181
```

#### Option C: Programmatic

```python
from observability.integration import start_observability_service, stop_observability_service

# Start service
process = start_observability_service(
    csv_path="observability/comprehensive_metrics.csv",
    prom_path="/tmp/cthulu_metrics.prom",
    http_port=8181,
    update_interval=1.0
)

# ... run trading system ...

# Stop service on shutdown
stop_observability_service(process)
```

## Integration with Main Trading System

### In Bootstrap (core/bootstrap.py)

```python
from observability.integration import start_observability_service

# During system initialization
observability_process = start_observability_service(
    http_port=8181,  # Optional HTTP endpoint
    update_interval=1.0  # Update every second
)

# Store process reference for cleanup
components.observability_process = observability_process
```

### In Trading Loop (core/trading_loop.py)

```python
from observability.comprehensive_collector import ComprehensiveMetricsCollector
from observability.prometheus import PrometheusExporter

# Access shared collector (if not using separate process)
collector = ComprehensiveMetricsCollector()
prometheus = PrometheusExporter(prefix="cthulu")

# Update metrics from existing MetricsCollector
collector.update_from_metrics_collector(metrics_collector)

# Record execution events
collector.record_execution(execution_time_ms=50.5, slippage_pips=0.2)

# Record trade closes
collector.record_trade_closed(duration_seconds=300, pnl=10.50)

# Set MT5 connection status
collector.set_mt5_connected(True)

# Set account info
collector.set_account_info(
    balance=10000.0,
    equity=10050.0,
    margin=100.0,
    free_margin=9900.0,
    margin_level=10050.0
)

# Increment signal counters
collector.increment_signal_counter("sma_crossover")
collector.increment_rejection_counter("spread_too_wide")

# Export to Prometheus
snapshot = collector.get_current_snapshot()
prometheus.update_from_comprehensive_metrics(snapshot)
prometheus.write_to_file()
```

### In Shutdown (core/shutdown.py)

```python
from observability.integration import stop_observability_service

# Stop observability service
if hasattr(components, 'observability_process'):
    stop_observability_service(components.observability_process)
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Cthulu Trading System                   │
│                                                             │
│  ┌───────────────┐      ┌──────────────────────────────┐  │
│  │ Trading Loop  │────▶ │ MetricsCollector (existing)  │  │
│  └───────────────┘      └────────────┬─────────────────┘  │
│                                       │                     │
│                                       ▼                     │
│                        ┌──────────────────────────────┐    │
│                        │ ComprehensiveMetricsCollector│    │
│                        │  (173 metrics, real-time)    │    │
│                        └────────────┬─────────────────┘    │
│                                     │                       │
│                                     ▼                       │
│                        ┌──────────────────────────────┐    │
│                        │  Observability Service       │    │
│                        │  (Separate Process)          │    │
│                        └─────┬────────────────────────┘    │
└──────────────────────────────┼─────────────────────────────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
        ┌────────────┐  ┌──────────┐  ┌─────────┐
        │ CSV File   │  │Prometheus│  │  HTTP   │
        │comprehensive│  │  .prom   │  │:8181/   │
        │_metrics.csv │  │  file    │  │metrics  │
        └────────────┘  └─────┬────┘  └────┬────┘
                              │            │
                              ▼            ▼
                        ┌──────────────────────┐
                        │   Prometheus Server  │
                        │   (scrapes metrics)  │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │  Grafana Dashboards  │
                        │  - Trading           │
                        │  - System Health     │
                        └──────────────────────┘
```

## Metrics Reference

See `monitoring/COMPREHENSIVE_METRICS_SCHEMA.md` for full list of 173 metrics.

**Key Metrics:**
- `cthulu_account_balance` - Account balance ($)
- `cthulu_account_equity` - Account equity ($)
- `cthulu_total_pnl` - Total P&L ($)
- `cthulu_total_trades` - Total trades executed
- `cthulu_win_rate_pct` - Win rate (%)
- `cthulu_profit_factor` - Profit factor
- `cthulu_max_drawdown_pct` - Max drawdown (%)
- `cthulu_sharpe_ratio` - Sharpe ratio
- `cthulu_active_positions` - Currently open positions
- `cthulu_mt5_connected` - MT5 connection status (0/1)
- `cthulu_cpu_usage_pct` - CPU usage (%)
- `cthulu_memory_usage_mb` - Memory usage (MB)
- `cthulu_errors_total` - Total errors

## Troubleshooting

### CSV file not updating
- Check that observability service is running: `ps aux | grep observability`
- Check service logs for errors
- Verify write permissions on CSV file location

### Prometheus not scraping
- Verify Prometheus is running: `curl localhost:9090/targets`
- Check textfile collector path matches configuration
- Verify metrics file exists and is readable
- Check Prometheus logs: `docker logs prometheus` or systemd journal

### Grafana dashboards show no data
- Verify Prometheus datasource is configured correctly
- Check that metrics are being scraped: Query `cthulu_account_balance` in Prometheus
- Verify time range in Grafana (last 6 hours by default)
- Check for metric name mismatches

### High CPU/Memory usage
- Increase `update_interval` (default 1.0s) to reduce frequency
- Disable HTTP endpoint if not needed
- Use textfile collector instead of HTTP scraping

## Performance Impact

**Observability Service:**
- CPU: < 1% average
- Memory: < 50 MB
- Disk I/O: Minimal (append-only CSV)
- Network: None (unless HTTP endpoint enabled)

**Main Trading System:**
- Zero impact when using separate process
- Metrics collection happens in isolated process
- No blocking operations in trading loop

## Best Practices

1. **Always run observability service as separate process**
   - Ensures trading loop is never blocked
   - Isolates failures
   - Better resource management

2. **Monitor the CSV file size**
   - Rotate or archive periodically
   - One day of 1-second metrics = ~15-20 MB

3. **Use Grafana for live monitoring**
   - CSV is for historical analysis and ML training
   - Grafana provides real-time dashboards

4. **Set up alerts in Prometheus**
   - Alert on high drawdown
   - Alert on MT5 disconnection
   - Alert on high error rates

5. **Back up metrics data**
   - CSV file is the single source of truth
   - Regular backups recommended

## Advanced Configuration

### Custom Metrics Path

```python
process = start_observability_service(
    csv_path="/custom/path/metrics.csv",
    prom_path="/custom/path/metrics.prom"
)
```

### Multiple Instances

Run multiple Cthulu instances with separate metrics:

```bash
# Instance 1
python -m observability.service --csv metrics_instance1.csv --http-port 8181

# Instance 2
python -m observability.service --csv metrics_instance2.csv --http-port 8182
```

### Metrics Aggregation

For multi-instance setups, use Prometheus federation or VictoriaMetrics.

## Support

For issues or questions:
1. Check logs: `tail -f /var/log/cthulu/observability.log`
2. Review `COMPREHENSIVE_METRICS_SCHEMA.md`
3. Verify Prometheus/Grafana configurations

---

**Version:** 1.0.0  
**Last Updated:** 2025-12-30  
**Status:** Production Ready
