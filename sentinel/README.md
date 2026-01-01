# 🛡️ SENTINEL

**Version:** 1.0.0 | **Codename:** Guardian

Sentinel is an **independent watchdog system** that monitors Cthulu and MetaTrader 5, providing automatic crash recovery and system health monitoring.

> ⚠️ **IMPORTANT:** Sentinel is NOT part of Cthulu. It is a completely separate system that survives Cthulu crashes and orchestrates recovery.

---

## 🎯 Purpose

Sentinel solves the "Turing Problem" for algorithmic trading:
- **Crashes** - Auto-recovery from Cthulu crashes
- **Disconnections** - MT5 reconnection monitoring
- **Algo Off** - Detection of disabled algo trading
- **System Health** - Real-time monitoring & metrics

---

## 🚀 Quick Start

### Launch Sentinel Dashboard
```bash
# Set PYTHONPATH to include workspace directory
$env:PYTHONPATH = "C:\workspace"
cd C:\workspace
python -m sentinel.gui
```

Or create a batch file `start_sentinel.bat`:
```batch
@echo off
set PYTHONPATH=C:\workspace
cd C:\workspace
python -m sentinel.gui
```

### CLI Mode (headless)
```bash
$env:PYTHONPATH = "C:\workspace"
cd C:\workspace
python -m sentinel --headless
```

---

## 🎮 Controls

| Button | Action |
|--------|--------|
| **🔄 Force Recovery** | Stops any zombie Cthulu process and restarts with last known config |
| **🛑 Emergency Stop** | Immediately terminates Cthulu (positions remain open) |
| **🤖 Enable Algo Trading** | Attempts to re-enable algo trading in MT5 |
| **☑️ Auto-Restart** | Toggle automatic crash recovery (default: ON) |

---

## 📊 Monitored States

### System States
| State | Description |
|-------|-------------|
| `HEALTHY` | Cthulu running + MT5 algo enabled |
| `DEGRADED` | Partial functionality |
| `CRITICAL` | Crash detected |
| `RECOVERING` | Recovery in progress |
| `OFFLINE` | All systems stopped |

### Cthulu States
| State | Description |
|-------|-------------|
| `RUNNING` | Active and healthy |
| `STOPPED` | Not running |
| `CRASHED` | Process died unexpectedly |
| `UNRESPONSIVE` | Process frozen |

### MT5 States
| State | Description |
|-------|-------------|
| `ALGO_ENABLED` | Trading active |
| `ALGO_DISABLED` | Trading paused |
| `DISCONNECTED` | Connection lost |
| `NOT_RUNNING` | MT5 not started |

---

## ⚙️ Configuration

Sentinel auto-detects the last used Cthulu config. Priority order:
1. `config.json`
2. `config_battle_test.json`
3. `config_backup.json`

### CLI Options
```bash
python -m sentinel --help

Options:
  --interval FLOAT    Poll interval in seconds (default: 5.0)
  --no-auto-restart   Disable automatic crash recovery
  --no-auto-algo      Disable automatic algo re-enable
  --config STRING     Specify Cthulu config file
  --gui               Start GUI dashboard (default)
  --headless          Run CLI only, no GUI
```

---

## 🔒 Safety Features

1. **Emergency Stop Threshold**
   - 5 crashes in 10 minutes = automatic shutdown
   - Prevents runaway recovery loops

2. **Recovery Cooldown**
   - 30 second wait before restart
   - Prevents rapid-fire restarts

3. **Max Recovery Attempts**
   - 5 attempts maximum
   - Manual intervention required after

---

## 📁 Directory Structure

```
C:\workspace\sentinel\
├── __init__.py          # Package init
├── __main__.py          # CLI entry point
├── core/
│   ├── __init__.py
│   └── guardian.py      # Core watchdog logic
├── gui/
│   ├── __init__.py
│   ├── __main__.py      # GUI entry point
│   └── dashboard.py     # Tkinter dashboard
├── logs/
│   └── sentinel_*.log   # Daily log files
└── README.md
```

---

## 🔄 Recovery Flow

```
Crash Detected
      │
      ▼
Check Crash Frequency
      │
      ├─── Too Many? ──► EMERGENCY STOP
      │
      ▼
30s Cooldown
      │
      ▼
Ensure MT5 Running
      │
      ▼
Enable Algo Trading
      │
      ▼
Start Cthulu (last config)
      │
      ▼
Verify Running
      │
      ├─── Success ──► Resume Monitoring
      │
      └─── Fail ──► Increment Attempts
```

---

## 🐙 Relationship with Cthulu

```
┌─────────────────────────────────────────┐
│              SENTINEL                    │
│         (Independent Process)            │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │         MONITORS                 │   │
│  │                                 │   │
│  │  ┌─────────┐    ┌─────────┐   │   │
│  │  │ CTHULU  │    │   MT5   │   │   │
│  │  └─────────┘    └─────────┘   │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      RECOVERY ACTIONS           │   │
│  │  • Restart Cthulu               │   │
│  │  • Start MT5                    │   │
│  │  • Enable Algo                  │   │
│  │  • Emergency Stop               │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## 📝 Logs

Logs are stored in `C:\workspace\sentinel\logs\`:
- Daily rotation: `sentinel_YYYYMMDD.log`
- Contains all state changes, recoveries, and errors

---

## 🛠️ Development

Sentinel is designed to be:
- **Independent** - Survives Cthulu crashes
- **Lightweight** - Minimal resource usage
- **Reliable** - Robust error handling
- **Simple** - Clear recovery logic

---

*Sentinel v1.0.0 Guardian - Watching over Cthulu so you don't have to.*
