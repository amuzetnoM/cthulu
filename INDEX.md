# SYSTEM INDEX

![](https://img.shields.io/badge/Version-5.1.0_APEX-4B0082?style=for-the-badge&labelColor=0D1117&logo=git&logoColor=white)
![](https://img.shields.io/github/last-commit/amuzetnoM/cthulu?style=for-the-badge&labelColor=0D1117&logo=github&logoColor=white)

<p align="center">
  <img src="assets/cthulu-black.png" width="400" />
</p>

## OVERVIEW

Cthulu is an autonomous multi-strategy trading system for MetaTrader 5 featuring 7 active trading strategies, 12 technical indicators, and the revolutionary SAFE (Set And Forget Engine) paradigm for fully autonomous operation.

**Current Version:** v5.1.0 "APEX" — Production Ready

---

## CORE DOCUMENTATION

### Getting Started
| Document | Description |
|----------|-------------|
| [Introduction](docs/01_INTRODUCTION.md) | System overview and comprehensive user guide |
| [Quick Start](docs/02_QUICKSTART.md) | Installation and first-time setup |
| [Usage & Terms](docs/03_USAGE.md) | Terms of use and basic operations |

### System Architecture
| Document | Description |
|----------|-------------|
| [Architecture](docs/04_ARCHITECTURE.md) | Technical architecture with comprehensive diagrams |
| [Features Guide](docs/05_FEATURES_GUIDE.md) | Complete feature documentation and SAFE engine |
| [Mindsets](docs/06_MINDSETS.md) | Trading profiles: Conservative, Balanced, Aggressive, Ultra-Aggressive |

### Risk & Position Management
| Document | Description |
|----------|-------------|
| [Risk Management](docs/07_RISK.md) | Risk configuration and stop-loss strategies |
| [Position Management](docs/08_POSITION_MANAGEMENT.md) | Profit scaling, lifecycle, and trade adoption |

### Deployment & Operations
| Document | Description |
|----------|-------------|
| [Deployment](docs/09_DEPLOYMENT.md) | Production deployment strategies (Docker, systemd) |
| [Observability](docs/10_OBSERVABILITY.md) | Metrics, monitoring, and Prometheus setup |
| [Backtesting](docs/11_BACKTESTING.md) | Strategy validation and backtesting framework |

### Advanced Topics
| Document | Description |
|----------|-------------|
| [Machine Learning & RL](docs/12_ML-RL.md) | ML/RL integration philosophy and implementation |
| [Performance Tuning](docs/13_PERFORMANCE_TUNING.md) | Optimization and benchmarking strategies |
| [Advisory Modes](docs/14_ADVISORY.md) | Testing modes and paper trading |
| [Utilities](docs/15_UTILITIES.md) | Infrastructure components and helper modules |

### Security & Compliance
| Document | Description |
|----------|-------------|
| [Security](docs/16_SECURITY.md) | Security guidelines and best practices |
| [Mathematics](docs/17_MATHEMATICS.md) | Mathematical foundations for risk and sizing |
| [Hecktor Integration](docs/18_HECKTOR.md) | 👾 Cthulu x 👽 Hecktor vector database integration |
| [Privacy Policy](docs/19_PRIVACY_POLICY.md) | Data handling and privacy practices |

### Documentation Meta
| Document | Description |
|----------|-------------|
| [Documentation Gaps](docs/DOCUMENTATION_GAPS_ANALYSIS.md) | Analysis of documentation coverage |
| [Documentation Review](docs/DOCUMENTATION_REVIEW_SUMMARY.md) | Executive summary of documentation status |
| [Changelog](docs/Changelog/CHANGELOG.md) | Complete version history and release notes |

---

## MODULE DIRECTORIES

### Core Trading System
| Module | Description | Documentation |
|--------|-------------|---------------|
| **advisory** | Advisory and ghost trading modes for safe testing | [README](advisory/README.md) |
| **cognition** | ML/RL cognition engine for intelligent augmentation | [README](cognition/README.md) |
| **execution** | Order execution engine with MT5 integration | Core module |
| **strategy** | Trading strategies (RSI, EMA, Momentum, Scalping, etc.) | Core module |
| **indicators** | Technical indicators (RSI, MACD, Bollinger, ADX, etc.) | Core module |

### Risk & Position Management
| Module | Description | Documentation |
|--------|-------------|---------------|
| **risk** | Risk management and position sizing | [README](risk/README.md) |
| **position** | Position lifecycle and profit scaling | [README](position/README.md) |
| **exit** | Exit strategies (trailing stop, profit target, time-based) | Core module |

### Infrastructure & Utilities
| Module | Description | Documentation |
|--------|-------------|---------------|
| **connector** | MetaTrader 5 connector and session management | Core module |
| **utils** | Circuit breakers, rate limiters, caching, retry logic | [README](utils/README.md) |
| **persistence** | Database layer for trades, signals, and metrics | Core module |
| **sentinel** | System monitoring and health checks | [README](sentinel/README.md) |

### Monitoring & Observability
| Module | Description | Documentation |
|--------|-------------|---------------|
| **monitoring** | Trade monitoring and metrics collection | [README](monitoring/README.md) |
| **observability** | Structured logging, Prometheus metrics, runbooks | [README](observability/README.md) |
| **rpc** | RPC server for external integrations | [README](rpc/README.md) |

### Testing & Validation
| Module | Description | Documentation |
|--------|-------------|---------------|
| **backtesting** | Strategy validation and historical testing | [README](backtesting/README.md) |
| **training** | ML/RL model training and validation | [README](training/README.md) |
| **audit** | Security audits and compliance reports | [README](audit/README.md) |

### Deployment & Configuration
| Module | Description | Documentation |
|--------|-------------|---------------|
| **deployment** | Production deployment configurations | [README](deployment/README.md) |
| **configs** | Configuration templates and mindset presets | [README](configs/mindsets/README.md) |

---

## QUICK REFERENCE

### Essential Links
- **System Overview**: [OVERVIEW.md](OVERVIEW.md)
- **Changelog**: [docs/Changelog/CHANGELOG.md](docs/Changelog/CHANGELOG.md)
- **License**: [LICENSE](LICENSE)

### Key Features
- 7 Active Trading Strategies
- 12 Technical Indicators
- Multi-Strategy Fallback System
- Enterprise Risk Management
- Real-Time Monitoring & Alerts
- 185+ Passing Tests, 95% Coverage

### Quick Start Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Start with interactive setup
python -m cthulu --config config.json

# Skip setup for automation
python -m cthulu --config config.json --skip-setup

# Dry run mode (no real orders)
python -m cthulu --config config.json --dry-run
```

---

## SUPPORT

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Browse `/docs` directory for detailed guides
- **Community**: See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines

---

**👾 Built with focus on safety, testability, and production readiness**

## SYSTEM ARCHITECTURE

```mermaid
flowchart LR
    subgraph INPUT["Input Layer"]
        MT5[MetaTrader 5]
        NEWS[News Feeds]
    end
    
    subgraph CORE["Core Engine"]
        DATA[Data Layer]
        IND[Indicators]
        STRAT[Strategy Engine]
        REGIME[Regime Detection]
    end
    
    subgraph EXECUTION["Execution Layer"]
        RISK[Risk Manager]
        EXEC[Execution Engine]
        POS[Position Manager]
        EXIT[Exit Strategies]
    end
    
    subgraph STORAGE["Persistence Layer"]
        DB[SQLite Database]
        LOGS[Structured Logs]
    end
    
    subgraph MONITORING["Monitoring Layer"]
        GUI[Desktop GUI]
        PROM[Prometheus]
        RPC[RPC Server]
    end
    
    MT5 --> DATA
    NEWS --> DATA
    DATA --> IND
    IND --> REGIME
    REGIME --> STRAT
    STRAT --> RISK
    RISK --> EXEC
    EXEC --> POS
    POS --> EXIT
    EXIT --> DB
    POS --> DB
    DB --> LOGS
    DB --> GUI
    LOGS --> PROM
    GUI --> RPC
    
    style CORE fill:#00ff88,stroke:#00cc6a,color:#000
    style EXECUTION fill:#00aaff,stroke:#0088cc,color:#000
    style MONITORING fill:#ffaa00,stroke:#dd8800,color:#000
```

---

## QUICK START

### Installation

```bash
# Clone repository
git clone https://github.com/amuzetnoM/cthulu.git
cd cthulu

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy configuration template
cp config.example.json config.json

# Edit configuration with your MT5 credentials
nano config.json  # or use your preferred editor
```

### Running Cthulu

```bash
# Interactive setup (recommended for first-time users)
python -m cthulu --config config.json

# Skip setup wizard (for automation)
python -m cthulu --config config.json --skip-setup

# Dry run mode (no real orders)
python -m cthulu --config config.json --dry-run

# Debug mode
python -m cthulu --config config.json --log-level DEBUG
```

### Configuration Presets

Cthulu includes pre-configured mindsets:

- **Conservative**: Low risk, capital preservation (1-2% position size)
- **Balanced**: Standard trading (2% position size)
- **Aggressive**: Active trading (5% position size)
- **Ultra-Aggressive**: High-frequency trading (15% position size)

```bash
# Use a mindset preset
python -m cthulu --config config.json --mindset aggressive
```

---

## TRADING STRATEGIES

### Strategy Overview

| Strategy | Type | Market Regime | Signal Speed |
|----------|------|---------------|--------------|
| **RSI Reversal** | Reversal | Volatile/Reversal | Instant |
| **EMA Crossover** | Trend | Trending | Fast |
| **SMA Crossover** | Trend | Trending (Weak) | Medium |
| **Momentum Breakout** | Breakout | Volatile Breakout | Medium |
| **Scalping** | Mean Reversion | Ranging (Tight) | Ultra-Fast |
| **Mean Reversion** | Reversal | Ranging | Fast |
| **Trend Following** | Trend | Trending (Strong) | Slow |

### Multi-Strategy Fallback System

When the primary strategy returns no signal, Cthulu automatically tries up to 3 alternative strategies:

1. Primary strategy attempts signal generation
2. If no signal, try alternative strategy #1
3. If no signal, try alternative strategy #2
4. If no signal, try alternative strategy #3
5. If all fail, skip bar and continue

This ensures maximum opportunity capture across all market conditions.

---

## TECHNICAL INDICATORS

Cthulu uses 12 advanced technical indicators:

1. **RSI** (Relative Strength Index) - Overbought/oversold detection
2. **MACD** (Moving Average Convergence Divergence) - Trend following
3. **Bollinger Bands** - Volatility and breakout detection
4. **Stochastic Oscillator** - Momentum analysis
5. **ADX** (Average Directional Index) - Trend strength
6. **Supertrend** - Dynamic support/resistance
7. **VWAP** (Volume Weighted Average Price) - Institutional levels
8. **ATR** (Average True Range) - Volatility measurement
9. **VPT** (Volume Price Trend) - Volume confirmation
10. **Volume Oscillator** - Volume momentum
11. **Price Volume Trend** - Cumulative volume
12. **Williams %R** - Overbought/oversold momentum

---

## EXIT STRATEGIES

Cthulu employs 4 priority-based exit strategies:

1. **Priority 90 - Adverse Movement** (Emergency)
   - Flash crash protection
   - Rapid adverse movement detection
   
2. **Priority 50 - Time-Based**
   - Maximum hold time enforcement
   - Weekend/day-end protection
   
3. **Priority 40 - Profit Target**
   - Take profit levels
   - Partial closes at multiple levels
   
4. **Priority 25 - Trailing Stop**
   - ATR-based dynamic stops
   - Profit lock mechanism

---

## MONITORING & OBSERVABILITY

### Desktop GUI

- Real-time trade monitoring
- Position P&L tracking
- Manual trade placement
- Strategy performance metrics

### Prometheus Metrics

- Trade performance snapshots
- Rolling Sharpe ratio
- Drawdown tracking
- System health metrics

### Structured Logging

- JSON-formatted logs
- Correlation IDs
- Trade provenance tracking
- Audit trail

---

## RISK MANAGEMENT

### Position Sizing

- **Percentage-based**: 1-15% of account balance
- **Kelly Criterion**: Mathematically optimal sizing
- **Fixed Lot Size**: Static position sizes
- **Volatility-based**: ATR-adjusted sizing

### Risk Limits

- **Daily Loss Limit**: Automatic pause on breach
- **Position Limits**: Per-symbol and total exposure
- **Emergency Shutdown**: Manual kill-switch
- **Margin Monitoring**: Real-time margin checks

### Safety Features

- **Survival Mode**: Automatic recovery from critical states
- **Equity Curve Management**: Dynamic risk adjustment
- **Liquidity Trap Detection**: Avoid illiquid markets
- **Flash Crash Protection**: Emergency exit triggers

---

## DEPLOYMENT OPTIONS

### Local Development

```bash
python -m cthulu --config config.json
```

### Docker Container

```bash
docker build -t cthulu .
docker run -d --name cthulu-trader cthulu
```

### Linux Service (systemd)

```bash
sudo systemctl enable cthulu
sudo systemctl start cthulu
```

### Windows Service (NSSM)

```powershell
nssm install Cthulu "C:\workspace\cthulu\venv\Scripts\python.exe"
nssm start Cthulu
```

---

## SUPPORT & COMMUNITY

- **Documentation**: Browse the `/docs` directory for detailed guides
- **Issues**: Report bugs via GitHub Issues
- **Changelog**: See [CHANGELOG.md](docs/Changelog/CHANGELOG.md) for version history
- **License**: MIT License - See [LICENSE](LICENSE)

---

## DISCLAIMER

⚠️ **Trading Financial Instruments Carries Risk**

This software is provided for educational and research purposes. Trading financial instruments involves substantial risk of loss. Past performance is not indicative of future results. 

- Only trade with capital you can afford to lose
- Always test on demo accounts first
- Understand the system before deploying with real money
- Review all risk management settings carefully

**The authors and contributors of Cthulu are not responsible for any trading losses incurred.**

---

## LICENSE

MIT License © 2024-2025 Cthulu Contributors

See [LICENSE](LICENSE) file for complete details.

---

**Built with focus on safety, testability, and production readiness. 👾**
