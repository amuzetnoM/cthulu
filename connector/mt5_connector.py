"""
MT5 Connector - Clean Implementation
Handles all MetaTrader 5 communication with proper error handling.
"""
import logging
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import MT5, fallback for dry-run mode
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 module not available")


@dataclass
class PositionInfo:
    """Position information from MT5."""
    ticket: int
    symbol: str
    type: int  # 0=buy, 1=sell
    volume: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    magic: int
    comment: str
    time: float


class MT5Connector:
    """
    MetaTrader 5 connection manager.
    
    Handles:
    - Connection/disconnection
    - Position retrieval
    - Order placement
    - Position modification
    - Symbol/tick data
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MT5 connector.
        
        Args:
            config: System configuration with MT5 credentials
        """
        self.config = config
        self._connected = False
        self._account_info = None
        
        # Get credentials from environment or config
        self.login = int(os.environ.get('MT5_LOGIN', config.get('mt5', {}).get('login', 0)))
        self.password = os.environ.get('MT5_PASSWORD', config.get('mt5', {}).get('password', ''))
        self.server = os.environ.get('MT5_SERVER', config.get('mt5', {}).get('server', ''))
        
        self.dry_run = config.get('mode', 'live').lower() == 'dry_run'
        
    def connect(self) -> bool:
        """
        Connect to MT5 terminal.
        
        Returns:
            True if connected successfully
        """
        if self.dry_run:
            logger.info("Dry-run mode: MT5 connection simulated")
            self._connected = True
            return True
        
        if not MT5_AVAILABLE:
            logger.error("MT5 module not available")
            return False
        
        for attempt in range(1, 4):
            logger.info(f"Connecting to MT5 (attempt {attempt}/3)...")
            
            try:
                if not mt5.initialize():
                    logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                    continue
                
                if self.login:
                    logger.info("Initializing MT5 with credentials...")
                    if not mt5.login(self.login, self.password, self.server):
                        logger.error(f"MT5 login failed: {mt5.last_error()}")
                        continue
                
                self._account_info = mt5.account_info()
                if self._account_info is None:
                    logger.error("Failed to get account info")
                    continue
                
                self._connected = True
                
                # Log connection info (mask sensitive data)
                login_masked = f"****{str(self.login)[-4:]}" if self.login else "N/A"
                logger.info(f"Connected to {self.server} (account: {login_masked})")
                logger.info(f"Balance: ${self._account_info.balance:.2f}, Trade allowed: {self._account_info.trade_allowed}")
                
                return True
                
            except Exception as e:
                logger.error(f"MT5 connection error: {e}")
        
        logger.error("Failed to connect to MT5 after 3 attempts")
        return False
    
    def disconnect(self):
        """Disconnect from MT5."""
        if MT5_AVAILABLE and self._connected and not self.dry_run:
            mt5.shutdown()
        self._connected = False
        logger.info("Disconnected from MT5")
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get current account information."""
        if self.dry_run:
            return {
                'balance': 1000.0,
                'equity': 1000.0,
                'margin': 0.0,
                'free_margin': 1000.0,
                'margin_level': 0.0,
                'trade_allowed': True
            }
        
        if not self._connected:
            return {}
        
        info = mt5.account_info()
        if info is None:
            return {}
        
        return {
            'balance': info.balance,
            'equity': info.equity,
            'margin': info.margin,
            'free_margin': info.margin_free,
            'margin_level': info.margin_level,
            'trade_allowed': info.trade_allowed
        }
    
    def get_positions(self) -> List[PositionInfo]:
        """Get all open positions."""
        if self.dry_run:
            return []
        
        if not self._connected:
            return []
        
        positions = mt5.positions_get()
        if positions is None:
            return []
        
        result = []
        for pos in positions:
            result.append(PositionInfo(
                ticket=pos.ticket,
                symbol=pos.symbol,
                type=pos.type,
                volume=pos.volume,
                price_open=pos.price_open,
                price_current=pos.price_current,
                sl=pos.sl,
                tp=pos.tp,
                profit=pos.profit,
                magic=pos.magic,
                comment=pos.comment,
                time=pos.time
            ))
        
        return result
    
    def get_position(self, ticket: int) -> Optional[PositionInfo]:
        """Get a specific position by ticket."""
        positions = self.get_positions()
        for pos in positions:
            if pos.ticket == ticket:
                return pos
        return None
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information."""
        if self.dry_run:
            return {
                'symbol': symbol,
                'point': 0.01,
                'digits': 2,
                'spread': 10,
                'trade_tick_size': 0.01,
                'volume_min': 0.01,
                'volume_max': 100.0,
                'volume_step': 0.01
            }
        
        if not self._connected:
            return {}
        
        info = mt5.symbol_info(symbol)
        if info is None:
            logger.warning(f"Symbol info not found for {symbol}")
            return {}
        
        return {
            'symbol': info.name,
            'point': info.point,
            'digits': info.digits,
            'spread': info.spread,
            'trade_tick_size': info.trade_tick_size,
            'volume_min': info.volume_min,
            'volume_max': info.volume_max,
            'volume_step': info.volume_step
        }
    
    def get_tick(self, symbol: str) -> Dict[str, Any]:
        """Get current tick for symbol."""
        if self.dry_run:
            return {
                'bid': 4400.0,
                'ask': 4400.5,
                'last': 4400.25,
                'time': 0
            }
        
        if not self._connected:
            return {}
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {}
        
        return {
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'time': tick.time
        }
    
    def get_ohlcv(self, symbol: str, timeframe: str, count: int = 200):
        """
        Get OHLCV data for symbol.
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe string (M1, M5, H1, etc.)
            count: Number of bars to retrieve
            
        Returns:
            DataFrame with OHLCV data or None
        """
        if self.dry_run:
            import pandas as pd
            import numpy as np
            
            # Generate dummy data
            dates = pd.date_range(end=pd.Timestamp.now(), periods=count, freq='5min')
            base_price = 4400.0
            
            data = {
                'time': dates,
                'open': np.random.normal(base_price, 5, count),
                'high': np.random.normal(base_price + 3, 5, count),
                'low': np.random.normal(base_price - 3, 5, count),
                'close': np.random.normal(base_price, 5, count),
                'volume': np.random.randint(100, 1000, count)
            }
            return pd.DataFrame(data)
        
        if not self._connected:
            return None
        
        # Map timeframe string to MT5 constant
        tf_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
        }
        
        mt5_tf = tf_map.get(timeframe.upper(), mt5.TIMEFRAME_M5)
        
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)
        
        if rates is None or len(rates) == 0:
            logger.warning(f"No OHLCV data for {symbol} {timeframe}")
            return None
        
        import pandas as pd
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        return df
    
    def place_order(
        self,
        symbol: str,
        order_type: str,  # 'buy' or 'sell'
        volume: float,
        price: float = 0,
        sl: float = 0,
        tp: float = 0,
        magic: int = 123456,
        comment: str = "Cthulu"
    ) -> Dict[str, Any]:
        """
        Place a market order.
        
        Args:
            symbol: Symbol to trade
            order_type: 'buy' or 'sell'
            volume: Lot size
            price: Price (0 for market)
            sl: Stop loss (0 for none)
            tp: Take profit (0 for none)
            magic: Magic number
            comment: Order comment
            
        Returns:
            Order result dict
        """
        if self.dry_run:
            import random
            return {
                'success': True,
                'ticket': random.randint(100000, 999999),
                'price': price or 4400.0,
                'volume': volume
            }
        
        if not self._connected:
            return {'success': False, 'error': 'Not connected'}
        
        # Get symbol info for price
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {'success': False, 'error': f'Symbol {symbol} not found'}
        
        # Determine order type and price
        if order_type.lower() == 'buy':
            mt5_type = mt5.ORDER_TYPE_BUY
            entry_price = tick.ask
        else:
            mt5_type = mt5.ORDER_TYPE_SELL
            entry_price = tick.bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_type,
            "price": entry_price,
            "sl": sl if sl != 0 else 0.0,
            "tp": tp if tp != 0 else 0.0,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        logger.info(f"Placing MARKET order: {order_type.upper()} {volume} {symbol}")
        
        result = mt5.order_send(request)
        
        if result is None:
            return {'success': False, 'error': 'Order send failed - no result'}
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed: {result.retcode} - {result.comment}")
            return {
                'success': False,
                'error': result.comment,
                'retcode': result.retcode
            }
        
        logger.info(f"Order executed: Ticket #{result.order} | Price: {result.price} | Volume: {result.volume}")
        
        return {
            'success': True,
            'ticket': result.order,
            'price': result.price,
            'volume': result.volume
        }
    
    def modify_position(
        self,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> bool:
        """
        Modify position SL/TP.
        
        Args:
            ticket: Position ticket
            sl: New stop loss (None to keep current)
            tp: New take profit (None to keep current)
            
        Returns:
            True if modification successful
        """
        if self.dry_run:
            logger.info(f"Dry-run: Modified position {ticket} SL={sl} TP={tp}")
            return True
        
        if not self._connected:
            return False
        
        # Get current position
        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            logger.warning(f"Position {ticket} not found")
            return False
        
        pos = position[0]
        
        # Use current values if not specified
        new_sl = sl if sl is not None else pos.sl
        new_tp = tp if tp is not None else pos.tp
        
        # Round to proper precision
        symbol_info = mt5.symbol_info(pos.symbol)
        if symbol_info:
            digits = symbol_info.digits
            new_sl = round(new_sl, digits) if new_sl else 0.0
            new_tp = round(new_tp, digits) if new_tp else 0.0
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": pos.symbol,
            "sl": new_sl,
            "tp": new_tp,
        }
        
        logger.info(f"Attempting to modify position {ticket}: sl={new_sl}, tp={new_tp}")
        
        result = mt5.order_send(request)
        
        if result is None:
            logger.error(f"Failed to modify position {ticket} - no result")
            return False
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"MT5 modify FAILED: retcode={result.retcode}, comment={result.comment}")
            return False
        
        logger.info(f"Position {ticket} modified: SL={new_sl}, TP={new_tp}")
        return True
    
    def close_position(self, ticket: int, volume: Optional[float] = None) -> bool:
        """
        Close a position.
        
        Args:
            ticket: Position ticket
            volume: Volume to close (None for full)
            
        Returns:
            True if close successful
        """
        if self.dry_run:
            logger.info(f"Dry-run: Closed position {ticket}")
            return True
        
        if not self._connected:
            return False
        
        # Get position
        position = mt5.positions_get(ticket=ticket)
        if position is None or len(position) == 0:
            logger.warning(f"Position {ticket} not found for close")
            return False
        
        pos = position[0]
        close_volume = volume if volume else pos.volume
        
        # Get tick for close price
        tick = mt5.symbol_info_tick(pos.symbol)
        if tick is None:
            return False
        
        # Close is opposite of position type
        if pos.type == 0:  # Buy position - sell to close
            close_type = mt5.ORDER_TYPE_SELL
            close_price = tick.bid
        else:  # Sell position - buy to close
            close_type = mt5.ORDER_TYPE_BUY
            close_price = tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": close_volume,
            "type": close_type,
            "position": ticket,
            "price": close_price,
            "magic": pos.magic,
            "comment": "Cthulu close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result is None:
            return False
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Close failed: {result.retcode} - {result.comment}")
            return False
        
        logger.info(f"Position {ticket} closed at {close_price}")
        return True
