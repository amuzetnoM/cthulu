"""
Trend Following Strategy

Follows established trends using ADX for trend strength confirmation.
Uses moving averages and trend continuation patterns for entries.
"""

import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime

from cthulu.strategy.base import Strategy, Signal, SignalType


class TrendFollowingStrategy(Strategy):
    """
    Trend Following Strategy using ADX and moving averages.

    Enters on trend continuation signals when ADX confirms trend strength.
    Uses wider stops and longer targets for trend trades.

    Configuration:
        fast_ma: Fast moving average period (default: 20)
        slow_ma: Slow moving average period (default: 50)
        adx_period: ADX period (default: 14)
        adx_threshold: ADX trend strength threshold (default: 25)
        atr_multiplier: ATR multiplier for SL (default: 2.0)
        risk_reward_ratio: Risk/reward ratio (default: 3.0)
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize trend following strategy."""
        super().__init__("trend_following", config)

        # Strategy parameters
        self.fast_ma = config.get('params', {}).get('fast_ma', 20)
        self.slow_ma = config.get('params', {}).get('slow_ma', 50)
        self.adx_period = config.get('params', {}).get('adx_period', 14)
        self.adx_threshold = config.get('params', {}).get('adx_threshold', 25)
        self.atr_multiplier = config.get('params', {}).get('atr_multiplier', 2.0)
        self.risk_reward_ratio = config.get('params', {}).get('risk_reward_ratio', 3.0)

        # State
        self._state = {
            'trend_direction': 0,  # 1 = uptrend, -1 = downtrend, 0 = no trend
            'last_signal': None
        }

        self.logger.info(
            f"Trend Following initialized: MA({self.fast_ma},{self.slow_ma}), "
            f"ADX({self.adx_period}, {self.adx_threshold})"
        )

    def on_bar(self, bar: pd.Series) -> Optional[Signal]:
        """
        Process new bar and check for trend following signals.

        Args:
            bar: Latest bar with indicators

        Returns:
            Signal if trend continuation setup detected, None otherwise
        """
        # Need required indicators
        required_cols = ['close', 'high', 'low', 'atr']
        if not all(col in bar for col in required_cols):
            return None

        # Check for ADX
        adx_col = f'adx_{self.adx_period}' if f'adx_{self.adx_period}' in bar else 'adx'
        if adx_col not in bar:
            return None

        # Check for moving averages
        fast_ma_col = f'sma_{self.fast_ma}' if f'sma_{self.fast_ma}' in bar else f'ema_{self.fast_ma}'
        slow_ma_col = f'sma_{self.slow_ma}' if f'sma_{self.slow_ma}' in bar else f'ema_{self.slow_ma}'

        if fast_ma_col not in bar or slow_ma_col not in bar:
            return None

        close = bar['close']
        high = bar['high']
        low = bar['low']
        atr = bar['atr']
        adx = bar[adx_col]
        fast_ma = bar[fast_ma_col]
        slow_ma = bar[slow_ma_col]

        # Check for trend direction and strength
        ma_trend = 1 if fast_ma > slow_ma else -1  # 1 = uptrend, -1 = downtrend
        trend_strength = adx >= self.adx_threshold

        # Update trend state
        if trend_strength:
            self._state['trend_direction'] = ma_trend
        else:
            self._state['trend_direction'] = 0

        # Only trade if we have a confirmed trend
        if not trend_strength or self._state['trend_direction'] == 0:
            return None

        # Bullish trend continuation: Price above fast MA, fast MA above slow MA, strong uptrend
        if (self._state['trend_direction'] == 1 and  # Uptrend confirmed
            close > fast_ma and                    # Price above fast MA
            fast_ma > slow_ma and                  # Fast MA above slow MA
            low <= fast_ma * 1.002):              # Recent dip to fast MA (pullback)

            # Calculate entry and stops
            entry_price = close
            stop_loss = slow_ma  # Stop below slow MA
            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * self.risk_reward_ratio)

            return Signal(
                id=self.generate_signal_id(),
                timestamp=bar.name,
                symbol=self.config.get('params', {}).get('symbol', 'UNKNOWN'),
                timeframe=self.config.get('timeframe', '1H'),
                side=SignalType.LONG,
                action='BUY',
                price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence=0.80,
                reason=f"Trend continuation uptrend (ADX={adx:.1f})",
                metadata={
                    'strategy_type': 'trend_following',
                    'trend_direction': 'up',
                    'adx': float(adx),
                    'fast_ma': float(fast_ma),
                    'slow_ma': float(slow_ma),
                    'risk': float(risk),
                    'reward': float(risk * self.risk_reward_ratio)
                }
            )

        # Bearish trend continuation: Price below fast MA, fast MA below slow MA, strong downtrend
        elif (self._state['trend_direction'] == -1 and  # Downtrend confirmed
              close < fast_ma and                      # Price below fast MA
              fast_ma < slow_ma and                    # Fast MA below slow MA
              high >= fast_ma * 0.998):               # Recent rally to fast MA (pullback)

            # Calculate entry and stops
            entry_price = close
            stop_loss = slow_ma  # Stop above slow MA
            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * self.risk_reward_ratio)

            return Signal(
                id=self.generate_signal_id(),
                timestamp=bar.name,
                symbol=self.config.get('params', {}).get('symbol', 'UNKNOWN'),
                timeframe=self.config.get('timeframe', '1H'),
                side=SignalType.SHORT,
                action='SELL',
                price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                confidence=0.80,
                reason=f"Trend continuation downtrend (ADX={adx:.1f})",
                metadata={
                    'strategy_type': 'trend_following',
                    'trend_direction': 'down',
                    'adx': float(adx),
                    'fast_ma': float(fast_ma),
                    'slow_ma': float(slow_ma),
                    'risk': float(risk),
                    'reward': float(risk * self.risk_reward_ratio)
                }
            )

        return None



