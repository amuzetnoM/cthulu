"""
ATR (Average True Range) Indicator
"""
import numpy as np
from typing import Union


def calculate_atr(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14
) -> float:
    """
    Calculate ATR (Average True Range).
    
    Formula:
    TR = max(high - low, |high - prev_close|, |low - prev_close|)
    ATR = SMA(TR, period)
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of closing prices
        period: ATR period (default: 14)
        
    Returns:
        ATR value
    """
    if len(high) < period + 1:
        return abs(high[-1] - low[-1]) if len(high) > 0 else 0.0
    
    # Calculate True Range
    tr = []
    for i in range(1, len(high)):
        tr1 = high[i] - low[i]
        tr2 = abs(high[i] - close[i - 1])
        tr3 = abs(low[i] - close[i - 1])
        tr.append(max(tr1, tr2, tr3))
    
    # Calculate ATR (Wilder's smoothing)
    atr = np.mean(tr[:period])
    
    for i in range(period, len(tr)):
        atr = (atr * (period - 1) + tr[i]) / period
    
    return round(atr, 5)


def calculate_atr_series(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14
) -> np.ndarray:
    """
    Calculate ATR series for entire price array.
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of closing prices
        period: ATR period
        
    Returns:
        Array of ATR values
    """
    if len(high) < period + 1:
        return np.full(len(high), abs(high[-1] - low[-1]))
    
    # Calculate True Range
    tr = np.zeros(len(high))
    tr[0] = high[0] - low[0]
    
    for i in range(1, len(high)):
        tr1 = high[i] - low[i]
        tr2 = abs(high[i] - close[i - 1])
        tr3 = abs(low[i] - close[i - 1])
        tr[i] = max(tr1, tr2, tr3)
    
    # Calculate ATR series
    atr = np.zeros(len(high))
    atr[:period] = np.nan
    atr[period] = np.mean(tr[1:period + 1])
    
    for i in range(period + 1, len(high)):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
    
    return atr
