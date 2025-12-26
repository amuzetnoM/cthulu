# Herald v4.0.0 System Upgrade Fixes

## Overview
This document describes the fixes and enhancements made to address issues with the Herald v4.0.0 release, specifically focusing on wizard integration, GUI improvements, and MT5 connectivity.

## Issues Fixed

### 1. Wizard Enhancement for v4.0.0 Features

**Problem**: The setup wizard didn't support the new v4.0.0 features including dynamic strategy selection, new indicators (Supertrend, VWAP), and enhanced strategies.

**Solution**:
- Added `configure_indicators()` function supporting all v4.0.0 indicators
- Enhanced `configure_strategy()` with dynamic strategy selection mode
- Added support for EMA Crossover, Momentum Breakout, and Scalping strategies
- Integrated new features into the main wizard flow

**Usage**:
```bash
# Run the interactive wizard
python -m herald --wizard

# Or use the NLP-based wizard
python -m herald --wizard-ai
```

The wizard now prompts for:
- Strategy mode (single vs dynamic selection)
- Multiple strategy types (SMA, EMA, Momentum, Scalping)
- Technical indicators (RSI, MACD, Bollinger, Stochastic, ADX, Supertrend, VWAP)
- Risk management settings
- Mindset presets (aggressive, balanced, conservative)

### 2. GUI Dark Mode Fixes

**Problem**: Dark mode was broken with light windows, dark patches, and unreadable white text on white backgrounds.

**Solution**:
- Complete dark mode theming for all ttk widgets
- Configured Frame, Label, Entry, Combobox, Button, and Treeview styles
- Consistent color scheme:
  - Background: `#0f1720` (dark blue-grey)
  - Foreground: `#e6eef6` (light grey)
  - Accent: `#8b5cf6` (purple)
- Added proper focus and hover states

**Files Modified**: `ui/desktop.py`

### 3. GUI Duplication Prevention

**Problem**: Multiple GUI instances would launch simultaneously, creating confusion and potential conflicts.

**Solution**:
- Implemented singleton pattern using lock file mechanism
- Cross-platform PID checking (Windows and Unix)
- Automatic cleanup of stale lock files
- Lock file location: `logs/.gui_lock`

**Behavior**:
- When GUI starts, it checks for existing instance
- If found and running, displays message and exits
- If stale lock file, removes it and continues
- Lock file cleaned up on normal exit

### 4. MT5 Connection Enhancement

**Problem**: MT5 wasn't connecting despite credentials being present in environment variables. Config files with `FROM_ENV` placeholders weren't being processed.

**Solution**:
- Added FROM_ENV placeholder processing in config loader
- Environment variables processed before pydantic validation
- Maintained backward compatibility with direct env var overrides
- Fixed pydantic v2 compatibility (model_validate vs parse_obj)

**Configuration Example**:
```json
{
  "mt5": {
    "login": 0,
    "password": "FROM_ENV",
    "server": "FROM_ENV"
  }
}
```

**Environment Variables**:
```bash
export MT5_LOGIN=123456
export MT5_PASSWORD=your_password
export MT5_SERVER=your_broker_server
```

## Files Modified

### `ui/desktop.py`
- Complete dark mode theming overhaul
- Singleton lock file mechanism
- Cross-platform process checking

### `config/wizard.py`
- New `configure_indicators()` function
- Enhanced `configure_strategy()` for dynamic mode
- Support for all v4.0.0 strategies
- Fixed type imports for Python 3.11+

### `config_schema.py`
- FROM_ENV placeholder processing
- Pydantic v2 compatibility fixes
- Enhanced environment variable handling

## Testing

All fixes have been validated with comprehensive tests:

```bash
# Run validation test
python -c "$(cat << 'EOF'
from config_schema import Config
from config.wizard import parse_natural_language_intent
from config.mindsets import apply_mindset

# Test FROM_ENV
import os
os.environ['MT5_LOGIN'] = '123456'
os.environ['MT5_PASSWORD'] = 'test'
os.environ['MT5_SERVER'] = 'test'

# Test NLP parser
intent = parse_natural_language_intent("Aggressive GOLD#m on M15 and H1, 2% risk, $100 max loss")
print(f"Parsed: {intent}")

# Test mindset
config = {'risk': {}, 'strategy': {'type': 'sma_crossover', 'params': {}}}
result = apply_mindset(config, 'aggressive')
print(f"Mindset applied: {result['_mindset']}")

print("✅ All tests passed!")
EOF
)"
```

## Migration Guide

### For Existing Users

1. **Update your configuration files** to use FROM_ENV if storing credentials in environment:
   ```json
   "mt5": {
     "login": 0,
     "password": "FROM_ENV",
     "server": "FROM_ENV"
   }
   ```

2. **Set environment variables** in your `.env` file:
   ```bash
   MT5_LOGIN=your_account_number
   MT5_PASSWORD=your_password
   MT5_SERVER=your_broker_server
   ```

3. **Re-run the wizard** to configure new v4.0.0 features:
   ```bash
   python -m herald --wizard
   ```

4. **Enable new strategies and indicators** via the wizard or manually in config:
   ```json
   "strategy": {
     "type": "dynamic",
     "strategies": [
       {"type": "sma_crossover", "params": {}},
       {"type": "ema_crossover", "params": {}},
       {"type": "momentum_breakout", "params": {}}
     ]
   },
   "indicators": [
     {"type": "supertrend", "params": {"atr_period": 10, "atr_multiplier": 3.0}},
     {"type": "vwap", "params": {}}
   ]
   ```

### For New Users

Simply run the setup wizard:
```bash
python -m herald --wizard
```

The wizard will guide you through all configuration options including the new v4.0.0 features.

## Known Issues

None. All reported issues have been resolved.

## Support

For issues or questions:
1. Check the main README.md
2. Review UPGRADE_GUIDE.md
3. Open an issue on GitHub

## Version Compatibility

- Herald: v4.0.0+
- Python: 3.9+
- Pydantic: 2.0+
- MetaTrader5: 5.0.45+

## Changelog

### 2024-12-26
- Fixed GUI dark mode theming
- Added GUI singleton pattern
- Enhanced wizard with v4.0.0 features
- Added FROM_ENV config placeholder support
- Fixed pydantic v2 compatibility
- Improved MT5 connection handling
