"""
Herald Autonomous Trading System

Main orchestrator implementing the Phase 2 autonomous trading loop.
"""

import sys
import time
import signal as sig_module
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from herald.connector.mt5_connector import mt5
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

__version__ = "3.0.0"

from herald.connector.mt5_connector import MT5Connector, ConnectionConfig
from herald.data.layer import DataLayer
from herald.strategy.base import Strategy, SignalType
from herald.execution.engine import ExecutionEngine, OrderRequest, OrderType, OrderStatus
from herald.risk.manager import RiskManager, RiskLimits
from herald.position.manager import PositionManager
from herald.persistence.database import Database, TradeRecord, SignalRecord
from herald.observability.logger import setup_logger
from herald.observability.metrics import MetricsCollector

# Exit strategies
from herald.exit.trailing_stop import TrailingStop
from herald.exit.time_based import TimeBasedExit
from herald.exit.profit_target import ProfitTargetExit
from herald.exit.adverse_movement import AdverseMovementExit

# Indicators
from herald.indicators.rsi import RSI
from herald.indicators.macd import MACD
from herald.indicators.bollinger import BollingerBands
from herald.indicators.stochastic import Stochastic
from herald.indicators.adx import ADX


# Global shutdown flag
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    shutdown_requested = True
    print("\nShutdown signal received, closing positions...")


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to config file (JSON or Python dict)
        
    Returns:
        Configuration dictionary
    """
    import json
    
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    return config


def load_indicators(indicator_configs: Dict[str, Any]) -> List:
    """
    Load and configure indicators.
    
    Args:
        indicator_configs: Dictionary of indicator configurations
        
    Returns:
        List of configured indicator instances
    """
    indicators = []
    indicator_map = {
        'rsi': RSI,
        'macd': MACD,
        'bollinger': BollingerBands,
        'stochastic': Stochastic,
        'adx': ADX
    }
    
    # Handle both list and dict formats
    if isinstance(indicator_configs, list):
        # List format: [{"type": "rsi", "params": {...}}, ...]
        for indicator_config in indicator_configs:
            indicator_type = indicator_config.get('type', '').lower()
            params = indicator_config.get('params', {})
            
            if indicator_type in indicator_map:
                indicator = indicator_map[indicator_type](**params)
                indicators.append(indicator)
    else:
        # Dict format: {"rsi": {...}, "macd": {...}}
        for indicator_type, params in indicator_configs.items():
            indicator_type_lower = indicator_type.lower()
            
            if indicator_type_lower in indicator_map:
                indicator = indicator_map[indicator_type_lower](**params)
                indicators.append(indicator)
            
    return indicators


def load_strategy(strategy_config: Dict[str, Any]) -> Strategy:
    """
    Load and configure trading strategy.
    
    Args:
        strategy_config: Strategy configuration
        
    Returns:
        Configured strategy instance
    """
    from herald.strategy.sma_crossover import SmaCrossover
    
    strategy_type = strategy_config['type'].lower()
    
    if strategy_type == 'sma_crossover':
        return SmaCrossover(config=strategy_config)
    else:
        raise ValueError(f"Unknown strategy type: {strategy_type}")


def load_exit_strategies(exit_configs: Dict[str, Any]) -> List:
    """
    Load and configure exit strategies.
    
    Args:
        exit_configs: Dictionary of exit strategy configurations
        
    Returns:
        List of configured exit strategy instances, sorted by priority (highest first)
    """
    exit_strategies = []
    exit_map = {
        'trailing_stop': TrailingStop,
        'time_based': TimeBasedExit,
        'profit_target': ProfitTargetExit,
        'adverse_movement': AdverseMovementExit
    }
    
    # Handle both list and dict formats
    if isinstance(exit_configs, list):
        # List format: [{"type": "trailing_stop", "enabled": true, ...}, ...]
        for exit_config in exit_configs:
            exit_type = exit_config.get('type', '').lower()
            enabled = exit_config.get('enabled', True)
            
            if exit_type in exit_map and enabled:
                strategy = exit_map[exit_type](exit_config)
                exit_strategies.append(strategy)
    else:
        # Dict format: {"trailing_stop": {...}, "time_based": {...}}
        for exit_type, config in exit_configs.items():
            exit_type_lower = exit_type.lower()
            enabled = config.get('enabled', True)
            
            if exit_type_lower in exit_map and enabled:
                strategy = exit_map[exit_type_lower](config)
                exit_strategies.append(strategy)
            
    # Sort by priority (highest first)
    exit_strategies.sort(key=lambda x: x.priority, reverse=True)
    
    return exit_strategies


def main():
    """Main autonomous trading loop for Phase 2."""
    
    # Load environment variables from .env
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    # Parse arguments
    epilog = (
        "Examples:\n"
        "  herald --config config.json --log-level DEBUG\n"
        "  herald --config ./configs/prod.json --dry-run --log-level INFO"
    )

    parser = argparse.ArgumentParser(
        description=f"Herald — Adaptive Trading Intelligence (v{__version__})",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--config', type=str, required=True, help="Path to JSON config file")
    parser.add_argument('--log-level', type=str, default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument('--dry-run', action='store_true', 
                       help="Dry run mode (simulate orders without placing them)")
    parser.add_argument('--version', action='version', version=f"Herald {__version__}")
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logger(
        name='herald',
        level=args.log_level,
        log_file='herald.log',
        json_format=False
    )
    
    # Register signal handlers
    sig_module.signal(sig_module.SIGINT, signal_handler)
    sig_module.signal(sig_module.SIGTERM, signal_handler)
    
    logger.info("=" * 70)
    logger.info(f"Herald Autonomous Trading System v{__version__} - Phase 2")
    logger.info("=" * 70)
    
    # Load configuration
    try:
        config = load_config(args.config)
        logger.info(f"Configuration loaded from {args.config}")
        
        # Override MT5 credentials from environment variables (security best practice)
        mt5_login = os.getenv('MT5_LOGIN')
        mt5_password = os.getenv('MT5_PASSWORD')
        mt5_server = os.getenv('MT5_SERVER')
        
        if mt5_login and mt5_password and mt5_server:
            config['mt5']['login'] = int(mt5_login)
            config['mt5']['password'] = mt5_password
            config['mt5']['server'] = mt5_server
            logger.info("MT5 credentials loaded from .env file")
        else:
            logger.warning("MT5 credentials not found in .env - using config file values")
            
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
        
    # Initialize modules
    try:
        # 1. MT5 Connector
        logger.info("Initializing MT5 connector...")
        connection_config = ConnectionConfig(**config['mt5'])
        connector = MT5Connector(connection_config)
        
        # 2. Data Layer
        logger.info("Initializing data layer...")
        data_layer = DataLayer(cache_enabled=config.get('cache_enabled', True))
        
        # 3. Risk Manager
        logger.info("Initializing risk manager...")
        risk_config = config['risk']
        risk_limits = RiskLimits()
        risk_limits.max_position_size_pct = risk_config.get('max_position_size_pct', 0.02)
        risk_limits.max_total_exposure_pct = risk_config.get('max_total_exposure_pct', 0.10)
        risk_limits.max_daily_loss_pct = risk_config.get('max_daily_loss_pct', 0.05)
        risk_limits.max_positions_per_symbol = risk_config.get('max_positions_per_symbol', 1)
        risk_limits.max_total_positions = risk_config.get('max_total_positions', 3)
        risk_limits.min_risk_reward_ratio = risk_config.get('min_risk_reward_ratio', 1.0)
        risk_manager = RiskManager(risk_limits)
        
        # 4. Execution Engine
        logger.info("Initializing execution engine...")
        execution_engine = ExecutionEngine(connector)
        
        # 5. Position Manager
        logger.info("Initializing position manager...")
        position_manager = PositionManager(connector, execution_engine)
        
        # 6. Persistence
        logger.info("Initializing database...")
        db_path = config.get('database', {}).get('path', 'herald.db')
        database = Database(db_path)
        
        # 7. Metrics
        logger.info("Initializing metrics collector...")
        metrics = MetricsCollector()
        
        # 8. Load indicators
        logger.info("Loading indicators...")
        indicators = load_indicators(config.get('indicators', []))
        logger.info(f"Loaded {len(indicators)} indicators")
        
        # 9. Load strategy
        logger.info("Loading trading strategy...")
        strategy = load_strategy(config['strategy'])
        logger.info(f"Loaded strategy: {strategy.__class__.__name__}")
        
        # 10. Load exit strategies
        logger.info("Loading exit strategies...")
        exit_strategies = load_exit_strategies(config.get('exit_strategies', []))
        logger.info(f"Loaded {len(exit_strategies)} exit strategies")
        for es in exit_strategies:
            logger.info(f"  - {es.name} (priority: {es.priority}, enabled: {es.is_enabled()})")
            
    except Exception as e:
        logger.error(f"Failed to initialize modules: {e}", exc_info=True)
        return 1
        
    # Connect to MT5
    try:
        logger.info("Connecting to MetaTrader 5...")
        if not connector.connect():
            logger.error("Failed to connect to MT5")
            return 1
            
        account_info = connector.get_account_info()
        logger.info(f"Connected to MT5 account {account_info['login']}")
        logger.info(f"Balance: {account_info['balance']:.2f}, Equity: {account_info['equity']:.2f}")
        
    except Exception as e:
        logger.error(f"Connection error: {e}", exc_info=True)
        return 1
        
    # Trading configuration
    symbol = config['trading']['symbol']
    timeframe = getattr(mt5, config['trading']['timeframe'])
    poll_interval = config['trading'].get('poll_interval', 60)
    lookback_bars = config['trading'].get('lookback_bars', 500)
    
    logger.info(f"Trading configuration: {symbol} on {config['trading']['timeframe']}")
    logger.info(f"Poll interval: {poll_interval}s, Lookback: {lookback_bars} bars")
    
    if args.dry_run:
        logger.warning("DRY RUN MODE - No real orders will be placed")
        
    # Main trading loop
    logger.info("Starting autonomous trading loop...")
    logger.info("Press Ctrl+C to shutdown gracefully")
    
    loop_count = 0
    global shutdown_requested
    
    try:
        while not shutdown_requested:
            loop_count += 1
            loop_start = datetime.now()
            logger.debug(f"Loop #{loop_count} started at {loop_start}")
            
            # 4. Market data ingestion
            try:
                rates = connector.get_rates(
                    symbol=symbol,
                    timeframe=timeframe,
                    count=lookback_bars
                )
                
                if rates is None or len(rates) == 0:
                    logger.warning("No market data received, skipping cycle")
                    time.sleep(poll_interval)
                    continue
                    
                df = data_layer.normalize_rates(rates, symbol=symbol)
                logger.debug(f"Retrieved {len(df)} bars for {symbol}")
                
            except Exception as e:
                logger.error(f"Market data error: {e}", exc_info=True)
                time.sleep(poll_interval)
                continue
                
            # 5. Calculate indicators
            try:
                # Calculate SMA indicators for strategy (required by sma_crossover)
                df['sma_20'] = df['close'].rolling(window=20).mean()
                df['sma_50'] = df['close'].rolling(window=50).mean()
                
                # Calculate ATR for stop loss calculation
                high_low = df['high'] - df['low']
                high_close = (df['high'] - df['close'].shift()).abs()
                low_close = (df['low'] - df['close'].shift()).abs()
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                df['atr'] = true_range.rolling(window=14).mean()
                
                # Calculate additional indicators from config
                for indicator in indicators:
                    indicator_data = indicator.calculate(df)
                    # Merge indicator data into main DataFrame
                    if indicator_data is not None:
                        df = df.join(indicator_data, how='left')
                        
                logger.debug(f"Calculated SMA, ATR, and {len(indicators)} additional indicators")
                
            except Exception as e:
                logger.error(f"Indicator calculation error: {e}", exc_info=True)
                time.sleep(poll_interval)
                continue
                
            # 6. Generate strategy signals
            try:
                current_bar = df.iloc[-1]
                signal = strategy.on_bar(current_bar)
                
                if signal:
                    logger.info(
                        f"Signal generated: {signal.side.name} {signal.symbol} "
                        f"(confidence: {signal.confidence:.2f})"
                    )
                    
            except Exception as e:
                logger.error(f"Strategy signal error: {e}", exc_info=True)
                signal = None
                
            # 7. Process entry signals
            if signal and signal.side in [SignalType.LONG, SignalType.SHORT]:
                try:
                    # Get current account info and positions
                    account_info = connector.get_account_info()
                    current_positions = len(position_manager.get_positions(symbol=symbol))
                    
                    # Risk approval
                    approved, reason, position_size = risk_manager.approve(
                        signal=signal,
                        account_info=account_info,
                        current_positions=current_positions
                    )
                    
                    if approved:
                        logger.info(f"Risk approved: {position_size:.2f} lots - {reason}")
                        
                        if not args.dry_run:
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
                            
                            # Execute order
                            logger.info(f"Placing {order_req.side} order for {order_req.volume} lots")
                            result = execution_engine.place_order(order_req)
                            
                            if result.status == OrderStatus.FILLED:
                                logger.info(
                                    f"Order filled: ticket={result.order_id}, "
                                    f"price={result.fill_price:.5f}"
                                )
                                
                                # Track position
                                position_info = position_manager.track_position(
                                    result,
                                    metadata=signal.metadata
                                )
                                
                                # Record in database
                                signal_record = SignalRecord(
                                    timestamp=signal.timestamp,
                                    symbol=signal.symbol,
                                    side=signal.side.name,
                                    confidence=signal.confidence,
                                    price=result.fill_price,
                                    stop_loss=signal.stop_loss,
                                    take_profit=signal.take_profit,
                                    strategy_name=strategy.__class__.__name__,
                                    metadata=signal.metadata,
                                    executed=True,
                                    execution_timestamp=datetime.now()
                                )
                                database.record_signal(signal_record)
                                
                                trade_record = TradeRecord(
                                    signal_id=signal.id,
                                    order_id=result.order_id,
                                    symbol=signal.symbol,
                                    side=signal.side.name,
                                    entry_price=result.fill_price,
                                    volume=result.filled_volume,
                                    stop_loss=signal.stop_loss,
                                    take_profit=signal.take_profit,
                                    entry_timestamp=datetime.now(),
                                    commission=result.commission
                                )
                                database.record_trade(trade_record)
                                
                            else:
                                logger.error(
                                    f"Order failed: {result.status.name} - {result.message}"
                                )
                        else:
                            logger.info("[DRY RUN] Would place order here")
                    else:
                        logger.info(f"Risk rejected: {reason}")
                        
                except Exception as e:
                    logger.error(f"Order execution error: {e}", exc_info=True)
                    
            # 8. Monitor positions and check exits
            try:
                positions = position_manager.monitor_positions()
                
                if positions:
                    logger.debug(f"Monitoring {len(positions)} open positions")
                    
                    total_pnl = sum(p.unrealized_pnl for p in positions)
                    logger.debug(f"Total unrealized P&L: {total_pnl:.2f}")
                    
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
                        for exit_strategy in exit_strategies:
                            if not exit_strategy.is_enabled():
                                continue
                                
                            exit_signal = exit_strategy.should_exit(position, exit_data)
                            
                            if exit_signal:
                                logger.info(
                                    f"Exit triggered by {exit_signal.strategy_name}: "
                                    f"{exit_signal.reason}"
                                )
                                
                                if not args.dry_run:
                                    # Close position
                                    close_result = position_manager.close_position(
                                        ticket=position.ticket,
                                        reason=exit_signal.reason,
                                        partial_volume=exit_signal.partial_volume
                                    )
                                    
                                    if close_result.status == OrderStatus.FILLED:
                                        logger.info(
                                            f"Position closed: ticket={position.ticket}, "
                                            f"P&L={position.unrealized_pnl:.2f}"
                                        )
                                        
                                        # Update database
                                        database.update_trade_exit(
                                            order_id=position.ticket,
                                            exit_price=close_result.fill_price,
                                            profit=position.unrealized_pnl,
                                            exit_reason=exit_signal.reason
                                        )
                                        
                                        # Record metrics
                                        metrics.record_trade(
                                            profit=position.unrealized_pnl,
                                            symbol=position.symbol
                                        )
                                        
                                        # Update risk manager
                                        risk_manager.record_trade_result(position.unrealized_pnl)
                                        
                                    else:
                                        logger.error(
                                            f"Failed to close position {position.ticket}: "
                                            f"{close_result.message}"
                                        )
                                else:
                                    logger.info("[DRY RUN] Would close position here")
                                    
                                # Exit after first strategy triggers (highest priority wins)
                                break
                                
            except Exception as e:
                logger.error(f"Position monitoring error: {e}", exc_info=True)
                
            # 9. Health monitoring
            try:
                if not connector.is_connected():
                    logger.warning("Connection lost, attempting reconnect...")
                    
                    if connector.reconnect():
                        logger.info("Reconnection successful")
                        # Reconcile positions after reconnect
                        reconciled = position_manager.reconcile_positions()
                        logger.info(f"Reconciled {reconciled} positions")
                    else:
                        logger.error("Reconnection failed")
                        break
                        
            except Exception as e:
                logger.error(f"Health check error: {e}", exc_info=True)
                
            # Performance monitoring
            if loop_count % 100 == 0:
                logger.info(f"Performance metrics after {loop_count} loops:")
                metrics.print_summary()
                
                # Position statistics
                stats = position_manager.get_statistics()
                logger.info(f"Position stats: {stats}")
                
            # 10. Wait for next cycle
            loop_duration = (datetime.now() - loop_start).total_seconds()
            logger.debug(f"Loop completed in {loop_duration:.2f}s")
            
            sleep_time = max(0, poll_interval - loop_duration)
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        return 1
    finally:
        # Cleanup and shutdown
        logger.info("Initiating graceful shutdown...")
        
        try:
            # Close all open positions
            if not args.dry_run:
                logger.info("Closing all open positions...")
                close_results = position_manager.close_all_positions("System shutdown")
                logger.info(f"Closed {len(close_results)} positions")
                
            # Print final metrics
            logger.info("Final performance metrics:")
            metrics.print_summary()
            
            # Disconnect from MT5
            connector.disconnect()
            logger.info("Disconnected from MT5")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
            
        logger.info("=" * 70)
        logger.info("Herald Autonomous Trading System - Stopped")
        logger.info("=" * 70)
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
