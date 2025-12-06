```
   __ __                 __    __
  / // /__ _______ ___ _/ /___/ /
 / _  / -_) __/ _ `/ // / / _  / 
/_//_/\__/_/  \_,_/\_,_/_/\_,_/  
                                 
```

# Herald
*version 2.0.0*  [[CHANGELOG]](docs/CHANGELOG.md)

![Status](https://img.shields.io/badge/status-production--ready-success?style=for-the-badge)
[![Python](https://img.shields.io/badge/python-3.10--3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![MT5](https://img.shields.io/badge/MetaTrader-5-0066CC?style=for-the-badge)](https://www.metatrader5.com/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)
[![Phase](https://img.shields.io/badge/phase-2%20complete-blue?style=for-the-badge)](docs/CHANGELOG.md)

> **Adaptive Trading Intelligence for MetaTrader 5**
> A complete autonomous trading system with entry and exit execution, technical indicators, and advanced position management

A comprehensive automated trading system for MetaTrader 5 following enterprise-grade architecture patterns.
Built with focus on incremental development, robust risk management, and production-ready deployment.

**NEW in v2.0**: Full autonomous trading with 5 technical indicators, intelligent position management, and 4 priority-based exit strategies.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

Herald implements a staged, modular approach to automated trading.
The architecture emphasizes clear boundaries, testability, and safety with pluggable components that can be 
enhanced without disrupting core functionality.

### Design Principles

- **Single Responsibility**: Each module has a focused, well-defined role
- **Clear Boundaries**: Communication via standardized interfaces and data contracts
- **Replaceability**: Swap implementations (strategies, data sources) without core changes
- **Event-Driven**: Signals flow through approval and execution pipeline
- **Safety First**: Multiple layers of risk management and validation

### Data Flow

**Phase 1 Foundation:**
```
Market Data → Data Layer → Strategy → Signal → Risk Check → Execution → Persistence
```

**Phase 2 Autonomous Trading (NEW):**
```
Market Data → Indicators (5) → Strategy Signals → Risk Approval → 
Order Execution → Position Tracking → Exit Detection (4) → Position Close → 
Persistence & Metrics
```

---

## Features

### Core Infrastructure (Phase 1)

| Component | Description |
|-----------|-------------|
| **MT5 Connector** | Reliable session management with automatic reconnection and rate limiting |
| **Data Layer** | Normalized OHLCV data pipeline with caching and resampling |
| **Strategy Engine** | Pluggable strategy architecture starting with SMA crossover |
| **Execution Engine** | Idempotent order submission with partial fill handling |
| **Risk Manager** | Position sizing, exposure limits, daily loss guards, emergency shutdown |
| **Persistence** | SQLite database for trades, signals, and performance metrics |
| **Observability** | Structured logging with health checks and status monitoring |

### Autonomous Trading (Phase 2) 🆕

| Component | Description |
|-----------|-------------|
| **Technical Indicators** | 5 indicators: RSI, MACD, Bollinger Bands, Stochastic, ADX |
| **Position Manager** | Real-time tracking, P&L monitoring, MT5 synchronization |
| **Exit Strategies** | 4 strategies: Trailing stop, time-based, profit target, adverse movement |
| **Autonomous Loop** | Complete 10-step trading cycle with health monitoring |
| **Priority System** | Emergency → Time → Profit → Trailing stop execution order |
| **Reconciliation** | Automatic position sync after connection loss |
| **Dry-Run Mode** | Test strategies without real orders |

---

## Architecture

```
herald/
├── connector/         # MT5 connection management
│   └── mt5_connector.py
├── data/             # Market data normalization
│   └── layer.py
├── strategy/         # Trading strategies
│   ├── base.py
│   └── sma_crossover.py
├── execution/        # Order execution
│   └── engine.py
├── risk/             # Risk management
│   └── manager.py
├── indicators/       # 🆕 Technical indicators
│   ├── base.py
│   ├── rsi.py
│   ├── macd.py
│   ├── bollinger.py
│   ├── stochastic.py
│   └── adx.py
├── position/         # 🆕 Position management
│   └── manager.py
├── exit/             # 🆕 Exit strategies
│   ├── base.py
│   ├── trailing_stop.py
│   ├── time_based.py
│   ├── profit_target.py
│   └── adverse_movement.py
├── persistence/      # Database layer
│   └── database.py
├── observability/    # Logging and monitoring
│   ├── logger.py
│   └── metrics.py
└── __main__.py       # 🆕 Autonomous orchestrator
```

### Component Responsibilities

#### Phase 1 - Foundation

**Connector**
- MT5 session lifecycle (connect, disconnect, health checks)
- Rate limiting and timeout handling
- Exception consolidation and reconnection policy

**Data Layer**
- OHLCV normalization to pandas DataFrames
- Multi-timeframe resampling
- Data caching for backtesting
- Indicator integration

**Strategy**
- Signal generation from market data
- Configurable parameters
- State management
- Signal validation

**Execution Engine**
- Order placement (market/limit/stop)
- Idempotent order submission
- Partial fill handling
- Position closure and modification

**Risk Manager**
- Position sizing (percent/volatility-based)
- Exposure limits (per-symbol, total)
- Daily loss limits with auto-pause
- Emergency shutdown capability

#### Phase 2 - Autonomous Trading 🆕

**Indicators**
- RSI: Overbought/oversold detection (14 period)
- MACD: Trend following with crossovers (12/26/9)
- Bollinger Bands: Volatility and breakout detection (20/2)
- Stochastic: Momentum oscillator (%K/%D)
- ADX: Trend strength measurement (+DI/-DI)

**Position Manager**
- Real-time position tracking synced with MT5
- Continuous P&L calculation
- Position lifecycle management (track, monitor, close)
- Partial and full position closing
- Reconciliation after connection loss
- Position age and exposure analytics

**Exit Strategies** (Priority-based)
1. **Adverse Movement** (Priority 90 - Emergency)
   - Flash crash protection
   - Rapid adverse movement detection
   - 60-second time window analysis

2. **Time-Based** (Priority 50)
   - Maximum hold time enforcement
   - Weekend protection (Friday close)
   - Day trading mode (EOD close)

3. **Profit Target** (Priority 40)
   - Percentage/pip-based targets
   - Multiple levels with partial closes
   - Volatility-adjusted targets

4. **Trailing Stop** (Priority 25)
   - ATR-based dynamic stops
   - Never moves against profit
   - Activation after profit threshold

**Autonomous Orchestrator**
- 10-step continuous trading loop
- Module initialization and configuration loading
- Market data ingestion and indicator calculation
- Signal generation and risk approval
- Order execution and position tracking
- Exit detection and position closing
- Health monitoring and reconnection
- Graceful shutdown with position cleanup

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- MetaTrader 5 terminal installed
- Active MT5 demo or live account

### Automated Setup

#### Windows (PowerShell)

```powershell
# Clone or navigate to Herald directory
cd C:\workspace\Herald

