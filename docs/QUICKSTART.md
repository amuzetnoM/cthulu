# Herald Quick Start Guide

## Version 4.0.0 - Multi-Strategy Autonomous Trading

## 📦 Installation

### 1. Set Up Python Environment

```powershell
# Navigate to Herald directory
cd C:\workspace\herald

# Create virtual environment (Python 3.10-3.14 recommended)
python -m venv venv312

# Activate virtual environment
.\venv312\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure MT5 Credentials

**Option 1: Environment Variables (Recommended)**
```powershell
# Set environment variables
$env:MT5_LOGIN = "your_account_number"
$env:MT5_PASSWORD = "your_password"
$env:MT5_SERVER = "YourBroker-MT5"
```

**Option 2: Config File**
```powershell
# Run setup wizard (recommended)
python -m herald --wizard --config config.json

# Or edit config.json directly
code config.json
```

### 3. Enable Algo Trading in MT5

**IMPORTANT:** Before running Herald:
1. Open MetaTrader 5 terminal
2. Go to **Tools → Options → Expert Advisors**
3. Check **Allow automated trading**
4. Check **Allow DLL imports** (if applicable)
5. Click OK

### 4. Verify Installation

```powershell
# Check MT5 installation
python -c "import MetaTrader5 as mt5; print('MT5 version:', mt5.version())"

# Check Herald installation
python -c "import herald; print('Herald version:', herald.__version__)"
```

## 🚀 Running Herald

### Start Multi-Strategy Autonomous Trading

```powershell
# Start Herald with interactive setup wizard (recommended)
python -m herald --wizard --config config.json
```

The **interactive setup wizard** will guide you through:
1. **Trading Mindset** — Choose conservative, balanced, or aggressive
2. **Symbol** — Enter your trading instrument (EURUSD, XAUUSD#, BTCUSD#, etc.)
3. **Timeframe** — Select M5, M15, M30, H1, H4, or D1
4. **Risk Management** — Set daily loss limit, position size, max positions
5. **Strategy Settings** — Choose from 4 strategies: SMA, EMA, Momentum, Scalping
6. **Technical Indicators** — Select from 8 indicators including Supertrend, VWAP

After setup, Herald will:
1. Save your configuration to `config.json`
2. Connect to MT5 terminal
3. Load selected indicators and strategy
4. Start the autonomous multi-strategy trading loop
5. Monitor positions and execute exits automatically
6. Display desktop GUI for monitoring (optional)

### Launch Desktop GUI

```powershell
# Launch monitoring GUI only
python -m herald --gui
```

### Skip Setup Wizard (Automation)

```powershell
# Use existing config without wizard (for CI/automation)
python -m herald --config config.json --skip-setup
```

### Choose Trading Mindset

```powershell
# Use predefined risk profiles
python -m herald --config config.json --mindset aggressive
python -m herald --config config.json --mindset balanced    # default
python -m herald --config config.json --mindset conservative
```

### Monitor Logs

```powershell
# View logs in real-time
Get-Content .\herald.log -Wait -Tail 50
```

## 🎯 Pre-Launch Checklist

- [ ] Virtual environment created and activated (Python 3.10-3.14)
- [ ] Dependencies installed (`pip list` shows MetaTrader5, pandas, pydantic)
- [ ] MT5 credentials configured (env vars or config file)
- [ ] MT5 terminal installed with algo trading enabled
- [ ] Demo/Training account credentials configured
- [ ] Trading symbol available on your broker
- [ ] Test run completed successfully

## 📊 Multi-Strategy System Architecture

**Phase 4 Multi-Strategy Trading:**

1. **Market Regime Detection** - Analyze current market conditions (5 regimes)
2. **Dynamic Strategy Selection** - Choose optimal strategy based on regime and performance
3. **Market Data Ingestion** - Get OHLCV from MT5 with provider fallbacks
4. **Indicator Calculation** - 8 indicators: RSI, MACD, Bollinger, Stochastic, ADX, Supertrend, VWAP, Anchored VWAP
5. **Signal Generation** - Selected strategy evaluates indicator confluence
6. **Risk Approval** - Position sizing and limit checks with Kelly/dynamic sizing
7. **Order Execution** - Idempotent market orders with ML instrumentation
8. **Position Tracking** - Real-time monitoring with external trade adoption
9. **Exit Detection** - 4 exit strategies with priority system
10. **Performance Learning** - Update strategy affinity matrix
11. **Health Monitoring** - Connection recovery, reconciliation, GUI updates

## 🔧 Common Issues

### "Authorization failed"
- Ensure algo trading is enabled in MT5: Tools → Options → Expert Advisors
- Verify credentials (MT5_LOGIN, MT5_PASSWORD, MT5_SERVER) are correct
- Check server name matches your broker exactly

### "Failed to connect to MT5"
- MT5 terminal must be installed and running
- Try closing MT5 before running Herald (it will restart it)
- Check the MT5 path in config.json

### "Symbol not found"
- Check if your symbol is available on your broker
- Enable the symbol in MT5 MarketWatch first
- Change symbol in config to one your broker supports

### "Trading not allowed"
- Verify your account allows automated trading
- Check MT5 terminal Options → Expert Advisors → Allow automated trading
- For live trading, set LIVE_RUN_CONFIRM=1 environment variable

### "Config validation error"
- Run the wizard: `python -m herald --wizard --config config.json`
- Or check config.json syntax and required fields

## 🛑 Stopping Herald

Press `Ctrl+C` to gracefully shut down. The bot will:
1. Stop generating new signals
2. Optionally close all open positions
3. Disconnect from MT5 terminal
4. Save final state and logs
5. Close GUI if running

## 📚 Documentation

- **FEATURES_GUIDE.md** - Complete feature overview
- **ARCHITECTURE.md** - System design and data flow
- **CHANGELOG.md** - Version history and updates
- **SECURITY.md** - Security hardening and best practices
- **PERFORMANCE_TUNING.md** - Optimization and monitoring

---

**Remember:** Always test with a demo/training account before going live!
