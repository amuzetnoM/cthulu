"""
Position Lifecycle Manager - Clean Implementation
Handles adoption of external trades and position lifecycle events.
"""
import logging
from typing import Dict, Any, List, Optional
import time

logger = logging.getLogger(__name__)


class PositionLifecycle:
    """
    Manages the lifecycle of positions.
    
    Responsibilities:
    - Scan for and adopt external trades
    - Track position events (open, modify, close)
    - Apply initial SL/TP to adopted positions
    """
    
    def __init__(
        self,
        trade_manager,
        connector,
        adoption_policy: Dict[str, Any]
    ):
        """
        Initialize lifecycle manager.
        
        Args:
            trade_manager: TradeManager instance
            connector: MT5 connector
            adoption_policy: Adoption configuration
        """
        self.trade_manager = trade_manager
        self.connector = connector
        
        # Adoption policy
        self.enabled = adoption_policy.get('enabled', True)
        self.min_age = adoption_policy.get('min_trade_age_seconds', 0)
        self.apply_sltp = adoption_policy.get('apply_sltp_on_adopt', True)
        self.log_only = adoption_policy.get('log_only', False)
        
        if self.enabled:
            logger.info(f"External trade adoption ENABLED (log_only: {self.log_only})")
        else:
            logger.info("External trade adoption DISABLED")
    
    def scan_and_adopt(self) -> int:
        """
        Scan for external trades and adopt them.
        
        Returns:
            Number of trades adopted
        """
        if not self.enabled:
            return 0
        
        return self.trade_manager.scan_and_adopt()
    
    def on_position_opened(self, ticket: int, signal: Dict[str, Any]):
        """
        Handle position opened event.
        
        Args:
            ticket: Position ticket
            signal: Signal that opened the position
        """
        logger.info(f"Position opened: {ticket}")
    
    def on_position_closed(self, ticket: int, result: Dict[str, Any]):
        """
        Handle position closed event.
        
        Args:
            ticket: Position ticket
            result: Close result with P&L
        """
        logger.info(f"Position closed: {ticket}, P&L: {result.get('profit', 0):.2f}")
        
        # Clean up tracking
        self.trade_manager.remove_position(ticket)
    
    def on_position_modified(self, ticket: int, changes: Dict[str, Any]):
        """
        Handle position modified event.
        
        Args:
            ticket: Position ticket  
            changes: What was modified (sl, tp, etc.)
        """
        logger.debug(f"Position modified: {ticket}, changes: {changes}")
