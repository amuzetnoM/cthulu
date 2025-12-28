---
title: Observability & Metrics
description: Performance metrics, Prometheus exporter, and guidance for monitoring Cthulhu
tags: [observability, metrics, prometheus]
slug: /docs/observability/metrics
---

# Observability & Performance Metrics

This document describes Cthulhu's performance metrics, how they're computed, and how to expose them via the built-in Prometheus exporter.

## Overview

Cthulhu now produces a comprehensive performance snapshot that is suitable for realtime monitoring and historical analysis.
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

## Prometheus exporter

Cthulhu includes a lightweight Prometheus exporter (`cthulhu.observability.prometheus.PrometheusExporter`) that can be enabled via configuration and will expose the following metric families (prefix configurable via `prefix`):

- `<prefix>_trades_total`
- `<prefix>_trades_won`
- `<prefix>_trades_lost`
- `<prefix>_pnl_total`, `<prefix>_profit_total`, `<prefix>_loss_total`
- `<prefix>_win_rate`, `<prefix>_profit_factor`
- `<prefix>_drawdown_percent`, `<prefix>_drawdown_abs`
- `<prefix>_drawdown_duration_seconds`, `<prefix>_current_drawdown_duration_seconds`
- `<prefix>_avg_rr`, `<prefix>_median_rr`, `<prefix>_rr_count`
- `<prefix>_expectancy`
- `<prefix>_sharpe`, `<prefix>_rolling_sharpe`
- Per-symbol: `<prefix>_symbol_realized_pnl{symbol}`, `<prefix>_symbol_unrealized_pnl{symbol}`, `<prefix>_symbol_open_positions{symbol}`, `<prefix>_symbol_exposure{symbol}`

### How to enable

Add the following to your config JSON under `observability`:

```json
"observability": {
  "prometheus": {
    "enabled": true,
    "prefix": "cthulhu"
  }
}
```

Then run Cthulhu normally. The exporter is updated automatically during the main loop (on the scheduled performance summary sync) and can be written to a textfile (for Node Exporter's textfile collector) or extended to serve via HTTP if required.

## Best practices

- Use `avg_rr`, `median_rr`, and `rr_count` together to understand the distribution and sample size of R:R statistics.
- Monitor `expectancy` to track whether the strategy has positive expected value per trade.
- Use `max_drawdown_duration_seconds` combined with `max_drawdown_pct` to know how long drawdowns persist and inform risk decisions.
- Compare `sharpe_ratio` and `rolling_sharpe` to detect recent changes in strategy behavior.

## Troubleshooting & notes

- Metrics rely on accurate trade recording in the database. Ensure the database is persisted between runs for historical metrics to be meaningful.
- If you observe `UNKNOWN` symbols in metrics, check your strategy config to ensure `config['strategy']['params']['symbol']` is set; some strategies were updated to rely on this field.

---

For examples and more details, see `docs/changelog/CHANGELOG.md` and the tests (`tests/unit/test_metrics_improved.py`, `tests/unit/test_metrics_prometheus_integration.py`).