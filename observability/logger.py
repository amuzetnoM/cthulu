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
    name: str = "herald",
    level: str = "INFO",
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
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    if json_format:
        # JSON format for production
        formatter = logging.Formatter(
            '{"timestamp":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
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