# Run automated setup
.\scripts\setup.ps1
```

#### Linux/macOS

```bash
# Clone or navigate to Herald directory
cd ~/herald

# Run automated setup
bash scripts/setup.sh
```

### Manual Setup

```powershell
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy config template
cp config/config.example.yaml config/config.yaml

# Edit configuration
notepad config/config.yaml  # Windows
nano config/config.yaml     # Linux/macOS
```

### Configure Credentials

**Option 1: Environment Variables (Recommended)**

```bash
# Copy template
cp .env.example .env

# Edit .env file with your credentials
# .env is already in .gitignore for security
nano .env  # or use your preferred editor
```

```bash
# .env file
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=Broker-Demo

RISK_PER_TRADE=0.02
MAX_DAILY_LOSS=0.05

LOG_LEVEL=INFO
DRY_RUN=false
```

**Option 2: Configuration File**

Edit `config.json` (see `config.example.json`):

```json
{
  "mt5": {
    "login": 12345678,
    "password": "your_password",
    "server": "Broker-Demo",
    "path": "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
  },
  "trading": {
    "symbol": "EURUSD",
    "timeframe": "TIMEFRAME_H1",
    "poll_interval": 60,
    "lookback_bars": 500
  },
  "risk": {
    "max_position_size": 1.0,
    "default_position_size": 0.1,
    "max_daily_loss": 500.0,
    "max_positions_per_symbol": 1,
    "max_total_positions": 3
  },
  "strategy": {
    "type": "sma_crossover",
    "params": {
      "fast_period": 10,
      "slow_period": 30
    }
  },
  "indicators": [
    {"type": "rsi", "params": {"period": 14}},
    {"type": "macd", "params": {"fast_period": 12, "slow_period": 26, "signal_period": 9}},
    {"type": "bollinger", "params": {"period": 20, "std_dev": 2.0}},
    {"type": "adx", "params": {"period": 14}}
  ],
  "exit_strategies": [
    {"type": "adverse_movement", "enabled": true, "params": {"movement_threshold_pct": 1.0}},
    {"type": "time_based", "enabled": true, "params": {"max_hold_hours": 24.0}},
    {"type": "profit_target", "enabled": true, "params": {"target_pct": 2.0}},
    {"type": "trailing_stop", "enabled": true, "params": {"atr_multiplier": 2.0}}
  ]
}
```

### Run Herald (Autonomous Trading)

```bash
# Autonomous trading with config file
python -m herald --config config.json

