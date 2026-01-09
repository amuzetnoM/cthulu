"""
RSI (Relative Strength Index) Indicator
"""
import numpy as np
from typing import Union


def calculate_rsi(close: np.ndarray, period: int = 14) -> float:
    """
    Calculate RSI (Relative Strength Index).
    
    Formula:
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    
    Args:
        close: Array of closing prices
        period: RSI period (default: 14)
        
    Returns:
        RSI value (0-100)
    """
    if len(close) < period + 1:
        return 50.0
    
    # Calculate price changes
    deltas = np.diff(close)
    
    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Calculate average gain/loss (Wilder's smoothing)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    # Apply Wilder smoothing for remaining periods
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def calculate_rsi_series(close: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Calculate RSI series for entire price array.
    
    Args:
        close: Array of closing prices
        period: RSI period
        
    Returns:
        Array of RSI values
    """
    if len(close) < period + 1:
        return np.full(len(close), 50.0)
    
    deltas = np.diff(close)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    rsi_values = np.full(len(close), np.nan)
    
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            rsi_values[i + 1] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi_values[i + 1] = 100 - (100 / (1 + rs))
    
    return rsi_values
