# Signal Stress Test Checklist

**Version:** 1.2
**Last Updated:** 2025-12-29

---

## 🎯 DIRECTIVE (Quick-Read)

**PURPOSE:** Authoritative runbook for automated signal stress-testing, monitoring, observability and corrective actions. This document enables any AI agent or human to understand the full testing methodology and current state.

**CURRENT STATE:**
- **Account:** Demo ****0069 ($1000 balance)
- **Symbol:** BTCUSD#
- **Mindset:** ultra_aggressive
- **Prometheus:** http://127.0.0.1:8181/metrics
- **RPC Server:** http://127.0.0.1:8278/trade
- **Goal:** 120 minutes error-free runtime with continuous injection

**WHAT WE'RE DOING:**
1. Running Cthulu in live trading mode on a demo account
2. Injecting signals via RPC to stress test the full pipeline
3. Validating all 11 indicators calculate correctly
4. Ensuring risk management approves/rejects appropriately
5. Verifying orders execute on MT5
6. Fine-tuning parameters based on results
7. Upgrading system to be cutting-edge

**HOW TO CONTINUE:**
1. Read this checklist to understand test scope
2. Read [observability_guide.md](observability_guide.md) for execution steps
3. Run `.\monitoring\run_stress.ps1 -DurationMinutes 120`
4. Monitor via `.\monitoring\dual_monitor.ps1`
5. Update [SYSTEM_REPORT.md](../SYSTEM_REPORT.md) with findings

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [SYSTEM_REPORT.md](../SYSTEM_REPORT.md) | **Source of truth** - Final findings and system grade |
| [observability_guide.md](observability_guide.md) | How-to instructions for running tests |
| [monitoring_report.md](monitoring_report.md) | Analysis, insights, recommendations |

---

# Cthulu Signal Checklist — Exhaustive Test Matrix

Purpose: provide a surgical, exhaustive list of signals and edge-cases to exercise the full signal→risk→execution lifecycle, including observability and grading hooks.

Instructions: each checklist item includes: name, trigger method, expected system behavior, Prometheus metrics to observe, log lines to validate, grading criteria, and remediation notes.

---

## 1) Basic Signal Types

### 1.1 Long Market Signal (BUY)
- [ ] **Test ID:** SIG-001
- **Trigger:** RPC POST `{"symbol":"BTCUSD#","side":"BUY","volume":0.01}`
- **Expected Flow:**
  1. Signal received by RPC server
  2. RiskEvaluator.approve() called
  3. Spread check passes (< max_spread_points)
  4. Position size calculated
  5. ExecutionEngine.place_order() called
  6. MT5 receives MARKET BUY order
  7. Order filled, ticket returned
  8. Position tracked in PositionManager
  9. Trade recorded in database
- **Metrics:** `cthulu_trades_total++`, `cthulu_open_positions++`
- **Logs:** "Signal generated: LONG", "Risk approved:", "Placing MARKET order", "Order executed: Ticket #"
- **Grade:** PASS if full flow recorded; WARN if rejected with valid reason

### 1.2 Short Market Signal (SELL)
- [ ] **Test ID:** SIG-002
- **Trigger:** RPC POST `{"symbol":"BTCUSD#","side":"SELL","volume":0.01}`
- **Expected:** Mirror of BUY flow
- **Metrics:** Same as above
- **Grade:** PASS if order filled

### 1.3 Limit Order
- [ ] **Test ID:** SIG-003
- **Trigger:** RPC POST with `price` field set
- **Expected:** LIMIT order submitted, pending until price reached
- **Metrics:** Order submitted but not immediately filled

### 1.4 Stop Order
- [ ] **Test ID:** SIG-004
- **Trigger:** Signal with STOP order type
- **Expected:** Stop order placed, triggers on price breach

---

## 2) Indicator Validation Tests

