"""
Market Regime Classifier - Clean Implementation
Classifies market conditions to guide strategy selection.
"""
import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classifications."""
    TRENDING_UP_STRONG = "trending_up_strong"
    TRENDING_UP_WEAK = "trending_up_weak"
    TRENDING_DOWN_STRONG = "trending_down_strong"
    TRENDING_DOWN_WEAK = "trending_down_weak"
    RANGING_TIGHT = "ranging_tight"
    RANGING_WIDE = "ranging_wide"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class RegimeClassifier:
    """
    Classifies market regime based on indicators.
    
    Uses:
    - ADX for trend strength
    - RSI for overbought/oversold
    - Price returns for direction
    - Volatility for range/volatile detection
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize regime classifier."""
        self.config = config or {}
        
        # Thresholds
        self.adx_trend_threshold = self.config.get('adx_trend_threshold', 25)
        self.adx_strong_threshold = self.config.get('adx_strong_threshold', 40)
        self.volatility_threshold = self.config.get('volatility_threshold', 0.02)
    
    def classify(
        self,
        indicators: Dict[str, Any],
        market_data: Any = None
    ) -> str:
        """
        Classify current market regime.
        
        Args:
            indicators: Calculated indicators (RSI, ADX, etc.)
            market_data: OHLCV data (optional, for returns calculation)
            
        Returns:
            Regime string (e.g., "trending_up_strong")
        """
        adx = indicators.get('ADX', 20)
        rsi = indicators.get('RSI', 50)
        
        # Calculate returns if data available
        returns = 0
        volatility = 0
        
        if market_data is not None and len(market_data) >= 20:
            closes = market_data['close'].values
            returns = (closes[-1] - closes[-20]) / closes[-20]
            volatility = closes[-20:].std() / closes[-20:].mean()
        
        # Classify
        regime = self._determine_regime(adx, rsi, returns, volatility)
        
        logger.info(f"Market regime: {regime} (ADX={adx:.1f}, RSI={rsi:.1f}, Returns={returns:.3f}, Vol={volatility:.3f})")
        
        return regime
    
    def _determine_regime(
        self,
        adx: float,
        rsi: float,
        returns: float,
        volatility: float
    ) -> str:
        """Determine regime from metrics."""
        
        # High volatility
        if volatility > self.volatility_threshold:
            return MarketRegime.VOLATILE.value
        
        # Strong trend
        if adx > self.adx_strong_threshold:
            if returns > 0 and rsi > 50:
                return MarketRegime.TRENDING_UP_STRONG.value
            elif returns < 0 and rsi < 50:
                return MarketRegime.TRENDING_DOWN_STRONG.value
        
        # Weak trend
        if adx > self.adx_trend_threshold:
            if returns > 0:
                return MarketRegime.TRENDING_UP_WEAK.value
            else:
                return MarketRegime.TRENDING_DOWN_WEAK.value
        
        # Ranging
        if volatility > 0.01:
            return MarketRegime.RANGING_WIDE.value
        else:
            return MarketRegime.RANGING_TIGHT.value
    
    def get_recommended_strategies(self, regime: str) -> Dict[str, float]:
        """
        Get strategy recommendations for a regime.
        
        Returns dict of strategy -> weight multiplier.
        """
        recommendations = {
            MarketRegime.TRENDING_UP_STRONG.value: {
                'trend_following': 1.0,
                'ema_crossover': 0.9,
                'momentum_breakout': 0.8,
                'sma_crossover': 0.7,
                'scalping': 0.5,
                'mean_reversion': 0.3,
                'rsi_reversal': 0.3
            },
            MarketRegime.TRENDING_DOWN_STRONG.value: {
                'trend_following': 1.0,
                'ema_crossover': 0.9,
                'momentum_breakout': 0.8,
                'sma_crossover': 0.7,
                'scalping': 0.5,
                'mean_reversion': 0.3,
                'rsi_reversal': 0.3
            },
            MarketRegime.RANGING_TIGHT.value: {
                'scalping': 1.0,
                'mean_reversion': 0.9,
                'rsi_reversal': 0.8,
                'trend_following': 0.3,
                'momentum_breakout': 0.3
            },
            MarketRegime.RANGING_WIDE.value: {
                'mean_reversion': 1.0,
                'scalping': 0.8,
                'rsi_reversal': 0.7,
                'trend_following': 0.4
            },
            MarketRegime.VOLATILE.value: {
                'mean_reversion': 0.5,
                'scalping': 0.4,
                'trend_following': 0.3
            }
        }
        
        return recommendations.get(regime, {
            'ema_crossover': 0.5,
            'trend_following': 0.5,
            'scalping': 0.5
        })
