"""
Cthulu Trading Loop Module

This module contains the core trading loop logic, extracted from __main__.py
for better modularity, testability, and maintainability.

The trading loop handles:
- Market data ingestion
- Dynamic indicator calculation
- Signal generation
- Risk approval and position sizing
- Order execution
- Position monitoring
- Exit strategy evaluation
- Health checks and reconnection

All error handling, logging, and state management is preserved from the original implementation.
"""

import time
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import pandas as pd

from cthulu.strategy.base import Strategy, SignalType
from cthulu.execution.engine import ExecutionEngine, OrderRequest, OrderType, OrderStatus
from cthulu.risk.evaluator import RiskEvaluator
from cthulu.position.tracker import PositionTracker
from cthulu.position.lifecycle import PositionLifecycle
from cthulu.position.adoption import TradeAdoptionManager, TradeAdoptionPolicy
from cthulu.persistence.database import Database, TradeRecord, SignalRecord
from cthulu.observability.metrics import MetricsCollector
from cthulu.connector.mt5_connector import MT5Connector
from cthulu.data.layer import DataLayer


@dataclass
class TradingLoopContext:
    """
    Context object containing all dependencies needed by the trading loop.
    
    This dataclass provides clean dependency injection and makes the trading
    loop testable in isolation.
    """
    # Core trading components
    connector: MT5Connector
    data_layer: DataLayer
    execution_engine: ExecutionEngine
    risk_manager: RiskEvaluator
    position_tracker: PositionTracker
    position_lifecycle: PositionLifecycle
    trade_adoption_manager: TradeAdoptionManager
    exit_coordinator: PositionLifecycle
    database: Database
    metrics: MetricsCollector
    logger: logging.Logger
    
    # Configuration
    symbol: str
    timeframe: Any  # MT5 timeframe constant
    poll_interval: int
    lookback_bars: int
    dry_run: bool
    
    # Trading components
    indicators: List[Any]
    exit_strategies: List[Any]
    trade_adoption_policy: TradeAdoptionPolicy
    config: Dict[str, Any]
    
    # Optional components
    strategy: Optional[Strategy] = None
    advisory_manager: Optional[Any] = None
    exporter: Optional[Any] = None  # Prometheus exporter
    ml_collector: Optional[Any] = None
    position_manager: Optional[Any] = None
    summary_path: Optional[Any] = None
    persist_summary_fn: Optional[Any] = None
    
    # CLI args
    args: Optional[Any] = None


