"""
Scalping Strategy

Ultra-fast strategy optimized for M1/M5 timeframes with quick entries and exits.
Uses tight stops and quick profit targets for high-frequency trading.
"""

import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime

from herald.strategy.base import Strategy, Signal, SignalType


class ScalpingStrategy(Strategy):
    """
    Scalping Strategy for M1/M5 timeframes.
    
    Designed for rapid-fire trades with tight stops and quick profits.
    Uses multiple fast indicators and strict entry conditions.
    
    Configuration:
        fast_ema: Fast EMA period (default: 5)
        slow_ema: Slow EMA period (default: 10)
        rsi_period: RSI period (default: 7)
        rsi_oversold: RSI oversold level (default: 25)
        rsi_overbought: RSI overbought level (default: 75)
        atr_multiplier: ATR multiplier for SL (default: 1.0, very tight)
        risk_reward_ratio: Risk/reward ratio (default: 2.0)
        spread_limit_pips: Max spread for entry (default: 2.0)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize scalping strategy."""
        super().__init__("scalping", config)
        
        # Strategy parameters - optimized for scalping
        self.fast_ema = config.get('params', {}).get('fast_ema', 5)
        self.slow_ema = config.get('params', {}).get('slow_ema', 10)
        self.rsi_period = config.get('params', {}).get('rsi_period', 7)
        self.rsi_oversold = config.get('params', {}).get('rsi_oversold', 25)
        self.rsi_overbought = config.get('params', {}).get('rsi_overbought', 75)
        self.atr_multiplier = config.get('params', {}).get('atr_multiplier', 1.0)
        self.risk_reward_ratio = config.get('params', {}).get('risk_reward_ratio', 2.0)
        self.spread_limit_pips = config.get('params', {}).get('spread_limit_pips', 2.0)
        
        # State
        self._state = {
            'last_signal': None,
            'last_trade_time': None,
            'ema_fast': None,
            'ema_slow': None
        }
        
        self.logger.info(
            f"Scalping Strategy initialized: fast_ema={self.fast_ema}, "
            f"slow_ema={self.slow_ema}, rsi_oversold={self.rsi_oversold}"
        )
        
    def on_tick(self, tick: Dict[str, Any]) -> Optional[Signal]:
        """
        Process tick data for ultra-fast scalping.
        
        Args:
            tick: Tick data with bid/ask prices
            
        Returns:
            Signal if conditions met, None otherwise
        """
        # For scalping, we prefer tick-level data
        # This method can be used for sub-bar trading
        return None  # Implement tick-based logic if needed
        
    def on_bar(self, bar: pd.Series) -> Optional[Signal]:
        """
        Process new bar for scalping opportunities.
        
        Args:
            bar: Latest bar with indicators
            
        Returns:
            Signal if scalping opportunity found, None otherwise
        """
        # Check required indicators
        ema_fast_col = f'ema_{self.fast_ema}'
        ema_slow_col = f'ema_{self.slow_ema}'
        
        if ema_fast_col not in bar or ema_slow_col not in bar:
            self.logger.warning("EMA indicators not found")
            return None
        
        # Try to find RSI with specified period, fallback to default
        rsi_col = f'rsi_{self.rsi_period}' if f'rsi_{self.rsi_period}' in bar else 'rsi'
        if rsi_col not in bar or 'atr' not in bar:
            self.logger.warning("RSI or ATR not found")
            return None
            
        # Get values
        ema_fast = bar[ema_fast_col]
        ema_slow = bar[ema_slow_col]
        rsi = bar[rsi_col]
        atr = bar['atr']
        close = bar['close']
        
        # Check spread if available
        spread = bar.get('spread', 0)
        pip_value = bar.get('pip_value', 0.0001)
        spread_pips = spread / pip_value if pip_value > 0 else 0
        
        if spread_pips > self.spread_limit_pips:
            self.logger.debug(f"Spread too high: {spread_pips:.1f} pips")
            return None
        
        # Update state
        prev_fast = self._state['ema_fast']
        prev_slow = self._state['ema_slow']
        
        self._state['ema_fast'] = ema_fast
        self._state['ema_slow'] = ema_slow
        
        # Need previous values
        if prev_fast is None or prev_slow is None:
            return None
        
        # Bullish scalp: Fast EMA crosses above slow + RSI oversold recovery
        if (prev_fast <= prev_slow and ema_fast > ema_slow and 
            rsi > self.rsi_oversold and rsi < 60):
            
            signal = self._create_long_signal(close, atr, bar)
            if self.validate_signal(signal):
                self._state['last_signal'] = SignalType.LONG
                self._state['last_trade_time'] = datetime.now()
                return signal
                
        # Bearish scalp: Fast EMA crosses below slow + RSI overbought recovery
        elif (prev_fast >= prev_slow and ema_fast < ema_slow and 
              rsi < self.rsi_overbought and rsi > 40):
            
            signal = self._create_short_signal(close, atr, bar)
            if self.validate_signal(signal):
                self._state['last_signal'] = SignalType.SHORT
                self._state['last_trade_time'] = datetime.now()
                return signal
                
        return None
        
    def _create_long_signal(self, price: float, atr: float, bar: pd.Series) -> Signal:
        """Create LONG scalp signal."""
        # Very tight stop for scalping
        stop_loss = price - (atr * self.atr_multiplier)
        
        # Quick profit target
        risk = price - stop_loss
        take_profit = price + (risk * self.risk_reward_ratio)
        
        return Signal(
            id=self.generate_signal_id(),
            timestamp=bar.name,
            symbol=self.config.get('params', {}).get('symbol', 'UNKNOWN'),
            timeframe=self.config.get('timeframe', 'M5'),
            side=SignalType.LONG,
            action='BUY',
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=0.85,  # High confidence for scalping
            reason=f"Bullish scalp: EMA{self.fast_ema} > EMA{self.slow_ema}, RSI recovery",
            metadata={
                'ema_fast': float(self._state['ema_fast']),
                'ema_slow': float(self._state['ema_slow']),
                'rsi': float(bar['rsi']),
                'atr': float(atr),
                'risk_pips': float(risk / bar.get('pip_value', 0.0001)),
                'strategy_type': 'scalping'
            }
        )
        
    def _create_short_signal(self, price: float, atr: float, bar: pd.Series) -> Signal:
        """Create SHORT scalp signal."""
        # Very tight stop for scalping
        stop_loss = price + (atr * self.atr_multiplier)
        
        # Quick profit target
        risk = stop_loss - price
        take_profit = price - (risk * self.risk_reward_ratio)
        
        return Signal(
            id=self.generate_signal_id(),
            timestamp=bar.name,
            symbol=self.config.get('params', {}).get('symbol', 'UNKNOWN'),
            timeframe=self.config.get('timeframe', 'M5'),
            side=SignalType.SHORT,
            action='SELL',
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=0.85,  # High confidence for scalping
            reason=f"Bearish scalp: EMA{self.fast_ema} < EMA{self.slow_ema}, RSI recovery",
            metadata={
                'ema_fast': float(self._state['ema_fast']),
                'ema_slow': float(self._state['ema_slow']),
                'rsi': float(bar['rsi']),
                'atr': float(atr),
                'risk_pips': float(risk / bar.get('pip_value', 0.0001)),
                'strategy_type': 'scalping'
            }
        )