# Dry run mode (no real orders) - Test your setup safely
python -m herald --config config.json --dry-run

# With debug logging
python -m herald --config config.json --log-level DEBUG

# Quick test connection
python -c "from connector.mt5_connector import MT5Connector, ConnectionConfig; \
           import os; \
           config = ConnectionConfig(login=int(os.getenv('MT5_LOGIN')), \
                                     password=os.getenv('MT5_PASSWORD'), \
                                     server=os.getenv('MT5_SERVER')); \
           conn = MT5Connector(config); \
           print('Connected!' if conn.connect() else 'Failed')"
```

**What Happens When You Run:**
1. Connects to MT5 with your credentials
2. Initializes all modules (indicators, strategy, risk, execution, position manager)
3. Loads configured exit strategies (4 strategies by default)
4. Starts autonomous trading loop:
   - Fetches market data every 60 seconds (configurable)
   - Calculates 5 technical indicators
   - Generates strategy signals
   - Executes approved trades
   - Monitors open positions
   - Checks exit conditions (priority-based)
   - Closes positions when exit triggered
5. Logs all activity to console and `herald.log`
6. Stores trades in `herald.db` database

**Monitor Live Trading:**
```bash
# Watch log file
tail -f herald.log  # Linux/macOS
Get-Content herald.log -Wait -Tail 50  # Windows PowerShell

# Query database for open positions
python -c "from persistence.database import Database; \
           db = Database('herald.db'); \
           trades = db.get_open_trades(); \
           print(f'Open trades: {len(trades)}')"
```

---

## Configuration

Configuration is managed through YAML files in the `config/` directory.

### Core Settings

**MT5 Connection**
```yaml
mt5:
  login: int              # Account number
  password: str           # Account password
  server: str             # Broker server
  timeout: int            # Connection timeout (ms)
  portable: bool          # Portable MT5 installation
  path: str               # Custom MT5 path (optional)
```

**Trading Parameters**
```yaml
trading:
  symbol: str             # Primary trading symbol
  timeframe: str          # Analysis timeframe (M1, M5, H1, H4, D1)
  magic_number: int       # Unique bot identifier
  slippage: int           # Maximum slippage (points)
```

**Risk Management**
```yaml
risk:
  max_position_size_pct: float    # Max position size (% of balance)
  max_total_exposure_pct: float   # Max total exposure
  max_daily_loss_pct: float       # Daily loss limit
  max_positions_per_symbol: int   # Max positions per symbol
  max_total_positions: int        # Max concurrent positions
  min_risk_reward_ratio: float    # Minimum R:R for trades
  volatility_scaling: bool        # Enable ATR-based scaling
```

**Strategy Configuration**
```yaml
strategy:
  name: str                       # Strategy to use
  short_window: int               # Fast SMA period
  long_window: int                # Slow SMA period
  atr_period: int                 # ATR period
  atr_multiplier: float           # ATR multiplier for SL
  risk_reward_ratio: float        # R:R ratio for TP
```

---

## Usage

### Basic Operation

```python
from herald import MT5Connector, DataLayer, SmaCrossover, ExecutionEngine, RiskManager
from herald.connector import ConnectionConfig
from herald.risk import RiskLimits

# Initialize components
config = ConnectionConfig(
    login=12345678,
    password="password",
    server="Broker-Demo"
)

connector = MT5Connector(config)
connector.connect()

data_layer = DataLayer()
risk_manager = RiskManager(RiskLimits())
execution = ExecutionEngine(connector)

