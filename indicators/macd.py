"""
MACD (Moving Average Convergence Divergence) Indicator
"""
import numpy as np
from typing import Dict


def calculate_macd(
    close: np.ndarray,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Dict[str, float]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Formula:
    MACD Line = EMA(fast) - EMA(slow)
    Signal Line = EMA(MACD Line, signal_period)
    Histogram = MACD Line - Signal Line
    
    Args:
        close: Array of closing prices
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line period (default: 9)
        
    Returns:
        Dict with 'macd', 'signal', 'histogram'
    """
    if len(close) < slow_period + signal_period:
        return {
            'macd': 0.0,
            'signal': 0.0,
            'histogram': 0.0
        }
    
    # Calculate EMAs
    fast_ema = _calculate_ema(close, fast_period)
    slow_ema = _calculate_ema(close, slow_period)
    
    # MACD line
    macd_line = fast_ema - slow_ema
    
    # Calculate MACD series for signal line
    macd_series = _calculate_macd_series(close, fast_period, slow_period)
    
    # Signal line
    if len(macd_series) >= signal_period:
        signal_line = _calculate_ema(macd_series, signal_period)
    else:
        signal_line = macd_line
    
    # Histogram
    histogram = macd_line - signal_line
    
    return {
        'macd': round(macd_line, 5),
        'signal': round(signal_line, 5),
        'histogram': round(histogram, 5)
    }


def _calculate_ema(data: np.ndarray, period: int) -> float:
    """Calculate EMA for given period."""
    if len(data) < period:
        return data[-1] if len(data) > 0 else 0
    
    multiplier = 2 / (period + 1)
    ema = np.mean(data[:period])
    
    for price in data[period:]:
        ema = (price - ema) * multiplier + ema
    
    return ema


def _calculate_macd_series(
    close: np.ndarray,
    fast_period: int,
    slow_period: int
) -> np.ndarray:
    """Calculate MACD series for signal line calculation."""
    if len(close) < slow_period:
        return np.array([0.0])
    
    # Fast EMA series
    fast_mult = 2 / (fast_period + 1)
    fast_ema = np.zeros(len(close))
    fast_ema[fast_period - 1] = np.mean(close[:fast_period])
    
    for i in range(fast_period, len(close)):
        fast_ema[i] = (close[i] - fast_ema[i - 1]) * fast_mult + fast_ema[i - 1]
    
    # Slow EMA series
    slow_mult = 2 / (slow_period + 1)
    slow_ema = np.zeros(len(close))
    slow_ema[slow_period - 1] = np.mean(close[:slow_period])
    
    for i in range(slow_period, len(close)):
        slow_ema[i] = (close[i] - slow_ema[i - 1]) * slow_mult + slow_ema[i - 1]
    
    # MACD series (only valid after slow period)
    macd_series = fast_ema[slow_period - 1:] - slow_ema[slow_period - 1:]
    
    return macd_series


def calculate_macd_series_full(
    close: np.ndarray,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Dict[str, np.ndarray]:
    """
    Calculate full MACD series.
    
    Returns:
        Dict with arrays for 'macd', 'signal', 'histogram'
    """
    if len(close) < slow_period + signal_period:
        return {
            'macd': np.zeros(len(close)),
            'signal': np.zeros(len(close)),
            'histogram': np.zeros(len(close))
        }
    
    # Fast EMA
    fast_mult = 2 / (fast_period + 1)
    fast_ema = np.zeros(len(close))
    fast_ema[:fast_period] = np.nan
    fast_ema[fast_period - 1] = np.mean(close[:fast_period])
    
    for i in range(fast_period, len(close)):
        fast_ema[i] = (close[i] - fast_ema[i - 1]) * fast_mult + fast_ema[i - 1]
    
    # Slow EMA
    slow_mult = 2 / (slow_period + 1)
    slow_ema = np.zeros(len(close))
    slow_ema[:slow_period] = np.nan
    slow_ema[slow_period - 1] = np.mean(close[:slow_period])
    
    for i in range(slow_period, len(close)):
        slow_ema[i] = (close[i] - slow_ema[i - 1]) * slow_mult + slow_ema[i - 1]
    
    # MACD line
    macd_line = fast_ema - slow_ema
    macd_line[:slow_period - 1] = np.nan
    
    # Signal line
    signal_mult = 2 / (signal_period + 1)
    signal_line = np.zeros(len(close))
    signal_line[:slow_period + signal_period - 2] = np.nan
    
    valid_macd = macd_line[slow_period - 1:]
    if len(valid_macd) >= signal_period:
        signal_line[slow_period + signal_period - 2] = np.mean(valid_macd[:signal_period])
        
        for i in range(slow_period + signal_period - 1, len(close)):
            signal_line[i] = (macd_line[i] - signal_line[i - 1]) * signal_mult + signal_line[i - 1]
    
    # Histogram
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }
