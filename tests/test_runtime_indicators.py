import pandas as pd
import numpy as np
import logging

from herald.__main__ import ensure_runtime_indicators
from herald.strategy.scalping import ScalpingStrategy
from herald.indicators.rsi import RSI

logger = logging.getLogger('herald.tests')


def _make_ohlcv(n=500):
    rng = pd.date_range('2025-01-01', periods=n, freq='T')
    price = np.cumsum(np.random.normal(0, 0.1, n)) + 100.0
    df = pd.DataFrame({'open': price, 'high': price + 0.1, 'low': price - 0.1, 'close': price, 'volume': np.random.randint(1, 100, n)}, index=rng)
    return df


def test_ensure_runtime_indicators_computes_ema_and_rsi():
    df = _make_ohlcv(200)

    # Create a scalping strategy that expects rsi_period=7 and default fast/slow EMAs
    config = {
        'strategy': {
            'type': 'dynamic',
            'strategies': [
                {'type': 'scalping', 'params': {'fast_ema': 5, 'slow_ema': 10, 'rsi_period': 7}}
            ]
        }
    }

    strat = ScalpingStrategy({'params': {'fast_ema': 5, 'slow_ema': 10, 'rsi_period': 7}})
    indicators = []

    extra = ensure_runtime_indicators(df, indicators, strat, config, logger)

    # Should add at least an RSI indicator (because scalping expects it)
    types = [i.__class__.__name__.lower() for i in extra]
    assert 'rsi' in types or any(isinstance(i, RSI) for i in extra)

    # Apply the extra indicators to the DF (simulate main loop behavior)
    for ind in extra:
        data = ind.calculate(df)
        if data is not None:
            df = df.join(data, how='left')

    # Check EMA columns exist and RSI produced
    assert 'ema_5' in df.columns
    assert 'ema_10' in df.columns
    assert 'rsi_7' in df.columns or 'rsi' in df.columns
