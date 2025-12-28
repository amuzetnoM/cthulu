# Signal Stress Test Checklist — Directive

Directive (quick-read): Purpose: authoritative runbook for automated signal stress-testing, monitoring, observability and corrective actions. Current state: Live demo account ****0069, symbol=BTCUSD#, mindset=ultra_aggressive, Prometheus HTTP at http://127.0.0.1:8181/metrics. 

# Cthulu Signal Checklist — Exhaustive Test Matrix

Purpose: provide a surgical, exhaustive list of signals and edge-cases to exercise the full signal→risk→execution lifecycle, including observability and grading hooks.

Instructions: each checklist item includes: name, trigger method, expected system behavior, Prometheus metrics to observe, log lines to validate, grading criteria, and remediation notes.

1) Basic Signal Types
- Long Market Signal (sma_crossover / scalping)
  - Trigger: synthetic bar where fast>slow crossover + indicator conditions met.
  - Expected: Signal generated -> RiskEvaluator approves -> ExecutionEngine places MARKET order -> Order filled (or rejected by broker in demo) -> Metrics: Cthulu_trades_total, Cthulu_pnl_total; Logs: "Signal generated:", "Risk approved:", "Placing MARKET order", "Order executed".
  - Grade: pass if full flow recorded; severity-scaled if rejected with justification (spread, trade_allowed).

- Short Market Signal (mirror of Long)
  - Trigger, expected, metrics, logs as above (SELL).

- Limit/Stop Orders
  - Trigger: create signal requiring LIMIT or STOP; expected order submission with correct price fields and later fill/cancel behavior.
  - Metrics: instrument-specific execution latency, order outcome counts.

2) Strategy Variants
- Scalping (tick -> M1)
- EMA crossover
- Momentum breakout
- Mean reversion
(For each: ensure indicators exist, ATR present, spread thresholds, ensure strategy-specific params respected.)

3) Risk Manager Interactions
- Spread too high (absolute > threshold)
  - Trigger: set connector to fake high spread or simulate via synthetic bar; expected: RiskEvaluator rejects and logs reason.
  - Validate: Cthulu exporter metrics remain unchanged for trade count.

- Spread relative threshold (percent of mid)
  - Trigger: instrument with large price (BTCUSD) and moderate spread; expected: relative check triggers appropriately.

- Position sizing (percent / Kelly)
  - Trigger: signals with varying suggested sizes; validate the size computed follows config/risk limits and reflected in order request provenance.

- Circuit-breaker and daily loss
  - Trigger: simulate multiple losing trades (synthetic) to trip max_daily_loss or circuit break; expected: emergency shutdown flag and no new trades.

4) Execution Edge Cases
- Partial fills and multiple fills
- Rejected orders (broker-side retcode)
- Duplicate order idempotency (same client_tag)
- Orphan trade adoption (external open positions)
- Position close and partial close flows

5) Observability & Telemetry
- Prometheus metrics present and accurate: uptime, trades_total, trades_won/lost, pnl_total, win_rate, profit_factor, drawdown_percent, open_positions, avg_rr, expectancy
- Exporter HTTP and textfile working
- Order provenance log entries and telemetry records present

6) Data/Indicator Issues
- Missing indicator columns (ATR, RSI) -> strategy should log and skip
- NaN values in indicators -> strategy skips
- Price feed gaps -> system should detect and recover

7) Concurrency & Stability
- Multiple simultaneous signals (multi-symbol) -> ensure position limits respected
- High-frequency signal bursts -> idempotency and order throttling
- Restart/resume behavior -> state persistence and resumed metrics

8) Performance & Latency
- Measure time from signal generation to order placement (execution latency metric)
- Measure MT5 round-trip, order confirmation latency, and Prometheus exporter write latency

9) Safety Tests
- Ensure dry-run vs live flags respected
- Ensure trade_allowed checked and prevents real trades if false
- Ensure emergency_shutdown stops executions

10) Grading and Acceptance Criteria (automated)
- Each checklist item must record: start timestamp, end timestamp, duration, outcome (PASS/WARN/FAIL), relevant metrics snapshot, sample log excerpts, and remediation notes.
- Grading metrics (per-item):
  - Signal detection correctness (binary)
  - Execution success rate (0-1)
  - Risk-policy compliance (0-1)
  - Observability coverage (0-1)
  - Latency score (normalized)
- Aggregate grade computed as weighted sum; include formula in SYSTEM_REPORT.md.

---

Automation hooks:
- Each test will be executed programmatically by injecting synthetic bars or invoking test CLI that submits crafted Signal objects into the running loop (test harness to be implemented under monitoring/tests).
- All results will be appended to SYSTEM_REPORT.md with machine-readable JSON snippets and metric snapshots for traceability.

