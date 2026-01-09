"""Strategy module - Rule-based trading strategies."""
from .base import BaseStrategy, Signal
from .sma_crossover import SMACrossoverStrategy
from .ema_crossover import EMACrossoverStrategy
from .scalping import ScalpingStrategy
from .selector import StrategySelector

__all__ = [
    'BaseStrategy',
    'Signal',
    'SMACrossoverStrategy',
    'EMACrossoverStrategy',
    'ScalpingStrategy',
    'StrategySelector',
]
