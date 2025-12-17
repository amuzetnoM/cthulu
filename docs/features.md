# Herald Features (exhaustive)

This document lists the current, implemented features of Herald (as of the latest release).

Core trading & infrastructure
- MT5 connector with robust connect/reconnect and account introspection
- Config-driven run modes (dry-run, live-run gating via environment variables)
- Typed config schema and interactive NLP setup wizard
- Database persistence for signals and trades (sqlite by default)
- Metrics collector and logging (file and stdout)

Execution & risk
- Execution engine supporting MARKET / LIMIT orders, idempotency and reconciliation
- Idempotent order submission and tracking (client_tag based)
- Idempotent order close logic with filling-mode fallbacks (IOC/FOK) and retries
- Risk manager with position sizing, max exposure, and dynamic SL suggestions
- Exit strategies: Trailing Stop, Time-based, Profit Target, Adverse Movement

Position management
- Position Manager for track/monitor of Herald positions
- TradeManager for adopting external/manual trades and applying protective SL/TP
- Pending SL/TP retry queue with exponential backoff

Monitoring & automation
- TradeMonitor: background poller recording market snapshots and pending SL/TP
- Monitor emits ML events (heartbeat, market_snapshot, pending_sl_tp)
- Health checks and reconnect logic for MT5

ML & Instrumentation
- MLDataCollector: non-blocking JSONL gzipped writer (queue + background writer)
- Events captured: order_request, execution, market_snapshot, monitor.*, news_event, calendar_event, advisory.signal
- Rotate-by-size and fallback synchronous write for robustness
- Unit & gated integration tests for ML instrumentation

News & economic calendar
- Pluggable adapters: RSS adapter (no API), NewsAPI adapter, FRED adapter, TradingEconomics calendar adapter
- NewsManager: adapter orchestration with FileCache TTL for caching and fallback
- NewsIngestor: periodic fetcher that writes `news_event` and `calendar_event` into ML collector
- TradingEconomics adapter normalizes event importance (low/medium/high) for ML features
- Monitor integration: high-impact events can pause trading and emit alerts

Advisory & Ghost modes
- Advisory mode: record advisory signals without executing orders (advisory logging + ML events)
- Ghost mode: configurable small "test" trades to validate live plumbing (strict caps, durations, log-only option)
- Safety gates and logging for both advisory and ghost modes; disabled by default

Testing & CI
- Unit tests covering adapters, monitor, ML collector, advisory manager
- Integration tests gated by env flags to avoid unintended live API calls (e.g., RUN_NEWS_INTEGRATION, RUN_MT5_INTEGRATION)

Extensibility
- Pluggable adapters and modular components for indicators, strategies, and exit rules
- Clear extension points: add new news adapters, new exit strategies, new ML event types

Docs & releases
- CHANGELOG and RELEASE_NOTES placeholders; release workflow integrated
- A `herald/docs` folder with usage docs and feature descriptions


If you want this exported into a stakeholder-ready one-page PDF or a table of features grouped by priority, I can create that next.