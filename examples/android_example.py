#!/usr/bin/env python3
"""
Example: Using Cthulu on Android

This example demonstrates how to use Cthulu with the Android MT5 connector.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cthulu.connector import create_connector, get_connector_type
from cthulu.utils.platform_detector import get_platform_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main example function."""
    
    # Detect platform
    logger.info("Detecting platform...")
    platform_info = get_platform_info()
    
    logger.info(f"Platform: {platform_info.platform_type}")
    logger.info(f"Is Android: {platform_info.is_android}")
    
    # Configure connector
    if platform_info.is_android:
        config = {
            'bridge_type': 'rest',
            'bridge_host': '127.0.0.1',
            'bridge_port': 18812,
            'login': 0,
            'password': '',
            'server': '',
        }
    else:
        config = {
            'login': 0,
            'password': '',
            'server': '',
        }
    
    # Create and connect
    connector = create_connector(config)
    logger.info(f"Created connector: {type(connector).__name__}")
    
    if connector.connect():
        logger.info("✓ Connected to MT5!")
        
        # Get account info
        account_info = connector.get_account_info()
        if account_info:
            logger.info(f"Balance: ${account_info.get('balance', 0):.2f}")
        
        connector.disconnect()
        logger.info("✓ Disconnected")
        return 0
    else:
        logger.error("✗ Failed to connect")
        return 1


if __name__ == '__main__':
    sys.exit(main())
