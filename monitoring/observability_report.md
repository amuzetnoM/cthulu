# Observability Report

Last Updated: 2025-12-29

## Current Setup (what's present)
- Prometheus config: `monitoring/prometheus.yml` (scrapes `Cthulu:8181` and Prometheus itself)
- Local exporter: `observability/prometheus.py` provides a `PrometheusExporter` class and textfile writer
- Trade monitor: `monitoring/trade_monitor.py` records ML events and heartbeat
- Docker compose includes `prometheus` and `grafana` services in the repository root `docker-compose.yml`

## Quick summary of gaps & findings
- Prometheus scrape list is minimal (only `Cthulu` and Prometheus itself). No `node_exporter`, `blackbox`, or other exporters configured.
- Grafana provisioning files are missing; `docker-compose.yml` expects provisioning under `monitoring/grafana/` but those folders are not present.
- Metric naming currently uses `Cthulu_*` prefix via `PrometheusExporter` — good start, but needs strict naming conventions and labels for per-symbol/per-strategy metrics.
- No alerting rules or recording rules configured yet.

## Recommended upgrade plan (high-level)
1. Harden Prometheus:
   - Add `node_exporter` scrape job (host-level metrics), `blackbox_exporter` for endpoint checks.
   - Add relabeling and job/service labels (e.g., `job="cthulu_trading"`, `instance`, `service`) and `external_labels` for cluster identification.
   - Add recording rules for heavy aggregations (per-minute rate, rolling win_rate, drawdown_history).
2. Overhaul Grafana:
   - Provision `datasource` pointing at `http://prometheus:9090`.
   - Add curated dashboards: Overview, Trades & PnL, Risk & Drawdown, Strategy Performance, Latency/Health.
   - Use template variables (`$symbol`, `$strategy`, `$mindset`) and promote per-symbol drilldowns.
3. Masterclass metriculation (metrics design):
   - Use metric names: `cthulu_<domain>_<metric>` (lowercase, underscores). Example: `cthulu_trades_total`, `cthulu_symbol_realized_pnl{symbol="EURUSD"}`.
   - Use labels for cardinality control: `symbol`, `strategy`, `mindset`, `env` (prod/staging), `instance`.
   - Counters vs gauges: use counters for totals (trades_total, sl_tp_success_total), gauges for current values (open_positions, account_balance).
   - Expose histograms for latency-sensitive operations (order_latency_seconds_bucket).
   - Add semantic metrics for business KPIs: `cthulu_net_profit_1d`, `cthulu_win_rate_1d` (via recording rules).
4. Instrumentation & Exporters:
   - Ensure `observability.prometheus.PrometheusExporter` writes to `/var/lib/node_exporter/textfile_collectors/` (if using node textfile collector) or expose `/metrics` HTTP endpoint.
   - Add a lightweight HTTP metrics server (e.g., using `prometheus_client`) for scraping real-time metrics.
5. Alerts & Runbooks:
   - Define alerting rules for critical conditions: `MT5 disconnected`, `daily_loss_exceeded`, `high_order_latency`, `prometheus_down`.
   - Add runbooks and define severity, paging policy.

## Quick start — bring the stack up (local/dev)
Run from repository root:

```powershell
# Start Prometheus + Grafana + Cthulu (detached)
docker-compose up -d

# Tail logs
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

Notes:
- Grafana provisioning files added here so Grafana will load the Prometheus datasource and a starter dashboard on first run.
- If you want me to start the stack now, say so and I'll run `docker-compose up -d` in the terminal (requires Docker).

## Next steps (short-term execution)
- Add `node_exporter` service to `docker-compose.yml` and configure `prometheus.yml` to scrape it.
- Create recording rules and alerting rules files under `monitoring/rules/` and mount in the Prometheus service.
- Replace `PrometheusExporter` to expose `/metrics` over HTTP (preferred) and add histogram metrics for latency.
- Design Grafana dashboards iteratively; start with an Overview dashboard and expand.

## File changes added by this report
- Added Grafana provisioning files under `monitoring/grafana/` (datasource + dashboard)
- Created this `monitoring/observability_report.md`

