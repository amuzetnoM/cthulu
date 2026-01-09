"""
EMA Crossover Strategy - Rule-Based
Exponential Moving Average crossover with momentum confirmation.

Signal Logic:
- BUY when fast EMA crosses above slow EMA with RSI confirmation
- SELL when fast EMA crosses below slow EMA with RSI confirmation

Enhancements:
- MACD histogram confirmation
- RSI not overbought/oversold filter
- Continuation mode for trend riding
"""
import logging
import numpy as np
from typing import Dict, Any, Optional

from .base import BaseStrategy, Signal

logger = logging.getLogger(__name__)


class EMACrossoverStrategy(BaseStrategy):
    """
    Exponential Moving Average Crossover with momentum filters.
    
    Config:
    - fast_period: Fast EMA period (default: 12)
    - slow_period: Slow EMA period (default: 26)
    - signal_period: Signal line period (default: 9)
    - rsi_overbought: RSI overbought level (default: 70)
    - rsi_oversold: RSI oversold level (default: 30)
    """
    
    def __init__(self, config: Dict[str, Any], symbol: str):
        super().__init__(config, symbol)
        
        self.fast_period = config.get('fast_period', 12)
        self.slow_period = config.get('slow_period', 26)
        self.signal_period = config.get('signal_period', 9)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        
        self._last_trend = None
        self._bars_since_crossover = 0
        
        logger.info(f"EMA Crossover initialized: fast={self.fast_period}, slow={self.slow_period}")
    
    def generate_signal(
        self,
        data: Any,
        indicators: Dict[str, Any]
    ) -> Optional[Signal]:
        """Generate EMA crossover signal with momentum confirmation."""
        if data is None or len(data) < self.slow_period + 10:
            return None
        
        close = data['close'].values
        high = data['high'].values
        low = data['low'].values
        
        # Calculate EMAs
        fast_ema = self._calculate_ema(close, self.fast_period)
        slow_ema = self._calculate_ema(close, self.slow_period)
        
        # Previous values
        prev_fast = self._calculate_ema(close[:-1], self.fast_period)
        prev_slow = self._calculate_ema(close[:-1], self.slow_period)
        
        # Detect crossover
        bullish_cross = prev_fast <= prev_slow and fast_ema > slow_ema
        bearish_cross = prev_fast >= prev_slow and fast_ema < slow_ema
        
        # Current trend
        current_trend = 'bullish' if fast_ema > slow_ema else 'bearish'
        
        # Track crossover
        if bullish_cross or bearish_cross:
            self._bars_since_crossover = 0
            self._last_trend = current_trend
        else:
            self._bars_since_crossover += 1
        
        # Get indicators
        rsi = indicators.get('RSI', 50)
        atr = indicators.get('ATR', self._calculate_atr(high, low, close))
        macd_data = indicators.get('MACD', {})
        macd_hist = macd_data.get('histogram', 0) if isinstance(macd_data, dict) else 0
        
        entry_price = close[-1]
        signal = None
        
        # BULLISH CROSSOVER
        if bullish_cross:
            # Confirmation: RSI not overbought, MACD histogram positive
            if rsi < self.rsi_overbought and (macd_hist >= 0 or macd_hist is None):
                confidence = self._calculate_confidence(rsi, macd_hist, 'buy')
                sl, tp = self._calculate_atr_based_sltp(entry_price, 'buy', atr)
                
                signal = Signal(
                    direction='buy',
                    symbol=self.symbol,
                    confidence=confidence,
                    strategy_name='ema_crossover',
                    entry_price=entry_price,
                    sl=sl,
                    tp=tp,
                    reason=f"EMA bullish cross: {self.fast_period} > {self.slow_period}, RSI={rsi:.1f}"
                )
                logger.info(f"🟢 LONG EMA crossover: fast={fast_ema:.2f}, slow={slow_ema:.2f}, RSI={rsi:.1f}")
        
        # BEARISH CROSSOVER
        elif bearish_cross:
            # Confirmation: RSI not oversold, MACD histogram negative
            if rsi > self.rsi_oversold and (macd_hist <= 0 or macd_hist is None):
                confidence = self._calculate_confidence(rsi, macd_hist, 'sell')
                sl, tp = self._calculate_atr_based_sltp(entry_price, 'sell', atr)
                
                signal = Signal(
                    direction='sell',
                    symbol=self.symbol,
                    confidence=confidence,
                    strategy_name='ema_crossover',
                    entry_price=entry_price,
                    sl=sl,
                    tp=tp,
                    reason=f"EMA bearish cross: {self.fast_period} < {self.slow_period}, RSI={rsi:.1f}"
                )
                logger.info(f"🔴 SHORT EMA crossover: fast={fast_ema:.2f}, slow={slow_ema:.2f}, RSI={rsi:.1f}")
        
        # CONTINUATION (trend following)
        elif self._last_trend and self._bars_since_crossover <= 15:
            signal = self._check_continuation(
                close, fast_ema, slow_ema, rsi, atr, entry_price
            )
        
        return signal
    
    def _calculate_confidence(self, rsi: float, macd_hist: float, direction: str) -> float:
        """Calculate signal confidence based on indicators."""
        base_confidence = 0.70
        
        # RSI boost/penalty
        if direction == 'buy':
            if rsi < 40:  # Oversold - strong for buys
                base_confidence += 0.10
            elif rsi > 60:  # Getting overbought - penalty
                base_confidence -= 0.05
        else:
            if rsi > 60:  # Overbought - strong for sells
                base_confidence += 0.10
            elif rsi < 40:  # Getting oversold - penalty
                base_confidence -= 0.05
        
        # MACD histogram alignment
        if macd_hist is not None:
            if (direction == 'buy' and macd_hist > 0) or (direction == 'sell' and macd_hist < 0):
                base_confidence += 0.05
        
        return min(0.95, max(0.50, base_confidence))
    
    def _check_continuation(
        self, close, fast_ema, slow_ema, rsi, atr, entry_price
    ) -> Optional[Signal]:
        """Check for continuation entry."""
        
        if self._last_trend == 'bullish' and fast_ema > slow_ema:
            # RSI pullback from overbought
            if 45 < rsi < 60:
                sl, tp = self._calculate_atr_based_sltp(entry_price, 'buy', atr)
                return Signal(
                    direction='buy',
                    symbol=self.symbol,
                    confidence=0.60,
                    strategy_name='ema_crossover',
                    entry_price=entry_price,
                    sl=sl,
                    tp=tp,
                    reason="EMA continuation: bullish trend RSI pullback"
                )
        
        elif self._last_trend == 'bearish' and fast_ema < slow_ema:
            # RSI pullback from oversold
            if 40 < rsi < 55:
                sl, tp = self._calculate_atr_based_sltp(entry_price, 'sell', atr)
                return Signal(
                    direction='sell',
                    symbol=self.symbol,
                    confidence=0.60,
                    strategy_name='ema_crossover',
                    entry_price=entry_price,
                    sl=sl,
                    tp=tp,
                    reason="EMA continuation: bearish trend RSI pullback"
                )
        
        return None
    
    def get_regime_fitness(self, regime: str) -> float:
        """EMA crossover works well in trending and moderately ranging markets."""
        regime_scores = {
            'trending_up_strong': 0.95,
            'trending_up_weak': 0.85,
            'trending_down_strong': 0.95,
            'trending_down_weak': 0.85,
            'ranging_wide': 0.50,
            'ranging_tight': 0.35,
            'volatile': 0.55,
            'unknown': 0.55
        }
        return regime_scores.get(regime, 0.55)
    
    def _calculate_ema(self, data, period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(data) < period:
            return data[-1] if len(data) > 0 else 0
        
        multiplier = 2 / (period + 1)
        ema = np.mean(data[:period])  # SMA for initial
        
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
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
