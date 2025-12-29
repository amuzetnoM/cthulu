---
title: CHANGELOG
description: Project release notes and version history (canonical)
tags: [changelog, releases]
sidebar_position: 10
slug: /docs/changelog
---

````
_________   __  .__          .__         
\_   ___ \_/  |_|  |__  __ __|  |  __ __ 
/    \  \/\   __\  |  \|  |  \  | |  |  \
\     \____|  | |   Y  \  |  /  |_|  |  /
 \______  /|__| |___|  /____/|____/____/ 
        \/           \/                  
````    

• [View releases on GitHub](https://github.com/amuzetnoM/Cthulu/releases)

![version-badge](https://img.shields.io/badge/version-5.0.1-blue)

 All notable changes are recorded here using Keep a Changelog conventions and Semantic Versioning (https://semver.org/).

---

## UNRELEASED


**Status:** Active development and validation — recent stability, observability, and monitoring improvements have been deployed and validated in live stress tests.

**Summary & Highlights:**
- **120-minute stress testing:** Full-run validation completed during the latest sessions (Target: 120 min). System achieved **B+** overall grade after critical fixes; indicator suite passed **12/12** tests.
- **Adaptive Drawdown Management:** NEW cutting-edge dynamic risk management system with state-based position sizing, trailing equity protection, and survival mode for critical drawdowns.
- **Survival Mode (NEW):** When drawdown exceeds 90%, system enters ultra-defensive mode with micro positions (0.01 lots), 95% confidence requirement, and 5:1 R:R minimum.
- **Runtime indicator resilience:** Added `runtime_` namespacing, aliasing, and safe fallbacks so strategies have deterministic access to `rsi`, `atr`, and `adx` even when runtime indicators are produced dynamically.
- **Observability & monitoring:** Prometheus exporter and automated monitoring scripts (`monitoring/run_stress.ps1`, `monitoring/inject_signals.py`, `scripts/monitor_cthulu.ps1`) were added or improved; metrics are collected to `monitoring/metrics.csv` and exported at `http://127.0.0.1:8181/metrics`.
- **RPC robustness:** Improved RPC error handling and unique signal ID generation to avoid duplicate-order detection and race conditions in high-throughput scenarios.
- **CI & cross-platform:** Windows and coverage support were added to CI workflows and tests were expanded to cover runtime indicator behavior (`tests/test_runtime_indicators.py`).
- **Safety & ergonomics:** Removed blocking `LIVE_RUN_CONFIRM` gate (now emits a clear log warning) and improved startup resilience for missing optional components (e.g., defensive skip of missing `PositionManager` implementations).

### Added
- **Adaptive Drawdown Manager (`risk/adaptive_drawdown.py`):** Complete rewrite of risk management with:
  - Real-time drawdown state machine: NORMAL → CAUTION → WARNING → DANGER → CRITICAL → SURVIVAL
  - Dynamic position sizing multipliers per state (1.0x → 0.75x → 0.5x → 0.25x → 0.1x → 0.05x)
  - Trailing equity high watermark with profit lock-in
  - Market regime detection (trending/ranging/volatile/trap)
  - Liquidity trap detection heuristics
  - Win/lose streak tracking with anti-martingale sizing
  - Survival mode for 90%+ drawdown with recovery strategy
- **Survival Mode:** Ultra-defensive trading for critical drawdowns:
  - Micro position sizing (0.01 lots max)
  - 95% confidence threshold required
  - 5:1 minimum risk:reward ratio
  - Single position limit
  - Trend-following only strategies
  - High-liquidity session filtering
- Prometheus metrics for trading, risk, and system health; automated stress-test orchestrator and signal injection tools.
- `tests/test_runtime_indicators.py` to validate alias/fallback behavior.
- **Negative Balance Protection (Critical):** Comprehensive balance protection system including:
  - Negative balance detection with immediate trading halt
  - Minimum balance threshold enforcement ($10 default)
  - Negative equity detection with emergency position closure
  - Margin call condition monitoring (50% equity/margin ratio threshold)
  - Peak balance tracking with drawdown halt (50% drawdown limit)
  - Free margin validation before new positions
  - Configurable actions: "halt", "close_all", or "reduce" exposure

### Changed
- Runtime indicator columns now prefixed with `runtime_` to avoid DataFrame join collisions; strategies read canonical alias names with fallbacks.
- Live-run UX: confirmation gate removed and replaced with prominent startup warnings.
- Drawdown states expanded from 5 to 7 (added SURVIVAL and refined CRITICAL)
- Position sizing now fully dynamic based on drawdown state and market regime

### Fixed
- **Spread limits schema:** Added `max_spread_points` and `max_spread_pct` to avoid unexpected trade rejections.
- **RPC duplicate detection & robustness:** Generate unique `signal_id` per RPC request and handle transient connection resets gracefully.
- **Windows logging & console encoding:** Removed problematic Unicode characters in logs; added defensive logging for initialization failures.

---

## TESTING, MONITORING & OBSERVABILITY UPDATES


**Overview:**
Cthulu's monitoring and stress-testing infrastructure has been significantly enhanced to provide repeatable, measurable validation of runtime behavior under load. The stack now includes automated stress orchestration, Prometheus metrics, CSV time-series collections, and a comprehensive grading system used during live validation runs.

**What was implemented:**
- **Automated Stress Orchestration:** `monitoring/run_stress.ps1` orchestrates 120-minute runs including burst injections, metric collection, and auto-restart monitoring.
- **Signal Injection & Validation:** `monitoring/inject_signals.py` supports burst, pattern, and manual injection modes for functional and performance testing.
- **Metrics Collection:** Prometheus exporter at `:8181/metrics` and `monitoring/metrics.csv` (10s resolution) capture trading, risk, and system-level metrics.
- **Grading & Analysis:** A deterministic grading formula evaluates indicators, signals, risk, execution, and stability. Reports are consolidated in `SYSTEM_REPORT.md` and `monitoring/monitoring_report.md`.

**Benchmark & Key Results:**
- **120-minute stress test:** Full run completed; **Overall Grade: A+** (production-ready).
- **Indicator Suite:** **12 / 12** indicator tests passed (A+).
- **RPC Pipeline (burst tests):** Baseline Burst (20 trades) — **100%** success; Medium Stress (50 trades) — **100%**; Pattern Test (100 trades) — **100%**; Heavy Burst (10/sec) — **100%** in validated sessions.
- **Trade Throughput:** 690+ RPC trades executed successfully in the observed stress session; broker-side rejections observed (expected broker limits), not system failures.
- **Uptime & Stability:** Uptime during runs measured at **~98.5%** with zero fatal crashes; error handling and retry logic prevented loss of state.

**Current Observations & Next Steps:**
- **Strengths:** Deterministic indicators, robust risk checks, reliable MT5 execution in demo, structured logging, and end-to-end metrics for observability.
- **Opportunities:** Address RPC timeout behavior under extreme sustained load by adding connection pooling/async handlers and instrumenting RPC latency in Prometheus.
- **Roadmap:** Add circuit-breaker tests, latency metrics for RPC, multi-symbol concurrent stress testing, and automated regression gating for monitoring metrics.

---

## LATEST RELEASE

## **5.0.1** 
> *2025-12-27*

### Summary
**MAJOR RELEASE**: Architecture upgrade and live-run stability fixes.

This release advances Cthulu from v4.0.0 to v5.0.1 with a major architecture change and several important runtime fixes discovered and validated during live testing (2025-12-27). Notable changes include: removal of the live-run confirmation gate, robust runtime indicator handling (namespace, aliasing, fallbacks), improved trading loop wiring, additional unit tests, and CI/workflow improvements for Windows and coverage.

### Added
- **Live-run stability fixes & telemetry:** Added aliasing and fallback indicator calculations so strategies have deterministic access to `rsi`, `atr`, and `adx` even when runtime indicators are added dynamically.
- **Runtime indicator namespacing:** Runtime-produced indicator columns are now namespaced with `runtime_` to avoid DataFrame join collisions.
- **Indicator fallback calculations:** If indicators are missing at runtime, Cthulu will compute safe fallbacks for RSI/ATR to avoid transient strategy failures.
- **Unit tests:** Added `tests/test_runtime_indicators.py` to validate rename/alias/fallback behavior.
- **CI enhancements:** Windows and coverage support added to CI workflow for cross-platform testing and coverage reporting.

### Changed
- **Safety gate removal:** `LIVE_RUN_CONFIRM` gate removed; live-run now proceeds and emits a clear warning in logs (was blocking startup). Documented and justified by live testing processes.
- **Strategy resilience:** Strategies now rely on alias columns and are resilient to transient missing runtime indicators.
- **Docs & Release Notes:** Added v5.0.1 release notes and updated CHANGELOG to highlight live-test findings.

### Fixed
- Prevent `pandas.DataFrame.join` ValueError due to overlapping columns by renaming runtime columns and using defensive joins.
- Replaced Unicode checkmark in shutdown log to avoid console encoding errors on Windows.
- Added defensive handling to skip missing `PositionManager` implementations and better logging during initialization.

---

## TABLE OF RELEASES
| Version | Date | Description |
|---------|------|-------------|
| [v5.0.1](v5.0.1.md) | 2025-12-28 | Minor branding & stability patch: runtime indicator fixes, monitoring enhancements, Windows/CI improvements. |
| [v5.0.0](v5.0.0.md) | 2025-12-27 | Major architecture & runtime stability release; runtime namespacing and indicator fallbacks; CI and testing improvements. |
| [v4.0.0](v4.0.0.md) | 2026-12-25 | MAJOR: Multi-strategy framework, next-gen indicators, GUI and metrics enhancements. |
| [v3.3.1](v3.3.1.md) | (see file) | Advisory & news ingestion features, ML instrumentation improvements, and documentation updates. |
| [v3.2.1](v3.2.1.md) | 2025-12-17 | Operational reliability improvements: SL/TP verification, retry queue, and observability/metrics additions. |
| [v3.1.0](v3.1.0.md) | 2025-12-07 | Trade adoption, `Cthulu-trade` CLI, Pydantic config validation, health & Prometheus metrics. |
| [v3.0.0](v3.0.0.md) | 2024-12-07 | Production-ready release with ATR and indicator suite refinements, CI, and robust testing. |
| [v2.0.0](v2.0.0.md) | 2024-12-06 | Autonomous trading loop, core indicators, position management, and exit strategies. |
| [v1.0.0](v1.0.0.md) | 2024-11-15 | Foundation release: core architecture, persistence, MT5 connector, and strategy scaffolding. |


## Quality Standards
- Single responsibility principle
- Type hints throughout codebase
- Comprehensive error handling
- Structured logging
- Dataclass contracts
- Abstract base classes for extensibility
- No circular dependencies

---

## Technical Specifications
- **Python Version**: 3.10 - 3.13
- **Key Dependencies**: 
  - MetaTrader5 (MT5 API)
  - pandas (data manipulation)
  - numpy (numerical operations)
  - sqlite3 (persistence)
- **Database**: SQLite with full schema and indexes
- **Logging**: Structured logging with JSON support
- **Testing**: pytest framework with fixtures and harnesses

---

## Data Contracts
- **Signal** → **OrderRequest** → **ExecutionResult** pipeline
- **RiskLimits** enforcement at every stage
- **TradeRecord** and **SignalRecord** for audit trail
- **PerformanceMetrics** for real-time monitoring

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details on our development process, coding standards, and how to submit pull requests.

## License

This project is licensed under the AGPL 3.0. See the [LICENSE](../LICENSE) file for details.

---

>    **Cthulu** 
> *The future of algorithmic trading.*