# Load strategy
strategy = SmaCrossover({
    'symbol': 'XAUUSD',
    'timeframe': '1H',
    'short_window': 20,
    'long_window': 50
})

# Fetch and analyze data
rates = connector.get_rates('XAUUSD', mt5.TIMEFRAME_H1, 200)
df = data_layer.normalize_rates(rates)
df = data_layer.add_indicators(df, {
    'sma': [20, 50],
    'atr': 14
})

# Generate signal
latest_bar = df.iloc[-1]
signal = strategy.on_bar(latest_bar)

if signal:
    # Risk approval
    account = connector.get_account_info()
    approved, reason, size = risk_manager.approve(signal, account)
    
    if approved:
        # Execute trade
        order_req = OrderRequest(
            signal_id=signal.id,
            symbol=signal.symbol,
            side=signal.action,
            volume=size,
            order_type=OrderType.MARKET,
            sl=signal.stop_loss,
            tp=signal.take_profit
        )
        result = execution.place_order(order_req)
```

### Command Line Interface

```bash
# Start bot with default config
python -m herald

# Use custom config
python -m herald --config config/prod.yaml

# Dry run (no actual trading)
python -m herald --dry-run

# Backtest mode
python -m herald --backtest --start 2024-01-01 --end 2024-12-31

# Check system health
python -m herald --health-check

# View current positions
python -m herald --positions

# Emergency shutdown
python -m herald --shutdown
```

---

## Development

### Project Structure

```
Herald/
├── herald/                 # Main package
│   ├── connector/          # MT5 integration
│   ├── data/               # Data processing
│   ├── strategy/           # Trading strategies
│   ├── execution/          # Order execution
│   ├── risk/               # Risk management
│   ├── persistence/        # Database layer
│   └── observability/      # Logging/monitoring
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── config/                 # Configuration files
├── scripts/                # Utility scripts
├── docs/                   # Documentation
├── logs/                   # Log files
├── data/                   # Market data cache
└── output/                 # Reports and artifacts
```

### Adding a New Strategy

```python
from herald.strategy import Strategy, Signal, SignalType
import pandas as pd

class MyStrategy(Strategy):
    def __init__(self, config):
        super().__init__("my_strategy", config)
        self.threshold = config.get('threshold', 0.5)
    
    def on_bar(self, bar: pd.Series) -> Signal:
        # Your strategy logic
        if condition:
            return Signal(
                id=self.generate_signal_id(),
                timestamp=bar.name,
                symbol=self.config['symbol'],
                timeframe=self.config['timeframe'],
                side=SignalType.LONG,
                action='BUY',
                price=bar['close'],
                stop_loss=bar['close'] - bar['atr'] * 2,
                take_profit=bar['close'] + bar['atr'] * 4,
                confidence=0.8,
                reason="Custom strategy trigger"
            )
        return None
```

### Code Quality

```bash
# Format code
black herald/ tests/

# Lint
pylint herald/

# Type check
mypy herald/

# Run all checks
./scripts/quality_check.sh
```

---

## Testing

### Run Test Suite

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=herald --cov-report=html

# Specific test
pytest tests/unit/test_connector.py -v
```

### Test Categories

**Unit Tests**
- Connector connection logic
- Data normalization
- Strategy signal generation
- Risk calculations
- Order request building

**Integration Tests**
- Full MT5 connection cycle
- Data fetch and processing pipeline
- Strategy execution workflow
- Order placement and tracking

---

## Deployment

### Production Checklist

- [ ] Run on demo account for minimum 2 weeks
- [ ] Verify win rate and profit factor meet thresholds
- [ ] Test emergency shutdown procedure
- [ ] Configure monitoring and alerts
- [ ] Set up log aggregation
- [ ] Document backup and recovery procedures
- [ ] Review and test disaster recovery plan

### Running as Service

#### Windows (NSSM)

```powershell
# Install service
nssm install Herald "C:\workspace\Herald\venv\Scripts\python.exe" "-m herald"
nssm set Herald AppDirectory "C:\workspace\Herald"
nssm start Herald
```

#### Linux (systemd)

```ini
# /etc/systemd/system/herald.service
[Unit]
Description=Herald Trading Bot
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/opt/herald
ExecStart=/opt/herald/venv/bin/python -m herald
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable herald
sudo systemctl start herald
sudo systemctl status herald
```

