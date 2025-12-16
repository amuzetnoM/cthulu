"""
MT5 Connector Module

Handles MetaTrader 5 terminal connection, session management, and health monitoring.
Implements retry logic, rate limiting, and reconnection policies.
"""

try:
    import MetaTrader5 as mt5  # type: ignore
except Exception:
    # Minimal stub of MetaTrader5 for testing and import-time resilience
    class _Mt5Stub:
        ORDER_TYPE_BUY = 0
        ORDER_TYPE_SELL = 1
        TRADE_ACTION_DEAL = 0
        ORDER_TIME_GTC = 0
        ORDER_FILLING_FOK = 3
        TRADE_RETCODE_DONE = 10009

        def initialize(self, *args, **kwargs):
            return False

        def shutdown(self):
            return False

        def last_error(self):
            return {'code': 1, 'message': 'MT5 not available'}

    mt5 = _Mt5Stub()
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from herald.market.tick_manager import TickManager


@dataclass
class ConnectionConfig:
    """MT5 connection configuration"""
    login: int
    password: str
    server: str
    timeout: int = 60000
    portable: bool = False
    path: Optional[str] = None
    max_retries: int = 3
    retry_delay: int = 5


class MT5Connector:
    """
    MetaTrader 5 connection manager with health checks and reconnection logic.
    
    Provides reliable connection management.
    - Automatic reconnection on connection loss
    - Health checks and session monitoring
    - Rate limiting and timeout handling
    - Exception consolidation
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize MT5 connector.
        
        Args:
            config: Connection configuration
        """
        self.config = config
        self.connected = False
        self.logger = logging.getLogger("herald.connector")
        self._lock = Lock()
        self._last_request_time = 0.0
        self._min_request_interval = 0.1  # 100ms between requests
        # Tick manager for lightweight tick caching and subscriptions
        try:
            self._tick_manager = TickManager(self)
        except Exception:
            self._tick_manager = None
        
    def connect(self) -> bool:
        """
        Establish connection to MT5 terminal.
        
        Returns:
            True if connection successful
        """
        with self._lock:
            for attempt in range(1, self.config.max_retries + 1):
                try:
                    self.logger.info(f"Connecting to MT5 (attempt {attempt}/{self.config.max_retries})...")
                    
                    # Initialize MT5 with credentials directly (most reliable method)
                    self.logger.info("Initializing MT5 with credentials...")
                    
                    init_result = mt5.initialize(
                        login=self.config.login,
                        password=self.config.password,
                        server=self.config.server,
                        timeout=self.config.timeout
                    )
                    
                    if not init_result:
                        error = mt5.last_error()
                        raise ConnectionError(f"MT5 initialize failed: {error}")
                    
                    # Verify connection
                    account_info = mt5.account_info()
                    if not account_info:
                        raise ConnectionError("Connected but cannot retrieve account info")
                    
                    if account_info.login != self.config.login:
                        raise ConnectionError(f"Connected to wrong account: {account_info.login}")
                    
                    self.connected = True
                    # Mask account login in logs to avoid leaking full account numbers
                    acct_display = str(self.config.login)
                    acct_masked = acct_display if len(acct_display) <= 4 else f"****{acct_display[-4:]}"
                    self.logger.info(f"Connected to {self.config.server} (account: {acct_masked})")
                    self.logger.info(f"Balance: ${account_info.balance:.2f}, Trade allowed: {account_info.trade_allowed}")
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Connection attempt {attempt} failed: {e}")
                    if attempt < self.config.max_retries:
                        time.sleep(self.config.retry_delay)
                        
            self.logger.error("All connection attempts failed")
            return False
            
    def disconnect(self):
        """Disconnect from MT5 terminal."""
        with self._lock:
            if self.connected:
                mt5.shutdown()
                self.connected = False
                self.logger.info("Disconnected from MT5")
                
    def is_connected(self) -> bool:
        """
        Check if connected and terminal is responsive.
        
        Returns:
            True if connected and healthy
        """
        if not self.connected:
            return False
            
        try:
            # Test connection with terminal info request
            info = mt5.terminal_info()
            return info is not None and info.connected
        except Exception as e:
            self.logger.error(f"Connection check failed: {e}")
            self.connected = False
            return False
            
    def reconnect(self) -> bool:
        """
        Reconnect to MT5 terminal.
        
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
        
    def _normalize_symbol(self, s: str) -> str:
        """Return normalized symbol string for comparison (alphanumeric upper-case)."""
        if not s:
            return ""
        return ''.join(ch for ch in s.upper() if ch.isalnum())

    def _mt5_symbol_info_tick(self, symbol: str):
        """Low-level wrapper around mt5.symbol_info_tick to be used by TickManager.

        Returns the native mt5 tick object or None.
        """
        try:
            # Ensure symbol selected for terminal
            sel = self.ensure_symbol_selected(symbol)
            if not sel:
                return None
            self._rate_limit()
            return mt5.symbol_info_tick(sel)
        except Exception:
            return None

    def get_recent_ticks(self, symbol: str, seconds: float = 60.0, max_points: int = 200):
        """Return recent ticks for `symbol` from the in-memory ring buffer."""
        if self._tick_manager is None:
            return []
        return self._tick_manager.get_recent(symbol, seconds=seconds, max_points=max_points)

    def subscribe_ticks(self, symbol: str, callback, priority: str = 'high'):
        """Subscribe to tick updates for `symbol` with given priority (high/medium/low)."""
        if self._tick_manager is None:
            raise RuntimeError("Tick manager not initialized")
        self._tick_manager.subscribe(symbol, callback, priority=priority)

    def unsubscribe_ticks(self, symbol: str, callback):
        if self._tick_manager is None:
            return
        self._tick_manager.unsubscribe(symbol, callback)

    def _find_matching_symbol(self, desired: str) -> List[str]:
        """Return a list of available MT5 symbol names whose normalized form matches desired (or contains it)."""
        matches: List[str] = []
        try:
            all_symbols = mt5.symbols_get()
        except Exception:
            return matches
        if not all_symbols:
            return matches
        desired_norm = self._normalize_symbol(desired)
        for s in all_symbols:
            try:
                name_norm = self._normalize_symbol(s.name)
                if name_norm == desired_norm or desired_norm in name_norm or name_norm in desired_norm:
                    matches.append(s.name)
            except Exception:
                continue
        return matches

    def ensure_symbol_selected(self, symbol: str) -> Optional[str]:
        """Ensure symbol is selected in MT5, with flexible matching for common suffix/prefix variations.

        Returns the actual selected symbol name on success, or None on failure.
        """
        # Try direct selection
        try:
            if mt5.symbol_select(symbol, True):
                return symbol
        except Exception:
            pass

        # Try common variant swaps (#m <-> m#)
        variants = []
        if '#m' in symbol and 'm#' not in symbol:
            variants.append(symbol.replace('#m', 'm#'))
        if 'm#' in symbol and '#m' not in symbol:
            variants.append(symbol.replace('m#', '#m'))
        # Try removing # or m
        variants.append(symbol.replace('#', ''))
        variants.append(symbol.replace('m', ''))

        for v in variants:
            try:
                if mt5.symbol_select(v, True):
                    return v
            except Exception:
                continue

        # Try scanning available symbols with normalized comparison
        matches = self._find_matching_symbol(symbol)
        if matches:
            self.logger.debug(f"Found candidate symbols for {symbol}: {matches}")
            for m in matches:
                try:
                    if mt5.symbol_select(m, True):
                        self.logger.info(f"Selected symbol variant: {m} for requested {symbol}")
                        return m
                except Exception:
                    continue
            self.logger.warning(f"Found candidate symbols but failed to select any for {symbol}: {matches}")
        else:
            # Include hint about available symbols for debugging
            try:
                sample = mt5.symbols_get()[:20]
                sample_names = [s.name for s in sample]
                self.logger.debug(f"Available symbols (sample): {sample_names}")
            except Exception:
                pass

        return None

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
            self.logger.error("Not connected to MT5")
            return None
            
        self._rate_limit()
        
        try:
            # Ensure symbol is selected (flexible)
            selected = self.ensure_symbol_selected(symbol)
            if not selected:
                self.logger.error(f"Failed to select symbol {symbol}")
                return None
                
            # Fetch rates
            rates = mt5.copy_rates_from_pos(selected, timeframe, start_pos, count)
            
            if rates is None or len(rates) == 0:
                error = mt5.last_error()
                self.logger.error(f"Failed to fetch rates: {error}")
                return None
                
            # Convert numpy array to list of dicts
            return [
                {
                    'time': datetime.fromtimestamp(rate[0]),
                    'open': float(rate[1]),
                    'high': float(rate[2]),
                    'low': float(rate[3]),
                    'close': float(rate[4]),
                    'tick_volume': int(rate[5]),
                    'spread': int(rate[6]),
                    'real_volume': int(rate[7])
                }
                for rate in rates
            ]
            
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
            account = mt5.account_info()
            if account is None:
                return None
                
            return {
                'login': account.login,
                'server': account.server,
                'balance': account.balance,
                'equity': account.equity,
                'margin': account.margin,
                'margin_free': account.margin_free,
                'margin_level': account.margin_level,
                'profit': account.profit,
                'currency': account.currency,
                'leverage': account.leverage,
                'trade_allowed': account.trade_allowed,
            }
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
            info = mt5.symbol_info(symbol)
            if info is None:
                return None
                
            return {
                'name': info.name,
                'bid': info.bid,
                'ask': info.ask,
                'spread': info.spread,
                'digits': info.digits,
                'point': info.point,
                'trade_mode': info.trade_mode,
                'volume_min': info.volume_min,
                'volume_max': info.volume_max,
                'volume_step': info.volume_step,
                'contract_size': info.trade_contract_size,
                'currency_base': info.currency_base,
                'currency_profit': info.currency_profit,
                'currency_margin': info.currency_margin,
            }
        except Exception as e:
            self.logger.error(f"Error fetching symbol info: {e}")
            return None
            
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
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if not self.is_connected():
                return health
                
            health['connected'] = True
            
            # Check terminal
            terminal = mt5.terminal_info()
            if terminal:
                health['terminal_connected'] = terminal.connected
                health['trade_allowed'] = terminal.trade_allowed
                
            # Check account
            account = mt5.account_info()
            if account:
                health['account_valid'] = account.trade_allowed
                health['balance'] = account.balance
                health['equity'] = account.equity
                health['margin_level'] = account.margin_level
                
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
