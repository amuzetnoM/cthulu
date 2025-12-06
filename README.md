```
   __ __                 __    __
  / // /__ _______ ___ _/ /___/ /
 / _  / -_) __/ _ `/ // / / _  / 
/_//_/\__/_/  \_,_/\_,_/_/\_,_/  
                                 
```

# Herald
*version 1.0.0*

![Status](https://img.shields.io/badge/status-active-success?style=for-the-badge)
[![Python](https://img.shields.io/badge/python-3.10--3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![MT5](https://img.shields.io/badge/MetaTrader-5-0066CC?style=for-the-badge)](https://www.metatrader5.com/)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

> **Adaptive Trading Intelligence for MetaTrader 5**
> A modular, event-driven trading bot emphasizing safety, testability, and extensibility

A comprehensive automated trading system for MetaTrader 5 following enterprise-grade architecture patterns.
Built with focus on incremental development, robust risk management, and production-ready deployment.

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

Herald implements a staged, modular approach to automated trading per the system build_plan.md specification.
The architecture emphasizes clear boundaries, testability, and safety with pluggable components that can be 
enhanced without disrupting core functionality.

### Design Principles

- **Single Responsibility**: Each module has a focused, well-defined role
- **Clear Boundaries**: Communication via standardized interfaces and data contracts
- **Replaceability**: Swap implementations (strategies, data sources) without core changes
- **Event-Driven**: Signals flow through approval and execution pipeline
- **Safety First**: Multiple layers of risk management and validation

### Data Flow

```
Market Data → Data Layer → Strategy → Signal → Risk Check → Execution → Persistence
```

---

## Features

| Component | Description |
|-----------|-------------|
| **MT5 Connector** | Reliable session management with automatic reconnection and rate limiting |
| **Data Layer** | Normalized OHLCV data pipeline with caching and resampling |
| **Strategy Engine** | Pluggable strategy architecture starting with SMA crossover |
| **Execution Engine** | Idempotent order submission with partial fill handling |
| **Risk Manager** | Position sizing, exposure limits, daily loss guards, emergency shutdown |
| **Persistence** | SQLite database for trades, signals, and performance metrics |
| **Observability** | Structured logging with health checks and status monitoring |

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
├── persistence/      # Database layer
│   └── database.py
└── observability/    # Logging and monitoring
    └── logger.py
```

### Component Responsibilities

**Connector**
- MT5 session lifecycle (connect, disconnect, health checks)
- Rate limiting and timeout handling
- Exception consolidation and reconnection policy

**Data Layer**
- OHLCV normalization to pandas DataFrames
- Technical indicator calculation
- Multi-timeframe resampling
- Data caching for backtesting

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

### Configure MT5 Credentials

Edit `config/config.yaml`:

```yaml
mt5:
  login: 12345678          # Your MT5 account number
  password: "your_password"  # Account password
  server: "Broker-Demo"      # Broker server name
  timeout: 60000

trading:
  symbol: "XAUUSD"
  timeframe: "H1"
  
risk:
  max_position_size_pct: 0.02  # 2% risk per trade
  max_daily_loss_pct: 0.05     # 5% daily loss limit
  max_total_positions: 3

strategy:
  name: "sma_crossover"
  short_window: 20
  long_window: 50
```

### Run Herald

```python
# Start trading bot
python -m herald

# Run with specific config
python -m herald --config config/custom.yaml

# Dry run mode (no real orders)
python -m herald --dry-run
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

## Support

- Documentation: `docs/`
- Build Plan: `build_plan.md`
- Architecture: `docs/ARCHITECTURE.md`
- Issues: Create issue in repository

---

**Built with focus on safety, testability, and production readiness.**
