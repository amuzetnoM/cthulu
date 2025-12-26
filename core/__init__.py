"""
Herald Core Module

Contains the refactored core components of Herald:
- bootstrap: System initialization
- trading_loop: Main trading logic ✅
- indicator_loader: Indicator management  
- strategy_factory: Strategy creation
- exit_loader: Exit strategy loading
- shutdown: Graceful shutdown ✅
"""

from .indicator_loader import IndicatorLoader, IndicatorRequirementResolver
from .strategy_factory import StrategyFactory
from .bootstrap import HeraldBootstrap, SystemComponents
from .exit_loader import ExitStrategyLoader
from .trading_loop import TradingLoop, TradingLoopContext, ensure_runtime_indicators
from .shutdown import ShutdownHandler, create_shutdown_handler

__all__ = [
    'IndicatorLoader',
    'IndicatorRequirementResolver',
    'StrategyFactory',
    'HeraldBootstrap',
    'SystemComponents',
    'ExitStrategyLoader',
    'TradingLoop',
    'TradingLoopContext',
    'ensure_runtime_indicators',
    'ShutdownHandler',
    'create_shutdown_handler',
]
