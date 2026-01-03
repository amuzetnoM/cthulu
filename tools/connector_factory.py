"""
MT5 Connector Factory

Automatically selects and instantiates the appropriate MT5 connector
based on the current platform (Windows, Linux, Android).

This is a standalone tool - not integrated into the core system.
"""

import logging
from typing import Union, Optional, Dict, Any

from tools.platform_detector import get_platform_info, PlatformInfo
from cthulu.connector.mt5_connector import MT5Connector, ConnectionConfig
from cthulu.connector.mt5_connector_android import MT5ConnectorAndroid, AndroidConnectionConfig


logger = logging.getLogger("Cthulu.connector.factory")


def create_connector(
    config: Optional[Union[ConnectionConfig, AndroidConnectionConfig, Dict[str, Any]]] = None,
    force_platform: Optional[str] = None
) -> Union[MT5Connector, MT5ConnectorAndroid]:
    """
    Create and return the appropriate MT5 connector for the current platform.
    
    Args:
        config: Connection configuration (can be ConnectionConfig, AndroidConnectionConfig, or dict)
        force_platform: Force a specific platform connector ('windows', 'linux', 'android')
        
    Returns:
        Platform-specific MT5 connector instance
        
    Raises:
        ValueError: If platform is unsupported or configuration is invalid
        
    Example:
        >>> # Auto-detect platform and create connector
        >>> connector = create_connector(config_dict)
        >>> 
        >>> # Force Android connector
        >>> connector = create_connector(config_dict, force_platform='android')
    """
    # Detect platform
    platform_info = get_platform_info()
    
    # Determine which platform to use
    if force_platform:
        target_platform = force_platform.lower()
        logger.info(f"Forcing platform: {target_platform}")
    else:
        target_platform = platform_info.platform_type
        logger.info(f"Auto-detected platform: {target_platform}")
    
    # Log platform details
    logger.info(f"Platform details: {platform_info.system}, Python {platform_info.python_version}")
    if platform_info.is_android:
        logger.info(f"Running on Android (Termux: {platform_info.is_termux})")
    
    # Convert dict config to appropriate config object if needed
    if isinstance(config, dict):
        config = _dict_to_config(config, target_platform)
    
    # Create platform-specific connector
    if target_platform == "android":
        return _create_android_connector(config, platform_info)
    elif target_platform in ["windows", "linux", "macos"]:
        return _create_standard_connector(config, platform_info)
    else:
        raise ValueError(f"Unsupported platform: {target_platform}")


def _dict_to_config(
    config_dict: Dict[str, Any],
    platform: str
) -> Union[ConnectionConfig, AndroidConnectionConfig]:
    """Convert dictionary config to appropriate config object."""
    
    if platform == "android":
        # Create Android config
        return AndroidConnectionConfig(
            bridge_host=config_dict.get('bridge_host', '127.0.0.1'),
            bridge_port=config_dict.get('bridge_port', 18812),
            bridge_type=config_dict.get('bridge_type', 'rest'),
            login=config_dict.get('login', 0),
            password=config_dict.get('password', ''),
            server=config_dict.get('server', ''),
            timeout=config_dict.get('timeout', 60000),
            max_retries=config_dict.get('max_retries', 3),
            retry_delay=config_dict.get('retry_delay', 5),
            bridge_auth_token=config_dict.get('bridge_auth_token'),
            bridge_data_dir=config_dict.get('bridge_data_dir')
        )
    else:
        # Create standard config
        return ConnectionConfig(
            login=config_dict.get('login', 0),
            password=config_dict.get('password', ''),
            server=config_dict.get('server', ''),
            timeout=config_dict.get('timeout', 60000),
            portable=config_dict.get('portable', False),
            path=config_dict.get('path'),
            max_retries=config_dict.get('max_retries', 3),
            retry_delay=config_dict.get('retry_delay', 5),
            start_on_missing=config_dict.get('start_on_missing', False),
            start_wait=config_dict.get('start_wait', 5)
        )


def _create_android_connector(
    config: Optional[Union[AndroidConnectionConfig, ConnectionConfig]],
    platform_info: PlatformInfo
) -> MT5ConnectorAndroid:
    """Create Android-specific connector."""
    
    logger.info("Creating Android MT5 connector")
    
    # If standard config provided, convert to Android config
    if isinstance(config, ConnectionConfig):
        android_config = AndroidConnectionConfig(
            login=config.login,
            password=config.password,
            server=config.server,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay
        )
    elif config is None:
        android_config = AndroidConnectionConfig()
    else:
        android_config = config
    
    connector = MT5ConnectorAndroid(android_config)
    
    logger.info("Android connector created successfully")
    logger.info(f"Bridge configuration: {android_config.bridge_type} @ {android_config.bridge_host}:{android_config.bridge_port}")
    
    return connector


def _create_standard_connector(
    config: Optional[Union[ConnectionConfig, AndroidConnectionConfig]],
    platform_info: PlatformInfo
) -> MT5Connector:
    """Create standard (Windows/Linux) connector."""
    
    logger.info(f"Creating standard MT5 connector for {platform_info.platform_type}")
    
    # If Android config provided, extract relevant fields
    if isinstance(config, AndroidConnectionConfig):
        standard_config = ConnectionConfig(
            login=config.login,
            password=config.password,
            server=config.server,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay
        )
    elif config is None:
        standard_config = ConnectionConfig(login=0, password="", server="")
    else:
        standard_config = config
    
    connector = MT5Connector(standard_config)
    
    logger.info("Standard connector created successfully")
    
    return connector


def get_connector_type(platform: Optional[str] = None) -> str:
    """
    Get the connector type that would be used for a platform.
    
    Args:
        platform: Platform name or None for auto-detect
        
    Returns:
        Connector type ('android' or 'standard')
    """
    if platform:
        return 'android' if platform.lower() == 'android' else 'standard'
    
    platform_info = get_platform_info()
    return 'android' if platform_info.is_android else 'standard'
