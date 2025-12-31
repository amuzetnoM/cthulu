# 🛡️ SENTINEL - Cthulu Guardian System

**Version:** 1.0.0 "Guardian"  
**Status:** Production Ready

---

## Overview

SENTINEL is an independent watchdog system that monitors and protects Cthulu. It runs as a **completely separate process**, ensuring it survives any Cthulu crashes and can orchestrate automatic recovery.

### Key Features

- 🔄 **Auto-Crash Recovery** - Detects Cthulu crashes and restarts automatically
- 📡 **MT5 Connection Monitoring** - Ensures MetaTrader stays connected
- 🤖 **Algo Trading Watchdog** - Re-enables algo trading if disabled
- 📊 **WebUI Dashboard** - Real-time system health visualization
- 🚨 **Emergency Protocols** - Stops everything if repeated crashes detected
- 📝 **Comprehensive Logging** - All events logged for analysis

---

## Quick Start

### Basic Usage

```powershell
# Start Sentinel with default settings
python -m sentinel.core.guardian

# Start with WebUI
python -m sentinel.core.guardian --webui --webui-port 8282

# Custom poll interval (check every 10 seconds)
python -m sentinel.core.guardian --interval 10

# Disable auto-restart (monitoring only)
python -m sentinel.core.guardian --no-auto-restart
```

### As a Background Service

```powershell
# Run detached (survives terminal close)
Start-Process python -ArgumentList "-m sentinel.core.guardian --webui" -WindowStyle Hidden

# Or use Task Scheduler for Windows startup
```

---

## Configuration

### RecoveryConfig Options

| Option | Default | Description |
|--------|---------|-------------|
| `max_crash_recovery_attempts` | 5 | Max recovery attempts before stopping |
| `recovery_cooldown_seconds` | 30 | Wait time before recovery attempt |
| `heartbeat_timeout_seconds` | 120 | Max time without Cthulu heartbeat |
| `auto_restart_cthulu` | True | Automatically restart on crash |
| `auto_enable_algo` | True | Re-enable algo if disabled |
| `crash_threshold_for_emergency` | 5 | Crashes in window triggers emergency |
| `crash_window_minutes` | 10 | Time window for crash counting |

### Custom Configuration

```python
from sentinel.core import SentinelGuardian, RecoveryConfig

config = RecoveryConfig(
    max_crash_recovery_attempts=3,
    recovery_cooldown_seconds=60,
    auto_restart_cthulu=True,
    auto_enable_algo=True,
    cthulu_config="config_battle_test.json"
)

guardian = SentinelGuardian(config)
guardian.run(poll_interval=5.0)
```

---

## WebUI

Access the dashboard at `http://localhost:8282` when running with `--webui`.

### Dashboard Features

- **System State** - Overall health indicator (HEALTHY, DEGRADED, CRITICAL, OFFLINE)
- **Cthulu Status** - Running state and PID
- **MT5 Status** - Connection state and algo trading status
- **Crash Count** - Number of crashes and last crash time
- **Resource Usage** - CPU and memory metrics
- **Error Log** - Recent errors and warnings
- **Quick Actions** - Restart Cthulu, Stop, Start MT5, Enable Algo

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Full status JSON |
| `/api/health` | GET | Simple health check |
| `/api/restart-cthulu` | POST | Restart Cthulu |
| `/api/stop-cthulu` | POST | Stop Cthulu |
| `/api/start-mt5` | POST | Start MetaTrader 5 |
| `/api/enable-algo` | POST | Enable algo trading |

---

## System States

### SystemState

| State | Description |
|-------|-------------|
| `HEALTHY` | Cthulu running, MT5 connected, algo enabled |
| `DEGRADED` | Running but with issues (algo disabled, etc.) |
| `CRITICAL` | Crash detected, recovery needed |
| `RECOVERING` | Recovery in progress |
| `OFFLINE` | Both Cthulu and MT5 not running |

### CthhuluState

| State | Description |
|-------|-------------|
| `RUNNING` | Process active and responsive |
| `STARTING` | Process starting up |
| `STOPPED` | Cleanly stopped |
| `CRASHED` | Unexpected termination |
| `UNRESPONSIVE` | Process exists but not responding |

---

## Recovery Protocol

When SENTINEL detects a crash:

1. **Detection** - Process missing or unresponsive
2. **Cooldown** - Wait configured seconds before recovery
3. **Emergency Check** - If too many crashes, trigger emergency stop
4. **MT5 Check** - Ensure MetaTrader is running
5. **Algo Check** - Enable algo trading if disabled
6. **Restart Cthulu** - Launch with configured settings
7. **Verification** - Confirm Cthulu is running

### Emergency Stop

If crashes exceed threshold within the time window:
- All recovery attempts stop
- Alert logged
- Manual intervention required

---

## Callbacks

Register custom callbacks for events:

```python
def on_crash(metrics):
    send_telegram_alert(f"Cthulu crashed! Recovery attempt {metrics.recovery_attempts}")

def on_recovery(metrics):
    send_telegram_alert("Cthulu recovered successfully!")

guardian = SentinelGuardian()
guardian.register_callback("on_crash", on_crash)
guardian.register_callback("on_recovery", on_recovery)
guardian.run()
```

### Available Events

- `on_crash` - Called when crash detected
- `on_recovery` - Called after successful recovery
- `on_state_change` - Called when system state changes
- `on_emergency` - Called when emergency stop triggered

---

## Logs

Logs are stored in `sentinel/logs/`:

```
sentinel/logs/
├── sentinel_20250101.log  # Daily log file
├── sentinel_20250102.log
└── ...
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SENTINEL                                  │
│                    (Independent Process)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│   │   GUARDIAN   │────▶│   METRICS    │────▶│    WEBUI     │   │
│   │   (Monitor)  │     │  (Collector) │     │   (Server)   │   │
│   └──────┬───────┘     └──────────────┘     └──────────────┘   │
│          │                                                       │
│          ▼                                                       │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                 RECOVERY ENGINE                           │  │
│   │   • Crash Detection    • MT5 Monitor                     │  │
│   │   • Auto Restart       • Algo Enable                     │  │
│   │   • Emergency Stop     • Callback System                 │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│                       WATCHES                                    │
│          ┌─────────────────┼─────────────────┐                  │
│          ▼                 ▼                 ▼                  │
│   ┌────────────┐   ┌────────────┐   ┌────────────┐             │
│   │  CTHULU    │   │    MT5     │   │  SYSTEM    │             │
│   │ (Process)  │   │ (Terminal) │   │ (Resources)│             │
│   └────────────┘   └────────────┘   └────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integration with Existing Sentinel

If you already have a Sentinel system running elsewhere (e.g., systemd VM), you can:

1. **Merge** - Combine both into a unified system
2. **Cascade** - Have your existing Sentinel watch this one
3. **Parallel** - Run both for redundancy

For unprecedented control, the combined system can:
- Watch the watcher (your VM Sentinel watches this Sentinel)
- CLI algo enable (using MT5 Python API or AutoHotkey)
- Syndicate management across multiple accounts

---

## Requirements

- Python 3.10+
- psutil
- MetaTrader5 (optional, for full MT5 control)

```powershell
pip install psutil MetaTrader5
```

---

## License

Part of the Cthulu Trading System - MIT License
