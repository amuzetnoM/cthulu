---
title: Ultra-Aggressive Trading Guide
description: High-frequency scalping strategies and ultra-aggressive trading mindset configuration for experienced traders
tags: [ultra-aggressive, scalping, high-frequency, advanced-trading]
slug: /docs/ultra-aggressive-guide
sidebar_position: 8
---

![version-badge](https://img.shields.io/badge/version-5.1.0-indigo) ![codename-badge](https://img.shields.io/badge/codename-APEX-gold)

## Overview

The **Ultra-Aggressive** mindset is Cthulu's most aggressive trading configuration, designed for experienced traders who want maximum trading frequency with high-speed scalping strategies. This mode combines dynamic strategy selection with ultra-responsive indicators optimized for M1-M15 timeframes.

⚠️ **WARNING**: This mindset involves significantly higher risk and is only recommended for experienced traders who:
- Understand high-frequency trading dynamics
- Can tolerate large drawdowns
- Have adequate capital (minimum $500+ recommended)
- Are comfortable with rapid position turnover

## Key Features

### Dynamic Strategy Selection
- Automatically switches between multiple strategies based on market conditions
- Uses regime detection (ADX) to identify trending vs ranging markets
- Continuously evaluates strategy performance and adapts
- Available strategies:
  - **EMA Crossover** (8/21): Fast trend following
  - **Momentum Breakout**: Catches strong directional moves
  - **Scalping** (5/10 EMA): Ultra-fast entries on M1/M5
  - **SMA Crossover** (5/13): Additional fast crossover signals

### Ultra-Responsive Indicators
- RSI (7 & 14 period): Quick oversold/overbought detection
- MACD (12/26/9): Momentum confirmation
- Bollinger Bands (20, 2σ): Volatility-based entries
- ADX (14): Trend strength for regime detection
- Supertrend (10, 3x): Dynamic support/resistance
- VWAP: Institutional price levels

### Aggressive Risk Parameters
```json
"risk": {
  "position_size_pct": 15.0,         // 15% per trade (vs 2% balanced)
  "max_daily_loss": 500.0,           // $500 daily loss limit
  "max_positions_per_symbol": 3,     // Up to 3 concurrent positions
  "max_total_positions": 10,         // Total 10 positions
  "emergency_stop_loss_pct": 12.0    // 12% emergency stop
}
```

## How to Enable

### Method 1: Interactive Wizard
```bash
python __main__.py --config config.json --wizard
# Select option 4: "ultra_aggressive"
```

### Method 2: Command Line
```bash
python __main__.py --config config.json --mindset ultra_aggressive
```

### Method 3: Configuration File
Use the pre-configured template:
```bash
cp config_ultra_aggressive.json config.json
python __main__.py --config config.json
```

## Optimal Settings

### Recommended Timeframes
- **M1 (1 Minute)**: Maximum signal frequency, requires constant monitoring
- **M5 (5 Minutes)**: Balanced scalping frequency (recommended start)
- **M15 (15 Minutes)**: Slower scalping, easier to manage

### Recommended Symbols
Ultra-aggressive works best with:
- **EURUSD, GBPUSD**: Tight spreads, high liquidity
- **XAUUSD (Gold)**: High volatility, good for breakouts
- **Major crypto pairs**: BTCUSD, ETHUSD (with # suffix for CFDs)

Avoid:
- Exotic pairs with wide spreads
- Low liquidity instruments
- During low-volume periods (Asian session)

### Poll Interval
- Set to **15-30 seconds** for ultra-responsive signal detection
- Default in config: `"poll_interval": 15`

## Strategy Behavior

### Signal Generation
The ultra-aggressive mode generates signals much more frequently:
- **Confidence threshold**: 0.25 (vs 0.60 for balanced)
- More permissive RSI levels (20/80 vs 30/70)
- Tighter ATR multipliers (0.8-1.5x)
- Risk/reward targets: 2.5-3.5:1

### Position Management
- Faster entries and exits
- Trailing stops activate sooner
- Time-based exits after 1-2 hours (scalping mode)
- Profit targets hit more frequently

### Regime Adaptation
Every 3 minutes (180 seconds), Cthulu:
1. Calculates current market regime (trending/ranging)
2. Evaluates performance of each strategy
3. Selects the best-performing strategy for current conditions
4. Logs the active strategy switch

## Risk Management

### Capital Requirements
- **Minimum**: $500 (for 0.01 lot minimum sizes)
- **Recommended**: $2,000+ for proper diversification
- **Optimal**: $5,000+ for comfortable operation

### Daily Loss Limits
The ultra-aggressive mode has a $500 daily loss circuit breaker:
- If daily loss reaches $500, trading automatically stops
- Positions remain open but no new trades
- System requires manual restart after hitting limit
- Review your strategy if hitting this frequently

### Position Sizing
With 15% position size:
- $1,000 account → $150 per trade → ~0.03 lots on EURUSD
- $2,000 account → $300 per trade → ~0.06 lots
- Adjust `position_size_pct` in config if too aggressive

## Monitoring & Optimization

### Key Metrics to Watch
1. **Win Rate**: Target >50% for profitability
2. **Profit Factor**: Should be >1.5 at minimum
3. **Max Drawdown**: Don't exceed 20-25% of equity
4. **Sharpe Ratio**: Target >1.0 for risk-adjusted returns

### Performance Tuning
If experiencing issues:

**Too Many Trades, Losing Money**:
- Increase confidence threshold to 0.35-0.40
- Tighten spread limits (max 1-1.5 pips)
- Increase poll interval to 30-60 seconds
- Remove scalping from strategy mix

**Not Enough Signals**:
- Lower confidence threshold to 0.20
- Verify indicators are calculating (check logs)
- Ensure sufficient lookback bars (500+)
- Check market hours (avoid low-volume periods)

**High Slippage**:
- Only trade during high-volume periods (London/NY overlap)
- Check broker execution quality
- Reduce position size
- Switch to higher timeframes (M15 instead of M1)

## Troubleshooting

### Common Issues

#### "Strategy not generating signals"
- Check indicator calculations in logs
- Verify RSI/ATR are present: `grep "RSI\|ATR" Cthulu.log`
- Ensure EMA columns computed: Look for "Computed EMA columns" in logs
- Try running with `--log-level DEBUG` for detailed output

#### "Too aggressive, hitting daily loss limit"
- Reduce position size: Set `position_size_pct` to 10% or 8%
- Lower max positions: Set `max_total_positions` to 5 or 6
- Add filters: Increase confidence threshold to 0.30+
- Use wider stops: Increase ATR multipliers by 0.2-0.5

#### "Scalping strategy not trading on M1"
- M1 requires very frequent data updates (poll_interval: 15)
- Check spread: Must be <2 pips for entry
- Verify EMA crossovers happening: Check DEBUG logs
- RSI must be recovering from oversold/overbought zones

## Example Configuration

Complete ultra-aggressive config excerpt:
```json
{
  "trading": {
    "symbol": "EURUSD",
    "timeframe": "TIMEFRAME_M5",
    "poll_interval": 15,
    "lookback_bars": 500
  },
  "risk": {
    "position_size_pct": 15.0,
    "max_daily_loss": 500.0,
    "max_positions_per_symbol": 3,
    "max_total_positions": 10,
    "emergency_stop_loss_pct": 12.0,
    "use_kelly_sizing": true
  },
  "strategy": {
    "type": "dynamic",
    "dynamic_selection": {
      "enabled": true,
      "regime_check_interval": 180,
      "performance_weight": 0.4,
      "regime_weight": 0.4
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
        "type": "scalping",
        "params": {
          "fast_ema": 5,
          "slow_ema": 10,
          "rsi_period": 7,
          "rsi_oversold": 20,
          "rsi_overbought": 80,
          "atr_multiplier": 0.8,
          "risk_reward_ratio": 2.5
        }
      }
    ]
  },
  "confidence_threshold": 0.25
}
```

## Best Practices

1. **Start in Paper Trading**: Test ultra-aggressive settings in dry-run mode first
2. **Monitor Closely**: This mode requires active monitoring, especially initially
3. **Set Alerts**: Use GUI or logs to track performance hourly
4. **Review Daily**: Check metrics, adjust if win rate <45% or profit factor <1.3
5. **Scale Gradually**: Start with smaller position sizes, increase after proven results
6. **Know When to Stop**: If hitting daily loss limits frequently, switch to aggressive or balanced

## Further Reading

- [Risk Management Guide](RISK_MANAGEMENT.md)
- [Performance Tuning](PERFORMANCE_TUNING.md)
- [Strategy Configuration](FEATURES_GUIDE.md#strategies)
- [Indicator Details](FEATURES_GUIDE.md#indicators)

## Support

If you encounter issues with ultra-aggressive mode:
1. Check logs: `Cthulu.log` and `logs/latest_summary.txt`
2. Review strategy info: `logs/strategy_info.txt`
3. Open an issue with log excerpts and configuration used
4. Join discussions for tips from other ultra-aggressive users

---

**Remember**: Ultra-aggressive mode is HIGH RISK. Only use it if you fully understand the implications and can afford to lose your trading capital. Past performance does not guarantee future results.




