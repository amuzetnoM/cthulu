# Herald Quick Start Guide

## Version 2.0.0 - Autonomous Trading

## 📦 Installation

### 1. Set Up Python Environment

```powershell
# Navigate to Herald directory
cd C:\workspace\herald

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure MT5 Credentials

```powershell
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
code .env
```

**Required settings in .env:**
```dotenv
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-MT5
```

**Optional trading settings in .env:**
```dotenv
RISK_PER_TRADE=0.02
MAX_DAILY_LOSS=0.05
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
```

## 🚀 Running Herald

### Start Autonomous Trading

```powershell
# Make sure your .env file has credentials configured
python -m herald --config config.example.json
```

The bot will:
1. Load credentials from `.env` file
2. Connect to MT5 terminal
3. Load all Phase 2 indicators (RSI, MACD, Bollinger, Stochastic, ADX)
4. Start the autonomous trading loop
5. Monitor positions and execute exits automatically

### Monitor Logs

```powershell
# View logs in real-time
Get-Content .\logs\herald.log -Wait -Tail 50
```

## 🎯 Pre-Launch Checklist

- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip list` shows MetaTrader5, pandas, python-dotenv)
- [ ] `.env` file created with your MT5 credentials
- [ ] MT5 terminal installed with algo trading enabled
- [ ] Demo/Training account credentials configured
- [ ] Symbol XAUUSD is available on your broker

## 📊 Trading System Architecture

**Phase 2 Autonomous Trading:**

1. **Market Data Ingestion** - Get OHLCV from MT5
2. **Indicator Calculation** - RSI, MACD, Bollinger, Stochastic, ADX
3. **Signal Generation** - Strategy evaluates indicator confluence
4. **Risk Approval** - Position sizing and limit checks
5. **Order Execution** - Place market orders
6. **Position Tracking** - Monitor all open positions
7. **Exit Detection** - Trailing stop, time-based, profit target, adverse movement
8. **Position Close** - Execute exits automatically
9. **Health Monitoring** - Connection recovery and reconciliation

## 🔧 Common Issues

### "Authorization failed"
- Ensure algo trading is enabled in MT5: Tools → Options → Expert Advisors
- Verify credentials in `.env` are correct
- Check server name matches your broker exactly

### "Failed to connect to MT5"
- MT5 terminal must be installed
- Try closing MT5 before running Herald (it will start it)
- Check the MT5 path in your system

### "Symbol not found"
- Check if XAUUSD is available on your broker
- Enable the symbol in MT5 MarketWatch first
- Change symbol in config to one your broker supports

### "Trading not allowed"
- Verify your account allows automated trading
- Check MT5 terminal Options → Expert Advisors → Allow automated trading

## 🛑 Stopping Herald

Press `Ctrl+C` to gracefully shut down. The bot will:
1. Stop generating new signals
2. Close all open positions (optional)
3. Disconnect from MT5 terminal
4. Save state and logs

## 📚 Documentation

- **ARCHITECTURE.md** - System design and data flow
- **CHANGELOG.md** - Version history
- **development_log/build_plan.md** - Complete implementation plan (archival)

---

**Remember:** Always test with a demo/training account before going live!
