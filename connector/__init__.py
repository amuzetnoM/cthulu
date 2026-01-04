"""Connector module for MT5 integration - Android Native Version

This module provides full MT5 trading capabilities for Android/Termux environments
through a bridge architecture. All trading operations are supported.

Exports:
    MT5Connector: Main connector class (aliased from MT5ConnectorAndroid)
    ConnectionConfig: Configuration class (aliased from AndroidConnectionConfig)
    MT5Constants: All MT5 API constants
    
    Order Types:
        ORDER_TYPE_BUY, ORDER_TYPE_SELL, ORDER_TYPE_BUY_LIMIT, etc.
        
    Trade Actions:
        TRADE_ACTION_DEAL, TRADE_ACTION_PENDING, TRADE_ACTION_SLTP, etc.
        
    Return Codes:
        TRADE_RETCODE_DONE, TRADE_RETCODE_INVALID, TRADE_RETCODE_TIMEOUT
        
    Timeframes:
        TIMEFRAME_M1, TIMEFRAME_M5, TIMEFRAME_H1, TIMEFRAME_D1, etc.
"""

from .mt5_connector_android import (
    MT5ConnectorAndroid as MT5Connector,
    AndroidConnectionConfig as ConnectionConfig,
    MT5Constants,
    # Order types
    ORDER_TYPE_BUY,
    ORDER_TYPE_SELL,
    TRADE_ACTION_DEAL,
    ORDER_TIME_GTC,
    ORDER_FILLING_FOK,
    ORDER_FILLING_IOC,
    TRADE_RETCODE_DONE,
    # Helper classes
    _OrderResult,
    _Position,
    _SymbolTick,
)

# Re-export all constants at module level for compatibility
ORDER_TYPE_BUY_LIMIT = MT5Constants.ORDER_TYPE_BUY_LIMIT
ORDER_TYPE_SELL_LIMIT = MT5Constants.ORDER_TYPE_SELL_LIMIT
ORDER_TYPE_BUY_STOP = MT5Constants.ORDER_TYPE_BUY_STOP
ORDER_TYPE_SELL_STOP = MT5Constants.ORDER_TYPE_SELL_STOP

TRADE_ACTION_PENDING = MT5Constants.TRADE_ACTION_PENDING
TRADE_ACTION_SLTP = MT5Constants.TRADE_ACTION_SLTP
TRADE_ACTION_MODIFY = MT5Constants.TRADE_ACTION_MODIFY
TRADE_ACTION_REMOVE = MT5Constants.TRADE_ACTION_REMOVE

ORDER_TIME_DAY = MT5Constants.ORDER_TIME_DAY
ORDER_TIME_SPECIFIED = MT5Constants.ORDER_TIME_SPECIFIED
ORDER_TIME_SPECIFIED_DAY = MT5Constants.ORDER_TIME_SPECIFIED_DAY

ORDER_FILLING_RETURN = MT5Constants.ORDER_FILLING_RETURN

TRADE_RETCODE_INVALID = MT5Constants.TRADE_RETCODE_INVALID
TRADE_RETCODE_TIMEOUT = MT5Constants.TRADE_RETCODE_TIMEOUT

TIMEFRAME_M1 = MT5Constants.TIMEFRAME_M1
TIMEFRAME_M5 = MT5Constants.TIMEFRAME_M5
TIMEFRAME_M15 = MT5Constants.TIMEFRAME_M15
TIMEFRAME_M30 = MT5Constants.TIMEFRAME_M30
TIMEFRAME_H1 = MT5Constants.TIMEFRAME_H1
TIMEFRAME_H4 = MT5Constants.TIMEFRAME_H4
TIMEFRAME_D1 = MT5Constants.TIMEFRAME_D1
TIMEFRAME_W1 = MT5Constants.TIMEFRAME_W1
TIMEFRAME_MN1 = MT5Constants.TIMEFRAME_MN1

__all__ = [
    "MT5Connector",
    "ConnectionConfig",
    "MT5Constants",
    # Order types
    "ORDER_TYPE_BUY",
    "ORDER_TYPE_SELL",
    "ORDER_TYPE_BUY_LIMIT",
    "ORDER_TYPE_SELL_LIMIT",
    "ORDER_TYPE_BUY_STOP",
    "ORDER_TYPE_SELL_STOP",
    # Trade actions
    "TRADE_ACTION_DEAL",
    "TRADE_ACTION_PENDING",
    "TRADE_ACTION_SLTP",
    "TRADE_ACTION_MODIFY",
    "TRADE_ACTION_REMOVE",
    # Order time
    "ORDER_TIME_GTC",
    "ORDER_TIME_DAY",
    "ORDER_TIME_SPECIFIED",
    "ORDER_TIME_SPECIFIED_DAY",
    # Order filling
    "ORDER_FILLING_FOK",
    "ORDER_FILLING_IOC",
    "ORDER_FILLING_RETURN",
    # Return codes
    "TRADE_RETCODE_DONE",
    "TRADE_RETCODE_INVALID",
    "TRADE_RETCODE_TIMEOUT",
    # Timeframes
    "TIMEFRAME_M1",
    "TIMEFRAME_M5",
    "TIMEFRAME_M15",
    "TIMEFRAME_M30",
    "TIMEFRAME_H1",
    "TIMEFRAME_H4",
    "TIMEFRAME_D1",
    "TIMEFRAME_W1",
    "TIMEFRAME_MN1",
]




