"""
ATR (Average True Range) indicator implementation and wrapper

This module provides a simple function `calculate_atr` which returns a pandas
Series with ATR values based on High, Low, Close.
"""

import pandas as pd
from typing import Optional


def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR) over the given period.

    Args:
        data: DataFrame with 'high', 'low', 'close' columns and a DatetimeIndex
        period: ATR lookback period (default: 14)

    Returns:
        pandas Series with ATR values
    """
    # Validate
    if data is None or data.empty:
        raise ValueError("ATR: Dataframe empty")
    required = ['high', 'low', 'close']
    for r in required:
        if r not in data.columns:
            raise ValueError(f"ATR: Missing required column: {r}")
    if not isinstance(data.index, pd.DatetimeIndex):
        # Try to set index from 'time' column if present
        if 'time' in data.columns:
            data = data.set_index('time')
        else:
            raise ValueError("ATR: Index must be DatetimeIndex")

    high = data['high']
    low = data['low']
    close = data['close']

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=1).mean()
    atr.name = 'atr'
    return atr


__all__ = ["calculate_atr"]
