"""
Exit Strategy Module

Exit strategy implementations for position management.
"""

from exit.base import ExitStrategy, ExitSignal
from exit.trailing_stop import TrailingStop
from exit.time_based import TimeBasedExit
from exit.profit_target import ProfitTargetExit
from exit.adverse_movement import AdverseMovementExit

__all__ = [
    "ExitStrategy",
    "ExitSignal",
    "TrailingStop",
    "TimeBasedExit",
    "ProfitTargetExit",
    "AdverseMovementExit",
]
