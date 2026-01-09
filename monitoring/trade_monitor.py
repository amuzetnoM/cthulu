"""
Trade Monitor - Clean Implementation
Monitors open positions for SL/TP hits and status changes.
"""
import logging
import threading
import time
from typing import Dict, Any, Set, Optional

logger = logging.getLogger(__name__)


class TradeMonitor:
    """
    Background trade monitor.
    
    Monitors:
    - Position status changes (closed, modified)
    - SL/TP hits
    - Connection status
    """
    
    def __init__(
        self,
        connector,
        trade_manager,
        poll_interval: float = 5.0
    ):
        """
        Initialize trade monitor.
        
        Args:
            connector: MT5 connector
            trade_manager: TradeManager instance
            poll_interval: Polling interval in seconds
        """
        self.connector = connector
        self.trade_manager = trade_manager
        self.poll_interval = poll_interval
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._known_tickets: Set[int] = set()
        
        logger.info(f"TradeMonitor initialized (poll_interval={poll_interval}s)")
    
    def start(self):
        """Start the background monitor."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
        logger.info("TradeMonitor started")
    
    def stop(self):
        """Stop the background monitor."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        
        logger.info("TradeMonitor stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                self._check_positions()
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            
            time.sleep(self.poll_interval)
    
    def _check_positions(self):
        """Check position status."""
        positions = self.connector.get_positions()
        current_tickets = {p.ticket for p in positions}
        
        # Check for closed positions
        closed_tickets = self._known_tickets - current_tickets
        for ticket in closed_tickets:
            logger.info(f"Position {ticket} closed (detected by monitor)")
            self.trade_manager.remove_position(ticket)
        
        # Check for new positions
        new_tickets = current_tickets - self._known_tickets
        for ticket in new_tickets:
            logger.debug(f"New position detected: {ticket}")
        
        # Check positions missing SL/TP
        for pos in positions:
            if pos.sl == 0 or pos.tp == 0:
                logger.warning(f"Position #{pos.ticket} missing SL/TP: sl={pos.sl or None}, tp={pos.tp or None}")
        
        self._known_tickets = current_tickets
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitor status."""
        return {
            'running': self._running,
            'known_positions': len(self._known_tickets),
            'poll_interval': self.poll_interval
        }
