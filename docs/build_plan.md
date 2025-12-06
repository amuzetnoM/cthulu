# Adaptive Trading Intelligence — Build Plan

## File
`/c:/workspace/herald/build_plan.md`

## Summary
A staged, modular implementation plan for a MetaTrader 5 (MT5) trading bot. 
Start with a robust foundation (connection, execution, basic strategy, risk controls), then iteratively add analytical, machine learning, and production features. Emphasize modularity, testability, safety, and observability so new techniques and signals can be integrated without disrupting core behavior.

---

## Goals
- Build a working MT5 bot that can open/close positions and be extended safely.
- Create a clear architecture for incremental feature addition and experimentation.
- Ensure every component is testable, auditable, and deployable.

Non-goals:
- Optimize or tune advanced ML models in phase 1.
- Replace professional risk-management or infrastructure teams.

---

## Table of Contents
1. Architecture overview  
2. Phase-by-phase plan  
3. Component specifications  
4. Interfaces and data contracts  
5. Risk management & safety  
6. Testing & validation strategy  
7. CI/CD, deployment, and observability  
8. Roadmap / Milestones  
9. Quick start snippet (SMA crossover)

---

## 1. Architecture overview
Design principles:
- Single Responsibility: each module has a focused role.
- Clear boundaries: communication via well-defined interfaces/messages.
- Replaceable implementations: e.g., strategy plugins, data sources.
- Event-driven core: signals → trade requests → execution → feedback.

High-level components:
- Connector: MT5 session management, reconnects, rate-limits.
- Data Layer: historical and live market feed, normalization.
- Strategy Layer: pluggable strategies (SMA crossover to start).
- Execution Engine: order placement, modification, cancellation.
- Risk Engine: position sizing, stop loss / take profit enforcement.
- Persistence: trade logs, signals, metrics (SQLite / Postgres).
- Orchestration / Scheduler: manage periodic tasks and backtests.
- Observability: logging, metrics, alerts, dashboards.

Data flow (simplified):
market data -> data layer -> strategy -> signal -> risk check -> execution -> persistence -> monitoring

---

## 2. Phase-by-phase plan

Phase 1 — Foundation (MUST)
- MT5 Connection Module
    - Reliable connect/disconnect, timeout handling, reconnection policy.
    - Session health checks.
- Data ingestion
    - Fetch history, stream ticks and bars, normalization to Pandas.
- Basic Strategy
    - Simple moving average (SMA) crossover strategy on a configurable symbol/timeframe.
- Execution & Risk
    - Open/close logic, stop loss, take profit, position-sizing rule.
- Persistence & Logging
    - Structured logs, action audit trail, simple database schema.
- Local backtest harness for deterministic verification.

Phase 2 — Technical Analysis Layer
- Indicator library integration (RSI, ADX, Ichimoku, etc.).
- Multi-timeframe support and signal aggregation.
- Modular strategy registry and plugin loader.
- Performance improvements for high-frequency sampling.

Phase 3 — Machine Learning Integration
- Offline model evaluation pipeline (scikit-learn/PyTorch).
- Simple supervised models and feature engineering from TA.
- Model serving for inference (local or lightweight REST/gRPC).
- Model training reproducibility and versioning.

Phase 4 — Advanced Intelligence
- Reinforcement learning experiments (DQN/PPO) in sandboxed environments.
- Sentiment and alternative data ingestion (news, social).
- Regime detection and adaptive parameterization.

Phase 5 — Production Features
- Automated backtesting pipeline with walk-forward testing.
- Real-time monitoring dashboard and alerting.
- Safe deployment automation: canary / staging.
- Audit reports and trade-performance analytics.

---


Connector (MT5)
- Exposes: connect(), disconnect(), is_connected(), get_rates(symbol, timeframe, n), subscribe_ticks(symbols)
- Handles: login config, retries, exception consolidation

Data Layer
- Normalizes to DataFrame with timestamp index, OHLCV, volume.
- Stores raw and resampled series.
- Caching layer for repeated backtests.

