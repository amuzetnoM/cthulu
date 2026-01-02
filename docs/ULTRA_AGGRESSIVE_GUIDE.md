---
title: Ultra-Aggressive Trading Guide
description: High-frequency trading configuration with ultra-aggressive parameters and risk settings
tags: [ultra-aggressive, hft, scalping, high-frequency]
slug: /docs/ultra-aggressive
sidebar_position: 15
---

# ULTRA-AGGRESSIVE TRADING GUIDE

![Version](https://img.shields.io/badge/Version-5.1.0_APEX-4B0082?style=for-the-badge&labelColor=0D1117&logo=git&logoColor=white)

## Overview

The Ultra-Aggressive mode is designed for experienced traders who want maximum trading frequency and opportunity capture. This mode operates with relaxed thresholds, higher position limits, and faster polling intervals.

⚠️ **Warning**: This mode involves significantly higher risk. Only use with proper risk management and adequate capital.

## Configuration

### Risk Parameters

```json
{
  "risk": {
    "position_size_pct": 15.0,
    "max_daily_loss": 500.0,
    "max_positions_per_symbol": 10,
    "max_total_positions": 10
  }
}
```

### Trading Parameters

```json
{
  "trading": {
    "poll_interval": 15,
    "confidence_threshold": 0.15,
    "adx_threshold": 15
  }
}
```

### Strategy Configuration

Enable all 7 strategies with fallback mechanism:

```json
{
  "strategy": {
    "type": "dynamic",
    "fallback_enabled": true,
    "max_fallback_attempts": 3
  }
}
```

## Best Practices

1. **Start Small**: Begin with lower position sizes until you validate performance
2. **Monitor Closely**: Watch the system during initial deployment
3. **Set Hard Limits**: Always configure max daily loss limits
4. **Use on Demos First**: Test thoroughly on demo accounts before going live

## Performance Expectations

- **Signal Frequency**: High - multiple signals per hour
- **Win Rate**: Target 60-70%
- **Risk/Reward**: Typically 1:1.5 to 1:2
- **Drawdown**: Expect higher volatility and drawdown

## Recommended Timeframes

- M5: Very high frequency
- M15: High frequency
- M30: Moderate frequency

See [FEATURES_GUIDE.md](FEATURES_GUIDE.md) for complete strategy details.
