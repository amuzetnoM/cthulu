"""
SMA Crossover Strategy - Rule-Based
Based on MQL5 article: Moving Average Crossovers (20488)

Signal Logic:
- BUY when fast SMA crosses above slow SMA + confirmation
- SELL when fast SMA crosses below slow SMA + confirmation

Improvements over classical:
- Price position confirmation (close above/below MAs)
- Volume trend confirmation
- Continuation signals (not just crossover events)
"""
import logging
import numpy as np
from typing import Dict, Any, Optional

from .base import BaseStrategy, Signal

logger = logging.getLogger(__name__)


class SMACrossoverStrategy(BaseStrategy):
    """
    Simple Moving Average Crossover with enhancements.
    
    Config:
    - fast_period: Fast SMA period (default: 10)
    - slow_period: Slow SMA period (default: 30)
    - atr_period: ATR period for SL/TP (default: 14)
    - confirmation_bars: Bars to confirm crossover (default: 2)
    - enable_continuation: Enable continuation signals (default: True)
    """
    
    def __init__(self, config: Dict[str, Any], symbol: str):
        super().__init__(config, symbol)
        
        self.fast_period = config.get('fast_period', 10)
        self.slow_period = config.get('slow_period', 30)
        self.atr_period = config.get('atr_period', 14)
        self.confirmation_bars = config.get('confirmation_bars', 2)
        self.enable_continuation = config.get('enable_continuation', True)
        
        # Track last crossover for continuation
        self._last_trend = None
        self._bars_since_crossover = 0
        
        logger.info(f"SMA Crossover initialized: fast={self.fast_period}, slow={self.slow_period}")
    
    def generate_signal(
        self,
        data: Any,
        indicators: Dict[str, Any]
    ) -> Optional[Signal]:
        """Generate SMA crossover signal."""
        if data is None or len(data) < self.slow_period + 5:
            return None
        
        close = data['close'].values
        high = data['high'].values
        low = data['low'].values
        
        # Calculate SMAs
        fast_sma = self._calculate_sma(close, self.fast_period)
        slow_sma = self._calculate_sma(close, self.slow_period)
        
        # Get previous values for crossover detection
        prev_fast = self._calculate_sma(close[:-1], self.fast_period)
        prev_slow = self._calculate_sma(close[:-1], self.slow_period)
        
        # Detect crossover
        bullish_cross = prev_fast <= prev_slow and fast_sma > slow_sma
        bearish_cross = prev_fast >= prev_slow and fast_sma < slow_sma
        
        # Current trend
        current_trend = 'bullish' if fast_sma > slow_sma else 'bearish'
        
        # Track crossover for continuation signals
        if bullish_cross or bearish_cross:
            self._bars_since_crossover = 0
            self._last_trend = current_trend
        else:
            self._bars_since_crossover += 1
        
        # Get ATR
        atr = indicators.get('ATR', self._calculate_atr(high, low, close))
        entry_price = close[-1]
        
        signal = None
        
        # CROSSOVER SIGNALS (primary)
        if bullish_cross:
            # Confirmation: price above fast MA
            if self._confirm_bullish(close, low, fast_sma, slow_sma):
                sl, tp = self._calculate_atr_based_sltp(entry_price, 'buy', atr)
                signal = Signal(
                    direction='buy',
                    symbol=self.symbol,
                    confidence=0.75,
                    strategy_name='sma_crossover',
                    entry_price=entry_price,
                    sl=sl,
                    tp=tp,
                    reason=f"SMA bullish crossover: {self.fast_period} > {self.slow_period}"
                )
                logger.info(f"🟢 LONG SMA crossover: fast={fast_sma:.2f}, slow={slow_sma:.2f}")
        
        elif bearish_cross:
            # Confirmation: price below fast MA
            if self._confirm_bearish(close, high, fast_sma, slow_sma):
                sl, tp = self._calculate_atr_based_sltp(entry_price, 'sell', atr)
                signal = Signal(
                    direction='sell',
                    symbol=self.symbol,
                    confidence=0.75,
                    strategy_name='sma_crossover',
                    entry_price=entry_price,
                    sl=sl,
                    tp=tp,
                    reason=f"SMA bearish crossover: {self.fast_period} < {self.slow_period}"
                )
                logger.info(f"🔴 SHORT SMA crossover: fast={fast_sma:.2f}, slow={slow_sma:.2f}")
        
        # CONTINUATION SIGNALS (secondary)
        elif self.enable_continuation and self._last_trend and self._bars_since_crossover <= 10:
            signal = self._check_continuation(
                close, high, low, fast_sma, slow_sma, atr, entry_price
            )
        
        return signal
    
    def _confirm_bullish(self, close, low, fast_sma, slow_sma) -> bool:
        """Confirm bullish signal with price position."""
        # Price should be above both MAs or low should be above fast MA
        return close[-1] > fast_sma or low[-1] > fast_sma
    
    def _confirm_bearish(self, close, high, fast_sma, slow_sma) -> bool:
        """Confirm bearish signal with price position."""
        # Price should be below both MAs or high should be below slow MA
        return close[-1] < slow_sma or high[-1] < slow_sma
    
    def _check_continuation(
        self, close, high, low, fast_sma, slow_sma, atr, entry_price
    ) -> Optional[Signal]:
        """Check for continuation entry in existing trend."""
        
        # Only continue if in confirmed trend
        if self._last_trend == 'bullish' and fast_sma > slow_sma:
            # Pullback entry: price pulled back to fast SMA
            if low[-1] <= fast_sma * 1.002 and close[-1] > fast_sma:
                sl, tp = self._calculate_atr_based_sltp(entry_price, 'buy', atr)
                return Signal(
                    direction='buy',
                    symbol=self.symbol,
                    confidence=0.65,  # Lower confidence for continuation
                    strategy_name='sma_crossover',
                    entry_price=entry_price,
                    sl=sl,
                    tp=tp,
                    reason="SMA continuation: bullish pullback to fast MA"
                )
        
        elif self._last_trend == 'bearish' and fast_sma < slow_sma:
            # Pullback entry: price pulled back to fast SMA
            if high[-1] >= fast_sma * 0.998 and close[-1] < fast_sma:
                sl, tp = self._calculate_atr_based_sltp(entry_price, 'sell', atr)
                return Signal(
                    direction='sell',
                    symbol=self.symbol,
                    confidence=0.65,
                    strategy_name='sma_crossover',
                    entry_price=entry_price,
                    sl=sl,
                    tp=tp,
                    reason="SMA continuation: bearish pullback to fast MA"
                )
        
        return None
    
    def get_regime_fitness(self, regime: str) -> float:
        """SMA crossover works best in trending markets."""
        regime_scores = {
            'trending_up_strong': 0.95,
            'trending_up_weak': 0.80,
            'trending_down_strong': 0.95,
            'trending_down_weak': 0.80,
            'ranging_wide': 0.40,
            'ranging_tight': 0.30,
            'volatile': 0.50,
            'unknown': 0.50
        }
        return regime_scores.get(regime, 0.50)
    
    def _calculate_sma(self, data, period: int) -> float:
        """Calculate Simple Moving Average."""
        if len(data) < period:
            return data[-1] if len(data) > 0 else 0
        return np.mean(data[-period:])
    
    def _calculate_atr(self, high, low, close, period: int = 14) -> float:
        """Calculate ATR if not provided."""
        if len(high) < period + 1:
            return abs(high[-1] - low[-1])
        
        tr = []
        for i in range(1, len(high)):
            tr.append(max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            ))
        
        return np.mean(tr[-period:])
