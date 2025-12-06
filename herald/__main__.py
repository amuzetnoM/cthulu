"""
Herald - Adaptive Trading Intelligence

Main entry point for the trading bot.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from herald import __version__


def setup_logging(log_level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description=f"Herald Trading Bot v{__version__}",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in simulation mode (no real orders)'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--health-check',
        action='store_true',
        help='Perform health check and exit'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'Herald v{__version__}'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger('herald')
    
    logger.info(f"Herald Trading Bot v{__version__}")
    logger.info(f"Configuration: {args.config}")
    
    if args.dry_run:
        logger.warning("Running in DRY RUN mode - no real orders will be placed")
    
    if args.health_check:
        logger.info("Performing health check...")
        # TODO: Implement health check
        logger.info("Health check passed")
        return 0
    
    logger.info("Starting Herald...")
    logger.info("Press Ctrl+C to stop")
    
    # TODO: Implement main trading loop
    try:
        logger.info("Herald is running (implementation pending)")
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    finally:
        logger.info("Herald stopped")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