def ensure_runtime_indicators(df: pd.DataFrame, indicators: List, strategy: Strategy, 
                               config: Dict[str, Any], logger: logging.Logger) -> List:
    """
    Ensure indicators required by the active strategy/config are present.
    
    This function inspects the given strategy and configuration to find
    indicators (or indicator parameters) that the strategies expect to exist
    in the market data (e.g., EMA periods, RSI period, ADX). If missing,
    it creates indicator instances (temporary) and returns them so the
    main loop will calculate their columns during the same iteration.
    
    Args:
        df: Market data DataFrame
        indicators: List of configured indicators
        strategy: Trading strategy instance
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        List of additional indicator instances to add
    """
    from cthulu.indicators.rsi import RSI
    from cthulu.indicators.adx import ADX
    from cthulu.indicators.atr import ATR
    # Optional runtime indicators
    try:
        from cthulu.indicators.macd import MACD
    except Exception:
        MACD = None
    try:
        from cthulu.indicators.bollinger import BollingerBands
    except Exception:
        BollingerBands = None
    try:
        from cthulu.indicators.stochastic import Stochastic
    except Exception:
        Stochastic = None
    try:
        from cthulu.indicators.supertrend import Supertrend
    except Exception:
        Supertrend = None
    try:
        from cthulu.indicators.vwap import VWAP
    except Exception:
        VWAP = None
    
    required_emas = set()
    extra_indicators = []
    
    def collect_ema_periods(obj):
        if obj is None:
            return
        for attr in ('fast_period', 'slow_period', 'fast_ema', 'slow_ema', 'short_window', 'long_window'):
            if hasattr(obj, attr):
                try:
                    val = int(getattr(obj, attr))
                    if 'ema' in attr or 'fast_period' in attr or 'slow_period' in attr or 'fast_ema' in attr or 'slow_ema' in attr:
                        required_emas.add(val)
                except Exception:
                    pass
    
    # Strategy instance inspection
    try:
        from cthulu.strategy.strategy_selector import StrategySelector
        if isinstance(strategy, StrategySelector):
            for s in strategy.strategies.values():
                collect_ema_periods(s)
        else:
            collect_ema_periods(strategy)
    except Exception:
        collect_ema_periods(strategy)
    
    # Also check config-level strategies
    try:
        strat_cfg = config.get('strategy', {}) if isinstance(config, dict) else {}
        if strat_cfg.get('type') == 'dynamic':
            for s in strat_cfg.get('strategies', []):
                params = s.get('params', {}) if isinstance(s.get('params', {}), dict) else {}
                for attr in ('fast_period', 'slow_period', 'fast_ema', 'slow_ema'):
                    if attr in params and params[attr]:
                        try:
                            required_emas.add(int(params[attr]))
                        except Exception:
                            pass
        else:
            params = strat_cfg.get('params', {}) if isinstance(strat_cfg.get('params', {}), dict) else {}
            for attr in ('fast_period', 'slow_period', 'fast_ema', 'slow_ema'):
                if attr in params and params[attr]:
                    try:
                        required_emas.add(int(params[attr]))
                    except Exception:
                        pass
    except Exception:
        pass
    
    # Check for RSI requirement
    needs_rsi = False
    rsi_period = 14  # default
    try:
        # If strategy is a selector, check sub-strategies for RSI needs
        from cthulu.strategy.strategy_selector import StrategySelector
        if isinstance(strategy, StrategySelector):
            for s in strategy.strategies.values():
                if hasattr(s, 'rsi_period'):
                    needs_rsi = True
                    rsi_period = int(getattr(s, 'rsi_period'))
                    break
                if hasattr(s, 'rsi_oversold') or hasattr(s, 'rsi_overbought'):
                    needs_rsi = True
                    break
        else:
            if hasattr(strategy, 'rsi_period'):
                needs_rsi = True
                rsi_period = int(strategy.rsi_period)
            elif hasattr(strategy, 'rsi_oversold') or hasattr(strategy, 'rsi_overbought'):
                needs_rsi = True
    except Exception:
        pass
    
    # Check if RSI already exists
    if needs_rsi:
        # Ensure we add the strategy-specific RSI period (and also add default rsi if desired)
        rsi_col = f'rsi_{rsi_period}' if rsi_period != 14 else 'rsi'
        has_rsi = rsi_col in df.columns or any(getattr(i, 'name', '').upper() == 'RSI' for i in indicators)
        if not has_rsi:
            extra_indicators.append(RSI(period=rsi_period))
            logger.debug(f"Added runtime RSI indicator (period={rsi_period})")
    else:
        # Check config-level dynamic strategies for RSI needs as a fallback
        try:
            strat_cfg = config.get('strategy', {}) if isinstance(config, dict) else {}
            if strat_cfg.get('type') == 'dynamic':
                for s in strat_cfg.get('strategies', []):
                    params = s.get('params', {}) if isinstance(s.get('params', {}), dict) else {}
                    if 'rsi_period' in params and params['rsi_period']:
                        rp = int(params['rsi_period'])
                        rsi_col = f'rsi_{rp}' if rp != 14 else 'rsi'
                        if rsi_col not in df.columns and not any(getattr(i, 'name', '').upper() == 'RSI' for i in indicators):
                            extra_indicators.append(RSI(period=rp))
                            logger.debug(f"Added runtime RSI indicator from config (period={rp})")
                            break
        except Exception:
            pass
    
    # Check for ATR requirement
    needs_atr = False
    atr_period = 14
    try:
        if hasattr(strategy, 'atr_period'):
            needs_atr = True
            atr_period = int(strategy.atr_period)
        elif hasattr(strategy, 'use_atr') and strategy.use_atr:
            needs_atr = True
        # Strategy name-based heuristic (scalping strategies often need ATR)
        elif getattr(strategy, 'name', '').lower().find('scalp') != -1 or strategy.__class__.__name__.lower().find('scalp') != -1:
            needs_atr = True
    except Exception:
        pass
    
    if needs_atr:
        has_atr = 'atr' in df.columns or any(getattr(i, 'name', '').upper() == 'ATR' for i in indicators)
        if not has_atr:
            extra_indicators.append(ATR(period=atr_period))
            logger.debug(f"Added runtime ATR indicator (period={atr_period})")
    
    # Check for ADX requirement
    needs_adx = False
    try:
        from cthulu.strategy.strategy_selector import StrategySelector
        if isinstance(strategy, StrategySelector):
            needs_adx = True  # Dynamic selector uses ADX for regime detection
    except Exception:
        pass
    
    if needs_adx:
        has_adx = 'adx' in df.columns or any(getattr(i, 'name', '').upper() == 'ADX' for i in indicators)
        if not has_adx:
            extra_indicators.append(ADX(period=14))
            logger.debug("Added runtime ADX indicator for regime detection")

    # Check config-specified indicators and add runtime instances when requested
    try:
        conf_inds = config.get('indicators', []) if isinstance(config, dict) else []
        for ind in conf_inds:
            try:
                t = (ind.get('type') or '').lower()
                params = ind.get('params', {}) or {}
                if t in ('macd',) and MACD is not None:
                    extra_indicators.append(MACD(**params))
                elif t in ('bollinger', 'bollingerbands') and BollingerBands is not None:
                    extra_indicators.append(BollingerBands(**params))
                elif t in ('stochastic',) and Stochastic is not None:
                    extra_indicators.append(Stochastic(**params))
                elif t in ('supertrend',) and Supertrend is not None:
                    # Accept common alias 'atr_multiplier' -> 'multiplier'
                    try:
                        if 'atr_multiplier' in params and 'multiplier' not in params:
                            params = dict(params)
                            params['multiplier'] = params.pop('atr_multiplier')
                    except Exception:
                        pass
                    extra_indicators.append(Supertrend(**params))
                elif t in ('vwap',) and VWAP is not None:
                    extra_indicators.append(VWAP(**params))
            except Exception:
                continue
    except Exception:
        pass

    # Special-case: for scalping strategies, ensure an ATR column is present immediately
    try:
        strat_name = getattr(strategy, 'name', '') or strategy.__class__.__name__
        if (('scalp' in str(strat_name).lower()) or ('scalp' in strategy.__class__.__name__.lower())) and 'atr' not in df.columns:
            try:
                # Compute ATR fallback directly and attach in-place
                from cthulu.indicators.atr import ATR
                atr_ind = ATR(period=getattr(strategy, 'atr_period', 14))
                atr_series = atr_ind.calculate(df)
                if atr_series is not None:
                    if isinstance(atr_series, pd.Series):
                        df['atr'] = atr_series
                    else:
                        # If DataFrame, pick primary 'atr' column if present
                        if 'atr' in atr_series.columns:
                            df['atr'] = atr_series['atr']
                        else:
                            df['atr'] = atr_series.iloc[:, 0]
                # Remove any ATR instance from extra_indicators to avoid duplicate joins
                try:
                    extra_indicators = [i for i in extra_indicators if i.__class__.__name__.upper() != 'ATR']
                except Exception:
                    pass
            except Exception:
                logger.exception('Failed to compute inline ATR for scalping strategy')
    except Exception:
        pass
    
    return extra_indicators


