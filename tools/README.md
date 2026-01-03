# Standalone Tools

This directory contains **standalone utilities** that are NOT part of the core Cthulu system.

## Tools

### `platform_detector.py`
Platform detection utility that identifies the operating system (Windows, Linux, Android/Termux, macOS).

**Usage:**
```python
from tools.platform_detector import get_platform_info

info = get_platform_info()
print(f"Platform: {info.platform_type}")
print(f"Is Android: {info.is_android}")
```

### `connector_factory.py`
Factory pattern for creating MT5 connectors based on platform. This is a standalone tool for multi-platform deployments.

**Note:** This branch uses the Android connector directly in the core system. The factory is kept here as a reference implementation for multi-platform support.

**Usage:**
```python
from tools.connector_factory import create_connector

# Auto-detect platform
connector = create_connector(config)

# Force specific platform
connector = create_connector(config, force_platform='android')
```

## Purpose

These tools are maintained separately from the core system to:
- Keep the core system simple and focused
- Provide reference implementations for advanced use cases
- Enable experimentation without affecting production code

## This Branch

**This branch (`copilot/cthulu5-android-test`) is Android-only.** The core system uses `MT5ConnectorAndroid` directly, aliased as `MT5Connector`. The factory and platform detector are not used in the core system.
