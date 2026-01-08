"""
Exponential Moving Average Crossover Strategy

High-speed crossover strategy using EMA for faster reaction to price changes.
Optimized for day trading with quicker signals than SMA.
"""

import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime

from cthulu.strategy.base import Strategy, Signal, SignalType


class EmaCrossover(Strategy):
    """
    Exponential Moving Average Crossover Strategy.
    
    Generates faster signals than SMA crossover due to EMA's exponential weighting.
    Ideal for day trading and scalping with quicker response to price movements.
    
    Configuration:
        fast_period: Fast EMA period (default: 9)
        slow_period: Slow EMA period (default: 21)
        atr_period: ATR period for stop loss (default: 14)
        atr_multiplier: ATR multiplier for SL (default: 1.5, tighter than SMA)
        risk_reward_ratio: Risk/reward ratio (default: 2.5)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize EMA crossover strategy."""
        super().__init__("ema_crossover", config)
        
        # Strategy parameters - optimized for day trading
        self.fast_period = config.get('params', {}).get('fast_period', 9)
        self.slow_period = config.get('params', {}).get('slow_period', 21)
        self.atr_period = config.get('params', {}).get('atr_period', 14)
        self.atr_multiplier = config.get('params', {}).get('atr_multiplier', 1.5)
        self.risk_reward_ratio = config.get('params', {}).get('risk_reward_ratio', 2.5)
        
        # State
        self._state = {
            'last_signal': None,
            'last_crossover': None,
            'ema_fast': None,
            'ema_slow': None,
            'atr': None
        }
        
        self.logger.info(
            f"EMA Crossover initialized: fast={self.fast_period}, "
            f"slow={self.slow_period}, atr={self.atr_period}"
        )
        
    def on_bar(self, bar: pd.Series) -> Optional[Signal]:
        """
        Process new bar and check for crossover.
        
        Args:
            bar: Latest bar with indicators
            
        Returns:
            Signal if crossover detected, None otherwise
        """
        # Need EMA values - try multiple column naming conventions
        ema_fast_col = f'ema_{self.fast_period}'
        ema_slow_col = f'ema_{self.slow_period}'
        
        # Fallback to generic names if specific not found
        if ema_fast_col not in bar and 'ema_fast' in bar:
            ema_fast_col = 'ema_fast'
        if ema_slow_col not in bar and 'ema_slow' in bar:
            ema_slow_col = 'ema_slow'
        
        if ema_fast_col not in bar or ema_slow_col not in bar:
            self.logger.debug(f"EMA indicators not found - looking for: {ema_fast_col}, {ema_slow_col}")
            return None
            
        if 'atr' not in bar:
            self.logger.warning("ATR indicator not found in bar data")
            return None
            
        # Get current values
        ema_fast = bar[ema_fast_col]
        ema_slow = bar[ema_slow_col]
        atr = bar['atr']
        close = bar['close']
        
        # Update state
        prev_fast = self._state['ema_fast']
        prev_slow = self._state['ema_slow']
        
        self._state['ema_fast'] = ema_fast
        self._state['ema_slow'] = ema_slow
        self._state['atr'] = atr
        
        # Need previous values to detect crossover
        if prev_fast is None or prev_slow is None:
            return None
            
        # Check for bullish crossover
        if prev_fast <= prev_slow and ema_fast > ema_slow:
            signal = self._create_long_signal(close, atr, bar)
            if self.validate_signal(signal):
                self._state['last_signal'] = SignalType.LONG
                self._state['last_crossover'] = datetime.now()
                return signal
                
        # Check for bearish crossover
        elif prev_fast >= prev_slow and ema_fast < ema_slow:
            signal = self._create_short_signal(close, atr, bar)
            if self.validate_signal(signal):
                self._state['last_signal'] = SignalType.SHORT
                self._state['last_crossover'] = datetime.now()
                return signal
                
        return None
        
    def _create_long_signal(self, price: float, atr: float, bar: pd.Series) -> Signal:
        """Create LONG signal with calculated SL/TP."""
        # Tighter stop loss for day trading
        stop_loss = price - (atr * self.atr_multiplier)
        
        # Calculate take profit
        risk = price - stop_loss
        take_profit = price + (risk * self.risk_reward_ratio)
        
        return Signal(
            id=self.generate_signal_id(),
            timestamp=bar.name,
            symbol=self.config.get('params', {}).get('symbol', 'UNKNOWN'),
            timeframe=self.config.get('timeframe', '1H'),
            side=SignalType.LONG,
            action='BUY',
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=0.75,  # Higher confidence due to faster response
            reason=f"EMA crossover: {self.fast_period} crossed above {self.slow_period}",
            metadata={
                'ema_fast': float(self._state['ema_fast']),
                'ema_slow': float(self._state['ema_slow']),
                'atr': float(atr),
                'risk': float(risk),
                'reward': float(risk * self.risk_reward_ratio),
                'strategy_type': 'day_trading'
            }
        )
        
    def _create_short_signal(self, price: float, atr: float, bar: pd.Series) -> Signal:
        """Create SHORT signal with calculated SL/TP."""
        # Tighter stop loss for day trading
        stop_loss = price + (atr * self.atr_multiplier)
        
        # Calculate take profit
        risk = stop_loss - price
        take_profit = price - (risk * self.risk_reward_ratio)
        
        return Signal(
            id=self.generate_signal_id(),
            timestamp=bar.name,
            symbol=self.config.get('params', {}).get('symbol', 'UNKNOWN'),
            timeframe=self.config.get('timeframe', '1H'),
            side=SignalType.SHORT,
            action='SELL',
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=0.75,  # Higher confidence due to faster response
            reason=f"EMA crossover: {self.fast_period} crossed below {self.slow_period}",
            metadata={
                'ema_fast': float(self._state['ema_fast']),
                'ema_slow': float(self._state['ema_slow']),
                'atr': float(atr),
                'risk': float(risk),
                'reward': float(risk * self.risk_reward_ratio),
                'strategy_type': 'day_trading'
            }
        )




