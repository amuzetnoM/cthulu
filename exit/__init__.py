"""
Exit Strategy Module

Exit strategy implementations for position management.

Includes context-aware exit coordination for intelligent exit decision-making.
"""

from .base import ExitStrategy, ExitSignal
from .trailing_stop import TrailingStop, TrailingStopExit
from .time_based import TimeBasedExit
from .profit_target import ProfitTargetExit
from .adverse_movement import AdverseMovementExit
from .stop_loss import StopLossExit
from .take_profit import TakeProfitExit
from .exit_manager import ExitDecision, ExitStrategyManager
from .coordinator import ExitCoordinator, MarketContext, PositionContext, create_exit_coordinator
from .micro_account_protection import MicroAccountProtection, SurvivalModeExit
from .profit_scaling import ProfitScalingExit, AggressiveScalingExit, ProfitScaling, AggressiveScaling

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
    "ExitCoordinator",
    "MarketContext",
    "PositionContext",
    "create_exit_coordinator",
    "MicroAccountProtection",
    "SurvivalModeExit",
    "ProfitScalingExit",
    "AggressiveScalingExit",
    "ProfitScaling",
    "AggressiveScaling",
]




