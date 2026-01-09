"""
ADX (Average Directional Index) Indicator
Measures trend strength.
"""
import numpy as np
from typing import Dict, Union


def calculate_adx(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14
) -> float:
    """
    Calculate ADX (Average Directional Index).
    
    Formula:
    +DM = high - prev_high (if positive and > -DM, else 0)
    -DM = prev_low - low (if positive and > +DM, else 0)
    TR = max(high - low, |high - prev_close|, |low - prev_close|)
    +DI = 100 * EMA(+DM, period) / ATR
    -DI = 100 * EMA(-DM, period) / ATR
    DX = 100 * |+DI - -DI| / |+DI + -DI|
    ADX = EMA(DX, period)
    
    Args:
        high: Array of high prices
        low: Array of low prices
        close: Array of closing prices
        period: ADX period (default: 14)
        
    Returns:
        ADX value (0-100)
    """
    if len(high) < period * 2:
        return 25.0  # Default neutral value
    
    # Calculate +DM, -DM, and TR
    plus_dm = []
    minus_dm = []
    tr = []
    
    for i in range(1, len(high)):
        # +DM
        up_move = high[i] - high[i - 1]
        down_move = low[i - 1] - low[i]
        
        if up_move > down_move and up_move > 0:
            plus_dm.append(up_move)
        else:
            plus_dm.append(0)
        
        if down_move > up_move and down_move > 0:
            minus_dm.append(down_move)
        else:
            minus_dm.append(0)
        
        # True Range
        tr1 = high[i] - low[i]
        tr2 = abs(high[i] - close[i - 1])
        tr3 = abs(low[i] - close[i - 1])
        tr.append(max(tr1, tr2, tr3))
    
    # Smooth using Wilder's method
    def wilder_smooth(data, period):
        smoothed = [sum(data[:period])]
        for i in range(period, len(data)):
            smoothed.append(smoothed[-1] - (smoothed[-1] / period) + data[i])
        return smoothed
    
    atr = wilder_smooth(tr, period)
    plus_dm_smooth = wilder_smooth(plus_dm, period)
    minus_dm_smooth = wilder_smooth(minus_dm, period)
    
    # Calculate +DI and -DI
    plus_di = []
    minus_di = []
    
    for i in range(len(atr)):
        if atr[i] != 0:
            plus_di.append(100 * plus_dm_smooth[i] / atr[i])
            minus_di.append(100 * minus_dm_smooth[i] / atr[i])
        else:
            plus_di.append(0)
            minus_di.append(0)
    
    # Calculate DX
    dx = []
    for i in range(len(plus_di)):
        di_sum = plus_di[i] + minus_di[i]
        if di_sum != 0:
            dx.append(100 * abs(plus_di[i] - minus_di[i]) / di_sum)
        else:
            dx.append(0)
    
    # Calculate ADX (smoothed DX)
    if len(dx) < period:
        return 25.0
    
    adx = sum(dx[:period]) / period
    
    for i in range(period, len(dx)):
        adx = (adx * (period - 1) + dx[i]) / period
    
    return round(adx, 2)


def calculate_adx_with_di(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14
) -> Dict[str, float]:
    """
    Calculate ADX with +DI and -DI values.
    
    Returns:
        Dict with 'adx', 'plus_di', 'minus_di'
    """
    adx = calculate_adx(high, low, close, period)
    
    # Simplified DI calculation for latest value
    if len(high) < period + 1:
        return {'adx': adx, 'plus_di': 25.0, 'minus_di': 25.0}
    
    # Calculate recent DI values
    plus_dm_sum = 0
    minus_dm_sum = 0
    tr_sum = 0
    
    for i in range(-period, 0):
        up_move = high[i] - high[i - 1]
        down_move = low[i - 1] - low[i]
        
        if up_move > down_move and up_move > 0:
            plus_dm_sum += up_move
        if down_move > up_move and down_move > 0:
            minus_dm_sum += down_move
        
        tr1 = high[i] - low[i]
        tr2 = abs(high[i] - close[i - 1])
        tr3 = abs(low[i] - close[i - 1])
        tr_sum += max(tr1, tr2, tr3)
    
    if tr_sum == 0:
        return {'adx': adx, 'plus_di': 25.0, 'minus_di': 25.0}
    
    plus_di = 100 * plus_dm_sum / tr_sum
    minus_di = 100 * minus_dm_sum / tr_sum
    
    return {
        'adx': adx,
        'plus_di': round(plus_di, 2),
        'minus_di': round(minus_di, 2)
    }
