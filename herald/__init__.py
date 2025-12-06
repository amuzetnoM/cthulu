"""
Herald - Adaptive Trading Intelligence for MetaTrader 5

A modular, event-driven trading bot emphasizing safety, testability, and extensibility.
"""

__version__ = "1.0.0"
__author__ = "Herald Project"

from herald.connector.mt5_connector import MT5Connector
from herald.strategy.base import Strategy, Signal
from herald.execution.engine import ExecutionEngine
from herald.risk.manager import RiskManager

__all__ = [
    "MT5Connector",
    "Strategy",
    "Signal",
    "ExecutionEngine",
    "RiskManager",
]
