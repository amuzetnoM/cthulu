---
title: CHANGELOG
description: Project release notes and version history (canonical)
tags: [changelog, releases]
sidebar_position: 13
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

 ![](https://img.shields.io/badge/Version-5.1.0_APEX-4B0082?style=for-the-badge&labelColor=0D1117&logo=git&logoColor=white) 
 ![](https://img.shields.io/github/last-commit/amuzetnoM/cthulu?branch=main&style=for-the-badge&logo=github&labelColor=0D1117&color=6A00FF)

 All notable changes are recorded here using Keep a Changelog conventions and Semantic Versioning (https://semver.org/).

---

## UNRELEASED

> Documentation improvements and enhancements

### Added
- Comprehensive Mermaid flowchart diagrams throughout documentation
- Trade decision flow diagram showing complete signal-to-execution pipeline
- Strategy selection logic diagram with regime-based switching
- Exit strategy priority flow diagram with 4-tier system
- Multi-strategy ensemble architecture diagram
- Risk management flow diagram with validation checks
- System-wide INDEX.md with complete navigation and quick start
- Ultra-Aggressive Trading Guide with HFT configuration
- Consistent frontmatter across all documentation files

### Changed
- Replaced all ASCII diagrams with Mermaid flowchartLR implementations
- Enhanced ARCHITECTURE.md with multi-layered comprehensive diagrams
- Updated OVERVIEW.md with modern module structure visualization
- Improved documentation organization with sidebar positioning

### Removed
- Alt text from images and badges (for cleaner rendering)

---

## [5.1.0] "APEX"
> 2025-12-31

**Status:** ✅ RELEASED — *Cthulu reaches peak performance with ultra-aggressive signal generation and the **SAFE** paradigm!*

**Summary & Highlights:**
- 📈 **RSI Reversal Strategy (NEW):** Pure RSI-based trading without crossover requirements — instant signals on RSI extremes
- 🔄 **Multi-Strategy Fallback:** System tries up to 4 strategies per bar for maximum opportunity capture
- 📊 **7 Active Strategies:** Complete arsenal (EMA, Momentum, Scalping, Trend, SMA, Mean Reversion, RSI Reversal)
- ⚡ **Aggressive Configuration:** Optimized thresholds for ultra-aggressive signal generation
- 🔥 **SAFE Engine:** Set And Forget — truly autonomous trading capability
- ⚡ **Flash Orders (NEW, opt-in):** Immediate-fill speculative order type for top confidence signals (configurable, default: OFF) — designed to seize sub-second micro-trends while respecting risk limits.
- 🐙 **Execution & Perf Upgrades:** Async event loop + batching reduces signal-to-fill latency (~30%) and CPU per-signal (~40%); memory per worker improved (~25%).
- 🧯 **Emergency Kill-Switch & Audit Trail:** One-click global halt with automatic safe-recovery and complete audit logging for forensic analysis.
- 🔍 **Fire Metrics & Alerts:** Per-strategy fire-rate heatmaps, flash-order success rates, and alerting integrated into Prometheus for real-time monitoring.
- 🧪 **Live Validation:** Flash orders used in validation run — 5 high-quality trades captured, ~80% acceptance on flash orders, no safety violations observed.
### Added
- **RSI Reversal Strategy (`strategy/rsi_reversal.py`):**
  - Trades on RSI extreme reversals (overbought >85, oversold <25)
  - No crossover dependency — instant signal generation
  - Configurable cooldown (default: 2 bars between signals)
  - Integrated into StrategySelector with regime affinity matrix
- **Multi-Strategy Fallback Mechanism:**
  - Primary strategy tried first
  - If no signal, top 3 alternatives tried in score order
  - First valid signal wins
  - Dramatically increases trading activity
- **Mean Reversion Strategy** added to dynamic selection
- **Database WAL Mode** for concurrent access optimization

### Changed
- `confidence_threshold`: 0.25 → 0.15 (more signals)
- `adx_threshold`: 20 → 15 (weaker trend detection)
- `momentum rsi_threshold`: 50 → 45 (earlier momentum)
- `scalping rsi_overbought`: 80 → 75 (tighter boundary)
- `scalping spread_limit_pips`: 2.0 → 5.0 (flexible spreads)
- Strategy selector now scores 7 strategies with fallback

### Fixed
- Signal generation gap when market ranges without crossovers
- Database lock contention under high-throughput trading
- Strategy score stagnation in quiet market conditions

### Performance
- Live validation: 5 trades in 15 minutes
- RSI range captured: 67-92 (extreme overbought)
- All trades via RSI Reversal fallback
- System achieved SAFE (Set And Forget Engine) status

---

## [5.1.0] — 2025-12-28

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

## **5.1.0** 
> *2025-12-27*

### Summary
**MAJOR RELEASE**: Architecture upgrade and live-run stability fixes.

This release advances Cthulu from v4.0.0 to v5.1.0 with a major architecture change and several important runtime fixes discovered and validated during live testing (2025-12-27). Notable changes include: removal of the live-run confirmation gate, robust runtime indicator handling (namespace, aliasing, fallbacks), improved trading loop wiring, additional unit tests, and CI/workflow improvements for Windows and coverage.

### Added
- **Live-run stability fixes & telemetry:** Added aliasing and fallback indicator calculations so strategies have deterministic access to `rsi`, `atr`, and `adx` even when runtime indicators are added dynamically.
- **Runtime indicator namespacing:** Runtime-produced indicator columns are now namespaced with `runtime_` to avoid DataFrame join collisions.
- **Indicator fallback calculations:** If indicators are missing at runtime, Cthulu will compute safe fallbacks for RSI/ATR to avoid transient strategy failures.
- **Unit tests:** Added `tests/test_runtime_indicators.py` to validate rename/alias/fallback behavior.
- **CI enhancements:** Windows and coverage support added to CI workflow for cross-platform testing and coverage reporting.

### Changed
- **Safety gate removal:** `LIVE_RUN_CONFIRM` gate removed; live-run now proceeds and emits a clear warning in logs (was blocking startup). Documented and justified by live testing processes.
- **Strategy resilience:** Strategies now rely on alias columns and are resilient to transient missing runtime indicators.
- **Docs & Release Notes:** Added v5.1.0 release notes and updated CHANGELOG to highlight live-test findings.

### Fixed
- Prevent `pandas.DataFrame.join` ValueError due to overlapping columns by renaming runtime columns and using defensive joins.
- Replaced Unicode checkmark in shutdown log to avoid console encoding errors on Windows.
- Added defensive handling to skip missing `PositionManager` implementations and better logging during initialization.

---

## TABLE OF RELEASES
| Version | Date | Description |
|---------|------|-------------|
| [v5.1.0](v5.1.0.md) | 2025-12-28 | Minor branding & stability patch: runtime indicator fixes, monitoring enhancements, Windows/CI improvements. |
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




