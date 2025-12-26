"""Strategy module"""

from .base import Strategy, Signal, SignalType
from .sma_crossover import SmaCrossover
from .ema_crossover import EmaCrossover
from .momentum_breakout import MomentumBreakout
from .scalping import ScalpingStrategy
from .strategy_selector import StrategySelector, MarketRegime, StrategyPerformance

__all__ = [
    "Strategy", 
    "Signal", 
    "SignalType", 
    "SmaCrossover",
    "EmaCrossover",
    "MomentumBreakout",
    "ScalpingStrategy",
    "StrategySelector",
    "MarketRegime",
    "StrategyPerformance"
]
