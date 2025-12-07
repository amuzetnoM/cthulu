"""
Exit Strategy Module

Exit strategy implementations for position management.
"""

from .base import ExitStrategy, ExitSignal
from .trailing_stop import TrailingStop, TrailingStopExit
from .time_based import TimeBasedExit
from .profit_target import ProfitTargetExit
from .adverse_movement import AdverseMovementExit
from .stop_loss import StopLossExit
from .take_profit import TakeProfitExit
from .exit_manager import ExitDecision, ExitStrategyManager

__all__ = [
    "ExitStrategy",
    "ExitSignal",
    "TrailingStop",
    "TimeBasedExit",
    "ProfitTargetExit",
    "AdverseMovementExit",
    "StopLossExit",
    "TakeProfitExit",
    "ExitDecision",
    "ExitStrategyManager",
]