Strategy Interface (example)
- Methods: on_bar(bar), on_tick(tick), configure(params), state()
- Returns: Signal objects {type: LONG/SHORT/CLOSE, confidence, reason}

Execution Engine
- Receives Signal => makes OrderRequest after risk approval.
- Supports market/limit orders, partial fills handling.
- Idempotent order submission and external reconciliation.

Risk Engine
- Position sizing: fixed lots, percent of balance, volatility-based sizing.
- Hard guards: max exposure per-symbol, max total drawdown, daily stop-loss.
- Emergency shutdown API.

Persistence
- Schemas: trades, orders, positions, signals, metrics.
- Historical retention plan and export capability.

Observability
- Structured JSON logs, metrics (Prometheus), trace spans for critical ops.
- Alerting for connection loss, order failures, guard triggers.

---

## 4. Interfaces and data contracts
- Signal JSON:
    - {id, timestamp, symbol, timeframe, side, action, size_hint, price, stop_loss, take_profit, metadata}
- OrderRequest:
    - {signal_id, symbol, side, volume, order_type, price, sl, tp, client_tag}
- ExecutionResult:
    - {order_id, status, executed_price, executed_volume, timestamp, error (optional)}

Ensure all modules validate and log both requests and responses.

---

## 5. Risk management & safety
Mandatory runtime checks:
- Max position size per symbol and overall exposure.
- Per-day maximum loss limit and auto-pause behavior.
- Slippage and spread thresholds (reject trades if abnormal).
- Simulated mode toggle to test logic without real orders.
- Manual kill switch accessible via CLI or dashboard.

---

## 6. Testing & validation
- Unit tests for each pure module (indicators, position sizing).
- Integration tests: connector + execution in demo accounts or simulator.
- Deterministic backtests with seeded RNG and retained environments.
- Regression tests for historical trade-results comparison.
- Continuous metrics: PnL, Sharpe, max drawdown, win rate.

---

## 7. CI/CD, deployment, and observability
- CI: run lint, unit tests, static analysis, minimal backtest on PRs.
- CD: artifact build (Docker), staged deployment (canary on demo account), rollback path.
- Secrets: store credentials in secure vault; avoid committing keys.
- Monitoring: logs to central store, key metrics to Prometheus/Grafana, alerts via email/Slack.

---

## 8. Roadmap / Milestones (example timeline)
- Week 1–2: Connector, data ingestion, SMA strategy, basic execution.
- Week 3: Persistence, logging, simple backtest harness.
- Week 4: Risk engine, simulated run on demo account, first integration tests.
- Month 2–3: TA indicator suite, multi-timeframe aggregation.
- Month 3–6: ML experiments and model inference pipeline.
- Ongoing: hardening, dashboards, and production rollout.

---

## 9. Quick start: SMA crossover (pseudocode)
```python
# high-level pseudocode
from mt5_connector import MT5Connector
from strategy import SmaCrossover
from execution import ExecutionEngine
from risk import RiskEngine
from persistence import DB

mt5 = MT5Connector(config)
mt5.connect()

data = mt5.get_rates("EURUSD", timeframe="H1", n=500)
strategy = SmaCrossover(short_window=20, long_window=50)
signal = strategy.generate_signal(data)

if signal:
        order = RiskEngine.approve(signal, account_state=mt5.account_info())
        if order.approved:
                result = ExecutionEngine.place_order(order)
                DB.record(result)
```

---

## Appendix: Initial checklist
- [ ] Add config schema and secrets handling
- [ ] Implement MT5 connector with health checks
- [ ] Implement Data Layer and SMA strategy
- [ ] Implement Execution Engine and Risk Engine basic guards
- [ ] Add persistence and structured logging
- [ ] Run integration test on demo account

---

This plan focuses on a safe, incremental path from a functional SMA-based MT5 bot to a research-friendly, production-capable platform with clear extension points for indicators and ML models.
## 3. Component specifications
