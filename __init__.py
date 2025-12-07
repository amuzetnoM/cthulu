"""
Herald - Adaptive Trading Intelligence for MetaTrader 5

A modular, event-driven trading bot emphasizing safety, testability, and extensibility.
"""

__version__ = "3.0.0"
__author__ = "Herald Project"

from .connector.mt5_connector import MT5Connector, ConnectionConfig
from .strategy.base import Strategy, Signal, SignalType
from .execution.engine import ExecutionEngine, OrderRequest, ExecutionResult
from .risk.manager import RiskManager, RiskLimits
from .data.layer import DataLayer, BarData
from .persistence.database import Database, TradeRecord, SignalRecord
from .observability.metrics import MetricsCollector, PerformanceMetrics

__all__ = [
    "MT5Connector",
    "ConnectionConfig",
    "Strategy",
    "Signal",
    "SignalType",
    "ExecutionEngine",
    "OrderRequest",
    "ExecutionResult",
    "RiskManager",
    "RiskLimits",
    "DataLayer",
    "BarData",
    "Database",
    "TradeRecord",
    "SignalRecord",
    "MetricsCollector",
    "PerformanceMetrics",
]
