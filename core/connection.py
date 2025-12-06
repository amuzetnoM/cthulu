"""
MetaTrader 5 connection manager
Handles connection, reconnection, and health checks
"""

import MetaTrader5 as mt5
import time
from typing import Optional, Dict, Any
from datetime import datetime
import logging


class MT5Connection:
    """Manages MetaTrader 5 terminal connection"""
    
    def __init__(
        self,
        login: int,
        password: str,
        server: str,
        timeout: int = 60000,
        portable: bool = False,
        path: Optional[str] = None
    ):
        """
        Initialize MT5 connection manager
        
        Args:
            login: MT5 account number
            password: Account password
            server: Broker server name
            timeout: Connection timeout in milliseconds
            portable: Use portable MT5 installation
            path: Custom path to MT5 terminal
        """
        self.login = login
        self.password = password
        self.server = server
        self.timeout = timeout
        self.portable = portable
        self.path = path
        self.connected = False
        self.logger = logging.getLogger("Herald.MT5Connection")
        
    def connect(self, retries: int = 3) -> bool:
        """
        Connect to MT5 terminal
        
        Args:
            retries: Number of connection attempts
            
        Returns:
            True if connected successfully
        """
        for attempt in range(1, retries + 1):
            try:
                self.logger.info(f"Connecting to MT5 (attempt {attempt}/{retries})...")
                
                # Initialize MT5
                if self.path:
                    if not mt5.initialize(path=self.path, portable=self.portable):
                        raise ConnectionError(f"MT5 initialize failed: {mt5.last_error()}")
                else:
                    if not mt5.initialize():
                        raise ConnectionError(f"MT5 initialize failed: {mt5.last_error()}")
                
                # Login to account
                if not mt5.login(self.login, password=self.password, server=self.server):
                    error = mt5.last_error()
                    mt5.shutdown()
                    raise ConnectionError(f"MT5 login failed: {error}")
                
                self.connected = True
                self.logger.info(f"Successfully connected to {self.server}")
                return True
                
            except Exception as e:
                self.logger.error(f"Connection attempt {attempt} failed: {e}")
                if attempt < retries:
                    time.sleep(5)
                else:
                    self.logger.error("All connection attempts failed")
                    
        return False
        
    def disconnect(self):
        """Disconnect from MT5 terminal"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            self.logger.info("Disconnected from MT5")
            
    def is_connected(self) -> bool:
        """
        Check if connected to MT5
        
        Returns:
            True if connected and terminal is responsive
        """
        if not self.connected:
            return False
            
        try:
            # Test connection by getting terminal info
            info = mt5.terminal_info()
            return info is not None
        except Exception as e:
            self.logger.error(f"Connection check failed: {e}")
            self.connected = False
            return False
            
    def reconnect(self) -> bool:
        """
        Reconnect to MT5 terminal
        
        Returns:
            True if reconnection successful
        """
        self.logger.info("Attempting to reconnect...")
        self.disconnect()
        time.sleep(2)
        return self.connect()
        
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get current account information
        
        Returns:
            Dictionary with account details
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to MT5")
            
        account = mt5.account_info()
        if account is None:
            raise RuntimeError(f"Failed to get account info: {mt5.last_error()}")
            
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
            'name': account.name,
            'company': account.company
        }
        
    def get_terminal_info(self) -> Dict[str, Any]:
        """
        Get MT5 terminal information
        
        Returns:
            Dictionary with terminal details
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to MT5")
            
        terminal = mt5.terminal_info()
        if terminal is None:
            raise RuntimeError(f"Failed to get terminal info: {mt5.last_error()}")
            
        return {
            'connected': terminal.connected,
            'trade_allowed': terminal.trade_allowed,
            'community_connection': terminal.community_connection,
            'build': terminal.build,
            'name': terminal.name,
            'company': terminal.company,
            'path': terminal.path,
            'data_path': terminal.data_path,
            'commondata_path': terminal.commondata_path,
        }
        
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol information
        
        Args:
            symbol: Trading symbol (e.g., 'XAUUSD')
            
        Returns:
            Dictionary with symbol details or None
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to MT5")
            
        info = mt5.symbol_info(symbol)
        if info is None:
            self.logger.error(f"Symbol {symbol} not found")
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
            'trade_contract_size': info.trade_contract_size,
            'currency_base': info.currency_base,
            'currency_profit': info.currency_profit,
            'currency_margin': info.currency_margin,
        }
        
    def select_symbol(self, symbol: str) -> bool:
        """
        Enable symbol in MarketWatch
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if symbol enabled successfully
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to MT5")
            
        if not mt5.symbol_select(symbol, True):
            self.logger.error(f"Failed to select symbol {symbol}")
            return False
            
        self.logger.info(f"Symbol {symbol} enabled in MarketWatch")
        return True
        
    def health_check(self) -> Dict[str, bool]:
        """
        Perform comprehensive health check
        
        Returns:
            Dictionary with health status
        """
        health = {
            'connected': False,
            'trade_allowed': False,
            'account_valid': False,
            'terminal_ready': False
        }
        
        try:
            # Check connection
            if not self.is_connected():
                return health
            health['connected'] = True
            
            # Check terminal
            terminal = mt5.terminal_info()
            if terminal:
                health['trade_allowed'] = terminal.trade_allowed
                health['terminal_ready'] = terminal.connected
                
            # Check account
            account = mt5.account_info()
            if account:
                health['account_valid'] = account.trade_allowed
                
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            
        return health
        
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
