"""Strategy module"""

from herald.strategy.base import Strategy, Signal, SignalType
from herald.strategy.sma_crossover import SmaCrossover

__all__ = ["Strategy", "Signal", "SignalType", "SmaCrossover"]
