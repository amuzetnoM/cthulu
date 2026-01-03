"""
Android MT5 Connector Module

Provides MT5 connectivity for Android devices running Termux.
Uses a bridge/adapter pattern to communicate with MT5 Android app.

The connector supports multiple communication methods:
1. REST API bridge (recommended)
2. Socket-based communication
3. File-based IPC (fallback)

Prerequisites:
- MT5 Android app installed
- Bridge server running (see docs for setup)
"""

import os
import logging
import time
import json
import socket
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from pathlib import Path


# MT5 Constants - duplicated here for Android compatibility
# These match the MetaTrader5 package constants
class MT5Constants:
    """MT5 API constants for Android connector."""
    
    # Order types
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5
    
    # Trade actions
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_PENDING = 5
    TRADE_ACTION_SLTP = 6
    TRADE_ACTION_MODIFY = 7
    TRADE_ACTION_REMOVE = 8
    
    # Order time
    ORDER_TIME_GTC = 0
    ORDER_TIME_DAY = 1
    ORDER_TIME_SPECIFIED = 2
    ORDER_TIME_SPECIFIED_DAY = 3
    
    # Order filling
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_RETURN = 2
    
    # Trade retcodes
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_INVALID = 10013
    TRADE_RETCODE_TIMEOUT = 10012
    
    # Timeframes
    TIMEFRAME_M1 = 1
    TIMEFRAME_M5 = 5
    TIMEFRAME_M15 = 15
    TIMEFRAME_M30 = 30
    TIMEFRAME_H1 = 16385
    TIMEFRAME_H4 = 16388
    TIMEFRAME_D1 = 16408
    TIMEFRAME_W1 = 32769
    TIMEFRAME_MN1 = 49153


# Create module-level constants for backward compatibility
ORDER_TYPE_BUY = MT5Constants.ORDER_TYPE_BUY
ORDER_TYPE_SELL = MT5Constants.ORDER_TYPE_SELL
TRADE_ACTION_DEAL = MT5Constants.TRADE_ACTION_DEAL
ORDER_TIME_GTC = MT5Constants.ORDER_TIME_GTC
ORDER_FILLING_FOK = MT5Constants.ORDER_FILLING_FOK
ORDER_FILLING_IOC = MT5Constants.ORDER_FILLING_IOC
TRADE_RETCODE_DONE = MT5Constants.TRADE_RETCODE_DONE


@dataclass
class AndroidConnectionConfig:
    """Android MT5 connection configuration"""
    # Bridge connection settings
    bridge_host: str = "127.0.0.1"
    bridge_port: int = 18812  # MT5 bridge port
    bridge_type: str = "rest"  # rest, socket, or file
    
    # MT5 account credentials (passed to bridge)
    login: int = 0
    password: str = ""
    server: str = ""
    
    # Connection settings
    timeout: int = 60000
    max_retries: int = 3
    retry_delay: int = 5
    
    # Bridge-specific settings
    bridge_auth_token: Optional[str] = None
    bridge_data_dir: Optional[str] = None  # For file-based IPC


