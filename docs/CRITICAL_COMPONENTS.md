# Critical Components - DO NOT DELETE OR MODIFY WITHOUT REVIEW

This document lists the **critical components** that enable Cthulu's 500% success rate. 
**NEVER** delete, rename, or significantly modify these without thorough testing.

## 🔴 CRITICAL FILES (The Secret Sauce)

### 1. Entry Confluence Filter
**File:** `cognition/entry_confluence.py`
**Purpose:** Quality gates all trade entries, ensuring optimal timing and price levels
**Commit:** Restored from `ef3a53c`
**Impact if broken:** Signals execute at poor prices, win rate plummets
**Test:** Must import `EntryConfluenceFilter` and `EntryQuality`

### 2. Dynamic SL/TP Manager  
**File:** `risk/dynamic_sltp.py`
**Purpose:** 5-mode adaptive stop-loss/take-profit based on account state
**Modes:** 
- Conservative (drawdown > 15%)
- Balanced (10-15% drawdown)
- Aggressive (5-10% drawdown)
- Ultra-Aggressive (< 5% drawdown)
- Recovery (after losses)
**Impact if broken:** Poor risk management, account blown
**Test:** Must have `calculate_dynamic_sltp()` method

### 3. Trade Adoption System
**File:** `position/trade_manager.py`
**File:** `position/adoption.py`
**Purpose:** Adopts external/manual trades and applies Cthulu's SL/TP
**Impact if broken:** Manual trades unmanaged, risk exposure
**Test:** TradeManager must have `scan_and_adopt()` method

### 4. Strategy Selector
**File:** `strategy/strategy_selector.py`
**Purpose:** Dynamically selects best strategy based on market regime
**Required Strategies (7 total):**
- SMA Crossover
- EMA Crossover
- Momentum Breakout
- Scalping
- Mean Reversion
- Trend Following
- RSI Reversal
**Impact if broken:** Wrong strategy for market conditions
**Test:** All 7 strategies must load and be selectable

---

## 🟡 IMPORTANT INTEGRATIONS

### Entry Confluence Integration Points
1. **Bootstrap:** `core/bootstrap.py` - Initialize filter
2. **Trading Loop:** `core/trading_loop.py` - Call `analyze_entry()` before execution
3. **Config:** `config.json` - `entry_confluence.enabled = true`

### Dynamic SLTP Integration Points
1. **Bootstrap:** Initialize `DynamicSLTPManager`
2. **Position Lifecycle:** Call `_apply_dynamic_sltp()` in monitoring
3. **Config:** Risk thresholds and ATR multipliers

### Trade Adoption Integration Points
1. **Trading Loop:** Call `scan_and_adopt()` every loop iteration
2. **Config:** `orphan_trades.enabled = true`, `min_age_seconds = 0`

---

## 🟢 INDICATOR REQUIREMENTS

All strategies require these indicators to be computed **BEFORE** signal generation:

### Always Required:
- **SMA:** `sma_short` (10-period), `sma_long` (30-period)
- **EMA:** `ema_fast` (12-period), `ema_slow` (26-period)
- **RSI:** `rsi` (14-period)
- **ATR:** `atr` (14-period)
- **ADX:** `adx` (14-period)

### Runtime Added:
- MACD
- Bollinger Bands
- Stochastic
- VWAP

**Integration:** `core/trading_loop.py` - Indicators computed in `_calculate_indicators()` before strategies run

---

## 📋 PRE-DEPLOYMENT CHECKLIST

Before deploying **ANY** changes:

1. ✅ Run health check: `python scripts/health_check.py`
2. ✅ Run critical tests: `pytest tests/test_critical_paths.py -v`
3. ✅ Verify entry_confluence.py exists: `ls cognition/entry_confluence.py`
4. ✅ Verify config has all sections: `python -c "import json; print(json.load(open('config.json')).keys())"`
5. ✅ Test import of critical modules:
   ```python
   from cognition.entry_confluence import EntryConfluenceFilter
   from risk.dynamic_sltp import DynamicSLTPManager
   from position.trade_manager import TradeManager
   ```
6. ✅ Run 5-loop smoke test: `python -m cthulu --config config.json --skip-setup --max-loops 5`
7. ✅ Check logs for errors: `tail -n 100 logs/Cthulu.log`

---

## 🚨 REGRESSION PREVENTION

### What Caused the Recent Regression?
1. **Entry Confluence Filter deleted** - Restored from git commit `ef3a53c`
2. **Dynamic SLTP simplified** - Restored 5-mode system from `windows-ml` branch
3. **Trade Adoption broken** - TradeAdoptionManager incorrectly added, removed
4. **SMA/EMA indicators missing** - Fixed column name mismatches

### How to Prevent Future Regressions?
1. **Never delete files** without checking git history first
2. **Run health_check.py** before committing major changes
3. **Keep critical tests passing** - CI/CD pipeline will catch issues
4. **Document changes** to critical components in git commits
5. **Test in isolation** - Use `--max-loops 5` for quick validation
6. **Monitor logs** - Watch for warnings about missing indicators/components

---

## 📊 MONITORING HEALTHY SYSTEM

### Healthy System Indicators:
```
✅ Entry Confluence Filter ENABLED - signals will be quality-gated
✅ SMA Crossover initialized: short=10, long=30
✅ EMA Crossover initialized: fast=12, slow=26
✅ All 7 strategies loaded
✅ DynamicSLTPManager initialized
✅ External trade adoption ENABLED
✅ Added 6 runtime indicators: RSI, ADX, MACD, BB, Stochastic, VWAP
✅ NO warnings about "indicators not found"
```

### Unhealthy System Indicators:
```
❌ "entry_confluence.py" not found
❌ "SMA indicators not found" (warning every loop)
❌ Only 2 strategies loaded (should be 7)
❌ Trade adoption disabled
❌ Import errors on startup
```

---

## 🔧 QUICK FIXES

### Entry Confluence Missing?
```bash
cd C:\workspace\cthulu
git checkout ef3a53c -- cognition/entry_confluence.py
```

### Dynamic SLTP Simplified?
```bash
git checkout windows-ml -- risk/dynamic_sltp.py
```

### Strategies Not Loading?
Check `config.json` - All 7 strategies must have `"enabled": true`

### Indicators Missing?
Check `core/trading_loop.py` - SMA/EMA must be computed before strategies

---

**Last Updated:** 2026-01-08  
**System Version:** v5.1.0 APEX (Restored)  
**Win Rate:** 500% (when all components functional)
