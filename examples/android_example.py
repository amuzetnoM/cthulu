#!/usr/bin/env python3
"""
Example: Using Cthulu on Android

This example demonstrates how to use Cthulu with the Android MT5 connector.
This branch uses the Android connector directly (no factory pattern).
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cthulu.connector import MT5Connector, ConnectionConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main example function."""
    
    logger.info("Cthulu Android Example")
    logger.info("=" * 60)
    
    # Configure connector for Android
    logger.info("\nConfiguring Android MT5 connector...")
    
    # Android configuration (bridge required)
    config = ConnectionConfig(
        bridge_type='rest',
        bridge_host='127.0.0.1',
        bridge_port=18812,
        login=0,  # Set to 0 to attach to running MT5
        password='',
        server='',
        timeout=60000,
        max_retries=3
    )
    
    # Create connector (directly uses Android connector)
    logger.info("Creating MT5 connector...")
    connector = MT5Connector(config)
    logger.info(f"Connector type: {type(connector).__name__}")
    
    # Connect to MT5
    logger.info("\nConnecting to MT5...")
    if connector.connect():
        logger.info("✓ Successfully connected to MT5!")
        
        # Get account info
        logger.info("\nRetrieving account information...")
        account_info = connector.get_account_info()
        
        if account_info:
            logger.info(f"✓ Account Info:")
            logger.info(f"  Login: {account_info.get('login', 'N/A')}")
            logger.info(f"  Server: {account_info.get('server', 'N/A')}")
            logger.info(f"  Balance: ${account_info.get('balance', 0):.2f}")
        else:
            logger.warning("✗ Could not retrieve account info")
        
        # Disconnect
        logger.info("\nDisconnecting...")
        connector.disconnect()
        logger.info("✓ Disconnected successfully")
        
    else:
        logger.error("✗ Failed to connect to MT5")
        logger.error("\nTroubleshooting:")
        logger.error("1. Is the MT5 bridge server running?")
        logger.error("   python connector/mt5_bridge_server.py")
        logger.error("2. Is the MT5 Android app installed and logged in?")
        logger.error("3. Check bridge server logs for errors")
        return 1
    
    logger.info("\n" + "=" * 60)
    logger.info("Example completed successfully!")
    logger.info("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
