"""
Android MT5 Connector - Direct Integration

Simplified connector that uses MT5AndroidInterface directly.
No bridge server required - reads MT5 files and uses intents.

v1.0.0 Beta - Android Native Edition
"""

import logging
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from pathlib import Path

from connector.mt5_android_interface import (
    MT5AndroidInterface,
    MT5SymbolInfo,
    MT5AccountInfo,
    MT5Position,
    MT5Tick
)


# MT5 Constants
class MT5Constants:
    """MT5 API constants."""
    
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
    TRADE_RETCODE_PLACED = 10008
    TRADE_RETCODE_REQUOTE = 10004
    TRADE_RETCODE_REJECT = 10006
    TRADE_RETCODE_INVALID = 10013
    TRADE_RETCODE_TIMEOUT = 10012
    
    # Timeframes
    TIMEFRAME_M1 = 1
    TIMEFRAME_M5 = 5
    TIMEFRAME_M15 = 15
    TIMEFRAME_M30 = 30
    TIMEFRAME_H1 = 60
    TIMEFRAME_H4 = 240
    TIMEFRAME_D1 = 1440
    TIMEFRAME_W1 = 10080
    TIMEFRAME_MN1 = 43200


# Module-level exports
ORDER_TYPE_BUY = MT5Constants.ORDER_TYPE_BUY
ORDER_TYPE_SELL = MT5Constants.ORDER_TYPE_SELL
TRADE_ACTION_DEAL = MT5Constants.TRADE_ACTION_DEAL
ORDER_TIME_GTC = MT5Constants.ORDER_TIME_GTC
ORDER_FILLING_FOK = MT5Constants.ORDER_FILLING_FOK
ORDER_FILLING_IOC = MT5Constants.ORDER_FILLING_IOC
TRADE_RETCODE_DONE = MT5Constants.TRADE_RETCODE_DONE


@dataclass
class ConnectionConfig:
    """Connection configuration for Android MT5."""
    
    # MT5 data directory (auto-detected if not specified)
    mt5_data_dir: Optional[str] = None
    
    # MT5 account credentials (for display purposes)
    login: int = 0
    password: str = ""
    server: str = ""
    
    # Connection settings
    timeout: int = 60000
    max_retries: int = 3
    retry_delay: int = 5
    
    # For backwards compatibility with old configs
    bridge_type: str = "direct"  # Ignored - always direct now
    bridge_host: str = ""  # Ignored
    bridge_port: int = 0  # Ignored


# Alias for backwards compatibility
AndroidConnectionConfig = ConnectionConfig


class _OrderResult:
    """Order result wrapper for compatibility."""
    
    def __init__(self, data: Dict[str, Any]):
        self.retcode = data.get('retcode', 0)
        self.deal = data.get('deal', 0)
        self.order = data.get('order', 0)
        self.volume = data.get('volume', 0.0)
        self.price = data.get('price', 0.0)
        self.bid = data.get('bid', 0.0)
        self.ask = data.get('ask', 0.0)
        self.comment = data.get('comment', '')
        self.request_id = data.get('request_id', 0)
        self.queue_id = data.get('queue_id', '')
        self.status = data.get('status', '')


class _Position:
    """Position wrapper for compatibility."""
    
    def __init__(self, data: Dict[str, Any]):
        self.ticket = data.get('ticket', 0)
        self.symbol = data.get('symbol', '')
        self.type = data.get('type', 0)
        self.volume = data.get('volume', 0.0)
        self.price_open = data.get('price_open', 0.0)
        self.price_current = data.get('price_current', 0.0)
        self.sl = data.get('sl', 0.0)
        self.tp = data.get('tp', 0.0)
        self.profit = data.get('profit', 0.0)
        self.swap = data.get('swap', 0.0)
        self.magic = data.get('magic', 0)
        self.time = data.get('time', 0)
        self.comment = data.get('comment', '')


class _SymbolTick:
    """Symbol tick wrapper for compatibility."""
    
    def __init__(self, data: Dict[str, Any]):
        self.time = data.get('time', 0)
        self.bid = data.get('bid', 0.0)
        self.ask = data.get('ask', 0.0)
        self.last = data.get('last', 0.0)
        self.volume = data.get('volume', 0)


