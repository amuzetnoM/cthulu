# Legacy Code Notice

This directory contains legacy code from Herald v0.1.0 (prototype).

**Status**: Deprecated - Do not use for new development

## Legacy Structure

The following directories contain the old codebase:
- `core/` - Old connection, risk, and trade managers
- `strategies/` - Old strategy implementations
- `utils/` - Old utilities (config, logger)
- `indicators/` - Empty placeholder
- `ml/` - Empty placeholder directories
- `backtesting/` - Empty placeholder
- `main.py` - Old entry point

## Current Structure

Use the new `herald/` package structure:
- `herald/connector/` - MT5 integration
- `herald/data/` - Data layer
- `herald/strategy/` - Trading strategies
- `herald/execution/` - Order execution
- `herald/risk/` - Risk management
- `herald/__main__.py` - Main entry point

## Migration

Run Herald using:
```bash
python -m herald
```

Do NOT use:
```bash
python main.py  # Old, deprecated
```

## Removal Plan

Legacy directories will be removed in v2.0.0 after full migration verification.
Keep for now to support any users with old scripts.

---
Last Updated: December 6, 2024
