"""
Data Layer Module

Handles market data normalization, indicator calculation, and data preparation
for trading strategies. Provides unified interface for OHLCV data processing.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime


class DataLayer:
    """
    Data processing and normalization layer.
    
    Handles OHLCV data normalization, indicator calculation, and
    data preparation for strategies.
    """
    
    def __init__(self, cache_enabled: bool = True):
        """
        Initialize data layer.
        
        Args:
            cache_enabled: Enable data caching for performance
        """
        self.cache_enabled = cache_enabled
        self.logger = logging.getLogger("cthulhu.data.layer")
        self._cache = {}
        
    def normalize_rates(self, rates, timeframe: str = None, symbol: str = None) -> pd.DataFrame:
        """
        Normalize MT5 rates data to pandas DataFrame.

        Args:
            rates: MT5 rates data (numpy array or list of tuples)
            timeframe: Optional timeframe string for metadata
            symbol: Optional symbol name (for logging/metadata)

        Returns:
            DataFrame with OHLCV columns and datetime index
        """
        if rates is None or len(rates) == 0:
            self.logger.warning("Empty rates data received")
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(rates)
        # Attach symbol metadata when provided
        if symbol:
            try:
                df.attrs['symbol'] = symbol
            except Exception:
                pass
        
        # Ensure required columns
        required_cols = ['time', 'open', 'high', 'low', 'close', 'tick_volume']
        if not all(col in df.columns for col in required_cols):
            self.logger.error(f"Missing required columns in rates data")
            return pd.DataFrame()
            
        # Rename tick_volume to volume
        df['volume'] = df['tick_volume']
        
        # Convert time to datetime index
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        # Select and order columns
        df = df[['open', 'high', 'low', 'close', 'volume']]
        
        # Add real_volume if available
        has_dtype = hasattr(rates, 'dtype')
        if has_dtype and 'real_volume' in rates.dtype.names:
            df['real_volume'] = rates['real_volume']
            
        # Add spread if available
        if has_dtype and 'spread' in rates.dtype.names:
            df['spread'] = rates['spread']
            
        self.logger.debug(f"Normalized {len(df)} bars with columns: {list(df.columns)}")
        
        return df
        
    def add_indicators(self, data: pd.DataFrame, indicators: List) -> pd.DataFrame:
        """
        Add technical indicators to data.
        
        Args:
            data: DataFrame with OHLCV data
            indicators: List of Indicator instances
            
        Returns:
            DataFrame with added indicator columns
        """
        if data.empty:
            return data
            
        df = data.copy()
        
        for indicator in indicators:
            try:
                self.logger.debug(f"Calculating {indicator.name}")
                result = indicator.calculate(df)
                
                # Merge indicator results
                if isinstance(result, pd.Series):
                    df[result.name] = result
                elif isinstance(result, pd.DataFrame):
                    for col in result.columns:
                        df[col] = result[col]
                        
            except Exception as e:
                self.logger.error(f"Error calculating {indicator.name}: {e}", exc_info=True)
                
        return df
        
    def add_ema(self, data: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """
        Add EMA (Exponential Moving Average) to data.
        
        Args:
            data: DataFrame with close prices
            periods: List of EMA periods to calculate
            
        Returns:
            DataFrame with EMA columns added
        """
        df = data.copy()
        
        for period in periods:
            col_name = f'ema_{period}'
            df[col_name] = df['close'].ewm(span=period, adjust=False).mean()
            
        return df
        
    def add_sma(self, data: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """
        Add SMA (Simple Moving Average) to data.
        
        Args:
            data: DataFrame with close prices
            periods: List of SMA periods to calculate
            
        Returns:
            DataFrame with SMA columns added
        """
        df = data.copy()
        
        for period in periods:
            col_name = f'sma_{period}'
            df[col_name] = df['close'].rolling(window=period).mean()
            
        return df
        
    def add_atr(self, data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Add ATR (Average True Range) to data.
        
        Args:
            data: DataFrame with OHLC data
            period: ATR period
            
        Returns:
            DataFrame with ATR column added
        """
        df = data.copy()
        
        # Calculate True Range
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        # Calculate ATR as EMA of True Range
        df['atr'] = true_range.ewm(span=period, adjust=False).mean()
        
        return df
        
    def add_volume_analysis(self, data: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        Add volume analysis metrics.
        
        Args:
            data: DataFrame with volume data
            period: Lookback period
            
        Returns:
            DataFrame with volume analysis columns
        """
        df = data.copy()
        
        # Average volume
        df[f'volume_avg_{period}'] = df['volume'].rolling(window=period).mean()
        
        # Volume ratio
        df['volume_ratio'] = df['volume'] / df[f'volume_avg_{period}']
        
        # Volume trend
        df['volume_trend'] = df['volume'].rolling(window=period).apply(
            lambda x: 1 if x.iloc[-1] > x.mean() else -1, raw=False
        )
        
        return df
        
    def add_price_levels(self, data: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        Add support/resistance levels based on recent highs/lows.
        
        Args:
            data: DataFrame with OHLC data
            period: Lookback period
            
        Returns:
            DataFrame with price level columns
        """
        df = data.copy()
        
        # Recent high/low
        df[f'high_{period}'] = df['high'].rolling(window=period).max()
        df[f'low_{period}'] = df['low'].rolling(window=period).min()
        
        # Range
        df[f'range_{period}'] = df[f'high_{period}'] - df[f'low_{period}']
        
        # Position in range (0-1)
        df[f'position_in_range_{period}'] = (
            (df['close'] - df[f'low_{period}']) / df[f'range_{period}']
        ).fillna(0.5)
        
        return df
        
    def prepare_strategy_data(self, data: pd.DataFrame, strategy_config: Dict[str, Any]) -> pd.DataFrame:
        """
        Prepare data for a specific strategy.
        
        Args:
            data: Base OHLCV DataFrame
            strategy_config: Strategy configuration
            
        Returns:
            DataFrame with all required indicators for strategy
        """
        df = data.copy()
        
        strategy_type = strategy_config.get('type', '').lower()
        params = strategy_config.get('params', {})
        
        # Add strategy-specific indicators
        if strategy_type in ['sma_crossover']:
            fast_period = params.get('fast_period', params.get('short_window', 20))
            slow_period = params.get('slow_period', params.get('long_window', 50))
            df = self.add_sma(df, [fast_period, slow_period])
            df = self.add_atr(df, params.get('atr_period', 14))
            
        elif strategy_type in ['ema_crossover', 'scalping']:
            fast_period = params.get('fast_period', params.get('fast_ema', 9))
            slow_period = params.get('slow_period', params.get('slow_ema', 21))
            df = self.add_ema(df, [fast_period, slow_period])
            df = self.add_atr(df, params.get('atr_period', 14))
            
        elif strategy_type == 'momentum_breakout':
            lookback = params.get('lookback_period', 20)
            df = self.add_price_levels(df, lookback)
            df = self.add_volume_analysis(df, lookback)
            df = self.add_atr(df, params.get('atr_period', 14))
            
        return df
        
    def resample(self, data: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
        """
        Resample data to different timeframe.
        
        Args:
            data: DataFrame with OHLCV data
            target_timeframe: Target timeframe (e.g., '5T', '15T', '1H', '1D')
            
        Returns:
            Resampled DataFrame
        """
        if data.empty:
            return data
            
        # Resample OHLCV data
        resampled = data.resample(target_timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        return resampled
        
    def get_latest_bar(self, data: pd.DataFrame) -> pd.Series:
        """
        Get the most recent complete bar.
        
        Args:
            data: DataFrame with market data
            
        Returns:
            Latest bar as Series
        """
        if data.empty:
            return pd.Series()
            
        return data.iloc[-1]
        
    def clear_cache(self):
        """Clear cached data."""
        self._cache.clear()
        self.logger.info("Data cache cleared")
