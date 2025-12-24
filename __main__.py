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

__version__ = "3.3.1"

from herald.connector.mt5_connector import MT5Connector, ConnectionConfig
from herald.data.layer import DataLayer
from herald.strategy.base import Strategy, SignalType
from herald.execution.engine import ExecutionEngine, OrderRequest, OrderType, OrderStatus
from herald.risk.manager import RiskManager, RiskLimits
from herald.position.manager import PositionManager
from herald.position.trade_manager import TradeManager, TradeAdoptionPolicy
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


from config_schema import Config
from config.mindsets import apply_mindset, list_mindsets


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
        "  herald --config config.json                    # Interactive setup + trading\n"
        "  herald --config config.json --skip-setup       # Skip wizard, use existing config\n"
        "  herald --config config.json --dry-run          # Simulate without real orders\n"
        "  herald --config config.json --mindset aggressive\n"
        "\n"
        "Workflow:\n"
        "  Herald starts with an interactive setup wizard that guides you through\n"
        "  configuring symbol, timeframe, risk limits, and strategy settings.\n"
        "  Use --skip-setup to bypass the wizard for automated/headless runs.\n"
        "\n"
        "Mindsets:\n"
        "  aggressive    - Higher risk, faster entries, tighter stops\n"
        "  balanced      - Moderate risk, standard settings (default)\n"
        "  conservative  - Lower risk, wider stops, capital preservation"
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
    parser.add_argument('--symbol', type=str, default=None, help="Override trading symbol in config (e.g. GOLD#m)")
    parser.add_argument('--adopt-only', action='store_true', help="Only run external trade adoption and exit")
    parser.add_argument('--mindset', type=str, default=None,
                       choices=['aggressive', 'balanced', 'conservative'],
                       help="Trading mindset/risk profile (aggressive, balanced, conservative)")
    parser.add_argument('--skip-setup', action='store_true',
                       help="Skip interactive setup wizard (for automation/headless runs)")
    parser.add_argument('--wizard', action='store_true',
                       help="Open the interactive setup wizard and optionally start profiles")
    parser.add_argument('--wizard-ai', action='store_true',
                       help="Run the lightweight NLP-based wizard (describe intent in natural language)")
    parser.add_argument('--no-prompt', action='store_true',
                       help="Do not prompt on shutdown; leave positions open (useful for automated runs)")
    parser.add_argument('--manual-prompt', action='store_true',
                       help="Enable persistent interactive manual trade prompt in the terminal (interactive only)")
    parser.add_argument('--enable-rpc', action='store_true', help='Enable local RPC server (binds to localhost)')
    parser.add_argument('--rpc-host', type=str, default='127.0.0.1', help='RPC server host (default 127.0.0.1)')
    parser.add_argument('--rpc-port', type=int, default=8181, help='RPC server port (default 8181)')

    # Runtime ML toggle (CLI) — mutually exclusive enable/disable
    ml_group = parser.add_mutually_exclusive_group()
    ml_group.add_argument('--enable-ml', dest='enable_ml', action='store_true', help='Enable ML instrumentation (overrides config)')
    ml_group.add_argument('--disable-ml', dest='enable_ml', action='store_false', help='Disable ML instrumentation (overrides config)')
    parser.set_defaults(enable_ml=None)
    parser.add_argument('--version', action='version', version=f"Herald {__version__}")
    args = parser.parse_args()

    # If adopt-only is requested, skip interactive setup to avoid blocking prompts
    if args.adopt_only:
        args.skip_setup = True

    # Run interactive setup wizard (default behavior, skip with --skip-setup or --adopt-only)
    if args.wizard_ai:
        from config.wizard import run_nlp_wizard
        result = run_nlp_wizard(args.config)
        if result is None:
            print("Setup cancelled. Exiting.")
            return 0
        print("\nNLP wizard completed. Exiting.")
        return 0

    if args.wizard:
        from config.wizard import run_setup_wizard
        result = run_setup_wizard(args.config)
        if result is None:
            print("Setup cancelled. Exiting.")
            return 0
        # If wizard started profiles, user likely wants to exit the one-off wizard
        print("\nWizard completed. Exiting.")
        return 0

    if not args.skip_setup and not args.adopt_only:
        from config.wizard import run_setup_wizard
        result = run_setup_wizard(args.config)
        if result is None:
            print("Setup cancelled. Exiting.")
            return 0
        print("\nStarting Herald with configured settings...\n")
    
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
    
    # Load configuration using typed schema and mapping
    try:
        cfg = Config.load(args.config)
        logger.info(f"Configuration loaded from {args.config}")
        # Use model_dump() for Pydantic v2 compatibility
        config = cfg.model_dump() if hasattr(cfg, 'model_dump') else cfg.dict()
        
        # Apply mindset if specified
        if args.mindset:
            config = apply_mindset(config, args.mindset)
            logger.info(f"Applied '{args.mindset}' trading mindset")
            logger.info(f"  Risk: position_size_pct={config['risk'].get('position_size_pct', 2.0)}%, "
                       f"max_daily_loss=${config['risk'].get('max_daily_loss', 50)}")
        # Symbol override from CLI
        if args.symbol:
            config['trading']['symbol'] = args.symbol
            logger.info(f"Overriding trading symbol via CLI: {args.symbol}")

        # Apply symbol override if provided
        if args.symbol:
            config['trading']['symbol'] = args.symbol
            logger.info(f"Overriding trading symbol to: {args.symbol}")
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
        risk_config = config.get('risk', {})
        # Build RiskLimits with mapping and defaults
        risk_limits = RiskLimits(
            max_position_size_pct=risk_config.get('max_position_size_pct', 0.02),
            max_total_exposure_pct=risk_config.get('max_total_exposure_pct', 0.10),
            max_daily_loss_pct=risk_config.get('max_daily_loss_pct', 0.05),
            max_positions_per_symbol=risk_config.get('max_positions_per_symbol', 1),
            max_total_positions=risk_config.get('max_total_positions', 3),
            min_risk_reward_ratio=risk_config.get('min_risk_reward_ratio', 1.0),
        )
        risk_manager = RiskManager(risk_limits)
        
        # Ensure ml_collector is defined (safe default) so the execution engine construction does not raise
        ml_collector = None
        
        # 4. Execution Engine
        logger.info("Initializing execution engine...")
        execution_engine = ExecutionEngine(connector, risk_config=risk_config, ml_collector=ml_collector)
        
        # 5. Position Manager
        logger.info("Initializing position manager...")
        position_manager = PositionManager(connector, execution_engine)
        
        # 5b. Trade Manager (for adopting external trades)
        trade_adoption_config = config.get('orphan_trades', {})
        trade_adoption_policy = TradeAdoptionPolicy(
            enabled=trade_adoption_config.get('enabled', False),
            adopt_symbols=trade_adoption_config.get('adopt_symbols', []),
            ignore_symbols=trade_adoption_config.get('ignore_symbols', []),
            apply_exit_strategies=trade_adoption_config.get('apply_exit_strategies', True),
            max_adoption_age_hours=trade_adoption_config.get('max_adoption_age_hours', 0.0),
            log_only=trade_adoption_config.get('log_only', False)
        )
        # Provide default stop percentage and RR from risk config
        default_stop_pct = risk_config.get('emergency_stop_loss_pct', 8.0)
        default_rr = config.get('strategy', {}).get('params', {}).get('risk_reward_ratio', 2.0)
        trade_manager = TradeManager(position_manager, trade_adoption_policy, default_stop_pct=default_stop_pct, default_rr=default_rr, config=config)
        if trade_adoption_policy.enabled:
            logger.info(f"External trade adoption ENABLED (log_only: {trade_adoption_policy.log_only})")
        else:
            logger.info("External trade adoption disabled")
        
        # 6. Persistence
        logger.info("Initializing database...")
        db_path = config.get('database', {}).get('path', 'herald.db')
        database = Database(db_path)
        
        # 7. Metrics
        logger.info("Initializing metrics collector...")
        metrics = MetricsCollector()
        
        # 7b. ML instrumentation collector (optional, configurable via config['ml'] or CLI)
        def init_ml_collector(config, args, logger):
            ml_collector = None
            try:
                ml_config = config.get('ml', {}) if isinstance(config, dict) else {}
                ml_enabled = ml_config.get('enabled', True)
                # CLI overrides config when provided
                if hasattr(args, 'enable_ml') and args.enable_ml is not None:
                    ml_enabled = args.enable_ml
                if ml_enabled:
                    from herald.ML_RL.instrumentation import MLDataCollector
                    ml_prefix = ml_config.get('prefix', 'events')
                    ml_collector = MLDataCollector(prefix=ml_prefix)
                    logger.info('MLDataCollector initialized')
                else:
                    logger.info('ML instrumentation disabled via config/CLI')
            except Exception:
                logger.exception('Failed to initialize MLDataCollector; continuing without it')
            return ml_collector

        ml_collector = init_ml_collector(config, args, logger)

        # Advisory manager (advisory/ghost modes)
        try:
            from herald.advisory.manager import AdvisoryManager
            advisory_cfg = config.get('advisory', {}) if isinstance(config, dict) else {}
            advisory_manager = AdvisoryManager(advisory_cfg, execution_engine, ml_collector)
            if advisory_manager.enabled:
                logger.info(f"AdvisoryManager enabled (mode={advisory_manager.mode})")
        except Exception:
            advisory_manager = None
            logger.exception('Failed to initialize AdvisoryManager; continuing without it')


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

        # 11. Start trade monitor (optional, non-blocking)
        try:
            from herald.monitoring.trade_monitor import TradeMonitor
            monitor = TradeMonitor(position_manager, trade_manager=trade_manager, poll_interval=config.get('monitor_poll_interval', 5.0), ml_collector=ml_collector if ml_collector else None)
            monitor.start()
            logger.info(f"TradeMonitor started (ml_collector={type(monitor.ml_collector)})")
        except Exception:
            logger.exception('Failed to start TradeMonitor; continuing without it')

        # 11b. Optional interactive manual trade prompt (runs in background thread if enabled and interactive)
        def _manual_trade_prompt_thread(ex_engine, pos_manager, db, default_symbol: str):
            """Background thread that offers a persistent prompt to the user to place manual trades.

            This thread uses blocking input() calls so must only be used in interactive terminals.
            It will construct an OrderRequest and submit it via the provided ExecutionEngine.
            """
            import threading
            import sys

            thread_name = threading.current_thread().name
            logger.info(f"Manual trade prompt thread started ({thread_name})")
            try:
                while True:
                    try:
                        ans = input('\nPlace manual trade? (y/N): ').strip().lower()
                    except EOFError:
                        # Non-interactive stream closed
                        logger.info('Manual prompt input closed; stopping prompt thread')
                        break

                    if ans not in ('y', 'yes'):
                        # small delay to avoid tight loop
                        time.sleep(0.5)
                        continue

                    # Gather trade details
                    try:
                        symbol = input(f"Symbol [{default_symbol}]: ").strip() or default_symbol
                        side = (input("Side (BUY/SELL) [BUY]: ").strip() or 'BUY').upper()
                        volume_raw = input("Volume (lots) [0.01]: ").strip() or '0.01'
                        volume = float(volume_raw)
                        price_raw = input("Price (enter 'market' or a numeric limit price) [market]: ").strip() or 'market'
                        sl_raw = input("Stop Loss (optional, leave blank for none): ").strip() or None
                        tp_raw = input("Take Profit (optional, leave blank for none): ").strip() or None
                    except Exception as e:
                        logger.exception(f"Manual prompt input error: {e}")
                        continue

                    # Determine order type
                    try:
                        if price_raw.lower() in ('market', 'm', 'current', 'c'):
                            order_type = OrderType.MARKET
                            price = None
                        else:
                            order_type = OrderType.LIMIT
                            price = float(price_raw)
                    except Exception as e:
                        logger.error(f"Invalid price input: {e}")
                        continue

                    sl = float(sl_raw) if sl_raw else None
                    tp = float(tp_raw) if tp_raw else None

                    # Build and submit order
                    order_req = OrderRequest(
                        signal_id='manual_prompt',
                        symbol=symbol,
                        side='BUY' if side == 'BUY' else 'SELL',
                        volume=volume,
                        order_type=order_type,
                        price=price,
                        sl=sl,
                        tp=tp
                    )

                    logger.info(f"Manual request: {order_req.side} {order_req.volume} {order_req.symbol} @ {order_req.price or 'market'}")

                    try:
                        res = ex_engine.place_order(order_req)
                        if res and res.status == OrderStatus.FILLED:
                            logger.info(f"Manual order filled: ticket={res.order_id} price={res.fill_price}")
                            # Track position in registry
                            try:
                                tracked = pos_manager.track_position(res, signal_metadata={})
                                if tracked:
                                    logger.info(f"Tracked manual position: #{tracked.ticket}")
                                # Record to DB
                                try:
                                    tr = TradeRecord(
                                        signal_id='manual_prompt',
                                        order_id=res.order_id,
                                        symbol=order_req.symbol,
                                        side=order_req.side,
                                        entry_price=res.fill_price,
                                        volume=res.filled_volume,
                                        entry_time=datetime.now(),
                                    )
                                    db.record_trade(tr)
                                except Exception:
                                    logger.exception('Failed to record manual trade to DB')
                            except Exception:
                                logger.exception('Failed to track manual position')
                        else:
                            logger.error(f"Manual order failed: {getattr(res,'message',str(res))}")
                    except Exception:
                        logger.exception('Error placing manual order via ExecutionEngine')

            except Exception:
                logger.exception('Manual prompt thread failed')

        # Start interactive prompt if user requested it or if running interactively and stdin is a TTY
        try:
            import sys as _sys
            if (args.manual_prompt or (_sys.stdin.isatty() and not args.adopt_only)) and _sys.stdin.isatty():
                try:
                    import threading as _threading
                    prompt_thread = _threading.Thread(target=_manual_trade_prompt_thread, args=(execution_engine, position_manager, database, config.get('trading', {}).get('symbol', '')), daemon=True, name='manual-prompt')
                    prompt_thread.start()
                    logger.info('Manual trade prompt enabled (interactive)')
                except Exception:
                    logger.exception('Failed to start manual trade prompt thread')
        except Exception:
            logger.exception('Error initializing manual trade prompt')

        # Start RPC server if requested or if HERALD_API_TOKEN provided in env
        try:
            import os as _os
            if args.enable_rpc or _os.getenv('HERALD_API_TOKEN'):
                token = _os.getenv('HERALD_API_TOKEN')
                from herald.rpc.server import run_rpc_server
                try:
                    if args.enable_rpc and not token:
                        logger.warning('RPC server enabled without HERALD_API_TOKEN; running unauthenticated (local only)')
                    rpc_thread, rpc_server = run_rpc_server(args.rpc_host, args.rpc_port, token, execution_engine, risk_manager, position_manager, database)
                    logger.info('RPC server started')
                except Exception:
                    logger.exception('Failed to start RPC server')
        except Exception:
            logger.exception('Error initializing RPC server')

        # 11b. Optional News / Calendar ingest pipeline (opt-in via config or env)
        try:
            news_cfg = config.get('news', {}) if isinstance(config, dict) else {}
            env_enable = os.getenv('NEWS_INGEST_ENABLED')
            news_enabled = news_cfg.get('enabled', False) or (env_enable == '1')
            news_ingestor = None
            if news_enabled:
                from herald.news import RssAdapter, NewsApiAdapter, FREDAdapter, TradingEconomicsAdapter, NewsIngestor, NewsManager
                adapters = []
                # RSS fallback
                if os.getenv('NEWS_USE_RSS', str(news_cfg.get('use_rss', True))).lower() in ('1', 'true', 'yes'):
                    feeds = os.getenv('NEWS_RSS_FEEDS', news_cfg.get('rss_feeds', ''))
                    feeds_list = [f.strip() for f in feeds.split(',') if f.strip()]
                    if feeds_list:
                        adapters.append(RssAdapter(feeds=feeds_list))

                # API-based adapters
                if os.getenv('NEWSAPI_KEY'):
                    adapters.append(NewsApiAdapter(api_key=os.getenv('NEWSAPI_KEY')))
                if os.getenv('FRED_API_KEY'):
                    adapters.append(FREDAdapter(api_key=os.getenv('FRED_API_KEY')))

                cache_ttl = int(os.getenv('NEWS_CACHE_TTL', news_cfg.get('cache_ttl', 300)))
                news_manager = NewsManager(adapters=adapters, cache_ttl=cache_ttl)

                cal_adapter = None
                if os.getenv('ECON_CAL_API_KEY'):
                    cal_adapter = TradingEconomicsAdapter(api_key=os.getenv('ECON_CAL_API_KEY'))

                if ml_collector is None:
                    logger.warning('News ingest requested but MLDataCollector is not initialized; skipping NewsIngestor')
                else:
                    interval = int(os.getenv('NEWS_INGEST_INTERVAL', news_cfg.get('interval_seconds', 300)))
                    news_ingestor = NewsIngestor(news_manager, cal_adapter, ml_collector, interval_seconds=interval)
                    news_ingestor.start()
                    logger.info('NewsIngestor started (interval %ss). Adapters: %s calendar=%s', interval, [type(a).__name__ for a in adapters], type(cal_adapter).__name__ if cal_adapter else None)
                    # Wire monitor -> news_manager for real-time alerts
                    try:
                        if 'monitor' in locals() and monitor:
                            monitor.news_manager = news_manager
                            monitor.news_alert_window = int(os.getenv('NEWS_ALERT_WINDOW', news_cfg.get('alert_window', 600)))
                            logger.info('TradeMonitor wired to NewsManager for alerts (window %ss)', monitor.news_alert_window)
                    except Exception:
                        logger.exception('Failed to wire NewsManager to TradeMonitor')
        except Exception:
            logger.exception('Failed to initialize NewsIngestor; continuing without it')
            
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
        
        # Reconcile any existing Herald positions from previous session
        reconciled = position_manager.reconcile_positions()
        if reconciled > 0:
            logger.info(f"Reconciled {reconciled} existing Herald position(s)")
        
        # Adopt any external trades if enabled
        if args.adopt_only:
            if trade_adoption_policy.enabled:
                adopted = trade_manager.scan_and_adopt()
                logger.info(f"Adopted {adopted} external trade(s) (adopt-only mode). Exiting.")
            else:
                logger.warning("Adopt-only requested but external trade adoption is disabled in config.")
            return 0
        else:
            if trade_adoption_policy.enabled:
                adopted = trade_manager.scan_and_adopt()
                if adopted > 0:
                    logger.info(f"Adopted {adopted} external trade(s)")

        # If user requested adoption only mode, exit after adoption
        if args.adopt_only:
            logger.info("Adopt-only mode complete. Exiting.")
            return 0
        
    except Exception as e:
        logger.error(f"Connection error: {e}", exc_info=True)
        return 1
        
    # Trading configuration
    trading_config = config.get('trading', {})
    symbol = trading_config.get('symbol')
    timeframe = getattr(mt5, trading_config.get('timeframe'))
    poll_interval = trading_config.get('poll_interval', 60)
    lookback_bars = trading_config.get('lookback_bars', 500)
    
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

                            # Advisory / ghost handling
                            try:
                                if 'advisory_manager' in locals() and advisory_manager and advisory_manager.enabled:
                                    decision = advisory_manager.decide(order_req, signal)
                                else:
                                    decision = {'action': 'execute', 'result': None}
                            except Exception:
                                logger.exception('Advisory manager decision failed; defaulting to execute')
                                decision = {'action': 'execute', 'result': None}

                            if decision['action'] == 'execute':
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
                                        entry_time=datetime.now(),
                                        commission=result.commission
                                    )
                                    database.record_trade(trade_record)
                                    
                                else:
                                    logger.error(
                                        f"Order failed: {result.status.name} - {result.message}"
                                    )

                            elif decision['action'] == 'advisory':
                                logger.info('Advisory decision: not executing order; recording advisory signal')
                                signal_record = SignalRecord(
                                    timestamp=signal.timestamp,
                                    symbol=signal.symbol,
                                    side=signal.side.name,
                                    confidence=signal.confidence,
                                    price=None,
                                    stop_loss=signal.stop_loss,
                                    take_profit=signal.take_profit,
                                    strategy_name=strategy.__class__.__name__,
                                    metadata={**signal.metadata, 'advisory': True},
                                    executed=False
                                )
                                database.record_signal(signal_record)

                            elif decision['action'] == 'ghost':
                                logger.info('Ghost decision: small test trade executed (or attempted)')
                                res = decision.get('result')
                                # Record ghost attempt (do not adopt as live trade)
                                signal_record = SignalRecord(
                                    timestamp=signal.timestamp,
                                    symbol=signal.symbol,
                                    side=signal.side.name,
                                    confidence=signal.confidence,
                                    price=getattr(res, 'fill_price', None) if res else None,
                                    stop_loss=signal.stop_loss,
                                    take_profit=signal.take_profit,
                                    strategy_name=strategy.__class__.__name__,
                                    metadata={**signal.metadata, 'advisory': 'ghost', 'advisory_result': getattr(res, 'order_id', None) if res else None},
                                    executed=False
                                )
                                database.record_signal(signal_record)

                            else:
                                logger.warning('Advisory manager rejected order request')

                        else:
                            logger.info("[DRY RUN] Would place order here")
                    else:
                        logger.info(f"Risk rejected: {reason}")
                        
                except Exception as e:
                    logger.error(f"Order execution error: {e}", exc_info=True)
            
            # 7b. Scan and adopt external trades
            try:
                if trade_adoption_policy.enabled:
                    adopted = trade_manager.scan_and_adopt()
                    if adopted > 0:
                        logger.info(f"Adopted {adopted} external trade(s)")
            except Exception as e:
                logger.error(f"Trade adoption scan error: {e}", exc_info=True)
                    
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
                                            exit_time=datetime.now(),
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
            # Ask user what to do with open positions (do NOT force-close by default)
            if not args.dry_run:
                interactive = sys.stdin.isatty() and not getattr(args, 'no_prompt', False)
                if interactive:
                    try:
                        print("\nShutdown requested. What should I do with open positions?")
                        print("  [A] Close ALL positions")
                        print("  [N] Leave positions OPEN (default)")
                        print("  [S] Close specific tickets (comma-separated)")
                        choice = input("Choose (A/n/s): ").strip().lower()
                    except Exception:
                        choice = 'n'

                    if choice in ('a', 'all'):
                        logger.info("User requested: close ALL positions")
                        close_results = position_manager.close_all_positions("System shutdown")
                        logger.info(f"Closed {len(close_results)} positions")
                    elif choice in ('s', 'select'):
                        tickets = input("Enter ticket numbers to close (comma-separated): ").strip()
                        ids = [int(x.strip()) for x in tickets.split(',') if x.strip().isdigit()]
                        closed = 0
                        for t in ids:
                            res = position_manager.close_position(ticket=t, reason="User shutdown request")
                            if res and getattr(res, 'status', None) == getattr(res, 'status', None):
                                closed += 1
                        logger.info(f"Closed {closed} user-selected positions")
                    else:
                        logger.info("User chose to leave open positions untouched")
                else:
                    logger.info("Non-interactive shutdown: leaving open positions untouched (no prompt)")

            # Print final metrics
            logger.info("Final performance metrics:")
            metrics.print_summary()
            
            # Disconnect from MT5
            connector.disconnect()
            logger.info("Disconnected from MT5")

            # Stop NewsIngestor if it was started
            try:
                if 'news_ingestor' in locals() and news_ingestor:
                    news_ingestor.stop()
                    logger.info('NewsIngestor stopped')
            except Exception:
                logger.exception('Failed to stop NewsIngestor cleanly')

            # Close ML collector if present
            try:
                if 'ml_collector' in locals() and ml_collector:
                    ml_collector.close()
                    logger.info('MLDataCollector closed')
            except Exception:
                logger.exception('Failed to close MLDataCollector')
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
            
        logger.info("=" * 70)
        logger.info("Herald Autonomous Trading System - Stopped")
        logger.info("=" * 70)
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
