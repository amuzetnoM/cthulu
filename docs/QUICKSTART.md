# Herald Quick Start Guide

## 📦 Installation

### 1. Set Up Python Environment

```powershell
# Navigate to Herald directory
cd C:\workspace\Herald

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure MT5 Credentials

```powershell
# Copy example config
cp config.example.yaml config.yaml

# Edit config.yaml with your editor
code config.yaml
```

**Required settings in config.yaml:**
- `mt5.login`: Your MT5 account number
- `mt5.password`: Your account password
- `mt5.server`: Your broker's server name (e.g., "MetaQuotes-Demo")
- `trading.symbol`: Symbol to trade (default: XAUUSD)
- `trading.risk_per_trade`: Risk percentage (0.01 = 1%)

### 3. Verify MT5 Installation

Make sure MetaTrader 5 terminal is installed and can be launched.

```powershell
# Check MT5 installation
python -c "import MetaTrader5 as mt5; print('MT5 version:', mt5.version())"
```

## 🚀 Running Herald

### Demo Mode (Recommended First)

**IMPORTANT:** Always start with a demo account!

```powershell
# Make sure MT5 terminal is closed before running
python main.py
```

The bot will:
1. Connect to MT5 terminal
2. Load the MA Crossover strategy
3. Start monitoring the market
4. Execute trades based on signals

### Monitor Logs

```powershell
# View logs in real-time
Get-Content .\logs\herald.log -Wait -Tail 50
```

## 🎯 First Run Checklist

- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip list` shows MetaTrader5, pandas, PyYAML)
- [ ] `config.yaml` created with your MT5 credentials
- [ ] MT5 terminal installed (but not running - Herald will start it)
- [ ] Demo account credentials configured
- [ ] Symbol XAUUSD is available on your broker
- [ ] Risk settings reviewed (default: 1% per trade)

## 📊 Understanding the Strategy

**Simple Moving Average Crossover** (Phase 1):

- **Entry Signal:**
  - BUY: When 20-period MA crosses above 50-period MA
  - SELL: When 20-period MA crosses below 50-period MA

- **Risk Management:**
  - Stop Loss: 2 × ATR (Average True Range)
  - Take Profit: 1:2 Risk/Reward ratio
  - Position size: Calculated based on risk per trade

- **Filters:**
  - Maximum spread: 50 points
  - Trading hours: 7:00 - 20:00 UTC (configurable)
  - Maximum 3 concurrent positions

## 🔧 Common Issues

### "Failed to connect to MT5"
- Ensure MT5 terminal is installed
- Check login credentials in config.yaml
- Verify server name is correct
- Try with portable=true in config if using portable MT5

### "Symbol not found"
- Check if XAUUSD is available on your broker
- Try enabling the symbol in MT5 MarketWatch
- Change symbol in config.yaml to one your broker supports

### "Trading not allowed"
- Verify your demo account allows automated trading
- Check MT5 terminal Options → Expert Advisors → Allow automated trading
- Ensure account is not expired

### "Import MetaTrader5 could not be resolved"
- Make sure you activated the virtual environment
- Reinstall: `pip install --upgrade MetaTrader5`

## 📈 Monitoring Performance

Herald logs all trading activity:

```powershell
# View recent trades
Select-String -Path .\logs\herald.log -Pattern "TRADE OPENED|TRADE CLOSED" | Select-Object -Last 10

# Check signals generated
Select-String -Path .\logs\herald.log -Pattern "SIGNAL:" | Select-Object -Last 5

# Monitor daily P&L
Select-String -Path .\logs\herald.log -Pattern "Daily P&L"
```

## 🛑 Stopping Herald

Press `Ctrl+C` to gracefully shut down the bot. It will:
1. Stop generating new signals
2. Disconnect from MT5 terminal
3. Save logs

**Note:** Existing open positions will remain open. Close them manually in MT5 or run:

```python
python -c "from main import Herald; bot = Herald(); bot.initialize(); bot.trade_manager.close_all_positions()"
```

## ⚙️ Customizing the Strategy

Edit `config.yaml` to modify strategy parameters:

```yaml
strategy:
  name: "simple_ma_cross"
  params:
    fast_period: 20    # Fast MA period
    slow_period: 50    # Slow MA period
    confirmation_candles: 1  # Wait N candles after signal
  filters:
    min_atr_multiple: 1.5
    max_spread: 50
    trading_hours:
      start: 7   # UTC
      end: 20    # UTC
```

## 📚 Next Steps

After successful Phase 1 deployment:

1. **Monitor Performance**: Track strategy for at least 1 week on demo
2. **Analyze Results**: Review win rate, profit factor, drawdown
3. **Phase 2**: Add more indicators (RSI, MACD, Bollinger Bands)
4. **Phase 3**: Integrate machine learning models
5. **Phase 4**: Connect to gold_standard analysis signals

## 🆘 Getting Help

Check the logs first:
```powershell
Get-Content .\logs\herald.log -Tail 100
```

Common log patterns:
- `[INFO]` - Normal operation
- `[WARNING]` - Potential issues (spread too wide, risk limits)
- `[ERROR]` - Problems requiring attention

---

**Remember:** Always test with a demo account before going live!
