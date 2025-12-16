---
title: CHANGELOG
description: Project release notes and version history (canonical)
tags: [changelog, releases]
sidebar_position: 3
slug: /docs/changelog
---

• [View releases on GitHub](https://github.com/amuzetnoM/herald/releases)

![version-badge](https://img.shields.io/badge/version-3.1.0-blue)

 All notable changes are recorded here using Keep a Changelog conventions and Semantic Versioning (https://semver.org/).

---

## UNRELEASED

### In-Progress
- **NLP wizard**: added lightweight, local intent parser and interactive `--wizard-ai` option to propose and save configs from natural-language input (symbol, timeframe(s), mindset, risk profile). See `config/wizard.py` for details.

### Added
- **Per-mindset, per-timeframe configuration profiles** (configs/mindsets/*) enabling robust multi-timeframe deployments.
- **Adopt-only CLI mode** (`--adopt-only`) to scan and adopt external trades without entering the main trading loop.
-**Trade adoption enhancements**: automatic application of protective SL/TP (configurable via `risk.emergency_stop_loss_pct` and `strategy.params.risk_reward_ratio`) when adopting external trades.
- **Interactive shutdown prompt**: on graceful shutdown Herald now prompts the user to Close All / Leave Open / Close specific ticket(s) (use `--no-prompt` to disable for automation).
- **Symbol matching & market-data robustness**: improved MT5 symbol selection with normalized matching and variant detection to reduce `Failed to select symbol` errors.
- **SL/TP verification & retry queue**: after setting SL/TP Herald now *verifies* the broker accepted the modification by reading back the position; failures are logged and emit a Prometheus metric (`herald_sl_tp_failure_total`). Failed updates are queued and retried until success (with capped attempts).
- **Aggressive immediate SL/TP retry**: if initial SL/TP application fails during adoption, Herald makes several quick retry attempts (configurable) before queuing for background retries to ensure protection is applied as soon as possible.
- Test utilities: `scripts/place_test_trade.py` and `scripts/place_external_test_trade.py` added to place internal and external test trades for end-to-end verification.
- **Wizard enhancements**: multi-timeframe selection, save-as-mindset profiles, and one-click start (dry-run or live) from the wizard.


### Changed
- Default aggressive profiles now restrict orphan adoption to `GOLD#m` only (BTCUSD temporarily disabled) unless overridden.
- `run_herald_multi_tf.ps1` updated to support multiple symbols and timeframes and dry-run option.
- Added `--symbol` CLI flag to override trading symbol at startup.
- **Shutdown behavior**: graceful shutdown no longer force-closes positions by default; user must confirm closure interactively (or use `--no-prompt` to skip asking and leave positions intact).
- Adoption is performed every loop and pending SL/TP operations are retried (more resilient behavior).

### Fixed
- Reliability improvements to trade adoption and SL/TP application on adopted trades.
- Fixed intermittent market data failures caused by symbol-format mismatches (e.g., `GOLDm#` vs. `GOLD#m`) via normalization and candidate symbol selection.

### Security
- No security changes in this release.

---

# RELEASE HISTORY

## Table of contents
- [Unreleased](#unreleased)
- [3.1.0 — 2025-12-07](#310---2025-12-07)
- [3.0.0 — 2024-12-07](#300---2024-12-07)
- [2.0.0 — 2024-12-06](#200---2024-12-06)
- [1.0.0 — 2024-11-15](#100---2024-11-15)
- [Release Template](#release-template-use-for-future-releases)

---

## **3.1.0 — 2025-12-07**

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

## **3.0.0 — 2024-12-07**

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

## **2.0.0 — 2024-12-06**

### Summary
First public release marking baseline Phase 2 completion with autonomous trading and expanded indicators and execution machinery.

### Added
- Indicator set (RSI, MACD, Bollinger, Stochastic, ADX) and a base indicator library.


## **1.0.0 — 2024-11-15**

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

---

## Quality Standards
- Single responsibility principle
- Type hints throughout codebase
- Comprehensive error handling
- Structured logging
- Dataclass contracts
- Abstract base classes for extensibility
- No circular dependencies

---

### Development Tools
- **Requirements Files**
  - `requirements.txt` - Production dependencies
  - `requirements-dev.txt` - Development dependencies
  - Version pinning for reproducibility

- **Git Configuration**
  - `.gitignore` - Comprehensive exclusion rules
  - `.env.example` - Environment variable template
  - Repository structure

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
- **Testing**: pytest framework with fixtures

---

## Data Contracts
- **Signal** → **OrderRequest** → **ExecutionResult** pipeline
- **RiskLimits** enforcement at every stage
- **TradeRecord** and **SignalRecord** for audit trail
- **PerformanceMetrics** for real-time monitoring

---

  ## Release Template (Use for future releases)
  - Use Keep a Changelog conventions (https://keepachangelog.com) and Semantic Versioning (https://semver.org).
  - Prefer concise, one-sentence bullets grouped by Added / Changed / Fixed / Security / Deprecated / Removed.
  - Reference files and PRs where relevant.

  ---

  ## Contributing
  See [CONTRIBUTING.md](../CONTRIBUTING.md) for details on our development process and how to submit pull requests.

  ---

  This file is the canonical changelog location for Herald. For past release notes, prefer GitHub releases.

- **Configuration Requirements** (`config.example.json`)
  - Complete JSON configuration template
  - MT5 connection settings
  - Risk management parameters
  - Trading configuration (symbol, timeframe, polling)
  - Indicator configurations (all 5 indicators)
  - Exit strategy configurations (all 4 strategies)
  - Database and cache settings

#### Build Plan Updates
- Phase 2 marked as **COMPLETE**
- Comprehensive implementation checklist
- Verification details for all components
- Integration status confirmed
- Quality standards verification

### Technical Details
- **Total Lines of Code**: ~4,130 lines (Phase 2 only)
- **New Modules**: 17 files created
- **Updated Modules**: 2 files modified
- **Data Flow**: Complete end-to-end autonomous trading pipeline
- **Quality**: Production-ready, no stubs or placeholders


---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details on our development process, coding standards, and how to submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**Herald** - Adaptive Trading Intelligence  
*The future of algorithmic trading.*
