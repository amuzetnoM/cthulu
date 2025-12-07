---
title: Changelog
description: Herald project release notes and version history (canonical)
tags: [changelog, releases]
sidebar_position: 3
---

• [View releases on GitHub](https://github.com/amuzetnoM/herald/releases)

![version-badge](https://img.shields.io/badge/version-3.1.0-blue)

This is the canonical changelog for the Herald Project. All notable changes are recorded here using Keep a Changelog conventions and Semantic Versioning (https://semver.org/).

---

## Table of contents
- [Unreleased](#unreleased)
- [3.1.0 — 2025-12-07](#310---2025-12-07)
- [3.0.0 — 2024-12-07](#300---2024-12-07)
- [2.0.0 — 2024-12-06](#200---2024-12-06)
- [1.0.0 — 2024-11-15](#100---2024-11-15)
- [Release Template](#release-template-use-for-future-releases)

---

## Unreleased

### Added
- Placeholder for unreleased features and integration notes.

### Changed
- Notes for breaking changes, behavior updates, and refactors.

### Fixed
- Bug fixes and test improvements.

### Security
- Security-related changes and advisories.

---

## 3.1.0 — 2025-12-07

### Summary
Enhances trade management capabilities, adds CLI tooling, improves configuration validation, and introduces observability endpoints.

### Added
- External trade adoption (`position/trade_manager.py`) — Detect and manage externally created trades with configurable adoption policies.
- Command-line trade management (`scripts/trade_cli.py`) — Place, list and close positions from the CLI with optional dry-run.
- Predefined risk profiles (`config/mindsets.py`) — Quick presets for aggressive, balanced, and conservative trading.
- Pydantic-based configuration validation (`config_schema.py`) — Strongly-typed configuration models and environment variable overrides.
- Observability endpoints: `observability/health.py` and `observability/prometheus.py`.

### Changed
- Position reconciliation at startup now detects and tracks pre-existing positions across sessions.
- Exit strategies: return types and priority semantics standardized across implementations.

### Fixed
- Normalized return types and priority semantics for exit strategies.
- Reconciled `get_pnl_pips()` defaults and updated callers.

### Security
- Pre-commit hooks configured with `detect-secrets` and a `.secrets.baseline` file for secret scanning.

---

## 3.0.0 — 2024-12-07

### Summary
Production-ready system release with full MT5 integration, comprehensive testing, and CI automation.

### Added
- ATR indicator and enhancements to indicators (RSI, MACD, Bollinger, Stochastic, ADX).
- Exit Manager and exit strategies for stop loss, take profit, trailing and time-based exit.
- GitHub Actions-based CI with tests, linting, and coverage reporting.

### Changed
- Integration tests refactored to use pytest fixtures; improved lifecycle handling.

### Fixed
- MT5 connection handling, market data compatibility, and test edge cases.

---

## 2.0.0 — 2024-12-06

### Summary
First public release marking baseline Phase 2 completion with autonomous trading and expanded indicators and execution machinery.

### Added
- Indicator set (RSI, MACD, Bollinger, Stochastic, ADX) and a base indicator library.
- Position Manager and Execution Engine for consistent order placement and reconciliation.
- Exit strategies, configuration and initial documentation.

### Fixed
- Initial bug fixes and MT5 integration improvements.

---

## 1.0.0 — 2024-11-15

### Summary
Foundation release with core architecture, connector scaffolding, and initial modules.

### Added
- Project structure, connector, data layer, persistence, and initial strategy/indicator scaffolding.

---

## Release Template (Use for future releases)

### Added
- Brief feature description, file/list of changed files, and how to test.

### Changed
- Behavior changes with migration guidance.

### Deprecated
- Deprecated features with suggested alternatives.

### Removed
- Features removed and migration steps.

### Fixed
- Bug fixes and test updates.

### Security
- Security advisories and fixes.

---

## How we structure entries
- Use Keep a Changelog conventions (https://keepachangelog.com) and Semantic Versioning (https://semver.org).
- Prefer concise, one-sentence bullets grouped by Added / Changed / Fixed / Security / Deprecated / Removed.
- Reference files and PRs where relevant.

---

## Contributing
See `CONTRIBUTING.md` for guidance. When preparing a release, use the release template above and reference the PR(s) that implement the changes.
---
title: Changelog
description: Herald project release notes and version history (canonical)
tags: [changelog, releases]
sidebar_position: 3
---

# Changelog (canonical)

[← Back to Docs](../index.html) • [View releases on GitHub](https://github.com/amuzetnoM/herald/releases)

![version-badge](https://img.shields.io/badge/version-3.1.0-blue)

This is the canonical changelog for the Herald repository. Please update any references that point to `docs/CHANGELOG.md` to use this location: `docs/changelog/CHANGELOG.md`.

All notable changes are recorded here using Keep a Changelog conventions and Semantic Versioning (https://semver.org/).

---

## Table of contents
- [Unreleased](#unreleased)
- [3.1.0 — 2025-12-07](#310---2025-12-07)
- [3.0.0 — 2024-12-07](#300---2024-12-07)
- [2.0.0 — 2024-12-06](#200---2024-12-06)
- [1.0.0 — 2024-11-15](#100---2024-11-15)
- [Release Template](#release-template-use-for-future-releases)

---

## Unreleased

### Added
- Placeholder for unreleased features and integration notes.

### Changed
- Notes for breaking changes, behavior updates, and refactors.

### Fixed
- Bug fixes and test improvements.

### Security
- Security-related changes and advisories.

---

## 3.1.0 — 2025-12-07

### Summary
Enhances trade management capabilities, adds CLI tooling, improves configuration validation, and introduces observability endpoints.

### Added
- External trade adoption (`position/trade_manager.py`) — Detect and manage externally created trades with configurable adoption policies.
- Command-line trade management (`scripts/trade_cli.py`) — Place, list and close positions from the CLI with optional dry-run.
- Predefined risk profiles (`config/mindsets.py`) — Quick presets for aggressive, balanced, and conservative trading.
- Pydantic-based configuration validation (`config_schema.py`) — Strongly-typed configuration models and environment variable overrides.
- Observability endpoints: `observability/health.py` and `observability/prometheus.py`.

### Changed
- Position reconciliation at startup now detects and tracks pre-existing positions across sessions.
- Exit strategies: return types and priority semantics standardized across implementations.

### Fixed
- Normalized return types and priority semantics for exit strategies.
- Reconciled `get_pnl_pips()` defaults and updated callers.

### Security
- Pre-commit hooks configured with `detect-secrets` and a `.secrets.baseline` file for secret scanning.

---

## 3.0.0 — 2024-12-07

### Summary
Production-ready system release with full MT5 integration, comprehensive testing, and CI automation.

### Added
- ATR indicator and enhancements to indicators (RSI, MACD, Bollinger, Stochastic, ADX).
- Exit Manager and exit strategies for stop loss, take profit, trailing and time-based exit.
- GitHub Actions-based CI with tests, linting, and coverage reporting.

### Changed
- Integration tests refactored to use pytest fixtures; improved lifecycle handling.

### Fixed
- MT5 connection handling, market data compatibility, and test edge cases.

---

## 2.0.0 — 2024-12-06

### Summary
First public release marking baseline Phase 2 completion with autonomous trading and expanded indicators and execution machinery.

### Added
- Indicator set (RSI, MACD, Bollinger, Stochastic, ADX) and a base indicator library.
- Position Manager and Execution Engine for consistent order placement and reconciliation.
- Exit strategies, configuration and initial documentation.

### Fixed
- Initial bug fixes and MT5 integration improvements.

---

## 1.0.0 — 2024-11-15

### Summary
Foundation release with core architecture, connector scaffolding, and initial modules.

### Added
- Project structure, connector, data layer, persistence, and initial strategy/indicator scaffolding.

---

## Release Template (Use for future releases)

### Added
- Brief feature description, file/list of changed files, and how to test.

### Changed
- Behavior changes with migration guidance.

### Deprecated
- Deprecated features with suggested alternatives.

### Removed
- Features removed and migration steps.

### Fixed
- Bug fixes and test updates.

### Security
- Security advisories and fixes.

---

## How we structure entries
- Use Keep a Changelog conventions (https://keepachangelog.com) and Semantic Versioning (https://semver.org).
- Prefer concise, one-sentence bullets grouped by Added / Changed / Fixed / Security / Deprecated / Removed.
- Reference files and PRs where relevant.

---

## Contributing
See `CONTRIBUTING.md` for guidance. When preparing a release, use the release template above and reference the PR(s) that implement the changes.
---
title: Changelog
description: Herald project release notes and version history (canonical)
tags: [changelog, releases]
sidebar_position: 3
---

# Changelog (canonical)

[← Back to Docs](../index.html) • [View releases on GitHub](https://github.com/amuzetnoM/herald/releases)

![version-badge](https://img.shields.io/badge/version-3.1.0-blue)

All notable changes to the Herald Adaptive Trading Intelligence project are documented here.
This file follows Keep a Changelog conventions and uses Semantic Versioning (https://semver.org/).

## Table of contents
- [Unreleased](#unreleased)
- [3.1.0 — 2025-12-07](#310---2025-12-07)
- [3.0.0 — 2024-12-07](#300---2024-12-07)
- [2.0.0 — 2024-12-06](#200---2024-12-06)
- [1.0.0 — 2024-11-15](#100---2024-11-15)
- [Release Template](#release-template-use-for-future-releases)

---

## Unreleased

### Added
- Placeholder for unreleased features and integration notes.

### Changed
- Notes for breaking changes, behavior updates, and refactors.

### Fixed
- Bug fixes and test improvements.

### Security
- Security-related changes and advisories.

---

## 3.1.0 — 2025-12-07

### Summary
Enhances trade management capabilities, adds CLI tooling, improves configuration validation, and introduces observability endpoints.

### Added
- External trade adoption (`position/trade_manager.py`) — Detect and manage externally created trades with configurable adoption policies.
- Command-line trade management (`scripts/trade_cli.py`) — Place, list and close positions from the CLI with optional dry-run.
- Predefined risk profiles (`config/mindsets.py`) — Quick presets for aggressive, balanced, and conservative trading.
- Pydantic-based configuration validation (`config_schema.py`) — Strongly-typed configuration models and environment variable overrides.
- Observability endpoints: `observability/health.py` and `observability/prometheus.py`.

### Changed
- Position reconciliation at startup now detects and tracks pre-existing positions across sessions.
- Exit strategies: return types and priority semantics standardized across implementations.

### Fixed
- Normalized return types and priority semantics for exit strategies.
- Reconciled `get_pnl_pips()` defaults and updated callers.

### Security
- Pre-commit hooks configured with `detect-secrets` and a `.secrets.baseline` file for secret scanning.

---

## 3.0.0 — 2024-12-07

### Summary
Production-ready system release with full MT5 integration, comprehensive testing, and CI automation.

### Added
- ATR indicator and enhancements to indicators (RSI, MACD, Bollinger, Stochastic, ADX).
- Exit Manager and exit strategies for stop loss, take profit, trailing and time-based exit.
- GitHub Actions-based CI with tests, linting, and coverage reporting.

### Changed
- Integration tests refactored to use pytest fixtures; improved lifecycle handling.

### Fixed
- MT5 connection handling, market data compatibility, and test edge cases.

---

## 2.0.0 — 2024-12-06

### Summary
First public release marking baseline Phase 2 completion with autonomous trading and indicator set.

### Added
- Indicator library (RSI, MACD, Bollinger, Stochastic, ADX) and base indicator infrastructure.
- Position Manager, Execution Engine, and the initial Exit Strategy engine.
- Core strategy scaffolding and configuration management for MT5 integration.

### Changed
- Project structure refined for maintainability and modularity.

### Fixed
- Initial bug fixes and MT5 integration improvements.

---

## 1.0.0 — 2024-11-15

### Summary
Foundation release with core architecture and MT5 connector scaffolding; this release establishes project conventions and initial modules.

### Added
- Project infrastructure, data layer, connector, strategy engine scaffolding, and initial tests.

---

## Release Template (Use for future releases)

### Added
- Brief feature description, file/list of changed files, and how to test.

### Changed
- Behavior changes with migration guidance.

### Deprecated
- Deprecated features with suggested alternatives.

### Removed
- Features removed and migration steps.

### Fixed
- Bug fixes and test updates.

### Security
- Security advisories and fixes.

---

## How we structure entries
- Use Keep a Changelog conventions (https://keepachangelog.com) and Semantic Versioning (https://semver.org).
- Prefer concise, one-sentence bullets grouped by Added / Changed / Fixed / Security / Deprecated / Removed.
- Reference files and PRs where relevant.

---

## Contributing
See `CONTRIBUTING.md` for guidance. When preparing a release, use the release template above and reference the PR(s) that implement the changes.

---

This file is the canonical changelog location for Herald. If you have a local copy or link to other CHANGELOG files, please update them to point to `docs/changelog/CHANGELOG.md`.
---
title: Changelog
description: Herald project release notes and version history (canonical)
tags: [changelog, releases]
sidebar_position: 3
---

# Changelog (canonical)

[← Back to Docs](../index.html) • [View releases on GitHub](https://github.com/amuzetnoM/herald/releases)

![version-badge](https://img.shields.io/badge/version-3.1.0-blue)

All notable changes to the Herald Adaptive Trading Intelligence project are documented here.
This file follows Keep a Changelog conventions and uses Semantic Versioning (https://semver.org/).

## Table of contents
- [Unreleased](#unreleased)
- [3.1.0 — 2025-12-07](#310---2025-12-07)
- [3.0.0 — 2024-12-07](#300---2024-12-07)
- [Release Template](#release-template-use-for-future-releases)
- [How we structure entries](#how-we-structure-entries)

---

## Unreleased

### Added
- Placeholder for unreleased features and integration notes.

### Changed
- Notes for breaking changes, behavior updates, and refactors.

### Fixed
- Bug fixes and test improvements.

### Security
- Security-related changes and advisories.

---

## 3.1.0 — 2025-12-07

### Summary
Enhances trade management capabilities, adds CLI tooling, improves configuration validation, and introduces observability endpoints.

### Added
- External trade adoption (`position/trade_manager.py`) — Detect and manage externally created trades with configurable adoption policies.
- Command-line trade management (`scripts/trade_cli.py`) — Place, list and close positions from the CLI with optional dry-run.
- Predefined risk profiles (`config/mindsets.py`) — Quick presets for aggressive, balanced, and conservative trading.
- Pydantic-based configuration validation (`config_schema.py`) — Strongly-typed configuration models and environment variable overrides.
- Observability endpoints: `observability/health.py` and `observability/prometheus.py`.

### Changed
- Position reconciliation at startup now detects and tracks pre-existing positions across sessions.
- Exit strategies: return types and priority semantics standardized across implementations.

### Fixed
- Normalized return types and priority semantics for exit strategies.
- Reconciled `get_pnl_pips()` defaults and updated callers.

### Security
- Pre-commit hooks configured with `detect-secrets` and a `.secrets.baseline` file for secret scanning.

---

## 3.0.0 — 2024-12-07

### Summary
Production-ready system release with complete MT5 integration, comprehensive testing, and CI automation.

### Added
- ATR indicator and enhancements to indicators (RSI, MACD, Bollinger, Stochastic, ADX).
- Exit Manager and exit strategies for stop loss, take profit, trailing and time-based exit.
- GitHub Actions-based CI with tests, linting, and coverage reporting.

### Changed
- Integration tests refactored to use pytest fixtures; improved lifecycle handling.

### Fixed
- MT5 connection handling, market data compatibility, and test edge cases.

---

## Release Template (Use for future releases)

### Added
- Brief feature description, file/list of changed files, and how to test.

### Changed
- Behavior changes with migration guidance.

### Deprecated
- Deprecated features with suggested alternatives.

### Removed
- Features removed and migration steps.

### Fixed
- Bug fixes and test updates.

### Security
- Security advisories and fixes.

---

## How we structure entries
- Use Keep a Changelog conventions (https://keepachangelog.com) and Semantic Versioning (https://semver.org).
- Prefer concise, one-sentence bullets grouped by Added / Changed / Fixed / Security / Deprecated / Removed.
- Reference files and PRs where relevant.

---

## Contributing
See `CONTRIBUTING.md` for guidance. When preparing a release, use the release template above and reference the PR(s) that implement the changes.

---

This file is the canonical changelog location for Herald. If you have a local copy or link to other CHANGELOG files, please update them to point to `docs/changelog/CHANGELOG.md`.
---
title: Changelog (moved)
description: This file was moved to the canonical `docs/CHANGELOG.md`.
sidebar_position: 3
---

# Changelog (moved)

The canonical changelog for Herald now lives at: [../CHANGELOG.md](../CHANGELOG.md).

If you maintain links to `docs/changelog/CHANGELOG.md`, please update them to `docs/CHANGELOG.md`.

For a full release history, visit: https://github.com/amuzetnoM/herald/releases

---
title: Changelog (moved)
description: This file was moved to the canonical `docs/CHANGELOG.md`.
sidebar_position: 3
---

# Changelog (moved)

The canonical changelog for Herald now lives at: [docs/CHANGELOG.md](../CHANGELOG.md)

Please update any references to `docs/changelog/CHANGELOG.md` to `docs/CHANGELOG.md`.

## [Unreleased]

### Planned
- Phase 4: Machine Learning Integration
- Phase 5: Reinforcement Learning
- Phase 6-10: See comprehensive build plan

### Changed
- PositionInfo dataclass: made `open_price` optional and added backward-compatible mapping for `_legacy_entry_price` and `_legacy_position_type`; added `entry_price` read-only property mapping to `open_price`.
- `PositionManager`: added `get_positions_by_symbol` and `calculate_total_pnl` compatibility methods.
- Robustness: import-time resilience for environments without MetaTrader5 via connector stub; modules import `mt5` through `herald.connector.mt5_connector`.
- Docs & Clean-up: removed `build_plan.md` inline references from code docstrings; simplified descriptions.
- Flex Audit: canonicalized `audit_output/` as the single output directory and added `scripts/normalize_audit_output.py` to consolidate older output folders.
- CI: Added GitHub Actions workflow to run unit tests and lint on each push/PR.

---

## [2.0.0] - 2024-12-06 FIRST PUBLIC RELEASE

### 🎉 Herald's First Official Release

This marks Herald's **first public release** - a fully autonomous MetaTrader 5 trading system with complete entry and exit execution capabilities.

### Added - Phase 2: Autonomous Trading Execution

#### Indicator Library (`indicators/`)
- **Base Indicator Class** (`base.py`)
  - Abstract `Indicator` class with `calculate()`, `reset()`, `state()` methods
  - Data validation for OHLCV format
  - Thread-safe indicator state management
  - Metadata enrichment for signals

- **RSI Indicator** (`rsi.py`)
  - Relative Strength Index calculation with EMA smoothing
  - Configurable period (default: 14)
  - Overbought/oversold detection (70/30 thresholds)
  - Signal generation (BUY/SELL/NEUTRAL)

- **MACD Indicator** (`macd.py`)
  - Moving Average Convergence Divergence calculation
  - Fast EMA (12), Slow EMA (26), Signal line (9)
  - Histogram calculation
  - Bullish/bearish crossover detection

- **Bollinger Bands Indicator** (`bollinger.py`)
  - Upper, middle (SMA), and lower band calculation
  - Configurable period (20) and standard deviation (2.0)
  - Band width and %B calculation
  - Volatility state detection

- **Stochastic Oscillator** (`stochastic.py`)
  - %K and %D line calculation with smoothing
  - Configurable %K period (14) and %D period (3)
  - Overbought/oversold detection (80/20 thresholds)
  - Crossover signal detection in extreme zones

- **ADX Indicator** (`adx.py`)
  - Average Directional Index calculation
  - True Range and Directional Movement computation
  - +DI and -DI calculation
  - Trend strength detection (>25 trending, <20 ranging)
  - Trend direction identification

#### Position Management (`position/`)
- **PositionManager Class** (`manager.py`)
  - Real-time position tracking synchronized with MT5
  - Continuous P&L calculation and monitoring
  - Position lifecycle management (open, monitor, close)
  - Partial and full position closing
  - Emergency "close all" functionality
  - Position reconciliation after connection loss
  - Position age tracking (seconds/hours)
  - Unrealized and realized P&L tracking
  - Detailed position analytics and statistics
  - Integration with ExecutionEngine and RiskManager

- **PositionInfo Dataclass**
  - 18 fields including ticket, symbol, side, volume
  - Open and current prices, timestamps
  - P&L calculations (unrealized, realized, commission, swap)
  - Stop loss and take profit levels
  - Helper methods: `get_age_hours()`, `get_pnl_pips()`

#### Exit Strategy Engine (`exit/`)
- **Base Exit Strategy** (`base.py`)
  - Abstract `ExitStrategy` class with priority system
  - Priority-based execution (0-100 scale)
  - Enable/disable functionality per strategy
  - State management and reset capabilities
  - `should_exit()` method returning `ExitSignal`

- **ExitSignal Dataclass**
  - Ticket, reason, price, timestamp
  - Strategy name and confidence level
  - Partial volume support for scaled exits
  - Metadata dictionary for additional context

- **Trailing Stop Strategy** (`trailing_stop.py`)
  - ATR-based dynamic trailing stop distance
  - Activation after minimum profit threshold
  - Never moves stop against profit direction
  - Adapts to volatility changes
  - Configurable: ATR multiplier, activation profit, min distance
  - Priority: 25 (low - let profits run)

- **Time-Based Exit Strategy** (`time_based.py`)
  - Maximum hold time enforcement (configurable hours)
  - Weekend protection (Friday close before market close)
  - Day trading mode (EOD position closing)
  - Session-aware exit timing
  - Configurable: max hold time, session close offset, EOD time
  - Priority: 50 (medium)

- **Profit Target Exit Strategy** (`profit_target.py`)
  - Percentage-based and pip-based profit targets
  - Multiple target levels with partial closes
  - Risk/reward ratio enforcement
  - Volatility-adjusted targets (ATR scaling)
  - Target tracking per position
  - Configurable: target %, target pips, partial close levels
  - Priority: 40 (medium)

- **Adverse Movement Exit Strategy** (`adverse_movement.py`)
  - Rapid adverse price movement detection
  - Flash crash protection mechanism
  - Time window analysis (default 60 seconds)
  - Consecutive adverse move requirement
  - Volatility filter (ignore during known high volatility)
  - Cooldown period after exit
  - Configurable: movement threshold, time window, consecutive moves
  - Priority: 90 (critical - emergency exit)

#### Autonomous Orchestrator (`__main__.py`)
- **Complete 10-Step Trading Loop**
  1. Module initialization (all Phase 1 + Phase 2 components)
  2. Indicator and strategy loading from configuration
  3. MT5 connection with health check
  4. Market data ingestion (configurable timeframe and lookback)
  5. Technical indicator calculation (all 5 indicators)
  6. Strategy signal generation from enriched data
  7. Entry signal processing (risk approval → execution → tracking)
  8. Position monitoring (continuous P&L updates from MT5)
  9. Exit detection (priority-based strategy evaluation)
  10. Health monitoring (connection check, reconnection, reconciliation)

- **Safeguards and Recovery**
  - Graceful shutdown with position closing
  - Connection loss detection and automatic reconnection
  - Position reconciliation after reconnect
  - Exception handling (no crash on single error)
  - Signal handlers (SIGINT, SIGTERM)
  - Dry-run mode support (no real orders)
  - Comprehensive logging at all stages

- **Configuration Management**
  - JSON configuration file loading
  - Command-line argument parsing (--config, --log-level, --dry-run)
  - Module loading (indicators, strategy, exit strategies)
  - Dynamic timeframe and symbol configuration

#### Documentation
- **Phase 2 README** (`PHASE2_README.md`)
  - Complete Phase 2 overview and architecture
  - Quick start guide with configuration examples
  - Module documentation with code samples
  - Configuration reference
  - Database schema documentation
  - Performance monitoring guide
  - Troubleshooting section

- **Phase 2 Summary** (`PHASE2_SUMMARY.md`)
  - Detailed implementation statistics
  - Module-by-module breakdown
  - Code quality metrics
  - Integration verification
  - Performance characteristics
  - Deployment readiness checklist

- **Configuration Example** (`config.example.json`)
  - Complete JSON configuration template
  - MT5 connection settings
  - Risk management parameters
  - Trading configuration (symbol, timeframe, polling)
  - Indicator configurations (all 5 indicators)
  - Exit strategy configurations (all 4 strategies)
  - Database and cache settings

#### Build Plan Updates
- Phase 2 marked as **COMPLETE** in `docs/build_plan.md`
- Comprehensive implementation checklist
- Verification details for all components
- Integration status confirmed
- Quality standards verification

### Changed
- **Main Entry Point** (`__main__.py`)
  - Completely rewritten for autonomous trading
  - Integrated all Phase 2 modules
  - Added comprehensive error handling
  - Implemented full trading loop

### Technical Details
- **Total Lines of Code**: ~4,130 lines (Phase 2 only)
- **New Modules**: 17 files created
- **Updated Modules**: 2 files modified
- **Data Flow**: Complete end-to-end autonomous trading pipeline
- **Quality**: Production-ready, no stubs or placeholders

---

## [1.0.0] - 2024-11-15

### Added - Phase 1: Foundation Infrastructure

#### Core Architecture
- **Project Structure**
  - Modular architecture with clear separation of concerns
  - Single responsibility principle throughout
  - Event-driven design pattern
  - Pluggable component architecture

#### MT5 Connector (`connector/`)
- **MT5Connector Class** (`mt5_connector.py`)
  - Connection management with automatic reconnection
  - Session health monitoring
  - Rate limiting to prevent API throttling
  - Retry logic with exponential backoff
  - Account information retrieval
  - Market data fetching (OHLCV bars)
  - Order placement and management
  - Position querying
  - Exception handling and error consolidation

- **ConnectionConfig Dataclass**
  - Login, password, server configuration
  - Timeout settings
  - MT5 installation path
  - Comprehensive validation

#### Data Layer (`data/`)
- **DataLayer Class** (`layer.py`)
  - OHLCV data normalization to pandas DataFrame
  - Timestamp indexing
  - Data validation and cleaning
  - Caching layer for backtesting efficiency
  - Resampling capabilities
  - Symbol metadata management

- **BarData Dataclass**
  - Standardized OHLCV structure
  - Timestamp, symbol, timeframe
  - Volume and tick volume
  - Spread information

#### Strategy Engine (`strategy/`)
- **Base Strategy Interface** (`base.py`)
  - Abstract `Strategy` class
  - `on_bar()` and `on_tick()` event handlers
  - Signal generation interface
  - Strategy configuration and state management
  - Pluggable strategy architecture

- **Signal Dataclass**
  - Signal ID, timestamp, symbol
  - Signal type (LONG, SHORT, CLOSE, NEUTRAL)
  - Confidence level (0.0 to 1.0)
  - Stop loss and take profit levels
  - Signal reason and metadata

- **SignalType Enum**
  - LONG, SHORT, CLOSE, NEUTRAL states

- **SMA Crossover Strategy** (`sma_crossover.py`)
  - Fast and slow SMA calculation
  - Crossover detection (golden cross, death cross)
  - Signal generation with confidence scoring
  - Configurable periods (default: 10/30)
  - Example implementation for testing

#### Execution Engine (`execution/`)
- **ExecutionEngine Class** (`engine.py`)
  - Market and limit order support
  - Idempotent order submission
  - Partial fill handling
  - Order status tracking
  - Integration with MT5Connector
  - External order reconciliation
  - Comprehensive error handling

- **OrderRequest Dataclass**
  - Signal ID, symbol, side (BUY/SELL)
  - Volume, order type (MARKET/LIMIT)
  - Price, stop loss, take profit
  - Deviation tolerance
  - Magic number for order identification
  - Comment field

- **ExecutionResult Dataclass**
  - Order ID, status (PLACED, FILLED, REJECTED, etc.)
  - Fill price, filled volume
  - Request and fill timestamps
  - Commission and swap
  - Message and error details

- **OrderStatus Enum**
  - PLACED, FILLED, PARTIALLY_FILLED, REJECTED, CANCELLED, ERROR

- **OrderType Enum**
  - MARKET, LIMIT, STOP, STOP_LIMIT

#### Risk Management (`risk/`)
- **RiskManager Class** (`manager.py`)
  - Position sizing (fixed lots, percentage-based, Kelly criterion)
  - Maximum position size enforcement
  - Per-symbol position limits
  - Total position limits
  - Daily loss tracking with auto-reset
  - Emergency stop loss percentage
  - Circuit breaker mechanism
  - Daily P&L monitoring
  - Trade result recording

- **RiskLimits Dataclass**
  - Maximum position size
  - Default position size
  - Maximum daily loss
  - Max positions per symbol
  - Max total positions
  - Position size percentage
  - Kelly sizing option
  - Emergency stop loss percentage
  - Circuit breaker settings

#### Persistence Layer (`persistence/`)
- **Database Class** (`database.py`)
  - SQLite database with full schema
  - Trades table with entry/exit tracking
  - Signals table with execution status
  - Metrics table for performance tracking
  - Indexed queries for fast lookups
  - Connection pooling
  - Transaction management

- **TradeRecord Dataclass**
  - 15 fields including signal_id, order_id
  - Symbol, side, entry/exit prices
  - Volume, stop loss, take profit
  - Timestamps (entry, exit)
  - P&L (profit, commission, swap)
  - Exit reason, metadata

- **SignalRecord Dataclass**
  - 13 fields including timestamp, symbol, side
  - Confidence, price, stop loss, take profit
  - Strategy name, metadata
  - Execution status and timestamp
  - Rejection reason

#### Observability (`observability/`)
- **Logger Module** (`logger.py`)
  - Structured logging setup
  - JSON and human-readable formats
  - Console and file handlers
  - Configurable log levels
  - Log rotation support
  - Context-rich log messages

- **Metrics Collector** (`metrics.py`)
  - Performance metrics tracking
  - Win rate calculation
  - Profit factor computation
  - Sharpe ratio calculation
  - Maximum drawdown tracking (absolute and percentage)
  - Equity curve tracking
  - Average win/loss statistics
  - Trade count and distribution

- **PerformanceMetrics Dataclass**
  - 15+ fields for comprehensive performance analysis
  - Total trades, profitable trades, losing trades
  - Win rate, profit factor
  - Sharpe ratio, Sortino ratio
  - Max drawdown (absolute and percentage)
  - Average win, average loss
  - Total profit, total loss
  - Risk/reward ratio

#### Testing Infrastructure (`tests/`)
- **Unit Test Structure**
  - `tests/unit/` directory created
  - Test framework setup (pytest)
  - Mock fixtures for MT5 API
  - Sample test files for core modules

- **Integration Test Structure**
  - `tests/integration/` directory created
  - End-to-end workflow tests
  - Database integration tests
  - MT5 connection tests

#### Configuration
- **Example Configuration** (`.env.example`, `config.example.yaml`)
  - MT5 credentials template
  - Risk parameters
  - Trading configuration
  - Logging settings
  - Database configuration

#### Documentation
- **Build Plan** (`docs/build_plan.md`)
  - Comprehensive 5-phase roadmap
  - Phase 1 specifications and verification
  - Phase 2-5 planning
  - Architecture diagrams
  - Data flow documentation
  - Integration contracts

- **Architecture Documentation** (`docs/ARCHITECTURE.md`)
  - System architecture overview
  - Component responsibilities
  - Data flow diagrams
  - Integration points
  - Design patterns

- **Guide** (`docs/GUIDE.md`)
  - Getting started guide
  - Installation instructions
  - Configuration walkthrough
  - Usage examples
  - Best practices

- **README** (`README.md`)
  - Project overview
  - Features list
  - Quick start guide
  - Architecture summary
  - Development guidelines

- **HTML Documentation** (`docs/index.html`)
  - Interactive documentation website
  - Feature showcase
  - Code examples
  - API reference
  - Deployment guide

#### Development Tools
- **Requirements Files**
  - `requirements.txt` - Production dependencies
  - `requirements-dev.txt` - Development dependencies
  - Version pinning for reproducibility

- **Git Configuration**
  - `.gitignore` - Comprehensive exclusion rules
  - `.env.example` - Environment variable template
  - Repository structure

### Technical Specifications
- **Python Version**: 3.10 - 3.13
- **Key Dependencies**: 
  - MetaTrader5 (MT5 API)
  - pandas (data manipulation)
  - numpy (numerical operations)
  - sqlite3 (persistence)
- **Database**: SQLite with full schema and indexes
- **Logging**: Structured logging with JSON support
- **Testing**: pytest framework with fixtures

### Data Contracts
- **Signal** → **OrderRequest** → **ExecutionResult** pipeline
- **RiskLimits** enforcement at every stage
- **TradeRecord** and **SignalRecord** for audit trail
- **PerformanceMetrics** for real-time monitoring

### Quality Standards
- Single responsibility principle
- Type hints throughout codebase
- Comprehensive error handling
- Structured logging
- Dataclass contracts
- Abstract base classes for extensibility
- No circular dependencies

---

## [0.1.0] - 2024-10-01

### Added - Initial Project Setup

#### Project Initialization
- Repository created with basic structure
- Initial documentation framework
- Development environment setup
- Git repository initialized

#### Foundation
- Project name: Herald
- Vision: Adaptive Trading Intelligence for MetaTrader 5
- Core principles established
- Phased development approach defined

#### Documentation
- Initial README with project vision
- License file (MIT)
- Contributing guidelines
- Code of conduct

---

## Key Milestones Summary

| Version | Date | Milestone | Lines of Code |
|---------|------|-----------|---------------|
| 0.1.0 | Oct 2024 | Project initialization | ~100 |
| 1.0.0 | Nov 2024 | Phase 1: Foundation complete | ~2,500 |
| 2.0.0 | Dec 2024 | Phase 2: Autonomous trading | ~6,630+ |

---

## Upcoming Phases (Comprehensive MQL5 Coverage)

### Phase 3 - Advanced Technical Analysis
- Price Action Analysis (candlestick patterns, S/R zones, CHoCH detection)
- Advanced Chart Types (Kagi, Renko, Point and Figure)
- Volume Profile Trading (VPVR, VWAP, order flow)
- Statistical Analysis (linear regression, cointegration, correlation)
- Session-Based Trading (Opening Range Breakout)
- Extended Indicators (Ichimoku, Market Profile, momentum suite)

### Phase 4 - Machine Learning Integration
- Feature Engineering (technical, time-based, microstructure)
- Supervised Learning (Random Forest, XGBoost, SVM)
- Deep Learning (LSTM, GRU, Transformers, ResNeXt)
- ONNX Model Integration (Python-to-MQL5 pipeline)
- Model Serving Infrastructure

### Phase 5 - Reinforcement Learning & Advanced AI
- Trading Environment (Gym-style interface)
- DQN, PPO, A2C algorithms
- Market Regime Detection
- Sentiment & Alternative Data
- Strategy Meta-Learning

### Phase 6 - Integration & Infrastructure
- WebRequest/API Mastery
- Socket Communication
- Database Operations (PostgreSQL, Redis)
- Python Bridge & OpenCL Acceleration
- Multi-Currency EA Support

### Phase 7 - Risk Management & Options
- Advanced Risk Dashboard (VaR, CVaR)
- Position Sizing (Kelly, Optimal f)
- Options Greeks (Black-Scholes)
- Market Simulation & Stress Testing

### Phase 8 - Production & Testing
- MT5 Strategy Tester Integration
- Walk-Forward Optimization
- Genetic Optimization
- Performance Analytics Suite

### Phase 9 - Expert Advisor Patterns
- MVC Paradigm Implementation
- Event-Driven Architecture
- Services, Scripts, Libraries

### Phase 10 - GUI & Visualization
- Trading Control Panel
- Chart Overlays
- DirectX 3D Visualization

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details on our development process, coding standards, and how to submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**Herald** - Adaptive Trading Intelligence  
*Building the future of algorithmic trading, one phase at a time.*
