---
title: OBSERVABILITY
description: Performance metrics, Prometheus exporter, and guidance for monitoring Cthulu
tags: [observability, metrics, prometheus]
sidebar_position: 10
version: 5.2.0
---

![](https://img.shields.io/badge/Version-5.1.0_APEX-4B0082?style=for-the-badge&labelColor=0D1117&logo=git&logoColor=white) 
![](https://img.shields.io/github/last-commit/amuzetnoM/cthulu?style=for-the-badge&labelColor=0D1117&logo=github&logoColor=white) 


## Overview

> This document describes Cthulu's performance metrics, how they're computed, and how to expose them via the built-in Prometheus exporter.

Cthulu now produces a comprehensive performance snapshot that is suitable for realtime monitoring and historical analysis.
Key capabilities:
- Per-trade and per-symbol aggregates (realized/unrealized PnL, wins/losses, exposures)
- Risk:Reward (R:R) tracking (average, median, count)
- Expectancy calculation per trade
- Equity curve and robust max drawdown tracking (magnitude and duration in seconds)
- Rolling Sharpe ratio (configurable window)
- Historical replay of closed trades and seeding of open positions from the database on startup
- Live sync from `PositionManager` to keep metrics accurate during runtime

## PerformanceMetrics fields

Important fields available in `PerformanceMetrics` (snapshot returned by `MetricsCollector.get_metrics()`):

- `total_trades`, `winning_trades`, `losing_trades`
- `gross_profit`, `gross_loss`, `net_profit`
- `win_rate`, `avg_win`, `avg_loss`, `profit_factor`
- `avg_risk_reward`, `median_risk_reward`, `rr_count`
- `expectancy` (per trade)
- `max_drawdown_pct`, `max_drawdown_abs`
- `max_drawdown_duration_seconds`, `current_drawdown_duration_seconds`
- `sharpe_ratio`, `rolling_sharpe`
- `positions_opened_total`, `active_positions`
- `symbol_aggregates` (mapping symbol -> realized_pnl, unrealized_pnl, open_positions, exposure, rr summary)


### Prometheus exporter

Cthulu includes a lightweight Prometheus exporter (`cthulu.observability.prometheus.PrometheusExporter`) that ships with the project and can be enabled via configuration. The exporter exposes the following metric families (prefix configurable via `prefix`):

- `cthulu_trades_total`
- `cthulu_trades_won`
- `cthulu_trades_lost`
- `cthulu_pnl_total`, `cthulu_profit_total`, `cthulu_loss_total`
- `cthulu_win_rate`, `cthulu_profit_factor`
- `cthulu_drawdown_percent`, `cthulu_drawdown_abs`
- `cthulu_drawdown_duration_seconds`, `cthulu_current_drawdown_duration_seconds`
- `cthulu_avg_rr`, `cthulu_median_rr`, `cthulu_rr_count`
- `cthulu_expectancy`
- `cthulu_sharpe`, `cthulu_rolling_sharpe`
- Per-symbol: `cthulu_symbol_realized_pnl{symbol="EURUSD"}`, `cthulu_symbol_unrealized_pnl{symbol}`, `cthulu_symbol_open_positions{symbol}`, `cthulu_symbol_exposure{symbol}`

Notes and recommendations:

- Metric names should be lowercase with underscores (Prometheus best practice). The exporter defaults to the `Cthulu` prefix historically; prefer `cthulu` lowercase in config to match Prometheus conventions.
- Use labels for cardinality control: `symbol`, `strategy`, `mindset`, `env`, and `instance`.
- Use counters for totals and gauges for current state values. Expose histograms for latencies (e.g., `order_latency_seconds_bucket`).

### How to enable (recommended)

Add or update the following to your config JSON under `observability`:

```json
"observability": {
  "prometheus": {
    "enabled": true,
    "prefix": "cthulu",
    "mode": "http",        
    "http_port": 8181       
  }
}
```

Recommended behaviour:

- Expose an HTTP `/metrics` endpoint from the trading app (preferred). This enables direct Prometheus scraping and avoids textfile sync delays.
- If continuing to use Node Exporter's textfile collector, write metrics to a known path (example: `/var/lib/node_exporter/textfile_collectors/cthulu.prom`).

Docker-compose notes (what I added to the repository):

- `docker-compose.yml` now includes `prometheus`, `grafana`, and `node_exporter` services. Prometheus config `monitoring/prometheus.yml` includes a `node_exporter` scrape job and a `rule_files` entry for alerting/recording rules.
- Grafana provisioning files are in `monitoring/grafana/`: `datasource.yml`, `dashboards.yml`, and an initial `dashboards/cthulu_overview.json`.

### Best practices

- Use `cthulu_<domain>_<metric>` naming (lowercase). Example: `cthulu_trades_total`, `cthulu_symbol_realized_pnl{symbol="EURUSD"}`.
- Keep label cardinality low: avoid labels with high unique values (user IDs, timestamps).
- Add recording rules for heavy aggregations (rolling win_rate, per-minute/net PnL) and alerting rules for critical conditions (`cthulu_mt5_connected == 0`, `cthulu_drawdown_percent > 0.2`, `order_latency_seconds` spikes).

### Troubleshooting & notes

- Metrics rely on accurate trade recording in the database. Ensure the database is persisted between runs for historical metrics to be meaningful.
- If you observe `UNKNOWN` symbols in metrics, check your strategy config to ensure `config['strategy']['params']['symbol']` is set.
- Tests: see `tests/unit/test_metrics_improved.py` and `tests/unit/test_metrics_prometheus_integration.py` for example coverage.

## Best practices

- Use `avg_rr`, `median_rr`, and `rr_count` together to understand the distribution and sample size of R:R statistics.
- Monitor `expectancy` to track whether the strategy has positive expected value per trade.
- Use `max_drawdown_duration_seconds` combined with `max_drawdown_pct` to know how long drawdowns persist and inform risk decisions.
- Compare `sharpe_ratio` and `rolling_sharpe` to detect recent changes in strategy behavior.

## Troubleshooting & notes

- Metrics rely on accurate trade recording in the database. Ensure the database is persisted between runs for historical metrics to be meaningful.
- If you observe `UNKNOWN` symbols in metrics, check your strategy config to ensure `config['strategy']['params']['symbol']` is set; some strategies were updated to rely on this field.

---

## RPC Interface

Cthulu includes an RPC server for programmatic control. This enables external monitoring tools and scripts to inject trades and query system state.

**Default Endpoints:**
- `POST http://127.0.0.1:8278/trade` - Submit trade orders
- `GET http://127.0.0.1:8278/provenance` - Query order audit trail

**Configuration:**
```json
{
  "rpc": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 8278
  }
}
```

For complete RPC documentation, see [development_log/rpc.md](development_log/rpc.md).

---

## Real-Time Dashboard & Benchmarking (NEW in v5.1)

Cthulu v5.1 includes a comprehensive real-time monitoring dashboard with benchmarking capabilities.

### Dashboard Location
`observability/reporting/dashboard.html`

### Features

**Real-Time Charts (Auto-Refresh):**
- Balance & Equity tracking
- RSI oscillation with overbought/oversold zones
- ADX trend strength with color coding
- Price movement visualization

**Comprehensive Metrics Display:**
- All trading metrics from `comprehensive_metrics.csv`
- All indicator metrics from `indicator_metrics.csv`
- System health metrics from `system_health_metrics.csv`

**Benchmarking Tools:**
- Performance grade calculation (A+ to F)
- Win rate, profit factor, Sharpe ratio
- Risk:Reward distribution analysis
- Session duration tracking
- Strategy performance comparison

### CSV Data Sources

| CSV File | Purpose | Update Frequency |
|----------|---------|------------------|
| `comprehensive_metrics.csv` | Full trading state | Every loop (~15s) |
| `indicator_metrics.csv` | Technical indicators | Every loop |
| `system_health_metrics.csv` | CPU, memory, connections | Every loop |

### Launching the Dashboard

```powershell
# Option 1: PowerShell one-liner
Start-Process "C:\workspace\cthulu\observability\reporting\dashboard.html"

# Option 2: Run observability suite
cd C:\workspace\cthulu\observability
python run_all_collectors.py

# Option 3: Via monitoring script
.\monitoring\monitor_dashboard.ps1
```

### Custom Benchmarking

The dashboard calculates grades based on:

| Grade | Win Rate | Profit Factor | Criteria |
|-------|----------|---------------|----------|
| A+ | >70% | >3.0 | Exceptional performance |
| A | >60% | >2.5 | Excellent performance |
| B | >55% | >2.0 | Good performance |
| C | >50% | >1.5 | Acceptable performance |
| D | >45% | >1.0 | Below average |
| F | <45% | <1.0 | Needs improvement |

---

For examples and more details, see `docs/Changelog/CHANGELOG.md` and the tests (`tests/unit/test_metrics_improved.py`, `tests/unit/test_metrics_prometheus_integration.py`).


