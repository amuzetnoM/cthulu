"""
Base strategy class for all trading strategies
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import logging


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, connection, trade_manager, config):
        """
        Initialize strategy
        
        Args:
            connection: MT5Connection instance
            trade_manager: TradeManager instance
            config: Configuration object
        """
        self.connection = connection
        self.trade_manager = trade_manager
        self.config = config
        self.logger = logging.getLogger(f"Herald.{self.__class__.__name__}")
        
        # Strategy parameters
        self.symbol = config.get('trading.symbol', 'XAUUSD')
        self.timeframe = self._parse_timeframe(config.get('trading.timeframe', 'H1'))
        self.magic_number = config.get('trading.magic_number', 20241206)
        
        # State tracking
        self.last_signal = None
        self.last_signal_time = None
        
    def _parse_timeframe(self, tf_str: str) -> int:
        """
        Convert timeframe string to MT5 constant
        
        Args:
            tf_str: Timeframe string ('M1', 'M5', 'H1', etc.)
            
        Returns:
            MT5 timeframe constant
        """
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1,
        }
        return timeframe_map.get(tf_str.upper(), mt5.TIMEFRAME_H1)
        
    def get_candles(self, count: int = 500) -> Optional[pd.DataFrame]:
        """
        Fetch historical candles
        
        Args:
            count: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data or None
        """
        try:
            # Ensure symbol is selected
            self.connection.select_symbol(self.symbol)
            
            # Fetch candles
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                self.logger.error(f"Failed to get candles: {mt5.last_error()}")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching candles: {e}", exc_info=True)
            return None
            
    def get_current_price(self) -> Optional[Dict[str, float]]:
        """
        Get current bid/ask prices
        
        Returns:
            Dictionary with 'bid' and 'ask' prices
        """
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                return None
                
            return {
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': tick.ask - tick.bid
            }
            
        except Exception as e:
            self.logger.error(f"Error getting price: {e}")
            return None
            
    @abstractmethod
    def analyze(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Analyze market data and generate signal
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with signal information or None
            Example: {
                'action': 'BUY' or 'SELL',
                'confidence': 0.85,
                'stop_loss': 2010.50,
                'take_profit': 2050.00,
                'reason': 'MA crossover'
            }
        """
        pass
        
    @abstractmethod
    def should_close_position(self, position: Dict[str, Any], df: pd.DataFrame) -> tuple[bool, str]:
        """
        Check if position should be closed
        
        Args:
            position: Position dictionary
            df: Current market data
            
        Returns:
            (should_close, reason) tuple
        """
        pass
        
    def execute(self):
        """
        Main execution method called by bot
        Fetches data, analyzes, and executes trades
        """
        try:
            # Fetch market data
            df = self.get_candles()
            if df is None or len(df) < 50:
                self.logger.warning("Insufficient data for analysis")
                return
                
            # Analyze and get signal
            signal = self.analyze(df)
            
            # Check existing positions
            positions = self.trade_manager.get_positions(self.symbol)
            
            # Manage existing positions
            for position in positions:
                should_close, reason = self.should_close_position(position, df)
                if should_close:
                    self.trade_manager.close_position(position['ticket'], reason=reason)
                    
            # Open new position if signal and no existing positions
            if signal and len(positions) == 0:
                self._execute_signal(signal)
                
        except Exception as e:
            self.logger.error(f"Strategy execution error: {e}", exc_info=True)
            
    def _execute_signal(self, signal: Dict[str, Any]):
        """
        Execute trading signal
        
        Args:
            signal: Signal dictionary from analyze()
        """
        try:
            action = signal['action']
            
            self.logger.info(
                f"Signal: {action} {self.symbol} | "
                f"Confidence: {signal.get('confidence', 0):.2%} | "
                f"Reason: {signal.get('reason', 'N/A')}"
            )
            
            # Open position
            ticket = self.trade_manager.open_position(
                symbol=self.symbol,
                order_type=action,
                stop_loss=signal.get('stop_loss'),
                take_profit=signal.get('take_profit'),
                comment=f"Herald: {signal.get('reason', 'Signal')}"
            )
            
            if ticket:
                self.last_signal = action
                self.last_signal_time = datetime.now()
                self.logger.info(f"Position opened: Ticket #{ticket}")
            else:
                self.logger.warning("Failed to open position")
                
        except Exception as e:
            self.logger.error(f"Error executing signal: {e}", exc_info=True)
            
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range
        
        Args:
            df: DataFrame with OHLCV data
            period: ATR period
            
        Returns:
            Series with ATR values
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
