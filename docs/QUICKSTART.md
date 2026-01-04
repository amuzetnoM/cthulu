---
title: QUICK START - Android
description: Get started with Cthulu on Android/Termux - installation, configuration, and first trades
tags: [quickstart, installation, setup, android, termux]
sidebar_position: 3
---

![](https://img.shields.io/badge/Version-1.0.0_Beta-00FF00?style=for-the-badge&labelColor=0D1117&logo=android&logoColor=white) 

## Prerequisites

- **Android 7.0+** device (4GB+ RAM recommended)
- **Termux** from F-Droid (NOT Play Store - outdated)
- **MT5 Android App** from Play Store
- **Termux:API** (optional, for wake locks)

---

### 1. Initial Setup (Termux)

```bash
# Update Termux
pkg update && pkg upgrade -y

# Install required packages
pkg install python git tmux -y

# Clone repository
git clone https://github.com/amuzetnoM/cthulu.git
cd cthulu
git checkout cthulu5-android

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Credentials

Create your config file:
```bash
cp config.example.json config.json
nano config.json
```

Edit `config.json`:
```json
{
  "mt5": {
    "bridge_type": "rest",
    "bridge_host": "127.0.0.1",
    "bridge_port": 18812,
    "login": 12345678,
    "password": "your_password",
    "server": "YourBroker-Server"
  },
  "symbol": "EURUSD",
  "timeframe": "H1",
  "mindset": "balanced"
}
```

### 3. Start Trading

#### Option A: Background Service (Recommended)

```bash
# Start in tmux for persistence
tmux new -s cthulu

# Start bridge server
python connector/mt5_bridge_server.py &

# Start with background service
python -m cthulu.core.android_service --config config.json

# Detach: Ctrl+B, then D
```

#### Option B: Direct Run

```bash
# Start bridge
python connector/mt5_bridge_server.py &

# Run trading loop
python -m cthulu --config config.json
```

### 4. Keep Running in Background

```bash
# Acquire wake lock (prevents Android killing process)
termux-wake-lock

# Disable battery optimization for Termux
# Settings → Apps → Termux → Battery → Unrestricted
```

### 5. Monitor

```bash
# View logs
tail -f logs/cthulu_service.log

# Check health
curl http://127.0.0.1:18812/health

# Reattach to session
tmux attach -t cthulu
- Strategy selection (single or dynamic)
- Technical indicators

#### NLP Wizard (Advanced - describe in natural language)
```bash
python -m Cthulu --wizard-ai
```
Example input:
```
Aggressive GOLD#m on M15 and H1, 2% risk, $100 max loss
```

### 4. Start Trading

```bash
# Dry run (recommended first)
python -m Cthulu --config config.json --dry-run

# Live trading (requires confirmation)
export LIVE_RUN_CONFIRM=1
python -m Cthulu --config config.json
```



### Features
- Auto-refresh every 2 seconds
- Singleton instance (no duplicates)
- Graceful shutdown
- Log file monitoring

---

## 📊 Strategy Modes

### Single Strategy Mode
Choose one strategy:
- **SMA Crossover**: Simple moving average crossover (beginner-friendly)
- **EMA Crossover**: Exponential moving average (responsive)
- **Momentum Breakout**: Price momentum detection (aggressive)
- **Scalping**: Quick trades with tight stops (advanced)

### Dynamic Strategy Selection (New!)
System automatically switches between strategies based on:
- Market regime detection
- Strategy performance tracking
- Real-time conditions
- Confidence scores

Example config:
```json
{
  "strategy": {
    "type": "dynamic",
    "dynamic_selection": {
      "regime_detection_enabled": true,
      "performance_tracking_enabled": true,
      "min_confidence_threshold": 0.6
    },
    "strategies": [
      {"type": "sma_crossover", "params": {"fast_period": 10, "slow_period": 30}},
      {"type": "ema_crossover", "params": {"fast_period": 12, "slow_period": 26}},
      {"type": "momentum_breakout", "params": {"lookback_period": 20}},
      {"type": "scalping", "params": {"quick_period": 5, "trend_period": 20}}
    ]
  }
}
```

---

## 📈 Technical Indicators

Add indicators to enhance your strategy:

### Available Indicators
1. **RSI** (Relative Strength Index)
   - Momentum oscillator
   - Default: period=14, overbought=70, oversold=30

2. **MACD** (Moving Average Convergence Divergence)
   - Trend following
   - Default: fast=12, slow=26, signal=9

3. **Bollinger Bands**
   - Volatility indicator
   - Default: period=20, std_dev=2.0

4. **Stochastic**
   - Momentum indicator
   - Default: k=14, d=3, smooth=3

5. **ADX** (Average Directional Index)
   - Trend strength
   - Default: period=14

6. **Supertrend** ⭐ NEW in v4.0.0
   - Trend following
   - Default: atr_period=10, multiplier=3.0

7. **VWAP** ⭐ NEW in v4.0.0
   - Volume weighted average price
   - Intraday trading

Example config:
```json
{
  "indicators": [
    {"type": "supertrend", "params": {"atr_period": 10, "atr_multiplier": 3.0}},
    {"type": "rsi", "params": {"period": 14}},
    {"type": "vwap", "params": {}}
  ]
}
```

---

## 🎯 Mindset Presets

Pre-configured risk profiles:

### Aggressive
- Position size: 5% per trade
- Max positions: 5
- Daily loss limit: $100
- Faster signals, tighter stops

### Balanced (Recommended)
- Position size: 2% per trade
- Max positions: 3
- Daily loss limit: $50
- Moderate risk/reward

### Conservative
- Position size: 1% per trade
- Max positions: 2
- Daily loss limit: $25
- Wider stops, stricter filters

Apply via CLI:
```bash
python -m Cthulu --config config.json --mindset aggressive
```

Or during wizard setup.

---

## 🔧 Command Line Options

```bash
# Basic
python -m Cthulu --config config.json                    # Start with config

# Wizard
python -m Cthulu --wizard                                 # Interactive setup
python -m Cthulu --wizard-ai                             # NLP-based setup
python -m Cthulu --config config.json --skip-setup       # Skip wizard

# Trading Modes
python -m Cthulu --config config.json --dry-run          # Simulate trades
python -m Cthulu --config config.json --adopt-only       # Only manage existing trades

# Customization
python -m Cthulu --config config.json --mindset aggressive
python -m Cthulu --config config.json --symbol GOLD#m
python -m Cthulu --config config.json --enable-ml        # Enable ML features

# RPC Server
python -m Cthulu --config config.json --enable-rpc       # Enable RPC for GUI
```

---

## 🛠️ Troubleshooting

### MT5 Not Connecting
1. Check `.env` file has correct credentials
2. Verify MT5 terminal is installed and running
3. Check config uses FROM_ENV:
   ```json
   "mt5": {
     "password": "FROM_ENV",
     "server": "FROM_ENV"
   }
   ```

### GUI Issues
- **Dark mode broken**: Update to latest version (fixed)
- **Multiple GUIs**: Update to latest version (singleton pattern added)
- **Can't launch**: Check `logs/gui_stderr.log` for errors

### Configuration Issues
- Run wizard: `python -m Cthulu --wizard`
- Check example: `config.example.json`
- See documentation: `UPGRADE_FIXES.md`

---

## 📚 Additional Resources

- **Full Documentation**: `UPGRADE_GUIDE.md`
- **Fix Details**: `UPGRADE_FIXES.md`
- **Release Notes**: `release_notes/v4.0.0.md`
- **Implementation**: `IMPLEMENTATION_SUMMARY.md`

---


## 💡 Tips

1. **Start with dry-run**: Test your config without risking capital
2. **Use balanced mindset**: Good for most traders
3. **Monitor GUI**: Keep eye on active strategy and regime
4. **Review logs**: Check `Cthulu.log` for detailed activity
5. **Adjust gradually**: Small changes, measure impact

---

## 🆘 Support

- Issues: https://github.com/amuzetnoM/Cthulu/issues
- Discussions: https://github.com/amuzetnoM/Cthulu/discussions

Happy Trading! 🚀📈





