"""
Scalping Strategy - Rule-Based
Fast entries based on RSI divergence and EMA alignment.

Signal Logic:
- BUY when RSI oversold + price above short EMA + EMA alignment
- SELL when RSI overbought + price below short EMA + EMA alignment

Designed for quick entries with tight risk management.
"""
import logging
import numpy as np
from typing import Dict, Any, Optional

from .base import BaseStrategy, Signal

logger = logging.getLogger(__name__)


class ScalpingStrategy(BaseStrategy):
    """
    Scalping strategy with RSI and EMA filters.
    
    Config:
    - fast_ema: Fast EMA period (default: 5)
    - slow_ema: Slow EMA period (default: 10)
    - rsi_period: RSI period (default: 7)
    - rsi_oversold: Oversold threshold (default: 25)
    - rsi_overbought: Overbought threshold (default: 75)
    - atr_multiplier: ATR multiplier for SL (default: 1.0)
    """
    
    def __init__(self, config: Dict[str, Any], symbol: str):
        super().__init__(config, symbol)
        
        self.fast_ema = config.get('fast_ema', 5)
        self.slow_ema = config.get('slow_ema', 10)
        self.rsi_period = config.get('rsi_period', 7)
        self.rsi_oversold = config.get('rsi_oversold', 25)
        self.rsi_overbought = config.get('rsi_overbought', 75)
        self.atr_multiplier = config.get('atr_multiplier', 1.0)
        
        # Scalping-specific: tight SL/TP
        self.sl_atr_mult = 1.0
        self.tp_atr_mult = 1.5  # Tighter R:R for scalping
        
        logger.info(f"Scalping initialized: fast_ema={self.fast_ema}, slow_ema={self.slow_ema}, "
                   f"rsi_oversold={self.rsi_oversold}, rsi_overbought={self.rsi_overbought}")
    
    def generate_signal(
        self,
        data: Any,
        indicators: Dict[str, Any]
    ) -> Optional[Signal]:
        """Generate scalping signal."""
        if data is None or len(data) < self.slow_ema + 10:
            return None
        
        close = data['close'].values
        high = data['high'].values
        low = data['low'].values
        
        # Calculate EMAs
        fast = self._calculate_ema(close, self.fast_ema)
        slow = self._calculate_ema(close, self.slow_ema)
        
        # Get RSI (use provided or calculate)
        rsi = indicators.get('RSI')
        if rsi is None:
            rsi = self._calculate_rsi(close, self.rsi_period)
        
        # Get ATR
        atr = indicators.get('ATR', self._calculate_atr(high, low, close))
        
        entry_price = close[-1]
        signal = None
        
        # OVERSOLD + BULLISH ALIGNMENT
        if rsi <= self.rsi_oversold:
            # Price above fast EMA and fast above slow (trend confirmation)
            if close[-1] > fast and fast > slow:
                confidence = self._calculate_confidence(rsi, 'buy')
                sl, tp = self._calculate_scalp_sltp(entry_price, 'buy', atr)
                
                signal = Signal(
                    direction='buy',
                    symbol=self.symbol,
                    confidence=confidence,
                    strategy_name='scalping',
                    entry_price=entry_price,
                    sl=sl,
                    tp=tp,
                    reason=f"Scalp BUY: RSI oversold ({rsi:.1f}), EMA alignment"
                )
                logger.info(f"🟢 SCALP LONG: RSI={rsi:.1f}, EMA={fast:.2f}/{slow:.2f}")
        
        # OVERBOUGHT + BEARISH ALIGNMENT
        elif rsi >= self.rsi_overbought:
            # Price below fast EMA and fast below slow (trend confirmation)
            if close[-1] < fast and fast < slow:
                confidence = self._calculate_confidence(rsi, 'sell')
                sl, tp = self._calculate_scalp_sltp(entry_price, 'sell', atr)
                
                signal = Signal(
                    direction='sell',
                    symbol=self.symbol,
                    confidence=confidence,
                    strategy_name='scalping',
                    entry_price=entry_price,
                    sl=sl,
                    tp=tp,
                    reason=f"Scalp SELL: RSI overbought ({rsi:.1f}), EMA alignment"
                )
                logger.info(f"🔴 SCALP SHORT: RSI={rsi:.1f}, EMA={fast:.2f}/{slow:.2f}")
        
        # CONTRARIAN SCALP (extreme RSI)
        elif rsi <= 20 or rsi >= 80:
            signal = self._check_contrarian_scalp(
                close, fast, slow, rsi, atr, entry_price
            )
        
        return signal
    
    def _check_contrarian_scalp(
        self, close, fast, slow, rsi, atr, entry_price
    ) -> Optional[Signal]:
        """Check for contrarian scalp on extreme RSI."""
        
        # Extreme oversold - quick bounce play
        if rsi <= 20:
            sl, tp = self._calculate_scalp_sltp(entry_price, 'buy', atr)
            return Signal(
                direction='buy',
                symbol=self.symbol,
                confidence=0.60,
                strategy_name='scalping',
                entry_price=entry_price,
                sl=sl,
                tp=tp,
                reason=f"Contrarian scalp: extreme oversold RSI={rsi:.1f}"
            )
        
        # Extreme overbought - quick fade play
        elif rsi >= 80:
            sl, tp = self._calculate_scalp_sltp(entry_price, 'sell', atr)
            return Signal(
                direction='sell',
                symbol=self.symbol,
                confidence=0.60,
                strategy_name='scalping',
                entry_price=entry_price,
                sl=sl,
                tp=tp,
                reason=f"Contrarian scalp: extreme overbought RSI={rsi:.1f}"
            )
        
        return None
    
    def _calculate_scalp_sltp(self, entry_price: float, direction: str, atr: float) -> tuple:
        """Calculate tight SL/TP for scalping."""
        sl_distance = atr * self.sl_atr_mult
        tp_distance = atr * self.tp_atr_mult
        
        if direction == 'buy':
            sl = entry_price - sl_distance
            tp = entry_price + tp_distance
        else:
            sl = entry_price + sl_distance
            tp = entry_price - tp_distance
        
        return sl, tp
    
    def _calculate_confidence(self, rsi: float, direction: str) -> float:
        """Calculate confidence based on RSI extremity."""
        base = 0.70
        
        if direction == 'buy':
            # More oversold = higher confidence
            if rsi <= 15:
                return 0.85
            elif rsi <= 20:
                return 0.80
            elif rsi <= 25:
                return 0.75
        else:
            # More overbought = higher confidence
            if rsi >= 85:
                return 0.85
            elif rsi >= 80:
                return 0.80
            elif rsi >= 75:
                return 0.75
        
        return base
    
    def get_regime_fitness(self, regime: str) -> float:
        """Scalping works best in ranging/tight markets."""
        regime_scores = {
            'trending_up_strong': 0.50,
            'trending_up_weak': 0.70,
            'trending_down_strong': 0.50,
            'trending_down_weak': 0.70,
            'ranging_wide': 0.85,
            'ranging_tight': 0.95,
            'volatile': 0.40,
            'unknown': 0.60
        }
        return regime_scores.get(regime, 0.60)
    
    def _calculate_ema(self, data, period: int) -> float:
        """Calculate EMA."""
        if len(data) < period:
            return data[-1] if len(data) > 0 else 0
        
        multiplier = 2 / (period + 1)
        ema = np.mean(data[:period])
        
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_rsi(self, close, period: int = 14) -> float:
        """Calculate RSI."""
        if len(close) < period + 1:
            return 50.0
        
        deltas = np.diff(close)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_atr(self, high, low, close, period: int = 14) -> float:
        """Calculate ATR."""
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
