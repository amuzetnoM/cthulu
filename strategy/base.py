"""
Base Strategy Interface
All strategies must implement this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Trading signal output from a strategy."""
    direction: str  # 'buy' or 'sell'
    symbol: str
    confidence: float = 0.5
    strategy_name: str = ""
    entry_price: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'direction': self.direction,
            'symbol': self.symbol,
            'confidence': self.confidence,
            'strategy_name': self.strategy_name,
            'entry_price': self.entry_price,
            'sl': self.sl,
            'tp': self.tp,
            'reason': self.reason,
            'metadata': self.metadata
        }


class BaseStrategy(ABC):
    """
    Base strategy class - all strategies must inherit from this.
    
    Required methods:
    - generate_signal: Analyze data and return a signal (or None)
    - get_regime_fitness: Return how well strategy fits current regime
    """
    
    def __init__(self, config: Dict[str, Any], symbol: str):
        self.config = config
        self.symbol = symbol
        self.name = self.__class__.__name__
        self._last_signal_bar = -1  # Track to prevent duplicate signals
        
    @abstractmethod
    def generate_signal(
        self,
        data: Any,
        indicators: Dict[str, Any]
    ) -> Optional[Signal]:
        """
        Analyze market data and generate a trading signal.
        
        Args:
            data: OHLCV DataFrame
            indicators: Pre-calculated indicators dict
            
        Returns:
            Signal object or None if no signal
        """
        pass
    
    @abstractmethod
    def get_regime_fitness(self, regime: str) -> float:
        """
        Return how well this strategy fits the current market regime.
        
        Args:
            regime: Current market regime string
            
        Returns:
            Float 0.0 to 1.0 (1.0 = perfect fit)
        """
        pass
    
    def _is_new_bar(self, data: Any) -> bool:
        """Check if we're on a new bar to prevent duplicate signals."""
        if data is None or len(data) == 0:
            return False
        
        # Use timestamp if available, otherwise use length
        if hasattr(data, 'index') and len(data) > 0:
            try:
                current_bar_time = data.index[-1]
                if hasattr(self, '_last_bar_time') and current_bar_time == self._last_bar_time:
                    return False
                self._last_bar_time = current_bar_time
                return True
            except:
                pass
        
        # Fallback to length-based check
        current_bar = len(data) - 1
        if current_bar != self._last_signal_bar:
            self._last_signal_bar = current_bar
            return True
        return False
    
    def _calculate_atr_based_sltp(
        self,
        entry_price: float,
        direction: str,
        atr: float,
        sl_multiplier: float = 2.0,
        tp_multiplier: float = 4.0
    ) -> tuple:
        """Calculate ATR-based SL and TP."""
        sl_distance = atr * sl_multiplier
        tp_distance = atr * tp_multiplier
        
        if direction == 'buy':
            sl = entry_price - sl_distance
            tp = entry_price + tp_distance
        else:
            sl = entry_price + sl_distance
            tp = entry_price - tp_distance
        
        return sl, tp
