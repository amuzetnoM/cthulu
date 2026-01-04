# 🐙 Cthulu v5.1.0 APEX - Android Native Edition

![Version](https://img.shields.io/badge/Version-5.1.0_ANDROID-00FF00?style=for-the-badge&labelColor=0D1117&logo=android&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20Termux-3DDC84?style=for-the-badge&logo=android)
![Status](https://img.shields.io/badge/Status-Production%20Ready-00FF00?style=for-the-badge)

## Executive Summary

**Cthulu** is an **autonomous trading system** for MetaTrader 5 (MT5) designed to run natively on **Android devices via Termux**. This branch is fully Android-native with no Windows dependencies.

### Key Features

- 🤖 **Fully Autonomous** - Set and forget trading
- 📱 **Android Native** - Runs in Termux, persists in background
- 🧠 **AI-Enhanced** - Cognition engine for signal enhancement
- 🛡️ **Robust Risk Management** - Adaptive account phases
- 📊 **7 Trading Strategies** - Dynamic selection based on market regime
- 🚪 **14 Exit Strategies** - Priority-based exit coordination
- ⚡ **Real-time Execution** - Full trading capability via bridge

---

## Quick Start (Android/Termux)

### 1. Install Prerequisites

```bash
# Update Termux
pkg update && pkg upgrade -y

# Install required packages
pkg install python git tmux -y

# Install Python dependencies
pip install --upgrade pip
```

### 2. Clone & Setup

```bash
# Clone repository
git clone https://github.com/amuzetnoM/cthulu.git
cd cthulu
git checkout cthulu5-android

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure

```bash
# Copy example config
cp config.example.json config.json

# Edit with your MT5 credentials
nano config.json
```

**Minimal config.json:**
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

### 4. Start Trading

```bash
# Start in background with tmux (RECOMMENDED)
tmux new -s cthulu

# Start bridge server
python connector/mt5_bridge_server.py &

# Start trading (with background service)
python -m cthulu.core.android_service --config config.json

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t cthulu
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Android Device                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐    │
│  │                    Termux                        │    │
│  │  ┌─────────────────────────────────────────┐    │    │
│  │  │         Cthulu Trading System            │    │    │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  │    │    │
│  │  │  │ Core    │  │ Strategy │  │  Risk   │  │    │    │
│  │  │  │ Engine  │──│ Selector │──│ Manager │  │    │    │
│  │  │  └────┬────┘  └─────────┘  └─────────┘  │    │    │
│  │  │       │                                   │    │    │
│  │  │  ┌────┴────────────────────────────┐     │    │    │
│  │  │  │    MT5ConnectorAndroid          │     │    │    │
│  │  │  │    (Full Trading API)           │     │    │    │
│  │  │  └────────────────┬────────────────┘     │    │    │
│  │  │                   │ REST API             │    │    │
│  │  │  ┌────────────────┴────────────────┐     │    │    │
│  │  │  │      Bridge Server (Flask)      │     │    │    │
│  │  │  │      Port 18812                 │     │    │    │
│  │  │  └────────────────┬────────────────┘     │    │    │
│  │  └───────────────────│──────────────────────┘    │    │
│  └──────────────────────│───────────────────────────┘    │
│                         │ IPC                            │
│  ┌──────────────────────┴───────────────────────────┐    │
│  │              MT5 Android App                      │    │
│  │         (MetaQuotes Official App)                 │    │
│  └───────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Background Operation

### Why Background Matters

On Android, when you switch apps or turn off the screen, processes can be killed. Cthulu includes robust background support:

1. **Wake Locks** - Prevents Android from killing the process
2. **Signal Handling** - Handles SIGHUP gracefully (doesn't quit on terminal close)
3. **Watchdog** - Auto-restarts if trading loop hangs
4. **Notifications** - Status updates in Android notification bar
5. **tmux/screen** - Session persistence

### Using tmux (Recommended)

```bash
# Create session
tmux new -s cthulu

# Start Cthulu
python -m cthulu.core.android_service

# Detach (keeps running): Ctrl+B, then D

# List sessions
tmux list-sessions

# Reattach
tmux attach -t cthulu

# Kill session (stops Cthulu)
tmux kill-session -t cthulu
```

### Disable Battery Optimization

For best results, disable battery optimization for Termux:

1. **Settings → Apps → Termux → Battery → Unrestricted**
2. Or run: `termux-battery-status` to check

### Termux:API Integration

Install Termux:API for enhanced background support:

```bash
# Install from F-Droid
# Then in Termux:
pkg install termux-api

# Enable wake lock (keeps process alive)
termux-wake-lock

# Check battery
termux-battery-status
```

---

## Trading Capabilities

### Strategies

| Strategy | Type | Best For |
|----------|------|----------|
| EMA Crossover | Trend | Trending markets |
| SMA Crossover | Trend | Stable trends |
| Momentum Breakout | Momentum | Volatile breakouts |
| Scalping | Speed | Ranging, tight spreads |
| Trend Following | Trend | Strong ADX > 25 |
| Mean Reversion | Counter | Ranging markets |
| RSI Reversal | Counter | Oversold/overbought |

### Account Phases

| Phase | Balance | Max Lot | Risk/Trade |
|-------|---------|---------|------------|
| MICRO | $0-25 | 0.01 | 10% |
| SEED | $25-100 | 0.02 | 5% |
| GROWTH | $100-500 | 0.05 | 3% |
| ESTABLISHED | $500-2000 | 0.10 | 2% |
| MATURE | $2000+ | 0.50 | 1% |
| RECOVERY | Any (20%+ DD) | 0.01 | 2% |

### Exit Strategies (Priority Order)

1. **Survival Mode** (100) - Critical balance protection
2. **Micro Protection** (95) - Quick profits for small accounts
3. **Trailing Stop** (80) - Lock profits
4. **Profit Target** (70) - Fixed TP levels
5. **Confluence Exit** (65) - Multi-indicator agreement
6. **Time-Based** (60) - Max position age
7. **Adverse Movement** (50) - Rapid adverse detection

---

## Configuration

### Full Config Options

```json
{
  "mt5": {
    "bridge_type": "rest",
    "bridge_host": "127.0.0.1",
    "bridge_port": 18812,
    "login": 12345678,
    "password": "your_password",
    "server": "BrokerServer",
    "timeout": 60000
  },
  "symbol": "EURUSD",
  "timeframe": "H1",
  "mindset": "balanced",
  "magic_number": 123456,
  
  "risk": {
    "max_position_size": 0.05,
    "max_daily_loss_pct": 5.0,
    "max_drawdown_pct": 20.0
  },
  
  "android": {
    "enable_wake_lock": true,
    "enable_notifications": true,
    "watchdog_timeout_seconds": 120,
    "log_to_file": true
  }
}
```

### Mindsets

- `conservative` - Lower risk, longer timeframes
- `balanced` - Default, moderate approach
- `aggressive` - Higher risk, more trades
- `ultra_aggressive` - Maximum risk tolerance

---

## Monitoring

### Log Files

```bash
# View live logs
tail -f logs/cthulu_service.log

# View all logs
ls -la logs/
```

### Metrics CSV

```bash
# Trading metrics
cat metrics/comprehensive_metrics.csv

# System health
cat metrics/system_health.csv
```

### Status Commands

```bash
# Check if running
pgrep -f "cthulu"

# Check bridge server
curl http://127.0.0.1:18812/health

# Battery status
termux-battery-status
```

---

## Troubleshooting

### Bridge Connection Failed

```bash
# Check if bridge is running
curl http://127.0.0.1:18812/health

# Start bridge manually
python connector/mt5_bridge_server.py --host 127.0.0.1 --port 18812
```

### Process Killed in Background

1. Enable wake lock: `termux-wake-lock`
2. Disable battery optimization for Termux
3. Use the Android service: `python -m cthulu.core.android_service`

### MT5 App Not Responding

1. Ensure MT5 app is running and logged in
2. Check MT5 is connected to broker
3. Restart MT5 app and bridge server

### Out of Memory

1. Close other apps
2. Increase swap: `pkg install termux-am && termux-setup-storage`
3. Use a device with more RAM (4GB+ recommended)

---

## File Structure

```
cthulu/
├── core/
│   ├── android_service.py    # Background service manager
│   ├── bootstrap.py          # System initialization
│   └── trading_loop.py       # Main trading loop
│
├── connector/
│   ├── mt5_connector_android.py  # Full Android connector
│   ├── mt5_bridge_server.py      # Flask bridge server
│   └── __init__.py               # Exports and constants
│
├── strategy/                 # 7 trading strategies
├── indicators/               # 12 technical indicators
├── risk/                     # Risk management modules
├── position/                 # Position management
├── exit/                     # 14 exit strategies
├── cognition/                # AI/ML enhancement
├── observability/            # Metrics and monitoring
│
├── config.json               # Your configuration
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## Requirements

### Hardware

- Android 7.0+ device
- 4GB+ RAM recommended
- Storage for logs (~100MB)

### Software

- Termux (from F-Droid, NOT Play Store)
- Termux:API (optional, for wake locks)
- MT5 Android app (official from Play Store)
- Python 3.10+

### Python Packages

```
flask>=2.3.0
requests>=2.31.0
pandas>=2.0.0
numpy>=1.24.0
python-dotenv>=1.0.0
```

---

## Security

- All trading happens locally on your device
- Bridge server binds to localhost only (127.0.0.1)
- No data sent to external servers
- Credentials stored in config.json (keep secure)

---

## Support

- **Docs:** See `docs/ANDROID_SETUP.md` for detailed setup
- **Issues:** Report on GitHub
- **Logs:** Check `logs/cthulu_service.log`

---

## License

MIT License - See LICENSE file

---

**🐙 Happy Trading on Android!**
