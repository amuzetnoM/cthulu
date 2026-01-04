# Android MT5 Native Support

## Overview

Cthulu now supports running natively on Android devices using Termux! This allows you to run the full Cthulu trading system on your Android phone or tablet, connecting directly to the native MT5 Android app.

## Why Android Support?

- **Native Performance**: Run Cthulu directly on Android without the overhead of Windows containers or VMs
- **Stable MT5 App**: The MT5 Android app is mature and stable
- **Portability**: Run your trading bot on powerful mobile devices like the Samsung Galaxy Z Fold series
- **Lower Infrastructure Costs**: No need for Windows servers or VPS

## Prerequisites

1. **Android Device**
   - Android 7.0 or higher
   - Recommended: Flagship devices with sufficient RAM (4GB+)
   - Samsung Galaxy Z Fold series or similar high-end tablets are ideal

2. **Termux**
   - Install Termux from F-Droid (NOT Google Play - the Play Store version is outdated)
   - F-Droid: https://f-droid.org/packages/com.termux/

3. **MT5 Android App**
   - Install MetaTrader 5 from Google Play Store
   - Configure and login to your trading account

4. **Python Environment**
   - Python 3.10+ installed in Termux
   - Git for cloning repositories

## Installation

### Step 1: Set Up Termux

```bash
# Update Termux packages
pkg update && pkg upgrade

# Install required packages
pkg install python git

# Install pip packages
pip install --upgrade pip
```

### Step 2: Clone and Install Cthulu

```bash
# Clone Cthulu repository
cd ~
git clone https://github.com/amuzetnoM/cthulu.git
cd cthulu

# Checkout Android branch
git checkout copilot/cthulu5-android-test

# Install dependencies
pip install -r requirements.txt

# Install Android-specific dependencies
pip install flask requests
```

### Step 3: Set Up MT5 Bridge

The Android implementation uses a bridge server to communicate with the MT5 Android app. 

```bash
# Start the bridge server (in a separate Termux session)
python connector/mt5_bridge_server.py --host 127.0.0.1 --port 18812
```

**Note**: Keep this bridge server running while Cthulu is active. You can use `tmux` or `screen` to run it in the background:

```bash
# Install tmux
pkg install tmux

# Start tmux session
tmux new -s mt5bridge

# Run bridge server
python connector/mt5_bridge_server.py

# Detach from tmux: Press Ctrl+B, then D
# Reattach: tmux attach -t mt5bridge
```

### Step 4: Configure Cthulu for Android

Create or modify your `config.json`:

```json
{
  "mt5": {
    "platform": "android",
    "bridge_host": "127.0.0.1",
    "bridge_port": 18812,
    "bridge_type": "rest",
    "login": 12345678,
    "password": "your_password",
    "server": "YourBroker-Server"
  },
  "symbol": "EURUSD",
  "timeframe": "H1",
  ...
}
```

### Step 5: Run Cthulu

```bash
# Run Cthulu
python -m cthulu --config config.json
```

## Architecture

### Communication Flow

```
┌─────────────┐      REST API       ┌──────────────────┐      Native API      ┌─────────────┐
│   Cthulu    │ ←─────────────────→ │  MT5 Bridge      │ ←──────────────────→ │  MT5 App    │
│   (Python)  │   HTTP/JSON         │  Server (Flask)  │   File/Intent        │  (Android)  │
└─────────────┘                     └──────────────────┘                      └─────────────┘
```

### Components

1. **Cthulu Core**: The main trading system (unchanged)
2. **Platform Detector**: Automatically detects Android/Termux environment
3. **Connector Factory**: Selects appropriate connector based on platform
4. **Android Connector**: Android-specific MT5 connector
5. **Bridge Server**: Communication layer between Python and MT5 Android app

## Bridge Communication Methods

The Android connector supports three communication methods:

### 1. REST API (Recommended)

- Uses Flask REST API server
- Most reliable and feature-rich
- Requires `flask` package

```python
from cthulu.connector import create_connector

config = {
    'bridge_type': 'rest',
    'bridge_host': '127.0.0.1',
    'bridge_port': 18812,
    'login': 12345,
    'password': 'password',
    'server': 'Broker-Server'
}

connector = create_connector(config, force_platform='android')
connector.connect()
```

### 2. Socket Communication

- Direct socket connection
- Lower latency
- Requires custom bridge implementation

```python
config = {
    'bridge_type': 'socket',
    'bridge_host': '127.0.0.1',
    'bridge_port': 18813
}
```

### 3. File-Based IPC

- Simple file-based communication
- Fallback option
- Lower performance

```python
config = {
    'bridge_type': 'file',
    'bridge_data_dir': '/path/to/shared/dir'
}
```

## Platform Detection

Cthulu automatically detects when running on Android:

```python
from cthulu.utils.platform_detector import get_platform_info

info = get_platform_info()
print(f"Platform: {info.platform_type}")
print(f"Is Android: {info.is_android}")
print(f"Is Termux: {info.is_termux}")
```

## Connector Factory

The factory pattern automatically selects the right connector:

