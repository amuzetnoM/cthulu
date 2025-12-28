"""
Logging Module

Structured logging configuration.
JSON format for production, human-readable for development.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


def setup_logger(
    name: str = "Cthulu",
    level: "str|int" = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False
) -> logging.Logger:
    """
    Configure structured logger.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logs
        json_format: Use JSON format (for production)
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    # Support both integer and string levels
    if isinstance(level, int):
        level_value = level
    else:
        level_value = getattr(logging, str(level).upper(), logging.INFO)

    logger.setLevel(level_value)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level_value)
    
    if json_format:
        # JSON format for production
        formatter = logging.Formatter(
            '{"timestamp":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Compact human-readable format for development: short timestamp and no repeated logger name
        # Example: 2025-12-28T19:07:47 [INFO] Starting up
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get existing logger.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)