class MT5Connector:
    """
    Android MT5 Connector - Direct Integration.
    
    Uses MT5AndroidInterface directly to:
    - Read MT5 data files from Android storage
    - Queue orders for execution via MT5 app
    - Use termux-am intents to launch MT5
    
    No bridge server required.
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize Android MT5 connector.
        
        Args:
            config: Connection configuration
        """
        self.config = config
        self.connected = False
        self.logger = logging.getLogger("Cthulu.connector.android")
        self._lock = Lock()
        self._last_request_time = 0.0
        self._min_request_interval = 0.05  # 50ms between requests
        
        # Initialize Android interface
        data_dir = Path(config.mt5_data_dir) if config.mt5_data_dir else None
        self._interface = MT5AndroidInterface(data_dir)
        
        self.logger.info("Initializing Android MT5 connector (Direct Mode)")
        if self._interface.available:
            self.logger.info(f"MT5 data directory: {self._interface.data_dir}")
        else:
            self.logger.warning("MT5 data directory not found - running in limited mode")
    
    def connect(self, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Establish connection to MT5 data.
        
        Args:
            params: Optional connection parameters
            
        Returns:
            True if connection successful
        """
        with self._lock:
            self.logger.info("Connecting to MT5 Android data...")
            
            if not self._interface.available:
                self.logger.error("MT5 data directory not accessible")
                self.logger.error("Please ensure MT5 Android app is installed and has data")
                return False
            
            # Verify we can read data
            account_result = self._interface.get_account_info()
            if not account_result.get('success'):
                self.logger.warning("Could not read account info, but continuing...")
            
            self.connected = True
            self.logger.info("Connected to MT5 Android data")
            
            # Log account info if available
            if account_result.get('success'):
                data = account_result.get('data', {})
                login = data.get('login', 0)
                if login:
                    masked = f"****{str(login)[-4:]}" if len(str(login)) > 4 else str(login)
                    self.logger.info(f"Account: {masked}")
                    self.logger.info(f"Balance: ${data.get('balance', 0):.2f}")
            
            return True
    
    def disconnect(self):
        """Disconnect from MT5."""
        with self._lock:
            self.connected = False
            self.logger.info("Disconnected from MT5 Android")
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self.connected and self._interface.available
    
    def reconnect(self) -> bool:
        """Reconnect to MT5."""
        self.disconnect()
        time.sleep(1)
        return self.connect()
    
    def _rate_limit(self):
        """Apply rate limiting."""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    # =========================================================================
    # Account & Symbol Info
    # =========================================================================
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information."""
        self._rate_limit()
        result = self._interface.get_account_info()
        if result.get('success'):
            return result.get('data')
        return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information."""
        self._rate_limit()
        result = self._interface.get_symbol_info(symbol)
        if result.get('success'):
            return result.get('data')
        return None
    
    def symbol_info_tick(self, symbol: str) -> Optional[_SymbolTick]:
        """Get current tick for symbol."""
        self._rate_limit()
        result = self._interface.get_tick(symbol)
        if result.get('success'):
            return _SymbolTick(result.get('data', {}))
        
        # Fallback: use symbol info bid/ask
        sym_result = self._interface.get_symbol_info(symbol)
        if sym_result.get('success'):
            data = sym_result.get('data', {})
            return _SymbolTick({
                'bid': data.get('bid', 0),
                'ask': data.get('ask', 0),
                'time': int(time.time())
            })
        return None
    
    def ensure_symbol_selected(self, symbol: str) -> bool:
        """Ensure symbol is selected in Market Watch."""
        # On Android, symbols are always available if data exists
        return True
    
    # =========================================================================
    # Market Data
    # =========================================================================
    
    def get_rates(
        self,
        symbol: str,
        timeframe: int,
        count: int,
        start_pos: int = 0
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch historical rates.
        
        Args:
            symbol: Trading symbol
            timeframe: MT5 timeframe constant
            count: Number of bars
            start_pos: Starting position
            
        Returns:
            List of OHLCV dictionaries
        """
        self._rate_limit()
        result = self._interface.get_rates(symbol, timeframe, count)
        if result.get('success'):
            return result.get('data', [])
        return None
    
    # =========================================================================
    # Positions
    # =========================================================================
    
    def positions_get(self, ticket: Optional[int] = None) -> List[_Position]:
        """
        Get open positions.
        
        Args:
            ticket: Optional specific ticket to retrieve
            
        Returns:
            List of Position objects
        """
        # Note: Position reading from files requires additional implementation
        # For now, return empty - positions managed via MT5 app
        self.logger.debug("Position reading from files not fully implemented")
        return []
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions as dictionaries."""
        positions = self.positions_get()
        return [p.__dict__ for p in positions]
    
    # =========================================================================
    # Trading
    # =========================================================================
    
    def order_send(self, request: Dict[str, Any]) -> Optional[_OrderResult]:
        """
        Send a trading order.
        
        On Android, this queues the order and opens MT5 app.
        
        Args:
            request: MT5 order request dictionary
            
        Returns:
            OrderResult with queue_id if successful
        """
        self._rate_limit()
        
        self.logger.info(f"Order request: {request.get('symbol')} {request.get('type')} {request.get('volume')}")
        
        result = self._interface.send_order(request)
        
        if result.get('success'):
            data = result.get('data', {})
            self.logger.info(f"Order queued: {data.get('queue_id')}")
            
            # Return result with queue info
            return _OrderResult({
                'retcode': TRADE_RETCODE_DONE,  # Queued successfully
                'order': 0,
                'deal': 0,
                'volume': request.get('volume', 0),
                'price': request.get('price', 0),
                'queue_id': data.get('queue_id', ''),
                'status': data.get('status', 'QUEUED'),
                'comment': data.get('note', 'Order queued for manual execution')
            })
        else:
            self.logger.error(f"Order failed: {result.get('error')}")
            return _OrderResult({
                'retcode': MT5Constants.TRADE_RETCODE_REJECT,
                'comment': result.get('error', 'Unknown error')
            })
    
    def close_position_by_ticket(self, ticket: int, volume: Optional[float] = None) -> Optional[_OrderResult]:
        """
        Close a position by ticket.
        
        Args:
            ticket: Position ticket to close
            volume: Volume to close (None = full position)
            
        Returns:
            OrderResult
        """
        close_request = {
            'action': MT5Constants.TRADE_ACTION_DEAL,
            'position': ticket,
            'volume': volume,
            'type': 'CLOSE',
            'comment': 'Cthulu close'
        }
        
        return self.order_send(close_request)
    
    def modify_position(
        self,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Optional[_OrderResult]:
        """
        Modify position SL/TP.
        
        Args:
            ticket: Position ticket
            sl: New stop loss
            tp: New take profit
            
        Returns:
            OrderResult
        """
        modify_request = {
            'action': MT5Constants.TRADE_ACTION_SLTP,
            'position': ticket,
            'sl': sl,
            'tp': tp,
            'type': 'MODIFY',
            'comment': 'Cthulu modify'
        }
        
        return self.order_send(modify_request)
    
    # =========================================================================
    # Error Handling
    # =========================================================================
    
    def last_error(self) -> tuple:
        """Get last error code and message."""
        return (0, "No error")
    
    # =========================================================================
    # Pending Orders (from queue)
    # =========================================================================
    
    def get_pending_orders(self) -> List[Dict[str, Any]]:
        """Get pending orders from queue."""
        result = self._interface.get_pending_orders()
        if result.get('success'):
            return result.get('data', [])
        return []


# Alias for backwards compatibility
MT5ConnectorAndroid = MT5Connector


__all__ = [
    'MT5Connector',
    'MT5ConnectorAndroid', 
    'ConnectionConfig',
    'AndroidConnectionConfig',
    'MT5Constants',
    'ORDER_TYPE_BUY',
    'ORDER_TYPE_SELL',
    'TRADE_ACTION_DEAL',
    'ORDER_TIME_GTC',
    'ORDER_FILLING_FOK',
    'ORDER_FILLING_IOC',
    'TRADE_RETCODE_DONE',
    '_OrderResult',
    '_Position',
    '_SymbolTick',
]