class MT5ConnectorAndroid:
    """
    Android-specific MT5 connector implementation.
    
    This connector provides the same interface as MT5Connector but works
    with the MT5 Android app through a bridge/adapter layer.
    
    The bridge can be implemented as:
    - REST API server running on Android
    - Socket server for direct communication
    - File-based IPC for simple setups
    """
    
    def __init__(self, config: AndroidConnectionConfig):
        """
        Initialize Android MT5 connector.
        
        Args:
            config: Android connection configuration
        """
        self.config = config
        self.connected = False
        self.logger = logging.getLogger("Cthulu.connector.android")
        self._lock = Lock()
        self._last_request_time = 0.0
        self._min_request_interval = 0.1
        self._session = None  # For REST API session
        self._socket = None  # For socket connection
        
        self.logger.info("Initializing Android MT5 connector")
        self.logger.info(f"Bridge type: {config.bridge_type}")
        self.logger.info(f"Bridge endpoint: {config.bridge_host}:{config.bridge_port}")
        
    def _check_bridge_available(self) -> bool:
        """
        Check if the MT5 bridge is available and responsive.
        
        Returns:
            True if bridge is available
        """
        try:
            if self.config.bridge_type == "rest":
                return self._check_rest_bridge()
            elif self.config.bridge_type == "socket":
                return self._check_socket_bridge()
            elif self.config.bridge_type == "file":
                return self._check_file_bridge()
            else:
                self.logger.error(f"Unknown bridge type: {self.config.bridge_type}")
                return False
        except Exception as e:
            self.logger.error(f"Bridge availability check failed: {e}")
            return False
    
    def _check_rest_bridge(self) -> bool:
        """Check if REST API bridge is available."""
        try:
            import requests
            url = f"http://{self.config.bridge_host}:{self.config.bridge_port}/health"
            headers = {}
            if self.config.bridge_auth_token:
                headers['Authorization'] = f"Bearer {self.config.bridge_auth_token}"
            
            response = requests.get(url, headers=headers, timeout=5)
            return response.status_code == 200
        except ImportError:
            self.logger.warning("requests library not available for REST bridge")
            return False
        except Exception as e:
            self.logger.debug(f"REST bridge check failed: {e}")
            return False
    
    def _check_socket_bridge(self) -> bool:
        """Check if socket bridge is available."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((self.config.bridge_host, self.config.bridge_port))
            sock.close()
            return result == 0
        except Exception as e:
            self.logger.debug(f"Socket bridge check failed: {e}")
            return False
    
    def _check_file_bridge(self) -> bool:
        """Check if file-based bridge is available."""
        try:
            if not self.config.bridge_data_dir:
                return False
            
            bridge_dir = Path(self.config.bridge_data_dir)
            status_file = bridge_dir / "bridge_status.json"
            
            if not status_file.exists():
                return False
            
            # Check if status file is recent (updated within last 10 seconds)
            mtime = status_file.stat().st_mtime
            age = time.time() - mtime
            
            return age < 10
        except Exception as e:
            self.logger.debug(f"File bridge check failed: {e}")
            return False
    
    def _send_bridge_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send a request to the MT5 bridge.
        
        Args:
            method: API method name (e.g., 'initialize', 'get_account_info')
            params: Method parameters
            
        Returns:
            Response data or None on error
        """
        try:
            if self.config.bridge_type == "rest":
                return self._send_rest_request(method, params)
            elif self.config.bridge_type == "socket":
                return self._send_socket_request(method, params)
            elif self.config.bridge_type == "file":
                return self._send_file_request(method, params)
            else:
                self.logger.error(f"Unknown bridge type: {self.config.bridge_type}")
                return None
        except Exception as e:
            self.logger.error(f"Bridge request failed: {e}")
            return None
    
    def _send_rest_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send request via REST API."""
        try:
            import requests
            
            url = f"http://{self.config.bridge_host}:{self.config.bridge_port}/api/mt5/{method}"
            headers = {'Content-Type': 'application/json'}
            
            if self.config.bridge_auth_token:
                headers['Authorization'] = f"Bearer {self.config.bridge_auth_token}"
            
            response = requests.post(
                url,
                json=params,
                headers=headers,
                timeout=self.config.timeout / 1000
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"REST request failed: {response.status_code} - {response.text}")
                return None
                
        except ImportError:
            self.logger.error("requests library not available. Install with: pip install requests")
            return None
        except Exception as e:
            self.logger.error(f"REST request error: {e}")
            return None
    
    def _send_socket_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send request via socket."""
        try:
            request_data = {
                'method': method,
                'params': params,
                'timestamp': time.time()
            }
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config.timeout / 1000)
            sock.connect((self.config.bridge_host, self.config.bridge_port))
            
            # Send request
            request_json = json.dumps(request_data).encode('utf-8')
            sock.sendall(len(request_json).to_bytes(4, 'big'))
            sock.sendall(request_json)
            
            # Receive response
            response_len = int.from_bytes(sock.recv(4), 'big')
            response_data = b''
            while len(response_data) < response_len:
                chunk = sock.recv(min(4096, response_len - len(response_data)))
                if not chunk:
                    break
                response_data += chunk
            
            sock.close()
            
            return json.loads(response_data.decode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"Socket request error: {e}")
            return None
    
    def _send_file_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send request via file-based IPC."""
        try:
            if not self.config.bridge_data_dir:
                self.logger.error("bridge_data_dir not configured for file-based IPC")
                return None
            
            bridge_dir = Path(self.config.bridge_data_dir)
            bridge_dir.mkdir(parents=True, exist_ok=True)
            
            # Create request file
            request_id = f"{int(time.time() * 1000)}_{os.getpid()}"
            request_file = bridge_dir / f"request_{request_id}.json"
            response_file = bridge_dir / f"response_{request_id}.json"
            
            request_data = {
                'method': method,
                'params': params,
                'request_id': request_id,
                'timestamp': time.time()
            }
            
            with open(request_file, 'w') as f:
                json.dump(request_data, f)
            
            # Wait for response (with timeout)
            start_time = time.time()
            timeout_seconds = self.config.timeout / 1000
            
            while time.time() - start_time < timeout_seconds:
                if response_file.exists():
                    with open(response_file, 'r') as f:
                        response_data = json.load(f)
                    
                    # Clean up files
                    try:
                        request_file.unlink()
                        response_file.unlink()
                    except Exception:
                        pass
                    
                    return response_data
                
                time.sleep(0.1)
            
            # Timeout - clean up request file
            try:
                request_file.unlink()
            except Exception:
                pass
            
            self.logger.error(f"File request timeout for method: {method}")
            return None
            
        except Exception as e:
            self.logger.error(f"File request error: {e}")
            return None
    
    def connect(self) -> bool:
        """
        Establish connection to MT5 via Android bridge.
        
        Returns:
            True if connection successful
        """
        with self._lock:
            self.logger.info("Attempting to connect to MT5 Android app via bridge...")
            
            # Check if bridge is available
            if not self._check_bridge_available():
                self.logger.error("MT5 bridge is not available or not responding")
                self.logger.error(f"Please ensure the bridge server is running on {self.config.bridge_host}:{self.config.bridge_port}")
                self.logger.error("See documentation for bridge setup instructions")
                return False
            
            # Attempt connection with retries
            for attempt in range(1, self.config.max_retries + 1):
                try:
                    self.logger.info(f"Connection attempt {attempt}/{self.config.max_retries}...")
                    
                    # Send initialize request to bridge
                    params = {}
                    if self.config.login and self.config.login != 0:
                        params['login'] = self.config.login
                        params['password'] = self.config.password
                        params['server'] = self.config.server
                    
                    response = self._send_bridge_request('initialize', params)
                    
                    if not response:
                        raise ConnectionError("Bridge did not respond to initialize request")
                    
                    if not response.get('success'):
                        error_msg = response.get('error', 'Unknown error')
                        raise ConnectionError(f"Bridge initialization failed: {error_msg}")
                    
                    # Verify connection by getting account info
                    account_response = self._send_bridge_request('account_info', {})
                    if not account_response or not account_response.get('success'):
                        raise ConnectionError("Could not retrieve account info")
                    
                    account_data = account_response.get('data', {})
                    self.connected = True
                    
                    # Mask account login in logs
                    acct_login = account_data.get('login', 'unknown')
                    acct_display = str(acct_login)
                    acct_masked = acct_display if len(acct_display) <= 4 else f"****{acct_display[-4:]}"
                    
                    self.logger.info(f"Successfully connected to MT5 Android app")
                    self.logger.info(f"Server: {account_data.get('server', 'unknown')}")
                    self.logger.info(f"Account: {acct_masked}")
                    self.logger.info(f"Balance: ${account_data.get('balance', 0):.2f}")
                    
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Connection attempt {attempt} failed: {e}")
                    if attempt < self.config.max_retries:
                        time.sleep(self.config.retry_delay)
            
            self.logger.error("All connection attempts failed")
            return False
    
    def disconnect(self):
        """Disconnect from MT5 bridge."""
        with self._lock:
            if self.connected:
                try:
                    self._send_bridge_request('shutdown', {})
                except Exception as e:
                    self.logger.warning(f"Error during disconnect: {e}")
                
                self.connected = False
                self.logger.info("Disconnected from MT5 Android bridge")
    
    def is_connected(self) -> bool:
        """
        Check if connected to MT5 bridge.
        
        Returns:
            True if connected and healthy
        """
        if not self.connected:
            return False
        
        try:
            response = self._send_bridge_request('terminal_info', {})
            return response is not None and response.get('success', False)
        except Exception as e:
            self.logger.error(f"Connection check failed: {e}")
            self.connected = False
            return False
    
    def reconnect(self) -> bool:
        """
        Reconnect to MT5 bridge.
        
        Returns:
            True if reconnection successful
        """
        self.logger.info("Attempting reconnection...")
        self.disconnect()
        time.sleep(2)
        return self.connect()
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        
        self._last_request_time = time.time()
    
    def get_rates(
        self,
        symbol: str,
        timeframe: int,
        count: int,
        start_pos: int = 0
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch historical rates for a symbol.
        
        Args:
            symbol: Trading symbol
            timeframe: MT5 timeframe constant
            count: Number of bars to fetch
            start_pos: Starting position (0 = most recent)
            
        Returns:
            List of rate dictionaries or None on error
        """
        if not self.is_connected():
            if not self.connect():
                self.logger.error("Not connected to MT5 bridge")
                return None
        
        self._rate_limit()
        
        try:
            params = {
                'symbol': symbol,
                'timeframe': timeframe,
                'count': count,
                'start_pos': start_pos
            }
            
            response = self._send_bridge_request('copy_rates_from_pos', params)
            
            if not response or not response.get('success'):
                error = response.get('error', 'Unknown error') if response else 'No response'
                self.logger.error(f"Failed to fetch rates: {error}")
                return None
            
            return response.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error fetching rates: {e}", exc_info=True)
            return None
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current account information.
        
        Returns:
            Dictionary with account details or None
        """
        if not self.is_connected():
            return None
        
        self._rate_limit()
        
        try:
            response = self._send_bridge_request('account_info', {})
            
            if not response or not response.get('success'):
                return None
            
            return response.get('data', {})
            
        except Exception as e:
            self.logger.error(f"Error fetching account info: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol information and trading specifications.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with symbol details or None
        """
        if not self.is_connected():
            return None
        
        self._rate_limit()
        
        try:
            params = {'symbol': symbol}
            response = self._send_bridge_request('symbol_info', params)
            
            if not response or not response.get('success'):
                return None
            
            return response.get('data', {})
            
        except Exception as e:
            self.logger.error(f"Error fetching symbol info: {e}")
            return None
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions from MT5.
        
        Returns:
            List of position dictionaries
        """
        if not self.is_connected():
            return []
        
        self._rate_limit()
        
        try:
            response = self._send_bridge_request('positions_get', {})
            
            if not response or not response.get('success'):
                return []
            
            return response.get('data', [])
            
        except Exception as e:
            self.logger.error(f"Error fetching positions: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Dictionary with health status metrics
        """
        health = {
            'connected': False,
            'terminal_connected': False,
            'trade_allowed': False,
            'account_valid': False,
            'timestamp': datetime.now().isoformat(),
            'platform': 'android'
        }
        
        try:
            if not self.is_connected():
                return health
            
            health['connected'] = True
            
            # Check terminal via bridge
            terminal_response = self._send_bridge_request('terminal_info', {})
            if terminal_response and terminal_response.get('success'):
                terminal_data = terminal_response.get('data', {})
                health['terminal_connected'] = terminal_data.get('connected', False)
                health['trade_allowed'] = terminal_data.get('trade_allowed', False)
            
            # Check account
            account_response = self._send_bridge_request('account_info', {})
            if account_response and account_response.get('success'):
                account_data = account_response.get('data', {})
                health['account_valid'] = account_data.get('trade_allowed', False)
                health['balance'] = account_data.get('balance', 0)
                health['equity'] = account_data.get('equity', 0)
                health['margin_level'] = account_data.get('margin_level', 0)
        
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            health['error'] = str(e)
        
        return health
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    # Additional methods to match MT5Connector interface
    
    def get_point_value(self, symbol: str) -> Optional[float]:
        """Return point value in account currency for one point movement for symbol."""
        try:
            info = self.get_symbol_info(symbol)
            if not info:
                return None
            point = info.get('point')
            contract = info.get('contract_size') or info.get('trade_contract_size') or info.get('contract')
            if point is None:
                return None
            if contract is None:
                contract = 1.0
            return float(point) * float(contract)
        except Exception:
            return None
    
    def get_min_lot(self, symbol: str) -> float:
        """Return minimum tradable lot size for symbol."""
        try:
            info = self.get_symbol_info(symbol)
            if not info:
                return 0.01
            return float(info.get('volume_min', 0.01))
        except Exception:
            return 0.01
    
    def get_spread(self, symbol: str) -> Optional[float]:
        """Return current spread for symbol in points or price units."""
        try:
            info = self.get_symbol_info(symbol)
            if not info:
                return None
            spread = info.get('spread')
            if spread is not None:
                return float(spread)
            bid = info.get('bid')
            ask = info.get('ask')
            if bid is not None and ask is not None:
                return abs(float(ask) - float(bid))
            return None
        except Exception:
            return None
    
    def get_position_by_ticket(self, ticket: int) -> Optional[Dict[str, Any]]:
        """Return position information for a given MT5 position ticket."""
        try:
            if not self.is_connected():
                return None
            
            self._rate_limit()
            params = {'ticket': ticket}
            response = self._send_bridge_request('position_get', params)
            
            if not response or not response.get('success'):
                return None
            
            return response.get('data')
            
        except Exception as e:
            self.logger.error(f"Error fetching position by ticket {ticket}: {e}")
            return None
    
    def ensure_symbol_selected(self, symbol: str) -> Optional[str]:
        """Ensure symbol is selected in MT5."""
        try:
            params = {'symbol': symbol, 'enable': True}
            response = self._send_bridge_request('symbol_select', params)
            
            if response and response.get('success'):
                return symbol
            return None
            
        except Exception:
            return None
