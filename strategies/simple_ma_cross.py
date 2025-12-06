"""
Simple Moving Average Crossover Strategy
Phase 1 implementation - Foundation
"""

import pandas as pd
from typing import Optional, Dict, Any
from strategies.base_strategy import BaseStrategy


class SimpleMovingAverageCross(BaseStrategy):
    """
    Simple MA crossover strategy:
    - BUY when fast MA crosses above slow MA
    - SELL when fast MA crosses below slow MA
    - Close on opposite signal
    """
    
    def __init__(self, connection, trade_manager, config):
        """Initialize MA crossover strategy"""
        super().__init__(connection, trade_manager, config)
        
        # Strategy parameters
        self.fast_period = config.get('strategy.params.fast_period', 20)
        self.slow_period = config.get('strategy.params.slow_period', 50)
        self.confirmation_candles = config.get('strategy.params.confirmation_candles', 1)
        
        # Filters
        self.min_atr_multiple = config.get('strategy.filters.min_atr_multiple', 1.5)
        self.max_spread = config.get('strategy.filters.max_spread', 50)
        
        self.logger.info(
            f"MA Crossover initialized: Fast={self.fast_period}, Slow={self.slow_period}"
        )
        
    def analyze(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Analyze market data for MA crossover signals
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Signal dictionary or None
        """
        try:
            # Calculate moving averages
            df['ma_fast'] = df['close'].rolling(window=self.fast_period).mean()
            df['ma_slow'] = df['close'].rolling(window=self.slow_period).mean()
            
            # Calculate ATR for stop loss
            df['atr'] = self.calculate_atr(df, period=14)
            
            # Remove NaN values
            df = df.dropna()
            
            if len(df) < 2:
                return None
                
            # Get current and previous values
            current = df.iloc[-1]
            previous = df.iloc[-2]
            
            # Check for crossover
            bullish_cross = (
                previous['ma_fast'] <= previous['ma_slow'] and
                current['ma_fast'] > current['ma_slow']
            )
            
            bearish_cross = (
                previous['ma_fast'] >= previous['ma_slow'] and
                current['ma_fast'] < current['ma_slow']
            )
            
            # Apply filters
            if not self._apply_filters(current):
                return None
                
            # Generate signal
            if bullish_cross:
                return self._create_buy_signal(current)
            elif bearish_cross:
                return self._create_sell_signal(current)
                
            return None
            
        except Exception as e:
            self.logger.error(f"Analysis error: {e}", exc_info=True)
            return None
            
    def _apply_filters(self, current: pd.Series) -> bool:
        """
        Apply trading filters
        
        Args:
            current: Current candle data
            
        Returns:
            True if filters pass
        """
        # Check spread
        prices = self.get_current_price()
        if prices:
            spread = prices['spread']
            symbol_info = self.connection.get_symbol_info(self.symbol)
            spread_points = spread / symbol_info['point']
            
            if spread_points > self.max_spread:
                self.logger.debug(f"Spread too wide: {spread_points:.1f} points")
                return False
                
        # Check ATR (volatility)
        atr = current['atr']
        if pd.isna(atr) or atr <= 0:
            self.logger.debug("Invalid ATR value")
            return False
            
        # Check trading hours if configured
        trading_hours = self.config.get('strategy.filters.trading_hours')
        if trading_hours:
            from datetime import datetime
            current_hour = datetime.utcnow().hour
            start_hour = trading_hours.get('start', 0)
            end_hour = trading_hours.get('end', 23)
            
            if not (start_hour <= current_hour <= end_hour):
                self.logger.debug(f"Outside trading hours: {current_hour}:00 UTC")
                return False
                
        return True
        
    def _create_buy_signal(self, current: pd.Series) -> Dict[str, Any]:
        """
        Create BUY signal with SL/TP
        
        Args:
            current: Current candle data
            
        Returns:
            Signal dictionary
        """
        entry_price = current['close']
        atr = current['atr']
        
        # Calculate stop loss (2 ATR below entry)
        stop_loss = self.trade_manager.risk_manager.calculate_stop_loss(
            symbol=self.symbol,
            entry_price=entry_price,
            order_type='BUY',
            atr=atr,
            atr_multiple=2.0
        )
        
        # Calculate take profit (1:2 risk/reward)
        take_profit = self.trade_manager.risk_manager.calculate_take_profit(
            symbol=self.symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            order_type='BUY',
            risk_reward_ratio=2.0
        )
        
        return {
            'action': 'BUY',
            'confidence': 0.7,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': f'MA Crossover (Fast={self.fast_period} crossed above Slow={self.slow_period})',
            'indicators': {
                'ma_fast': current['ma_fast'],
                'ma_slow': current['ma_slow'],
                'atr': atr
            }
        }
        
    def _create_sell_signal(self, current: pd.Series) -> Dict[str, Any]:
        """
        Create SELL signal with SL/TP
        
        Args:
            current: Current candle data
            
        Returns:
            Signal dictionary
        """
        entry_price = current['close']
        atr = current['atr']
        
        # Calculate stop loss (2 ATR above entry)
        stop_loss = self.trade_manager.risk_manager.calculate_stop_loss(
            symbol=self.symbol,
            entry_price=entry_price,
            order_type='SELL',
            atr=atr,
            atr_multiple=2.0
        )
        
        # Calculate take profit (1:2 risk/reward)
        take_profit = self.trade_manager.risk_manager.calculate_take_profit(
            symbol=self.symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            order_type='SELL',
            risk_reward_ratio=2.0
        )
        
        return {
            'action': 'SELL',
            'confidence': 0.7,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': f'MA Crossover (Fast={self.fast_period} crossed below Slow={self.slow_period})',
            'indicators': {
                'ma_fast': current['ma_fast'],
                'ma_slow': current['ma_slow'],
                'atr': atr
            }
        }
        
    def should_close_position(self, position: Dict[str, Any], df: pd.DataFrame) -> tuple[bool, str]:
        """
        Check if position should be closed on opposite signal
        
        Args:
            position: Position dictionary
            df: Current market data
            
        Returns:
            (should_close, reason) tuple
        """
        try:
            # Calculate MAs
            df['ma_fast'] = df['close'].rolling(window=self.fast_period).mean()
            df['ma_slow'] = df['close'].rolling(window=self.slow_period).mean()
            df = df.dropna()
            
            if len(df) < 2:
                return False, ""
                
            current = df.iloc[-1]
            previous = df.iloc[-2]
            
            position_type = position['type']
            
            # Close BUY position on bearish cross
            if position_type == 'BUY':
                bearish_cross = (
                    previous['ma_fast'] >= previous['ma_slow'] and
                    current['ma_fast'] < current['ma_slow']
                )
                if bearish_cross:
                    return True, "MA Crossover - Bearish signal"
                    
            # Close SELL position on bullish cross
            elif position_type == 'SELL':
                bullish_cross = (
                    previous['ma_fast'] <= previous['ma_slow'] and
                    current['ma_fast'] > current['ma_slow']
                )
                if bullish_cross:
                    return True, "MA Crossover - Bullish signal"
                    
            return False, ""
            
        except Exception as e:
            self.logger.error(f"Error checking position closure: {e}")
            return False, ""