---

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to MT5
```
ERROR: MT5 initialize failed: (code, message)
```

**Solution**:
1. Verify MT5 terminal is installed
2. Check account credentials in config.yaml
3. Confirm broker server name is correct
4. Try portable mode if using portable MT5
5. Check MT5 terminal logs

### Trading Not Allowed

**Problem**: Orders rejected with "Trading not allowed"

**Solution**:
1. Check MT5 terminal allows automated trading (Tools → Options → Expert Advisors)
2. Verify account allows algo trading
3. Confirm symbol is available for trading
4. Check trading hours for symbol

### Signal Not Generated

**Problem**: Strategy not producing signals

**Solution**:
1. Verify sufficient historical data (need 200+ bars)
2. Check indicator calculations are not NaN
3. Review strategy configuration parameters
4. Enable debug logging to trace signal generation
5. Validate market conditions match strategy requirements

### Log Analysis

```powershell
# View recent errors
Select-String -Path logs\herald.log -Pattern "ERROR" | Select-Object -Last 20

# Monitor live
Get-Content logs\herald.log -Wait -Tail 50

# Search for specific pattern
Select-String -Path logs\herald.log -Pattern "signal generated"
```

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

**Disclaimer**: This software is for educational purposes. Trading financial instruments carries risk.
Past performance is not indicative of future results. Use at your own risk.

---

## Documentation

### Core Documentation
- **[CHANGELOG](docs/CHANGELOG.md)** - Complete version history from v0.1.0 to v2.0.0
- **[Build Plan](docs/build_plan.md)** - Phase 1 & 2 specifications and roadmap
- **[Architecture](docs/ARCHITECTURE.md)** - System architecture and design patterns
- **[Guide](docs/GUIDE.md)** - Comprehensive user guide

### Phase 2 Documentation 🆕
- **[Phase 2 README](PHASE2_README.md)** - Complete autonomous trading guide
- **[Phase 2 Summary](PHASE2_SUMMARY.md)** - Implementation details and statistics
- **[Configuration Example](config.example.json)** - Full JSON configuration template

### API Reference
- **[HTML Documentation](docs/index.html)** - Interactive documentation website

## Version History

| Version | Date | Status | Description |
|---------|------|--------|-------------|
| **2.0.0** | Dec 2024 | ✅ Complete | **Autonomous Trading** - Indicators, position management, exit strategies |
| **1.0.0** | Nov 2024 | ✅ Complete | **Foundation** - Core infrastructure, risk management, persistence |
| **0.1.0** | Oct 2024 | ✅ Complete | **Initial Setup** - Project initialization |

See [CHANGELOG.md](docs/CHANGELOG.md) for detailed release notes.

## Support

- **Documentation**: `docs/` directory
- **Phase 2 Guide**: [PHASE2_README.md](PHASE2_README.md)
- **Examples**: `config.example.json`, `.env.example`
- **Database**: Query `herald.db` for trade history
- **Logs**: Review `herald.log` for execution details
- **Issues**: Create issue in repository

## Roadmap

### ✅ Phase 1 - Foundation (Complete)
- MT5 connector with reconnection
- Data normalization and caching
- Strategy framework
- Execution engine
- Risk management
- Persistence layer

### ✅ Phase 2 - Autonomous Trading (Complete)
- 5 Technical indicators (RSI, MACD, Bollinger, Stochastic, ADX)
- Position manager with real-time tracking
- 4 Exit strategies (trailing, time, profit, adverse)
- Autonomous orchestrator loop
- Comprehensive monitoring

### 🔄 Phase 3 - Machine Learning (Planned)
- Offline model evaluation pipeline
- Feature engineering from indicators
- Model serving for inference
- Training reproducibility

### 📋 Phase 4 - Advanced Intelligence (Planned)
- Reinforcement learning (DQN/PPO)
- Sentiment analysis
- Regime detection
- Adaptive parameterization

### 📋 Phase 5 - Production Features (Planned)
- Automated backtesting pipeline
- Real-time monitoring dashboard
- Alert system
- Safe deployment automation
- Comprehensive audit reports

---

**Built with focus on safety, testability, and production readiness.**

*Herald v2.0.0 - Complete autonomous trading from data ingestion to position management to intelligent exits.*
