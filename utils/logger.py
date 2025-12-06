"""
Logging utilities for Herald trading bot
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


def setup_logger(
    name: str = "Herald",
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up logger with console and optional file output
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler with colors if available
    if HAS_COLORLOG:
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        ))
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
    
    logger.addHandler(console_handler)
    
    # File handler with rotation if log_file specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(file_handler)
    
    return logger


class TradingLogger:
    """Specialized logger for trading events"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
    def trade_opened(self, symbol: str, order_type: str, volume: float, price: float, sl: float, tp: float):
        """Log trade opening"""
        self.logger.info(
            f"TRADE OPENED: {order_type} {volume} {symbol} @ {price:.5f} | "
            f"SL: {sl:.5f} | TP: {tp:.5f}"
        )
        
    def trade_closed(self, symbol: str, ticket: int, profit: float, reason: str = ""):
        """Log trade closing"""
        profit_str = f"+${profit:.2f}" if profit >= 0 else f"-${abs(profit):.2f}"
        self.logger.info(
            f"TRADE CLOSED: {symbol} #{ticket} | Profit: {profit_str} | "
            f"Reason: {reason or 'Manual'}"
        )
        
    def signal_generated(self, symbol: str, signal: str, confidence: float = None):
        """Log trading signal"""
        conf_str = f" (confidence: {confidence:.2%})" if confidence else ""
        self.logger.info(f"SIGNAL: {signal} for {symbol}{conf_str}")
        
    def risk_check(self, passed: bool, reason: str):
        """Log risk management check"""
        status = "PASSED" if passed else "REJECTED"
        self.logger.warning(f"RISK CHECK {status}: {reason}")
        
    def error(self, context: str, error: Exception):
        """Log error with context"""
        self.logger.error(f"ERROR in {context}: {str(error)}", exc_info=True)
