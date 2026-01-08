# AI-NATIVE VERSION
> Windows  
> **UNSTABLE**

⚠️ **WARNING**: This branch is EXPERIMENTAL. For production, use **windows** branch (rule-based, stable).

---

# RULE-BASED VERSION
> Windows  
> **stable**

## Cthulu Autonomous Trading System v5.1.0

**Apex Release** - Rule-based algorithmic trading system for MT5.

### Overview
This is the **rule-based version** optimized for Windows. It uses:
- ✅ Technical indicators (EMA, SMA, RSI, ADX, MACD, Bollinger Bands, etc.)
- ✅ Multiple strategy selection (trend following, mean reversion, scalping, etc.)
- ✅ Entry confluence filtering (quality-based position sizing)
- ✅ Dynamic SL/TP management
- ✅ External trade adoption
- ✅ Risk management & position lifecycle
- ✅ Real-time monitoring & metrics (Prometheus)

### Key Features
- **Strategy Selector**: Automatically selects best strategy based on market regime
- **Entry Confluence Filter**: Scores entry quality (0-100) and adjusts position size
- **Dynamic SLTP**: Adapts stop-loss and take-profit based on market conditions
- **Trade Adoption**: Adopts external trades and manages them with dynamic SLTP
- **Multi-timeframe**: Supports M1, M5, M15, M30, H1, H4, D1
- **Real-time metrics**: Prometheus exporter on port 8181

### Quick Start

1. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

2. **Configure `.env`**:
   ```
   MT5_LOGIN=your_login
   MT5_PASSWORD=your_password
   MT5_SERVER=your_server
   MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
   ```

3. **Run**:
   ```powershell
   python -m cthulu --config config.json
   ```

### Configuration
Edit `config.json` to customize:
- **Symbol**: Trading symbol (e.g., `GOLDm#`)
- **Timeframe**: Chart timeframe (e.g., `TIMEFRAME_M30`)
- **Risk**: Position sizing, max drawdown, circuit breakers
- **Strategies**: Enable/disable specific strategies
- **Entry Confluence**: Minimum quality score for entries

### Documentation
- [Configuration Guide](docs/configuration.md)
- [Strategy Guide](docs/strategies.md)
- [Risk Management](docs/risk_management.md)
- [Monitoring](docs/monitoring.md)

### Architecture
```
core/           - Main trading loop & bootstrap
strategy/       - Trading strategies (EMA, SMA, scalping, etc.)
cognition/      - Entry confluence filter (rule-based quality scoring)
risk/           - Risk evaluator & dynamic SL/TP
execution/      - Order execution engine
position/       - Position tracker & lifecycle management
connector/      - MT5 connector
monitoring/     - Metrics & observability
```

### Branch Strategy
- **windows** (this branch): Rule-based system - **STABLE**
- **windows-ml**: AI/ML-native version - **UNSTABLE** (experimental)

### Data Export
The system exports trading events to `ML_RL/data/raw/` for analysis and future ML model development (on windows-ml branch).

### License
See LICENSE file.

### Support
For issues, questions, or contributions, please open an issue on GitHub.
