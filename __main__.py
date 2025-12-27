"""
Herald Autonomous Trading System

Main entry point - orchestrates system startup, trading loop, and shutdown.

This is the entry point that delegates to modular components:
- core.bootstrap: System initialization
- core.trading_loop: Main trading logic
- core.shutdown: Graceful shutdown
"""

import sys
import signal as sig_module
import logging
import argparse
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

__version__ = "5.0.0"  # Architectural overhaul complete

from core.bootstrap import HeraldBootstrap, SystemComponents
from core.trading_loop import TradingLoop, TradingLoopContext, ensure_runtime_indicators
from core.shutdown import ShutdownHandler, create_shutdown_handler
from config_schema import Config
from config.mindsets import apply_mindset, list_mindsets
from observability.logger import setup_logger

# Backwards-compatible helper for tests & integrations
# Signature matches older tests: init_ml_collector(config, args, logger)
def init_ml_collector(config=None, args=None, logger=None):
    """Initialize ML collector based on config and CLI args.

    Args:
        config: Application configuration dict/object
        args: Parsed CLI args (may contain flags to enable/disable ML)
        logger: Optional logger
    Returns: MLDataCollector-like object (best-effort stub if unavailable)
    """
    try:
        enabled = False
        prefix = 'events'

        if config is not None:
            try:
                # config may be dict-like
                enabled = bool(config.get('ml', {}).get('enabled', False))
                prefix = config.get('ml', {}).get('prefix', prefix)
            except Exception:
                pass

        # CLI arg override (support both enable_ml and ml flags)
        try:
            if args is not None and getattr(args, 'enable_ml', None) is not None:
                # Explicit CLI override: if False, disable collector (return None)
                if getattr(args, 'enable_ml') is False:
                    return None
                enabled = bool(getattr(args, 'enable_ml'))
            elif args is not None and getattr(args, 'ml', None) is not None:
                enabled = bool(getattr(args, 'ml'))
        except Exception:
            pass

        if not enabled:
            # return a no-op stub
            class _Stub:
                def record_event(self, *args, **kwargs):
                    return
                def record_order(self, *args, **kwargs):
                    return
                def record_execution(self, *args, **kwargs):
                    return
                def close(self, *args, **kwargs):
                    return
            return _Stub()

        from ML_RL.instrumentation import MLDataCollector
        return MLDataCollector(prefix=prefix)
    except Exception:
        # Best-effort stub if ML collector is unavailable or fails to initialize
        class _Stub2:
            def record_event(self, *args, **kwargs):
                return
            def record_order(self, *args, **kwargs):
                return
            def record_execution(self, *args, **kwargs):
                return
            def close(self, *args, **kwargs):
                return
        return _Stub2()

# Global shutdown flag
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    shutdown_requested = True
    print("\nShutdown signal received, initiating graceful shutdown...")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Herald Autonomous Trading System v5.0")
    parser.add_argument("--config", type=str, default="config.json",
                       help="Path to configuration file")
    parser.add_argument("--mindset", type=str, default=None,
                       help="Trading mindset (conservative/balanced/aggressive/ultra_aggressive)")
    parser.add_argument("--list-mindsets", action="store_true",
                       help="List available mindsets and exit")
    parser.add_argument("--dry-run", action="store_true",
                       help="Dry run mode (no actual trades)")
    parser.add_argument("--advisory", action="store_true",
                       help="Advisory mode (signals only, no execution)")
    parser.add_argument("--ghost", action="store_true",
                       help="Ghost mode (test strategy without actual trades)")
    parser.add_argument("--max-loops", type=int, default=None,
                       help="Maximum iterations (for testing)")
    return parser.parse_args()


def main():
    """
    Main entry point for Herald trading system.
    
    Flow:
        1. Parse arguments
        2. Bootstrap system (initialize all components)
        3. Run trading loop
        4. Graceful shutdown
    """
    global shutdown_requested
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Handle --list-mindsets
    if args.list_mindsets:
        print("\nAvailable Mindsets:")
        print("=" * 50)
        for name, description in list_mindsets().items():
            print(f"\n{name}:")
            print(f"  {description}")
        print("\n" + "=" * 50)
        return 0
        
    # Setup logger
    logger = setup_logger(
        name="herald",
        log_file="logs/herald.log",
        level=logging.INFO
    )
    
    logger.info("=" * 80)
    logger.info(f"Herald Autonomous Trading System v{__version__}")
    logger.info("=" * 80)
    logger.info(f"Configuration: {args.config}")
    logger.info(f"Mindset: {args.mindset or 'default'}")
    logger.info(f"Mode: {'Dry-run' if args.dry_run else 'Advisory' if args.advisory else 'Ghost' if args.ghost else 'Live'}")
    logger.info("=" * 80)
    
    # Register signal handlers
    sig_module.signal(sig_module.SIGINT, signal_handler)
    sig_module.signal(sig_module.SIGTERM, signal_handler)
    
    components: Optional[SystemComponents] = None
    
    try:
        # Phase 1: Bootstrap system
        logger.info("Phase 1: Bootstrapping system...")
        bootstrap = HeraldBootstrap(logger=logger)
        components = bootstrap.bootstrap(args.config, args)
        logger.info("System bootstrap complete")
        
        # Phase 2: Create trading loop context
        logger.info("Phase 2: Initializing trading loop...")
        trading_context = TradingLoopContext(
            connector=components.connector,
            data_layer=components.data_layer,
            strategy=components.strategy,
            execution_engine=components.execution_engine,
            risk_manager=components.risk_manager,
            position_tracker=components.position_tracker,
            position_lifecycle=components.position_lifecycle,
            trade_adoption_manager=components.trade_adoption_manager,
            exit_coordinator=components.exit_coordinator,
            database=components.database,
            metrics=components.metrics,
            logger=logger,
            symbol=components.config.get('symbol', 'EURUSD'),
            timeframe=components.config.get('timeframe', 1),  # MT5 M1
            poll_interval=components.config.get('poll_interval', 60),
            lookback_bars=components.config.get('lookback_bars', 100),
            dry_run=args.dry_run,
            indicators=components.indicators or [],
            exit_strategies=components.exit_strategies or [],
            trade_adoption_policy=components.config.get('trade_adoption', {}),
            config=components.config,
            args=args,
            ml_collector=components.ml_collector,
            advisory_manager=components.advisory_manager,
            exporter=components.exporter,
        )
        
        trading_loop = TradingLoop(trading_context)
        logger.info("Trading loop initialized")
        
        # Phase 3: Run trading loop
        logger.info("Phase 3: Starting trading loop...")
        logger.info("Press Ctrl+C to stop")
        trading_loop.run()
        
        logger.info("Trading loop completed")
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        shutdown_requested = True
        
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        shutdown_requested = True
        return 1
        
    finally:
        # Phase 4: Graceful shutdown
        if components:
            logger.info("Phase 4: Initiating graceful shutdown...")
            
            try:
                shutdown_handler = create_shutdown_handler(
                    connector=components.connector,
                    position_lifecycle=components.position_lifecycle,
                    position_tracker=components.position_tracker,
                    database=components.database,
                    metrics_collector=components.metrics,
                    ml_collector=components.ml_collector,
                    trade_monitor=components.monitor,
                    logger=logger
                )
                
                shutdown_handler.shutdown()
                logger.info("✓ Graceful shutdown complete")
                
            except Exception as e:
                logger.error(f"Error during shutdown: {e}", exc_info=True)
                
        logger.info("=" * 80)
        logger.info("Herald shutdown complete")
        logger.info("=" * 80)
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
