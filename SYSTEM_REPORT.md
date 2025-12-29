# Cthulu System Report

**Last Updated:** 2025-12-29 13:22:48Z

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Status | ✅ RUNNING (Live Mode) |
| Account | ****0069 (Demo) |
| Balance | $1029.58 |
| Symbol | BTCUSD# |
| Mindset | ultra_aggressive |
| Trade Allowed | True |
| MT5 Connection | Connected (XMGlobal-MT5 6) |
| Prometheus | http://127.0.0.1:8181/metrics |

---

## Current Session

- **Started:** 2025-12-29 13:22:48Z
- **Target Duration:** 120 minutes (goal: 0 errors)
- **Mode:** Live trading on demo account
- **PID:** 12900

---

## Monitoring Checklist

| Component | Status |
|-----------|--------|
| Trading loop | ✅ Running (30s intervals) |
| Market data | ✅ Fetching from MT5 |
| Indicators | ✅ 6 runtime indicators active |
| Strategy evaluation | ✅ EMA crossover selected |
| Risk management | ✅ Operational |
| MT5 connection | ✅ Stable |
| Prometheus metrics | ✅ Exporting on :8181 |

---

## Signal Generation Status

The system is operational but awaiting favorable market conditions for signal generation.
- Market regime: 	rending_up_weak (ADX=42.2, RSI=62.1)
- Selected strategy: ma_crossover (score=0.660)
- Current status: Monitoring for crossover conditions

---

## Notes

- This report is the source of truth for system state
- Detailed metrics are recorded in monitoring\metrics.csv
- Injection logs are recorded in logs\inject.log

---

## Session Log

| Timestamp | Event | Details |
|-----------|-------|---------|
| 2025-12-29 13:22:48Z | System started | PID 12900, Live mode, MT5 connected |


---
## Stress Test Session - 2025-12-29 13:30:04

### Configuration
- **Mindset:** ultra_aggressive
- **Symbol:** BTCUSD#
- **RPC:** Enabled on port 8278
- **Spread Limit:** 5000 points / 5%
- **Cthulu PID:** 12652

### Milestone: RPC Trade Execution Working
- First successful RPC trade at 13:30:04
- Order #600994186 filled at 89796.40
- SL: 88898.43, TP: 91592.33

### Running 120-minute Stress Test
