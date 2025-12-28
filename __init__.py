"""
Cthulhu - Adaptive Trading Intelligence

A modular, event-driven trading bot emphasizing safety, testability, and extensibility.
"""

__version__ = "5.0.1"
__author__ = "Cthulhu Project"

from .connector.mt5_connector import MT5Connector, ConnectionConfig
from .strategy.base import Strategy, Signal, SignalType
from .execution.engine import ExecutionEngine, OrderRequest, ExecutionResult
from .risk.manager import RiskManager, RiskLimits
from .data.layer import DataLayer
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
    "Database",
    "TradeRecord",
    "SignalRecord",
    "MetricsCollector",
    "PerformanceMetrics",
]