### 2.1 RSI (Relative Strength Index)
- [ ] **Test ID:** IND-001 - Overbought (RSI > 70)
- [ ] **Test ID:** IND-002 - Oversold (RSI < 30)
- [ ] **Test ID:** IND-003 - Neutral (RSI = 50)
- **Validation:** RSI values in range [0, 100]

### 2.2 MACD
- [ ] **Test ID:** IND-004 - Bullish crossover (histogram positive)
- [ ] **Test ID:** IND-005 - Bearish crossover (histogram negative)
- **Validation:** Signal line, histogram calculated correctly

### 2.3 Bollinger Bands
- [ ] **Test ID:** IND-006 - Price at upper band
- [ ] **Test ID:** IND-007 - Price at lower band
- **Validation:** Bands widen/narrow with volatility

### 2.4 ADX (Average Directional Index)
- [ ] **Test ID:** IND-008 - Strong trend (ADX > 25)
- [ ] **Test ID:** IND-009 - Ranging market (ADX < 20)
- **Validation:** DI+/DI- crossover detection

### 2.5 Supertrend
- [ ] **Test ID:** IND-010 - Uptrend (+1)
- [ ] **Test ID:** IND-011 - Downtrend (-1)
- **Validation:** Direction flips on price crossover

### 2.6 ATR (Average True Range)
- [ ] **Test ID:** IND-012 - High volatility
- [ ] **Test ID:** IND-013 - Low volatility
- **Validation:** ATR > 0, scales with price movement

### 2.7 Stochastic
- [ ] **Test ID:** IND-014 - Overbought (%K > 80)
- [ ] **Test ID:** IND-015 - Oversold (%K < 20)
- **Validation:** %K/%D crossover

### 2.8 VWAP
- [ ] **Test ID:** IND-016 - Price above VWAP
- [ ] **Test ID:** IND-017 - Price below VWAP
- **Validation:** VWAP anchored to session

### 2.9 Volume Indicators
- [ ] **Test ID:** IND-018 - Volume spike detection
- [ ] **Test ID:** IND-019 - Below average volume
- **Validation:** Volume ratio calculated

---

## 3) Risk Manager Tests

### 3.1 Spread Checks
- [ ] **Test ID:** RISK-001 - Spread too high (absolute)
  - **Trigger:** Trade during high-spread period
  - **Expected:** "Risk rejected: Spread X exceeds limit Y"
  - **Grade:** PASS if correctly rejected

- [ ] **Test ID:** RISK-002 - Spread relative threshold
  - **Trigger:** Large price instrument (crypto)
  - **Expected:** Uses max_spread_pct (5%) check

### 3.2 Position Sizing
- [ ] **Test ID:** RISK-003 - Percent risk sizing
  - **Trigger:** Trade with 2% risk_per_trade
  - **Expected:** Volume scaled to account balance

- [ ] **Test ID:** RISK-004 - Kelly criterion sizing
  - **Trigger:** Enable Kelly sizing in config
  - **Expected:** Optimal fraction calculated

### 3.3 Circuit Breakers
- [ ] **Test ID:** RISK-005 - Daily loss limit
  - **Trigger:** Simulate losses to hit max_daily_loss
  - **Expected:** Trading halted, "Circuit breaker triggered"

- [ ] **Test ID:** RISK-006 - Consecutive loss limit
  - **Trigger:** Multiple losing trades
  - **Expected:** Trading paused

### 3.4 Position Limits
- [ ] **Test ID:** RISK-007 - Max positions per symbol
  - **Trigger:** Open max_positions_per_symbol trades
  - **Expected:** Additional trades rejected

---

## 4) Execution Edge Cases

### 4.1 Order States
- [ ] **Test ID:** EXEC-001 - Partial fill handling
- [ ] **Test ID:** EXEC-002 - Rejected order (broker-side)
- [ ] **Test ID:** EXEC-003 - Requote handling
- [ ] **Test ID:** EXEC-004 - Timeout handling

### 4.2 Idempotency
- [ ] **Test ID:** EXEC-005 - Duplicate order detection
  - **Trigger:** Send same order twice with same client_tag
  - **Expected:** "Order already submitted as ticket #X"

