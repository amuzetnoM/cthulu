# Herald Trading System 
> Advanced Features Guide

## Overview

This document describes the major features of the Herald trading system, and its transformation from a basic SMA crossover system into a cutting-edge, multi-strategy autonomous trading platform with dynamic strategy selection and next-generation indicators.

## Table of Contents

1. [New Trading Strategies](#new-trading-strategies)
2. [Next-Generation Indicators](#next-generation-indicators)
3. [Dynamic Strategy Selection](#dynamic-strategy-selection)
4. [Ultra-Aggressive Mode](#ultra-aggressive-mode)
5. [Configuration Guide](#configuration-guide)
6. [Usage Examples](#usage-examples)
7. [Performance Tuning](#performance-tuning)

---

## New Trading Strategies

### 1. EMA Crossover Strategy

**Purpose**: Faster reaction to price changes for day trading
**Optimal Timeframes**: M15, M30, H1
**Key Features**:
- Uses Exponential Moving Averages (EMA) instead of Simple Moving Averages
- Faster signal generation due to exponential weighting
- Tighter stops (1.5x ATR vs 2.0x ATR)
- Higher confidence scores (0.75 vs 0.70)

**Configuration Example**:
```json
{
  "type": "ema_crossover",
  "params": {
    "fast_period": 9,
    "slow_period": 21,
    "atr_period": 14,
    "atr_multiplier": 1.5,
    "risk_reward_ratio": 2.5
  }
}
```

**When to Use**:
- Trending markets
- Day trading sessions
- When you need faster entries than SMA

---

### 2. Momentum Breakout Strategy

**Purpose**: Capture explosive moves with momentum confirmation
**Optimal Timeframes**: M15, H1, H4
**Key Features**:
- Breakout detection from consolidation zones
- Volume spike confirmation (1.5x average)
- RSI momentum validation
- Aggressive take profit (3.0x risk-reward ratio)
- High confidence signals (0.80)

**Configuration Example**:
```json
{
  "type": "momentum_breakout",
  "params": {
    "lookback_period": 20,
    "rsi_threshold": 55,
    "atr_multiplier": 1.5,
    "volume_multiplier": 1.5,
    "risk_reward_ratio": 3.0
  }
}
```

**Entry Conditions**:
- **Long**: Price breaks above recent high + RSI > 55 + Volume spike
- **Short**: Price breaks below recent low + RSI < 45 + Volume spike

**When to Use**:
- Volatile markets
- After consolidation periods
- Breakout trading sessions

---

### 3. Scalping Strategy

**Purpose**: Ultra-fast M1/M5 trading with tight stops
**Optimal Timeframes**: M1, M5
**Key Features**:
- Ultra-tight stops (1.0x ATR)
- Fast EMAs (5/10 crossover)
- RSI oversold/overbought recovery
- Spread filter (max 2 pips)
- Quick profit targets (2.0x R:R)
- Highest confidence (0.85)

**Configuration Example**:
```json
{
  "type": "scalping",
  "params": {
    "fast_ema": 5,
    "slow_ema": 10,
    "rsi_period": 7,
    "rsi_oversold": 25,
    "rsi_overbought": 75,
    "atr_multiplier": 1.0,
    "risk_reward_ratio": 2.0,
    "spread_limit_pips": 2.0
  }
}
```

**Entry Conditions**:
- **Long**: EMA5 crosses above EMA10 + RSI recovering from oversold (25-60)
- **Short**: EMA5 crosses below EMA10 + RSI recovering from overbought (40-75)
- **Filter**: Spread must be < 2 pips

**When to Use**:
- Ranging markets
- High liquidity sessions (London/NY overlap)
- Low spread periods
- Fast-paced trading

---

## Next-Generation Indicators

### 1. Supertrend Indicator

**Purpose**: Clear trend identification with dynamic support/resistance
**Type**: Trend-following

**How It Works**:
- Combines ATR with price action
- Provides dynamic support/resistance levels
- Clear directional signals (1 = bullish, -1 = bearish)
- Never whipsaws in strong trends

**Usage**:
```python
from herald.indicators.supertrend import Supertrend

indicator = Supertrend(period=10, multiplier=3.0)
result = indicator.calculate(data)

# Access values
supertrend_value = result['supertrend']
direction = result['supertrend_direction']  # 1 or -1
signal = result['supertrend_signal']  # Entry signals
```

**Interpretation**:
- Direction = 1: Bullish trend, use as trailing stop (below price)
- Direction = -1: Bearish trend, use as trailing stop (above price)
- Signal = 2: Strong buy signal (direction changed to 1)
- Signal = -2: Strong sell signal (direction changed to -1)

---

### 2. VWAP (Volume Weighted Average Price)

**Purpose**: Institutional-grade price analysis
**Type**: Volume-based

**How It Works**:
- Calculates average price weighted by volume
- Includes standard deviation bands
- Used by institutions for execution benchmarking
- Resets daily for intraday VWAP

**Usage**:
```python
from herald.indicators.vwap import VWAP

indicator = VWAP(std_dev_multiplier=2.0)
result = indicator.calculate(data)

# Access values
vwap = result['vwap']
upper_band = result['vwap_upper']  # 2x std dev
lower_band = result['vwap_lower']  # 2x std dev
```

**Trading Rules**:
- **Buy**: Price bounces from VWAP support (lower bands)
- **Sell**: Price rejects from VWAP resistance (upper bands)
- **Trend**: Price consistently above VWAP = bullish trend
- **Mean Reversion**: Price far from VWAP = expect return

**Anchored VWAP**:
Calculate VWAP from significant events (earnings, major news):
```python
from herald.indicators.vwap import AnchoredVWAP

indicator = AnchoredVWAP(anchor_index=50)  # Start from bar 50
result = indicator.calculate(data)
```

---

## Dynamic Strategy Selection

### Overview

The **StrategySelector** automatically chooses the best strategy based on:
1. Market regime (trending, ranging, volatile, consolidating)
2. Individual strategy performance
3. Strategy-regime affinity
4. Confidence scores

### Market Regime Detection

**Regimes Identified**:
- **TRENDING_UP**: Strong uptrend (ADX > 25, positive returns)
- **TRENDING_DOWN**: Strong downtrend (ADX > 25, negative returns)
- **RANGING**: Sideways movement (ADX < 20, low volatility)
- **VOLATILE**: High volatility (ATR spike, wide BB bands)
- **CONSOLIDATING**: Low volatility (narrow BB bands, low ADX)

**Detection Logic**:
```python
# Factors used:
- ADX value (trend strength)
- 20-period returns (direction)
- ATR ratio (volatility)
- Bollinger Band width (range compression)
```

### Strategy Affinity Matrix

Each strategy has optimal performance in certain regimes:

| Strategy | Trending Up | Trending Down | Ranging | Volatile | Consolidating |
|----------|-------------|---------------|---------|----------|---------------|
| **EMA Crossover** | 0.95 | 0.95 | 0.40 | 0.60 | 0.50 |
| **Momentum Breakout** | 0.80 | 0.80 | 0.50 | 0.90 | 0.30 |
| **Scalping** | 0.60 | 0.60 | 0.90 | 0.40 | 0.70 |
| **SMA Crossover** | 0.90 | 0.90 | 0.30 | 0.50 | 0.40 |

### Performance Tracking

For each strategy, the system tracks:
- **Win Rate**: % of winning trades
- **Profit Factor**: Total profit / Total loss
- **Recent Performance**: Last 50 signals
- **Average Confidence**: Mean confidence score
- **Signal Count**: Total signals generated

### Selection Algorithm

**Weighted Score Calculation**:
```
Total Score = (Performance × 0.4) + (Regime Affinity × 0.4) + (Confidence × 0.2)
```

**Performance Score** (0-1):
```
= (Win Rate × 0.5) + (min(Profit Factor/2, 1) × 0.3) + (Recent Performance × 0.2)
```

**Best Strategy**: Highest total score wins

### Usage Example

```python
from herald.strategy.strategy_selector import StrategySelector

# Create strategies
strategies = [
    EmaCrossover(config1),
    MomentumBreakout(config2),
    ScalpingStrategy(config3)
]

# Initialize selector
selector = StrategySelector(strategies=strategies, config={
    'regime_check_interval': 180,  # Check every 3 minutes
    'min_strategy_signals': 5,
    'performance_weight': 0.4,
    'regime_weight': 0.4,
    'confidence_weight': 0.2
})

# Generate signal (auto-selects best strategy)
signal = selector.generate_signal(data, latest_bar)

# Record outcome for learning
selector.record_outcome('ema_crossover', 'win', 150.0)

# Get performance report
report = selector.get_performance_report()
```

---

## Ultra-Aggressive Mode

### Configuration: `config_ultra_aggressive.json`

**Key Differences from Standard Aggressive**:

| Parameter | Standard Aggressive | Ultra-Aggressive |
|-----------|-------------------|------------------|
| **Position Size %** | 10% | 15% |
| **Max Positions** | 6 | 10 |
| **Confidence Threshold** | 0.35 | 0.25 |
| **Poll Interval** | 30s | 15s |
| **Strategy Type** | Single | Dynamic (4 strategies) |
| **Max Daily Loss** | $250 | $500 |

**Enabled Strategies** (All 4):
1. EMA Crossover (fast periods: 8/21)
2. Momentum Breakout (lookback: 15)
3. Scalping (very tight: 5/10 EMAs)
4. SMA Crossover (backup: 5/13)

**Exit Strategies** (More aggressive):
- **Adverse Movement**: 0.5% threshold (vs 1.0%), 30s window (vs 60s)
- **Time-Based**: 8 hours max hold (vs 24 hours)
- **Profit Target**: 1.5% target (vs 2.0%), 50% partial close
- **Trailing Stop**: 1.5x ATR (vs 2.0x), activates at 0.5% profit

**New Indicators**:
- RSI (14 and 7 periods for multi-timeframe)
- Supertrend (10 period, 3.0 multiplier)
- VWAP (2.0 std dev bands)

**Features Enabled**:
- ML instrumentation: `true`
- Adaptive parameters: `true`
- Multi-timeframe analysis: `true`

---

## Configuration Guide

### Complete Dynamic Strategy Configuration

```json
{
  "strategy": {
    "type": "dynamic",
    "dynamic_selection": {
      "enabled": true,
      "regime_check_interval": 180,
      "min_strategy_signals": 3,
      "performance_weight": 0.4,
      "regime_weight": 0.4,
      "confidence_weight": 0.2
    },
    "strategies": [
      {
        "type": "ema_crossover",
        "params": {
          "fast_period": 8,
          "slow_period": 21,
          "atr_multiplier": 1.2,
          "risk_reward_ratio": 3.0
        }
      },
      {
        "type": "momentum_breakout",
        "params": {
          "lookback_period": 15,
          "rsi_threshold": 50,
          "volume_multiplier": 1.3
        }
      },
      {
        "type": "scalping",
        "params": {
          "fast_ema": 5,
          "slow_ema": 10,
          "spread_limit_pips": 2.0
        }
      }
    ]
  },
  "indicators": [
    {"type": "rsi", "params": {"period": 14}},
    {"type": "rsi", "params": {"period": 7}},
    {"type": "supertrend", "params": {"period": 10, "multiplier": 3.0}},
    {"type": "vwap", "params": {"std_dev_multiplier": 2.0}},
    {"type": "macd", "params": {"fast_period": 12, "slow_period": 26}},
    {"type": "bollinger", "params": {"period": 20, "std_dev": 2.0}},
    {"type": "adx", "params": {"period": 14}}
  ]
}
```

---

## Usage Examples

### 1. Run with Ultra-Aggressive Configuration

```bash
# Interactive mode
python -m herald --config config_ultra_aggressive.json

# Automated mode (headless)
python -m herald --config config_ultra_aggressive.json --skip-setup --no-prompt

# Dry-run (no real trades)
python -m herald --config config_ultra_aggressive.json --dry-run

# Debug mode
python -m herald --config config_ultra_aggressive.json --log-level DEBUG
```

### 2. Monitor Dynamic Strategy Selection

The system logs strategy selection decisions:

```
INFO: Market regime detected: TRENDING_UP (ADX=32.5, Returns=2.34%, Vol=1.12)
INFO: Selected strategy: ema_crossover (score=0.856, perf=0.823, regime=0.950, conf=0.750)
INFO:   momentum_breakout: total=0.812, perf=0.765, regime=0.800
INFO:   scalping: total=0.634, perf=0.700, regime=0.600
```

### 3. Track Strategy Performance

```bash
# View performance report in logs
grep "Recorded" herald.log | tail -20

# Example output:
# Recorded win for ema_crossover: $152.30 (WinRate=68.42%)
# Recorded loss for momentum_breakout: $-48.20 (WinRate=62.50%)
```

### 4. Test Individual Strategies

```python
from herald.strategy.ema_crossover import EmaCrossover
from herald.strategy.momentum_breakout import MomentumBreakout

# Test EMA strategy
ema_strategy = EmaCrossover(config={
    'params': {'fast_period': 9, 'slow_period': 21}
})

# Test Momentum strategy
momentum_strategy = MomentumBreakout(config={
    'params': {'lookback_period': 20, 'rsi_threshold': 55}
})
```

---

## Performance Tuning

### 1. Strategy Selection Tuning

**Adjust Weights** for different trading styles:

```json
// Conservative (rely more on performance)
{
  "performance_weight": 0.6,
  "regime_weight": 0.3,
  "confidence_weight": 0.1
}

// Aggressive (adapt faster to regime)
{
  "performance_weight": 0.3,
  "regime_weight": 0.5,
  "confidence_weight": 0.2
}
```

**Regime Check Interval**:
- Fast adaptation: 120-180 seconds
- Balanced: 300 seconds (5 minutes)
- Slow/stable: 600+ seconds

### 2. Scalping Optimization

For best scalping performance:
- Use M1 or M5 timeframes
- Trade during high liquidity (London/NY overlap)
- Monitor spread (must be < 2 pips)
- Use tight risk management (1.0x ATR stops)

```json
{
  "trading": {
    "timeframe": "TIMEFRAME_M5",
    "poll_interval": 10
  },
  "risk": {
    "position_size_pct": 5.0,  // Smaller size for scalping
    "max_positions_per_symbol": 3
  }
}
```

### 3. Breakout Trading Optimization

For momentum breakouts:
- Use H1 or H4 for better breakouts
- Increase volume multiplier for stronger confirmation
- Use wider stops for volatile instruments

```json
{
  "params": {
    "lookback_period": 20,
    "volume_multiplier": 2.0,  // Stronger confirmation
    "atr_multiplier": 2.0       // Wider stops
  }
}
```

---

## Best Practices

### 1. Start Conservative

Begin with:
- Single strategy mode
- Lower position sizes (5%)
- Higher confidence thresholds (0.40+)
- Dry-run mode for 1 week

### 2. Gradually Increase Aggression

After successful testing:
- Enable dynamic strategy selection
- Increase position sizes
- Lower confidence threshold
- Add more concurrent positions

### 3. Monitor Performance

Track these metrics:
- Overall win rate (target: 55%+)
- Profit factor (target: 1.5+)
- Strategy selection accuracy
- Regime detection accuracy

### 4. Adjust Based on Market

- **Trending**: Favor EMA/SMA crossover strategies
- **Ranging**: Enable scalping strategy
- **Volatile**: Use momentum breakout
- **Low Volume**: Increase spread limits or pause

---

## Troubleshooting

### Issue: Strategy switches too frequently

**Solution**: Increase `regime_check_interval` and `min_strategy_signals`

### Issue: Low win rate in scalping

**Solution**: 
- Check spread (must be < 2 pips)
- Verify trading during high liquidity periods
- Tighten RSI thresholds (25/75 → 20/80)

### Issue: Breakout strategy triggers too early

**Solution**:
- Increase `volume_multiplier` (1.5 → 2.0)
- Raise `rsi_threshold` (55 → 60)
- Increase `lookback_period` (20 → 30)

---

## Conclusion

These upgrades transform Herald from a basic single-strategy system into a sophisticated multi-strategy platform with:

✅ **4 Advanced Strategies**: EMA, Momentum, Scalping, SMA
✅ **Dynamic Selection**: Auto-adapts to market conditions
✅ **Next-Gen Indicators**: Supertrend, VWAP
✅ **Performance Tracking**: Learn from every trade
✅ **Market Regime Detection**: 5 different regimes
✅ **Ultra-Aggressive Mode**: For experienced traders
✅ **Comprehensive Testing**: Full test coverage

The system is now ready for aggressive day trading and scalping while maintaining smart risk management and adaptive intelligence.
