"""Strategy module"""

from strategy.base import Strategy, Signal, SignalType
from strategy.sma_crossover import SmaCrossover

__all__ = ["Strategy", "Signal", "SignalType", "SmaCrossover"]
