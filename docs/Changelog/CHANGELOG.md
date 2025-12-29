---
title: CHANGELOG
description: Project release notes and version history (canonical)
tags: [changelog, releases]
sidebar_position: 10
slug: /docs/changelog
---

_________   __  .__          .__         
\_   ___ \_/  |_|  |__  __ __|  |  __ __ 
/    \  \/\   __\  |  \|  |  \  | |  |  \
\     \____|  | |   Y  \  |  /  |_|  |  /
 \______  /|__| |___|  /____/|____/____/ 
        \/           \/                  
        

• [View releases on GitHub](https://github.com/amuzetnoM/Cthulu/releases)

![version-badge](https://img.shields.io/badge/version-5.0.1-blue)

 All notable changes are recorded here using Keep a Changelog conventions and Semantic Versioning (https://semver.org/).

---

## UNRELEASED



> This section is for upcoming changes that are not yet released. The
> entries below are harvested from recent commits on the main branch and
> represent work that is deployed to the repository but not yet included
> in a published release. Replace this text with a summary of unreleased
> changes.


---

## TESTING, MONITORING & OBSERVABILITY UPDATES



> This section summarizes recent updates to testing, monitoring, and observat
 summaries. Please replace this text with a summary of changes to the monitoring
> and observability infrastructure, including new metrics, dashboards , alerts etc.


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




