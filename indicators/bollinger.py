"""
Bollinger Bands Indicator
"""
import numpy as np
from typing import Dict


def calculate_bollinger(
    close: np.ndarray,
    period: int = 20,
    std_dev: float = 2.0
) -> Dict[str, float]:
    """
    Calculate Bollinger Bands.
    
    Formula:
    Middle Band = SMA(close, period)
    Upper Band = Middle + (std_dev * StdDev)
    Lower Band = Middle - (std_dev * StdDev)
    
    Args:
        close: Array of closing prices
        period: SMA period (default: 20)
        std_dev: Standard deviation multiplier (default: 2.0)
        
    Returns:
        Dict with 'upper', 'middle', 'lower', 'width', 'percent_b'
    """
    if len(close) < period:
        current = close[-1] if len(close) > 0 else 0
        return {
            'upper': current,
            'middle': current,
            'lower': current,
            'width': 0.0,
            'percent_b': 0.5
        }
    
    # Middle band (SMA)
    middle = np.mean(close[-period:])
    
    # Standard deviation
    std = np.std(close[-period:], ddof=1)
    
    # Upper and lower bands
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    
    # Band width (normalized)
    width = (upper - lower) / middle if middle != 0 else 0
    
    # %B (position within bands)
    current_price = close[-1]
    if upper != lower:
        percent_b = (current_price - lower) / (upper - lower)
    else:
        percent_b = 0.5
    
    return {
        'upper': round(upper, 5),
        'middle': round(middle, 5),
        'lower': round(lower, 5),
        'width': round(width, 5),
        'percent_b': round(percent_b, 3)
    }


def calculate_bollinger_series(
    close: np.ndarray,
    period: int = 20,
    std_dev: float = 2.0
) -> Dict[str, np.ndarray]:
    """
    Calculate Bollinger Bands series.
    
    Returns:
        Dict with arrays for 'upper', 'middle', 'lower'
    """
    n = len(close)
    upper = np.full(n, np.nan)
    middle = np.full(n, np.nan)
    lower = np.full(n, np.nan)
    
    for i in range(period - 1, n):
        window = close[i - period + 1:i + 1]
        sma = np.mean(window)
        std = np.std(window, ddof=1)
        
        middle[i] = sma
        upper[i] = sma + (std_dev * std)
        lower[i] = sma - (std_dev * std)
    
    return {
        'upper': upper,
        'middle': middle,
        'lower': lower
    }


def bollinger_squeeze(
    close: np.ndarray,
    period: int = 20,
    std_dev: float = 2.0,
    squeeze_threshold: float = 0.02
) -> Dict[str, any]:
    """
    Detect Bollinger Band squeeze conditions.
    
    A squeeze occurs when bands narrow significantly,
    often preceding a volatility expansion.
    
    Args:
        close: Array of closing prices
        period: BB period
        std_dev: Standard deviation multiplier
        squeeze_threshold: Width threshold for squeeze
        
    Returns:
        Dict with 'is_squeeze', 'width', 'duration'
    """
    bb = calculate_bollinger(close, period, std_dev)
    
    # Calculate historical widths
    widths = []
    for i in range(period, len(close)):
        window = close[i - period:i]
        sma = np.mean(window)
        std = np.std(window, ddof=1)
        width = (2 * std_dev * std) / sma if sma != 0 else 0
        widths.append(width)
    
    current_width = bb['width']
    avg_width = np.mean(widths) if widths else current_width
    
    # Squeeze detection
    is_squeeze = current_width < avg_width * 0.5 or current_width < squeeze_threshold
    
    # Squeeze duration
    duration = 0
    if is_squeeze and widths:
        for w in reversed(widths):
            if w < avg_width * 0.5:
                duration += 1
            else:
                break
    
    return {
        'is_squeeze': is_squeeze,
        'width': current_width,
        'avg_width': avg_width,
        'duration': duration,
        'expansion_likely': is_squeeze and duration >= 5
    }