### 4.3 Position Management
- [ ] **Test ID:** EXEC-006 - Position close
- [ ] **Test ID:** EXEC-007 - Partial close
- [ ] **Test ID:** EXEC-008 - SL/TP modification

---

## 5) Observability Tests

### 5.1 Prometheus Metrics
- [ ] **Test ID:** OBS-001 - Metrics endpoint responds
- [ ] **Test ID:** OBS-002 - Trade counters increment
- [ ] **Test ID:** OBS-003 - PnL updates correctly
- [ ] **Test ID:** OBS-004 - Per-symbol labels present

### 5.2 Logging
- [ ] **Test ID:** OBS-005 - Order provenance logged
- [ ] **Test ID:** OBS-006 - Error stack traces captured
- [ ] **Test ID:** OBS-007 - Signal generation logged

---

## 6) Strategy Tests

### 6.1 SMA Crossover
- [ ] **Test ID:** STRAT-001 - Fast > Slow crossover (BUY)
- [ ] **Test ID:** STRAT-002 - Fast < Slow crossover (SELL)

### 6.2 Scalping
- [ ] **Test ID:** STRAT-003 - M1 timeframe signals

### 6.3 Momentum Breakout
- [ ] **Test ID:** STRAT-004 - Breakout detection

### 6.4 Mean Reversion
- [ ] **Test ID:** STRAT-005 - Reversion to mean

---

## 7) Stress & Stability Tests

### 7.1 High Frequency
- [ ] **Test ID:** STRESS-001 - Burst 100 trades @ 10/sec
- [ ] **Test ID:** STRESS-002 - Burst 200 trades @ 20/sec
- **Expected:** No crashes, graceful degradation

### 7.2 Concurrency
- [ ] **Test ID:** STRESS-003 - Multiple simultaneous signals
- [ ] **Test ID:** STRESS-004 - RPC under load

### 7.3 Recovery
- [ ] **Test ID:** STRESS-005 - Restart during open positions
- [ ] **Test ID:** STRESS-006 - MT5 reconnection

---

## 8) Safety Tests

- [ ] **Test ID:** SAFE-001 - Dry-run mode prevents real trades
- [ ] **Test ID:** SAFE-002 - trade_allowed=false blocks execution
- [ ] **Test ID:** SAFE-003 - Emergency shutdown stops all activity

---

## Grading Formula

```
Overall Grade = (
    Indicator_Score * 0.20 +
    Signal_Score * 0.20 +
    Risk_Score * 0.20 +
    Execution_Score * 0.20 +
    Stability_Score * 0.20
)

Letter Grade:
  A+ = 100%    A = 95-99%    A- = 90-94%
  B+ = 85-89%  B = 80-84%    B- = 75-79%  <- TARGET MINIMUM
  C  = 70-74%  D = 60-69%    F  = <60%
```

---

## Test Results Log

| Test ID | Status | Timestamp | Notes |
|---------|--------|-----------|-------|
| IND-001 | ✅ PASS | 2025-12-29 13:41 | RSI overbought detected |
| IND-002 | ✅ PASS | 2025-12-29 13:41 | RSI oversold detected |
| IND-003 | ✅ PASS | 2025-12-29 13:41 | RSI neutral correct |
| SIG-001 | ✅ PASS | 2025-12-29 13:45 | BUY order filled #600994186 |
| RISK-002 | ✅ PASS | 2025-12-29 13:57 | Spread config fixed |

---

## Automation Hooks

Each test can be executed programmatically:

```python
# Run all indicator tests
python monitoring\indicator_stress_test.py

# Run burst injection
python monitoring\inject_signals.py --mode burst --count 100 --rate 5

# Run pattern test
python monitoring\inject_signals.py --mode pattern --pattern "BUY,SELL,BUY" --repeat 50
```

All results are appended to SYSTEM_REPORT.md with timestamps and metric snapshots for traceability.