```python
from cthulu.connector import create_connector

# Auto-detect platform
connector = create_connector(config)

# Force specific platform
android_connector = create_connector(config, force_platform='android')
windows_connector = create_connector(config, force_platform='windows')
```

## Testing

### Run Android-Specific Tests

```bash
# Run all Android connector tests
pytest tests/test_android_connector.py -v

# Run specific test
pytest tests/test_android_connector.py::TestAndroidConnector::test_connect_success -v
```

### Manual Testing

```python
from cthulu.connector.mt5_connector_android import MT5ConnectorAndroid, AndroidConnectionConfig

# Create config
config = AndroidConnectionConfig(
    bridge_host='127.0.0.1',
    bridge_port=18812,
    login=12345,
    password='test',
    server='TestServer'
)

# Create connector
connector = MT5ConnectorAndroid(config)

# Test connection
if connector.connect():
    print("Connected!")
    account = connector.get_account_info()
    print(f"Balance: {account['balance']}")
    connector.disconnect()
```

## Troubleshooting

### Bridge Server Not Starting

**Problem**: Bridge server fails to start

**Solutions**:
1. Check if Flask is installed: `pip show flask`
2. Install Flask: `pip install flask`
3. Check if port is already in use: `netstat -tuln | grep 18812`

### Cannot Connect to Bridge

**Problem**: Cthulu cannot connect to bridge server

**Solutions**:
1. Verify bridge server is running: `curl http://127.0.0.1:18812/health`
2. Check firewall settings (Termux usually doesn't have issues)
3. Verify correct host/port in configuration
4. Check bridge server logs

### MT5 App Not Responding

**Problem**: Bridge cannot communicate with MT5 app

**Solutions**:
1. Ensure MT5 app is running and logged in
2. Check MT5 app permissions in Android settings
3. Try restarting MT5 app
4. Verify broker credentials are correct

### Performance Issues

**Problem**: Slow execution or high latency

**Solutions**:
1. Use REST API bridge (fastest)
2. Reduce polling frequency in configuration
3. Close other apps to free memory
4. Use a high-end device with sufficient RAM

## Limitations

### Current Limitations

1. **Bridge Dependency**: Requires a bridge server to run
2. **No Native MT5 Python Package**: The MetaTrader5 Python package doesn't work on Android
3. **Battery Usage**: Running Cthulu continuously will drain battery
4. **Background Restrictions**: Android may restrict background execution

### Future Improvements

1. **Direct MT5 Integration**: Work on direct integration with MT5 Android app
2. **Optimized Bridge**: Lower overhead bridge implementation
3. **Battery Optimization**: Power-efficient polling and execution
4. **Native Android Service**: Run Cthulu as an Android service

## Performance Considerations

### Device Requirements

- **Minimum**: Android 7.0, 2GB RAM, quad-core processor
- **Recommended**: Android 10+, 6GB+ RAM, octa-core processor
- **Optimal**: Samsung Galaxy Z Fold series, 12GB+ RAM

### Power Management

To prevent Android from killing Cthulu:

1. Disable battery optimization for Termux
2. Use "Don't optimize" setting for Termux in battery settings
3. Keep device plugged in during trading
4. Use `wakeLock` if available

### Network Stability

- Use stable WiFi connection
- Consider mobile data as backup
- Monitor connection status in Cthulu logs

## Security

### Best Practices

1. **Credentials**: Store credentials in `.env` file, not in code
2. **Bridge Security**: Use authentication token for bridge API
3. **Network**: Use localhost (127.0.0.1) for bridge communication
4. **Permissions**: Limit Termux and MT5 app permissions
5. **Updates**: Keep Termux, Python, and dependencies updated

### Authentication

Add authentication to bridge server:

```python
config = {
    'bridge_auth_token': 'your-secret-token-here'
}
```

## FAQ

### Q: Can I run Cthulu on Android without Termux?

A: Currently, no. Termux provides the Linux-like environment needed to run Python and Cthulu.

### Q: Does this work with MT4 Android app?

A: Not yet. This implementation is specific to MT5. MT4 support may be added in the future.

### Q: Can I run multiple Cthulu instances?

A: Yes, but each instance needs its own bridge server on a different port.

### Q: Will this drain my battery?

A: Yes, continuous trading will use significant battery. Keep device plugged in or use a power bank.

### Q: Is it as stable as Windows version?

A: The core Cthulu logic is identical. Stability depends on the bridge implementation and Android system stability.

### Q: Can I use this on a tablet?

A: Yes! Tablets with large screens (like Galaxy Tab S series) work great.

## Support

For issues specific to Android implementation:

1. Check logs in Cthulu and bridge server
2. Verify platform detection: `python -c "from cthulu.utils.platform_detector import get_platform_info; print(get_platform_info())"`
3. Test bridge separately: `python connector/mt5_bridge_server.py`
4. Open an issue on GitHub with:
   - Android version
   - Device model
   - Termux version
   - Python version
   - Error logs

## Contributing

Contributions to improve Android support are welcome!

Areas for contribution:
- Better MT5 Android app integration
- Performance optimizations
- Additional bridge communication methods
- Battery optimization strategies
- Documentation improvements

## License

Same as Cthulu main project (AGPL-3.0)

