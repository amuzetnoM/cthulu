"""
Data Layer - Clean Implementation
Centralized data access with caching and indicator calculation.
"""
import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataLayer:
    """
    Centralized data access layer.
    
    Responsibilities:
    - Fetch OHLCV data from connector
    - Cache data to reduce MT5 calls
    - Provide data to strategies and indicators
    """
    
    def __init__(self, connector, config: Dict[str, Any]):
        """
        Initialize data layer.
        
        Args:
            connector: MT5 connector
            config: System configuration
        """
        self.connector = connector
        self.config = config
        
        # Cache
        self._cache: Dict[str, pd.DataFrame] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_ttl = config.get('data', {}).get('cache_ttl_seconds', 5)
        
        logger.info("DataLayer initialized")
    
    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "M5",
        count: int = 200
    ) -> Optional[pd.DataFrame]:
        """
        Get OHLCV data for symbol.
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe (M1, M5, M15, H1, etc.)
            count: Number of bars
            
        Returns:
            DataFrame with columns: time, open, high, low, close, volume
        """
        import time
        
        cache_key = f"{symbol}_{timeframe}_{count}"
        now = time.time()
        
        # Check cache
        if cache_key in self._cache:
            cache_age = now - self._cache_timestamps.get(cache_key, 0)
            if cache_age < self._cache_ttl:
                return self._cache[cache_key].copy()
        
        # Fetch from connector
        try:
            data = self.connector.get_ohlcv(symbol, timeframe, count)
            
            if data is not None and len(data) > 0:
                # Ensure column names are lowercase
                data.columns = [c.lower() for c in data.columns]
                
                # Cache it
                self._cache[cache_key] = data
                self._cache_timestamps[cache_key] = now
                
                return data.copy()
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
        
        return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol."""
        try:
            tick = self.connector.get_tick(symbol)
            if tick:
                return (tick['bid'] + tick['ask']) / 2
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
        
        return None
    
    def get_spread(self, symbol: str) -> float:
        """Get current spread in points."""
        try:
            tick = self.connector.get_tick(symbol)
            if tick:
                return tick['ask'] - tick['bid']
        except Exception as e:
            logger.error(f"Error getting spread: {e}")
        
        return 0.0
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Data cache cleared")


def get_current_price(symbol: str) -> Optional[float]:
    """
    Convenience function to get current price.
    
    Note: This requires a global data layer instance or connector.
    Used for backward compatibility with old imports.
    """
    logger.warning("get_current_price called without DataLayer - returning None")
    return None
