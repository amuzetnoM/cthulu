## Monitoring & Trade Metrics — Designated Section

This section defines the precise, production-grade monitoring and trade-metrics framework to be used for live validation, tuning and continuous improvement. It is intentionally exhaustive and surgical so that every metric has a clear definition, collection method, frequency, alerting threshold, and recommended remediation/tuning action.

1) Real-time Health Checks (must be present in system report and automated monitor)
- Process & Connectivity
  - Process alive: PID present and responsive (heartbeat interval ≤ poll_interval). Collection: OS process list every 30s. Alert: missing for >30s.
  - MT5 connectivity: connector.get_account_info() succeeds and trade_allowed==True. Collection: every loop. Alert: failures >3 consecutive checks.
- Loop & Timing
  - Loop cycle time: measured per iteration (start->end). Collection: log at INFO per loop. Target: ≤ poll_interval. Alert: sustained overshoot >2× poll_interval.
- Log error/exception rate
  - Errors per minute and distinct stack traces. Collection: tail logs in rolling 1/5/60-minute windows. Alert: any ERROR containing Exception/Traceback or >1 error/min sustained.

2) Core Trade-Specific Metrics (definition, collection, and why it matters)
- Signals Generated (SG)
  - Definition: count of strategy signals created per timeframe (e.g., per hour). Includes signal side, symbol, confidence, and timestamp.
  - Collection: emitted at signal generation (INFO) and stored in Signals DB table.
  - Why: baseline for strategy activity; too low = overly conservative; too high = overtrading risk.
- Signals Accepted (SA)
  - Definition: signals approved by RiskEvaluator (approved==True).
  - Collection: logged when risk_manager.approve returns approved=True with position_size.
  - Metric: Acceptance rate = SA/SG. Target depends on strategy but track as KPI.
- Orders Placed (OP)
  - Definition: market orders actually sent to MT5 (execution_engine.place_order called).
  - Collection: execution returns (order_id, status, latency). Persist in Trades DB.
  - Why: ensures execution path is functioning end-to-end.
- Execution Latency (EL)
  - Definition: time between creation of OrderRequest and MT5 acknowledgement (ms).
  - Collection: measured at call and response in ExecutionEngine. Report percentiles (p50, p95, p99).
  - Alert: p95 latency > 500ms (tunable by market/instrument).
- Slippage (SL)
  - Definition: (executed_price - requested_price) normalized by instrument tick/point.
  - Collection: compare order_req.price (or market mid) vs execution price; record absolute ticks and currency value.
  - Alert: average slippage > configured tolerance (e.g., 3 ticks) or sudden jump.
- Win Rate & Profitability
  - Net P&L per trade, per day, per strategy, per symbol. Track sample size, mean, median, stddev.
  - Expectation: compute Sharpe-like metric and Sortino for downside risk. Monitor rolling 30/90-day stats.
- Max Adverse Excursion (MAE) & Max Favorable Excursion (MFE)
  - Definition: worst drawdown while trade was open, and best excursion respectively.
  - Collection: tracked continuously by PositionTracker while trade open (store high/low vs entry).
  - Use: identify stop distances and profit targets tuning.
- Average Trade Duration (ATD)
  - Definition: time between entry and exit. Distribution informs time-based exits and polling frequency.
- Order Fill Rate / Rejects
  - Definition: fraction of orders rejected or partially filled. Collection from execution result codes.

3) Data Sources & Aggregation
- Primary sources: logs/Cthulu.log, Signals DB, Trades DB (executions), PositionTracker in-memory (persist snapshots), MT5 connector responses.
- Aggregation: Create a lightweight collector (python/prom client or small ingestion script) that reads logs and DB tables every minute and writes time-series to Prometheus or CSV if Prometheus unavailable.
- Storage schema (minimum):
  - signals(id, ts, symbol, side, confidence, strategy, accepted)
  - orders(id, signal_id, ts_request, ts_ack, request_price, execution_price, volume, status, latency_ms)
  - trades(id, order_id, entry_ts, exit_ts, entry_price, exit_price, pnl, mae, mfe)

4) Thresholds & Alerting (suggested defaults)
- Connectivity: MT5 disconnects >3 attempts → alert (pager)
- Errors: any stack trace containing Exception in last 5 minutes → alert
- Acceptance rate: SA/SG < 0.05 (very conservative) or >0.5 (potentially unsafe) → investigate
- Latency: p95 > 500ms → alert
- Slippage: average > configured tolerance per-symbol → alert
- Drawdown: cumulative daily loss > max_daily_loss → emergency shutdown

5) Dashboards & Visualizations (must-haves)
- Real-time panel: process status, loop latency, MT5 connectivity, last signal time, last order time, last trade PnL
- Signal funnel: SG → SA → OP → Filled / Rejected (with rates and counts)
- Trade P&L panel: rolling PnL (1h/24h/7d), average trade PnL, win rate, expectency
- Risk panel: open exposure, exposure per-symbol, position_count, MAE/MFE histograms
- Execution panel: latency percentiles, slippage distribution, fill rate
- Incident timeline: errors/exceptions with stack trace links and associated loop numbers

6) Tuning & Surgical Guidance (how to use metrics to change system)
- If SG is too low: reduce strategy thresholds (lower confidence cutoff, shorten moving average periods) or enable more aggressive strategy (scalping) for test mode.
- If SA/SG is low: loosen risk limits (increase max_position_size_percent) or investigate balance/position constraints.
- If SL or Latency high: investigate execution_engine path, network, and MT5 instance; consider batch sizing or limit orders for less slippage.
- If MAE large relative to ATR: widen stops or reduce position size; if MFE >> TP, consider increasing TP or using scaling exits.
- For persistent inconsistent signals: capture recent bars and indicators for 100 signal events and run offline statistical tests (ADF, stationarity, signal-to-noise).

7) Experimentation & Continuous Validation
- Implement A/B testing of strategy params: run parallel instances with different fast/slow MA pairs and compare SG/SA/OP/PnL over rolling windows.
- Use synthetic backtests and live shadow mode (dry_run true) to collect signal characteristics without risk.
- Automate golden-run verification: the system must show no uncaught exceptions and >=1h runtime with stable metrics before handing to production.

8) Checklist to include in SYSTEM_REPORT.md (automated)
- "Process Alive" timestamp
- "Last Signal Generated" timestamp
- "Last Order Placed" timestamp
- Rolling 1h statistics for SG, SA, OP, WinRate, AvgPnL, p95 Latency, AvgSlippage
- Top-3 contributing errors (last 24h)