class TradingLoop:
    """
    Main trading loop implementation.
    
    This class encapsulates the core trading loop logic, making it testable
    and maintainable while preserving all error handling and state management.
    """
    
    def __init__(self, context: TradingLoopContext):
        """
        Initialize the trading loop with its context.
        
        Args:
            context: TradingLoopContext containing all dependencies
        """
        self.ctx = context
        self.loop_count = 0
        self._shutdown_requested = False
    
    def request_shutdown(self):
        """Request graceful shutdown of the trading loop."""
        self._shutdown_requested = True
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_requested
    
    def run(self) -> int:
        """
        Execute the main trading loop.
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
        self.ctx.logger.info("Starting autonomous trading loop...")
        self.ctx.logger.info("Press Ctrl+C to shutdown gracefully")
        
        try:
            while not self._shutdown_requested:
                self.loop_count += 1
                loop_start = datetime.now()
                self.ctx.logger.debug(f"Loop #{self.loop_count} started at {loop_start}")
                
                # Execute one iteration of the trading loop
                try:
                    self._execute_loop_iteration()
                except Exception as e:
                    self.ctx.logger.error(f"Error in loop iteration: {e}", exc_info=True)
                
                # Wait for next cycle
                loop_duration = (datetime.now() - loop_start).total_seconds()
                self.ctx.logger.debug(f"Loop completed in {loop_duration:.2f}s")
                
                sleep_time = max(0, self.ctx.poll_interval - loop_duration)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                # Debug/testing: exit after max_loops if requested
                try:
                    if self.ctx.args and getattr(self.ctx.args, 'max_loops', 0) and \
                       self.loop_count >= int(self.ctx.args.max_loops):
                        self.ctx.logger.info(f"Reached max_loops={self.ctx.args.max_loops}; exiting main loop for test")
                        break
                except Exception:
                    pass
        
        except KeyboardInterrupt:
            self.ctx.logger.info("Keyboard interrupt received")
            raise  # Re-raise to allow main shutdown handler to catch it
        except Exception as e:
            self.ctx.logger.error(f"Fatal error in main loop: {e}", exc_info=True)
            return 1
        
        return 0
    
    def _execute_loop_iteration(self):
        """Execute one iteration of the trading loop."""
        # 1. Market data ingestion
        self.ctx.logger.info(f"Loop #{self.loop_count}: Fetching market data...")
        df = self._ingest_market_data()
        if df is None:
            self.ctx.logger.warning("No market data received, skipping iteration")
            return
        
        # 2. Calculate indicators
        self.ctx.logger.info(f"Loop #{self.loop_count}: Calculating indicators...")
        df = self._calculate_indicators(df)
        if df is None:
            self.ctx.logger.warning("Indicator calculation failed")
            return
        
        # 3. Generate strategy signals
        self.ctx.logger.info(f"Loop #{self.loop_count}: Generating signals...")
        signal = self._generate_signal(df)
        
        # 4. Process entry signals
        if signal:
            self._process_entry_signal(signal)
        
        # 5. Scan and adopt external trades
        self._adopt_external_trades()
        
        # 6. Monitor positions and check exits
        self._monitor_positions(df)
        
        # 7. Health monitoring
        self._check_connection_health()
        
        # 8. Performance monitoring
        self._report_performance_metrics()
    
    def _ingest_market_data(self) -> Optional[pd.DataFrame]:
        """
        Ingest market data from MT5.
        
        Returns:
            DataFrame with market data, or None on error
        """
        try:
            rates = self.ctx.connector.get_rates(
                symbol=self.ctx.symbol,
                timeframe=self.ctx.timeframe,
                count=self.ctx.lookback_bars
            )
            
            if rates is None or len(rates) == 0:
                self.ctx.logger.warning("No market data received, skipping cycle")
                time.sleep(self.ctx.poll_interval)
                return None
            
            df = self.ctx.data_layer.normalize_rates(rates, symbol=self.ctx.symbol)
            self.ctx.logger.debug(f"Retrieved {len(df)} bars for {self.ctx.symbol}")
            return df
        
        except Exception as e:
            self.ctx.logger.error(f"Market data error: {e}", exc_info=True)
            time.sleep(self.ctx.poll_interval)
            return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Calculate all required indicators.
        
        Args:
            df: Market data DataFrame
            
        Returns:
            DataFrame with indicators, or None on error
        """
        try:
            # Calculate SMA indicators for strategy (use strategy params when available)
            try:
                short_w = getattr(self.ctx.strategy, 'short_window', None)
                long_w = getattr(self.ctx.strategy, 'long_window', None)
                if short_w and long_w:
                    df[f'sma_{short_w}'] = df['close'].rolling(window=int(short_w)).mean()
                    df[f'sma_{long_w}'] = df['close'].rolling(window=int(long_w)).mean()
                else:
                    # Fallback to legacy defaults
                    df['sma_20'] = df['close'].rolling(window=20).mean()
                    df['sma_50'] = df['close'].rolling(window=50).mean()
            except Exception:
                # If anything goes wrong, compute defaults and continue
                df['sma_20'] = df['close'].rolling(window=20).mean()
                df['sma_50'] = df['close'].rolling(window=50).mean()
            
            # Compute required EMA columns for strategies
            df = self._compute_ema_columns(df)
            
            # Add price levels for momentum breakout strategy
            try:
                needs_price_levels = False
                lookback_period = 20  # default
                
                # Check if current strategy is momentum breakout
                if hasattr(self.ctx.strategy, 'lookback_period') or \
                   (hasattr(self.ctx.strategy, '__class__') and 'momentum_breakout' in str(self.ctx.strategy.__class__).lower()):
                    needs_price_levels = True
                    lookback_period = getattr(self.ctx.strategy, 'lookback_period', 20)
                
                # Check if strategy selector contains momentum breakout
                elif hasattr(self.ctx.strategy, 'strategies'):
                    for strategy_name, strategy in self.ctx.strategy.strategies.items():
                        if 'momentum_breakout' in str(strategy.__class__).lower():
                            needs_price_levels = True
                            lookback_period = getattr(strategy, 'lookback_period', 20)
                            break
                
                if needs_price_levels:
                    # Add price levels
                    df[f'high_{lookback_period}'] = df['high'].rolling(window=lookback_period).max()
                    df[f'low_{lookback_period}'] = df['low'].rolling(window=lookback_period).min()
                    
                    # Add volume analysis
                    df[f'volume_avg_{lookback_period}'] = df['volume'].rolling(window=lookback_period).mean()
                    
                    self.ctx.logger.debug(f"Added price levels and volume analysis for lookback period {lookback_period}")
            except Exception as e:
                self.ctx.logger.debug(f"Could not add price levels: {e}")
            
            # Ensure runtime indicators (RSI/ATR/MACD/etc.) are added if the strategy needs them
            try:
                extra_indicators = ensure_runtime_indicators(
                    df, self.ctx.indicators, self.ctx.strategy, self.ctx.config, self.ctx.logger
                )
                if extra_indicators:
                    self.ctx.indicators.extend(extra_indicators)
                    try:
                        names = [getattr(i, 'name', i.__class__.__name__) for i in extra_indicators]
                    except Exception:
                        names = [i.__class__.__name__ for i in extra_indicators]
                    self.ctx.logger.info(f"Added {len(extra_indicators)} runtime indicators: {names}")
            except Exception:
                self.ctx.logger.exception('Failed to ensure runtime indicators')
            
            # Calculate configured indicators (and any runtime-added ones)
            try:
                for indicator in self.ctx.indicators:
                    try:
                        indicator_data = indicator.calculate(df)
                        if indicator_data is None:
                            continue

                        # Normalize Series -> DataFrame
                        if isinstance(indicator_data, pd.Series):
                            series_name = indicator_data.name or getattr(indicator, 'name', indicator.__class__.__name__).lower()
                            indicator_data = indicator_data.to_frame(name=series_name)

                        # Determine a base name for this indicator (use provided 'name' if available)
                        base = getattr(indicator, 'name', None) or indicator.__class__.__name__
                        base = str(base).lower()

                        # Build rename map to avoid column overlaps in df
                        rename_map = {}
                        for col in list(indicator_data.columns):
                            # If column already looks namespaced to this indicator (e.g., 'rsi_7' for RSI),
                            # keep that suffix but prefix with 'runtime_'. If the column equals the base name
                            # (e.g., 'adx'), use 'runtime_adx'. Otherwise namespace under indicator base.
                            if col == base or col.startswith(f"{base}_"):
                                new_col = f"runtime_{col}"
                            else:
                                new_col = f"runtime_{base}_{col}"

                            # Ensure deterministic uniqueness if df already has this column
                            final_col = new_col
                            i = 1
                            while final_col in df.columns:
                                final_col = f"{new_col}_{i}"
                                i += 1

                            if final_col != col:
                                rename_map[col] = final_col

                        if rename_map:
                            indicator_data = indicator_data.rename(columns=rename_map)
                            self.ctx.logger.debug(f"Renamed indicator columns to avoid overlap: {rename_map}")

                        # Join indicator data safely; if any columns overlap pandas will
                        # append the provided suffix to the joined columns to avoid
                        # raising ValueError about overlapping columns.
                        try:
                            df = df.join(indicator_data, how='left', rsuffix=f"_ind_{base}")
                        except Exception:
                            # As a final fallback, explicitly rename overlapping columns
                            # on the indicator side and then join.
                            overlaps = set(df.columns).intersection(indicator_data.columns)
                            if overlaps:
                                rename_map2 = {c: f"{c}_ind_{base}" for c in overlaps}
                                indicator_data = indicator_data.rename(columns=rename_map2)
                            df = df.join(indicator_data, how='left')

                    except Exception:
                        self.ctx.logger.exception(
                            f"Failed to calculate indicator {getattr(indicator, 'name', indicator.__class__.__name__)}"
                        )
            except Exception:
                self.ctx.logger.exception('Failed during indicator calculations')
            
            # Create friendly aliases for commonly-required indicators (so strategies can rely on expected column names)
            try:
                # RSI alias
                rsi_period = getattr(self.ctx.strategy, 'rsi_period', None)
                try:
                    rsi_period_int = int(rsi_period) if rsi_period is not None else None
                except Exception:
                    rsi_period_int = None
                rsi_col = f"rsi_{rsi_period_int}" if rsi_period_int and rsi_period_int != 14 else 'rsi'
                if rsi_col not in df.columns:
                    # find runtime-produced RSI columns (be permissive in matching)
                    rsi_candidates = [c for c in df.columns if 'rsi' in c.lower() and c.startswith('runtime_')]
                    if rsi_candidates:
                        # Prefer candidate that contains the period string, then exact 'rsi', else fallback to first
                        chosen = None
                        if rsi_period_int:
                            for c in rsi_candidates:
                                if f"rsi_{rsi_period_int}" in c.lower():
                                    chosen = c
                                    break
                        if not chosen:
                            for c in rsi_candidates:
                                if c.lower().endswith('rsi') or c.lower().endswith('rsi_'):
                                    chosen = c
                                    break
                        chosen = chosen or rsi_candidates[0]
                        df[rsi_col] = df[chosen]
                        self.ctx.logger.debug(f"Created RSI alias column '{rsi_col}' from '{chosen}'")
                # ATR alias
                if 'atr' not in df.columns:
                    atr_candidates = [c for c in df.columns if c.startswith('runtime_atr')]
                    if atr_candidates:
                        df['atr'] = df[atr_candidates[0]]
                        self.ctx.logger.debug(f"Created ATR alias column 'atr' from '{atr_candidates[0]}'")
                # ADX alias
                if 'adx' not in df.columns:
                    adx_candidates = [c for c in df.columns if 'adx' in c.lower() and c.startswith('runtime_')]
                    if adx_candidates:
                        # pick primary adx value if present
                        chosen = None
                        for c in adx_candidates:
                            if c.lower().endswith('adx') or c == 'runtime_adx':
                                chosen = c
                                break
                        chosen = chosen or adx_candidates[0]
                        df['adx'] = df[chosen]
                        self.ctx.logger.debug(f"Created ADX alias column 'adx' from '{chosen}'")
            except Exception:
                self.ctx.logger.exception('Failed while creating indicator alias columns')

            # Fallback: if required indicators are still missing, compute them directly
            try:
                # RSI fallback
                rsi_col = None
                try:
                    rsi_period = getattr(self.ctx.strategy, 'rsi_period', None)
                    rsi_period_int = int(rsi_period) if rsi_period is not None else None
                    rsi_col = f"rsi_{rsi_period_int}" if rsi_period_int and rsi_period_int != 14 else 'rsi'
                except Exception:
                    rsi_col = 'rsi'

                if rsi_col and rsi_col not in df.columns:
                    try:
                        from cthulu.indicators.rsi import RSI
                        rsi_ind = RSI(period=rsi_period_int or 14)
                        rsi_data = rsi_ind.calculate(df)
                        if isinstance(rsi_data, pd.Series):
                            rsi_name = rsi_data.name or (f"rsi_{rsi_period_int}" if rsi_period_int else 'rsi')
                            rsi_data = rsi_data.to_frame(name=rsi_name)

                        # Rename to runtime-safe column names for joining
                        rename_map = {}
                        for col in list(rsi_data.columns):
                            if col == 'rsi' or col.startswith('rsi_'):
                                new_col = f"runtime_{col}"
                            else:
                                new_col = f"runtime_rsi_{col}"
                            final_col = new_col
                            i = 1
                            while final_col in df.columns:
                                final_col = f"{new_col}_{i}"
                                i += 1
                            if final_col != col:
                                rename_map[col] = final_col

                        if rename_map:
                            rsi_data = rsi_data.rename(columns=rename_map)
                            self.ctx.logger.debug(f"Renamed RSI fallback columns: {rename_map}")

                        # Ensure overlapping columns don't raise merge errors
                        try:
                            df = df.join(rsi_data, how='left', rsuffix="_ind_rsi")
                        except Exception:
                            overlaps = set(df.columns).intersection(rsi_data.columns)
                            if overlaps:
                                rename_map2 = {c: f"{c}_ind_rsi" for c in overlaps}
                                rsi_data = rsi_data.rename(columns=rename_map2)
                            df = df.join(rsi_data, how='left')
                        # create alias if needed
                        if rsi_col not in df.columns:
                            candidates = [c for c in df.columns if 'rsi' in c.lower() and c.startswith('runtime_')]
                            if candidates:
                                chosen = None
                                if rsi_period_int:
                                    for c in candidates:
                                        if f"rsi_{rsi_period_int}" in c.lower():
                                            chosen = c
                                            break
                                chosen = chosen or candidates[0]
                                df[rsi_col] = df[chosen]
                                self.ctx.logger.debug(f"Created RSI alias '{rsi_col}' from '{chosen}' in fallback")
                    except Exception:
                        self.ctx.logger.exception('RSI fallback calculation failed')

                # ATR fallback
                if 'atr' not in df.columns:
                    try:
                        from cthulu.indicators.atr import ATR
                        atr_ind = ATR(period=getattr(self.ctx.strategy, 'atr_period', 14))
                        atr_data = atr_ind.calculate(df)
                        if isinstance(atr_data, pd.Series):
                            atr_name = atr_data.name or 'atr'
                            atr_data = atr_data.to_frame(name=atr_name)

                        # Rename similarly
                        rename_map = {}
                        for col in list(atr_data.columns):
                            if col == 'atr' or col.startswith('atr_'):
                                new_col = f"runtime_{col}"
                            else:
                                new_col = f"runtime_atr_{col}"
                            final_col = new_col
                            i = 1
                            while final_col in df.columns:
                                final_col = f"{new_col}_{i}"
                                i += 1
                            if final_col != col:
                                rename_map[col] = final_col
                        if rename_map:
                            atr_data = atr_data.rename(columns=rename_map)
                        try:
                            df = df.join(atr_data, how='left', rsuffix="_ind_atr")
                        except Exception:
                            overlaps = set(df.columns).intersection(atr_data.columns)
                            if overlaps:
                                rename_map2 = {c: f"{c}_ind_atr" for c in overlaps}
                                atr_data = atr_data.rename(columns=rename_map2)
                            df = df.join(atr_data, how='left')
                        if 'atr' not in df.columns:
                            candidates = [c for c in df.columns if 'atr' in c.lower() and c.startswith('runtime_')]
                            if candidates:
                                df['atr'] = df[candidates[0]]
                                self.ctx.logger.debug(f"Created ATR alias 'atr' from '{candidates[0]}' in fallback")
                    except Exception:
                        self.ctx.logger.exception('ATR fallback calculation failed')
            except Exception:
                self.ctx.logger.exception('Failed during indicator fallback calculations')

            self.ctx.logger.debug(f"Calculated SMA, ATR, and {len(self.ctx.indicators)} additional indicators")
            # Debug: log indicator columns for easy troubleshooting
            try:
                indicator_cols = [c for c in df.columns if any(k in c.lower() for k in ('rsi', 'atr', 'adx'))]
                self.ctx.logger.debug(f"Indicator-related columns: {indicator_cols}")
            except Exception:
                pass
            return df
        
        except Exception as e:
            self.ctx.logger.error(f"Indicator calculation error: {e}", exc_info=True)
            time.sleep(self.ctx.poll_interval)
            return None
    
    def _compute_ema_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute required EMA columns for strategies.
        
        Args:
            df: Market data DataFrame
            
        Returns:
            DataFrame with EMA columns added
        """
        try:
            required_emas = set()
            
            def collect_ema_periods(obj):
                if obj is None:
                    return
                # Common attribute names used across strategies
                for attr in ('fast_period', 'slow_period', 'fast_ema', 'slow_ema', 'short_window', 'long_window'):
                    if hasattr(obj, attr):
                        try:
                            val = int(getattr(obj, attr))
                            # skip sma names (short/long windows already handled)
                            if 'ema' in attr or 'fast_period' in attr or 'slow_period' in attr or 'fast_ema' in attr or 'slow_ema' in attr:
                                required_emas.add(val)
                        except Exception:
                            pass
            
            # If using StrategySelector, inspect child strategies
            try:
                from cthulu.strategy.strategy_selector import StrategySelector
                if isinstance(self.ctx.strategy, StrategySelector):
                    for s in self.ctx.strategy.strategies.values():
                        collect_ema_periods(s)
                else:
                    collect_ema_periods(self.ctx.strategy)
            except Exception:
                collect_ema_periods(self.ctx.strategy)
            
            # Also inspect scalping-specific attrs
            try:
                if hasattr(self.ctx.strategy, 'fast_ema'):
                    required_emas.add(int(getattr(self.ctx.strategy, 'fast_ema')))
                if hasattr(self.ctx.strategy, 'slow_ema'):
                    required_emas.add(int(getattr(self.ctx.strategy, 'slow_ema')))
            except Exception:
                pass
            
            # Fallback: collect EMA periods from configuration to ensure coverage
            try:
                strat_cfg = self.ctx.config.get('strategy', {}) if isinstance(self.ctx.config, dict) else {}
                if strat_cfg.get('type') == 'dynamic':
                    for s in strat_cfg.get('strategies', []):
                        params = s.get('params', {}) if isinstance(s.get('params', {}), dict) else {}
                        for key in ('fast_ema', 'slow_ema', 'fast_period', 'slow_period', 'short_window', 'long_window'):
                            if key in params and params[key]:
                                try:
                                    required_emas.add(int(params[key]))
                                except Exception:
                                    pass
                else:
                    params = strat_cfg.get('params', {}) if isinstance(strat_cfg.get('params', {}), dict) else {}
                    for key in ('fast_ema', 'slow_ema', 'fast_period', 'slow_period', 'short_window', 'long_window'):
                        if key in params and params[key]:
                            try:
                                required_emas.add(int(params[key]))
                            except Exception:
                                pass
                
                # If scalping is part of configured strategies ensure its default EMAs are included
                try:
                    scalping_periods = set()
                    # Check dynamic strategies
                    if strat_cfg.get('type') == 'dynamic':
                        for s in strat_cfg.get('strategies', []):
                            if s.get('type', '').lower() == 'scalping':
                                params = s.get('params', {}) or {}
                                # scalping may define explicit fast_ema/slow_ema
                                if params.get('fast_ema'):
                                    scalping_periods.add(int(params.get('fast_ema')))
                                if params.get('slow_ema'):
                                    scalping_periods.add(int(params.get('slow_ema')))
                    else:
                        if strat_cfg.get('type', '').lower() == 'scalping':
                            params = strat_cfg.get('params', {}) or {}
                            if params.get('fast_ema'):
                                scalping_periods.add(int(params.get('fast_ema')))
                            if params.get('slow_ema'):
                                scalping_periods.add(int(params.get('slow_ema')))
                    
                    # If scalping is present among runtime strategies, add defaults (5,10) as safe fallback
                    try:
                        from cthulu.strategy.strategy_selector import StrategySelector
                        if isinstance(self.ctx.strategy, StrategySelector):
                            if 'scalping' in (name.lower() for name in self.ctx.strategy.strategies.keys()):
                                scalping_periods.update({5, 10})
                    except Exception:
                        # Direct strategy instance
                        try:
                            if getattr(self.ctx.strategy, 'name', '').lower() == 'scalping':
                                scalping_periods.update({
                                    getattr(self.ctx.strategy, 'fast_ema', 5),
                                    getattr(self.ctx.strategy, 'slow_ema', 10)
                                })
                        except Exception:
                            pass
                    
                    required_emas.update({int(x) for x in scalping_periods if x})
                except Exception:
                    pass
                
                self.ctx.logger.debug(f"Collected EMA periods from config: {sorted(required_emas)}")
            except Exception:
                pass
            
            # Compute EMA columns
            if required_emas:
                for p in sorted(required_emas):
                    col = f'ema_{p}'
                    if col not in df.columns:
                        df[col] = df['close'].ewm(span=int(p), adjust=False).mean()
                self.ctx.logger.debug(f"Computed EMA columns: {[f'ema_{p}' for p in sorted(required_emas)]}")
        except Exception:
            self.ctx.logger.exception('Failed to compute EMA columns; continuing')
        
        return df
    
    def _generate_signal(self, df: pd.DataFrame):
        """
        Generate trading signal from strategy.
        
        Args:
            df: Market data DataFrame with indicators
            
        Returns:
            Signal object or None
        """
        try:
            current_bar = df.iloc[-1]
            
            # Diagnostic: log presence of RSI/ATR before strategy signal generation
            try:
                rsi_period = getattr(self.ctx.strategy, 'rsi_period', None)
                try:
                    rsi_period_int = int(rsi_period) if rsi_period is not None else None
                except Exception:
                    rsi_period_int = None
                rsi_col = f"rsi_{rsi_period_int}" if rsi_period_int and rsi_period_int != 14 else 'rsi'
                has_rsi = rsi_col in current_bar.index
                has_atr = 'atr' in current_bar.index
                self.ctx.logger.debug(f"Before strategy signal: has_rsi={has_rsi} (col={rsi_col}), has_atr={has_atr}")
                if has_rsi:
                    self.ctx.logger.debug(f"rsi value: {current_bar.get(rsi_col)}")
                if has_atr:
                    self.ctx.logger.debug(f"atr value: {current_bar.get('atr')}")
            except Exception:
                self.ctx.logger.exception('Failed to log indicator presence before strategy signal')
            
            # If dynamic selector, use its generator method
            try:
                from cthulu.strategy.strategy_selector import StrategySelector
                if isinstance(self.ctx.strategy, StrategySelector):
                    signal = self.ctx.strategy.generate_signal(df, current_bar)
                else:
                    signal = self.ctx.strategy.on_bar(current_bar)
            except Exception:
                # Fallback by duck-typing
                if hasattr(self.ctx.strategy, 'generate_signal'):
                    signal = self.ctx.strategy.generate_signal(df, current_bar)
                else:
                    signal = self.ctx.strategy.on_bar(current_bar)
            
            if signal:
                self.ctx.logger.info(
                    f"Signal generated: {signal.side.name} {signal.symbol} "
                    f"(confidence: {signal.confidence:.2f})"
                )
            else:
                self.ctx.logger.info("Strategy returned NO SIGNAL for this bar")
            
            return signal
        
        except Exception as e:
            self.ctx.logger.error(f"Strategy signal error: {e}", exc_info=True)
            return None
    
    def _process_entry_signal(self, signal):
        """
        Process an entry signal (risk approval + execution).
        
        Args:
            signal: Trading signal from strategy
        """
        if signal.side not in [SignalType.LONG, SignalType.SHORT]:
            return
        
        try:
            # Get current account info and positions
            account_info = self.ctx.connector.get_account_info()
            current_positions = len(self.ctx.position_manager.get_positions(symbol=self.ctx.symbol))
            
            # Risk approval
            approved, reason, position_size = self.ctx.risk_manager.approve(
                signal=signal,
                account_info=account_info,
                current_positions=current_positions
            )
            
            if approved:
                self.ctx.logger.info(f"Risk approved: {position_size:.2f} lots - {reason}")
                
                if not self.ctx.dry_run:
                    self._execute_order(signal, position_size)
                else:
                    self.ctx.logger.info("[DRY RUN] Would place order here")
            else:
                self.ctx.logger.info(f"Risk rejected: {reason}")
        
        except Exception as e:
            self.ctx.logger.error(f"Order execution error: {e}", exc_info=True)
    
    def _execute_order(self, signal, position_size: float):
        """
        Execute an order based on signal.
        
        Args:
            signal: Trading signal
            position_size: Approved position size in lots
        """
        # Create order request
        order_req = OrderRequest(
            signal_id=signal.id,
            symbol=signal.symbol,
            side="BUY" if signal.side == SignalType.LONG else "SELL",
            volume=position_size,
            order_type=OrderType.MARKET,
            sl=signal.stop_loss,
            tp=signal.take_profit
        )
        
        # Advisory / ghost handling
        try:
            if self.ctx.advisory_manager and self.ctx.advisory_manager.enabled:
                decision = self.ctx.advisory_manager.decide(order_req, signal)
            else:
                decision = {'action': 'execute', 'result': None}
        except Exception:
            self.ctx.logger.exception('Advisory manager decision failed; defaulting to execute')
            decision = {'action': 'execute', 'result': None}
        
        if decision['action'] == 'execute':
            self._execute_real_order(order_req, signal)
        elif decision['action'] == 'advisory':
            self._record_advisory_signal(signal)
        elif decision['action'] == 'ghost':
            self._record_ghost_signal(signal, decision.get('result'))
        else:
            self.ctx.logger.warning('Advisory manager rejected order request')
    
    def _execute_real_order(self, order_req: OrderRequest, signal):
        """Execute a real order."""
        self.ctx.logger.info(f"Placing {order_req.side} order for {order_req.volume} lots")
        result = self.ctx.execution_engine.place_order(order_req)
        
        if result.status == OrderStatus.FILLED:
            self.ctx.logger.info(
                f"Order filled: ticket={result.order_id}, "
                f"price={result.fill_price:.5f}"
            )
            
            # Track position
            self.ctx.position_manager.track_position(result, signal_metadata=signal.metadata)
            
            # Record in database
            signal_record = SignalRecord(
                timestamp=signal.timestamp,
                symbol=signal.symbol,
                side=signal.side.name,
                confidence=signal.confidence,
                price=result.fill_price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                metadata=signal.metadata,
                executed=True,
                execution_timestamp=datetime.now()
            )
            # compatibility: set strategy_name after construction in case dataclass signature differs
            try:
                signal_record.strategy_name = self.ctx.strategy.__class__.__name__
            except Exception:
                pass
            self.ctx.database.record_signal(signal_record)
            
            trade_record = TradeRecord(
                signal_id=signal.id,
                order_id=result.order_id,
                symbol=signal.symbol,
                side=signal.side.name,
                entry_price=result.fill_price,
                volume=result.filled_volume,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                entry_time=datetime.now(),
                commission=result.commission
            )
            self.ctx.database.record_trade(trade_record)
        else:
            self.ctx.logger.error(
                f"Order failed: {result.status.name} - {result.message}"
            )
    
    def _record_advisory_signal(self, signal):
        """Record an advisory (non-executed) signal."""
        self.ctx.logger.info('Advisory decision: not executing order; recording advisory signal')
        signal_record = SignalRecord(
            timestamp=signal.timestamp,
            symbol=signal.symbol,
            side=signal.side.name,
            confidence=signal.confidence,
            price=None,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            metadata={**signal.metadata, 'advisory': True},
            executed=False
        )
        # compatibility: set strategy_name after construction
        try:
            signal_record.strategy_name = self.ctx.strategy.__class__.__name__
        except Exception:
            pass
        self.ctx.database.record_signal(signal_record)
    
    def _record_ghost_signal(self, signal, result):
        """Record a ghost trade signal."""
        self.ctx.logger.info('Ghost decision: small test trade executed (or attempted)')
        signal_record = SignalRecord(
            timestamp=signal.timestamp,
            symbol=signal.symbol,
            side=signal.side.name,
            confidence=signal.confidence,
            price=getattr(result, 'fill_price', None) if result else None,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            metadata={
                **signal.metadata,
                'advisory': 'ghost',
                'advisory_result': getattr(result, 'order_id', None) if result else None
            },
            executed=False
        )
        # compatibility: set strategy_name after construction
        try:
            signal_record.strategy_name = self.ctx.strategy.__class__.__name__
        except Exception:
            pass
        self.ctx.database.record_signal(signal_record)
    
    def _adopt_external_trades(self):
        """Scan and adopt external trades if enabled."""
        try:
            if self.ctx.trade_adoption_policy and getattr(self.ctx.trade_adoption_policy, 'enabled', False):
                adopted = self.ctx.trade_adoption_manager.scan_and_adopt()
                if adopted > 0:
                    self.ctx.logger.info(f"Adopted {adopted} external trade(s)")
        except Exception as e:
            self.ctx.logger.error(f"Trade adoption scan error: {e}", exc_info=True)
    
    def _monitor_positions(self, df: pd.DataFrame):
        """
        Monitor open positions and check exit strategies.
        
        Args:
            df: Market data DataFrame with indicators
        """
        try:
            if not self.ctx.position_manager:
                self.ctx.logger.debug("Position manager unavailable; skipping position monitoring")
                return
            positions = self.ctx.position_manager.monitor_positions()
            if positions:
                self.ctx.logger.debug(f"Monitoring {len(positions)} open positions")
                total_pnl = sum(p.unrealized_pnl for p in positions)
                self.ctx.logger.debug(f"Total unrealized P&L: {total_pnl:.2f}")
            
            # Get account info for exit strategies
            account_info = self.ctx.connector.get_account_info()
            
            # Check each position against exit strategies
            for position in positions:
                # Prepare market data for exit strategies
                exit_data = {
                    'current_price': position.current_price,
                    'current_data': df.iloc[-1],
                    'account_info': account_info,
                    'indicators': {
                        'atr': df['atr'].iloc[-1] if 'atr' in df.columns else None
                    }
                }
                
                # Check exit strategies (already sorted by priority)
                for exit_strategy in self.ctx.exit_strategies:
                    if not exit_strategy.is_enabled():
                        continue
                    
                    exit_signal = exit_strategy.should_exit(position, exit_data)
                    
                    if exit_signal:
                        self._process_exit_signal(position, exit_signal)
                        # Exit after first strategy triggers (highest priority wins)
                        break
        
        except Exception as e:
            self.ctx.logger.error(f"Position monitoring error: {e}", exc_info=True)
    
    def _process_exit_signal(self, position, exit_signal):
        """
        Process an exit signal.
        
        Args:
            position: Position to close
            exit_signal: Exit signal from strategy
        """
        self.ctx.logger.info(
            f"Exit triggered by {exit_signal.strategy_name}: "
            f"{exit_signal.reason}"
        )
        
        if not self.ctx.dry_run:
            # Close position
            close_result = self.ctx.position_manager.close_position(
                ticket=position.ticket,
                reason=exit_signal.reason,
                partial_volume=exit_signal.partial_volume
            )
            
            if close_result.status == OrderStatus.FILLED:
                self.ctx.logger.info(
                    f"Position closed: ticket={position.ticket}, "
                    f"P&L={position.unrealized_pnl:.2f}"
                )
                
                # Update database
                self.ctx.database.update_trade_exit(
                    order_id=position.ticket,
                    exit_price=close_result.fill_price,
                    exit_time=datetime.now(),
                    profit=position.unrealized_pnl,
                    exit_reason=exit_signal.reason
                )
                
                # Record position closed for metrics
                try:
                    self.ctx.metrics.record_position_closed(position.symbol)
                except Exception:
                    self.ctx.logger.debug('Failed to record position closed in metrics', exc_info=True)
                
                # Update risk manager
                self.ctx.risk_manager.record_trade_result(position.unrealized_pnl)
            else:
                self.ctx.logger.error(
                    f"Failed to close position {position.ticket}: "
                    f"{close_result.message}"
                )
        else:
            self.ctx.logger.info("[DRY RUN] Would close position here")
    
    def _check_connection_health(self):
        """Check connection health and reconnect if necessary."""
        try:
            if not self.ctx.connector.is_connected():
                self.ctx.logger.warning("Connection lost, attempting reconnect...")
                
                success = self.ctx.connector.reconnect()
                if success:
                    self.ctx.logger.info("Reconnection successful")
                    # Reconcile positions after reconnect
                    reconciled = self.ctx.position_manager.reconcile_positions()
                    self.ctx.logger.info(f"Reconciled {reconciled} positions")
                else:
                    self.ctx.logger.error("Reconnection failed; will keep trying on subsequent cycles")
                    # Avoid tight-looping on repeated failures; wait a short backoff
                    try:
                        time.sleep(min(30, self.ctx.poll_interval))
                    except Exception:
                        pass
        except Exception as e:
            self.ctx.logger.error(f"Health check error: {e}", exc_info=True)
    
    def _report_performance_metrics(self):
        """Report performance metrics periodically."""
        # Publish periodic performance metrics every 10 loops for near-real-time observability
        if self.loop_count % 10 == 0:
            self.ctx.logger.info(f"Performance metrics after {self.loop_count} loops:")
            
            # Sync latest position stats into metrics
            stats = self.ctx.position_manager.get_statistics()
            try:
                pos_summary = self.ctx.position_manager.get_position_summary_by_symbol()
                self.ctx.metrics.sync_with_positions_summary(stats, pos_summary)
                
                # Persist summary if function provided
                if self.ctx.persist_summary_fn and self.ctx.summary_path:
                    try:
                        self.ctx.persist_summary_fn(self.ctx.metrics, self.ctx.logger, self.ctx.summary_path)
                    except Exception:
                        self.ctx.logger.exception('Failed to persist periodic metrics summary')
                
                # Ensure a Prometheus exporter exists (fallback) and publish metrics
                if self.ctx.exporter is None:
                    try:
                        # Initialize exporter unconditionally as a fallback to ensure metrics are exposed
                        from cthulu.observability.prometheus import PrometheusExporter
                        prom_cfg = self.ctx.config.get('observability', {}).get('prometheus', {}) if getattr(self.ctx, 'config', None) else {}
                        exporter = PrometheusExporter(prefix=prom_cfg.get('prefix', 'Cthulu'))
                        exporter._file_path = prom_cfg.get('textfile_path') or (r"C:\workspace\cthulu\metrics\Cthulu_metrics.prom" if os.name == 'nt' else "/tmp/Cthulu_metrics.prom")
                        http_port = prom_cfg.get('http_port', 8181)
                        try:
                            import threading
                            from http.server import BaseHTTPRequestHandler, HTTPServer
                            class _MetricsHandler(BaseHTTPRequestHandler):
                                def do_GET(self):
                                    if self.path != '/metrics':
                                        self.send_response(404)
                                        self.end_headers()
                                        return
                                    try:
                                        body = exporter.export_text().encode('utf-8')
                                        self.send_response(200)
                                        self.send_header('Content-Type', 'text/plain; version=0.0.4')
                                        self.send_header('Content-Length', str(len(body)))
                                        self.end_headers()
                                        self.wfile.write(body)
                                    except Exception:
                                        self.send_response(500)
                                        self.end_headers()
                            def _serve():
                                server = HTTPServer(('0.0.0.0', int(http_port)), _MetricsHandler)
                                exporter.logger.info(f"Starting fallback metrics HTTP server on port {http_port}")
                                try:
                                    server.serve_forever()
                                except Exception:
                                    exporter.logger.exception('Fallback metrics HTTP server stopped')
                            t = threading.Thread(target=_serve, daemon=True)
                            t.start()
                        except Exception:
                            self.ctx.logger.exception('Failed to start fallback HTTP metrics server')
                        self.ctx.exporter = exporter
                        self.ctx.logger.info('Prometheus exporter (fallback) initialized in trading loop')
                    except Exception:
                        self.ctx.logger.exception('Failed to initialize fallback Prometheus exporter')

                # Publish to Prometheus exporter if present
                if self.ctx.exporter is not None:
                    try:
                        self.ctx.metrics.publish_to_prometheus(self.ctx.exporter)
                        try:
                            fp = getattr(self.ctx.exporter, '_file_path', None)
                            self.ctx.exporter.write_to_file(fp)
                        except Exception:
                            self.ctx.logger.debug('Failed to write Prometheus metrics to file')
                    except Exception:
                        self.ctx.logger.debug('Failed to publish metrics to Prometheus exporter')
            except Exception:
                self.ctx.logger.exception('Failed to sync position summary into metrics')
            
            self.ctx.logger.info(f"Position stats: {stats}")




