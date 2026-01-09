"""
Trade Manager - Clean Implementation
Single source of truth for position tracking and adoption.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import time

logger = logging.getLogger(__name__)


@dataclass
class TrackedPosition:
    """A position being tracked by Cthulu."""
    ticket: int
    symbol: str
    type: int  # 0=buy, 1=sell
    volume: float
    price_open: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    profit: float = 0.0
    magic: int = 0
    comment: str = ""
    
    # Tracking metadata
    adopted: bool = False
    adoption_time: Optional[float] = None
    signal_id: Optional[str] = None
    entry_strategy: Optional[str] = None
    
    @property
    def is_buy(self) -> bool:
        return self.type == 0
    
    @property
    def direction(self) -> str:
        return 'buy' if self.is_buy else 'sell'


class TradeManager:
    """
    Central trade tracking and adoption manager.
    
    Responsibilities:
    - Track all positions (internal + adopted)
    - Detect and adopt external trades
    - Provide position lookup for SLTP management
    - Record trade lifecycle events
    """
    
    CTHULU_MAGIC = 123456  # Magic number for Cthulu-placed trades
    
    def __init__(self, connector, config: Dict[str, Any]):
        """
        Initialize Trade Manager.
        
        Args:
            connector: MT5 connector
            config: System configuration
        """
        self.connector = connector
        self.config = config
        
        # Position tracking
        self._positions: Dict[int, TrackedPosition] = {}
        self._adopted_tickets: Set[int] = set()
        
        # Adoption policy
        adoption_policy = config.get('adoption_policy', {})
        self.adoption_enabled = adoption_policy.get('enabled', True)
        self.min_trade_age = adoption_policy.get('min_trade_age_seconds', 0)
        self.apply_sltp_on_adopt = adoption_policy.get('apply_sltp_on_adopt', True)
        
        logger.info(f"TradeManager initialized: adoption_enabled={self.adoption_enabled}")
    
    def register_trade(
        self,
        ticket: int,
        signal: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """
        Register a trade placed by Cthulu.
        
        Args:
            ticket: Order ticket
            signal: Signal that triggered the trade
            result: Execution result
        """
        position = TrackedPosition(
            ticket=ticket,
            symbol=signal.get('symbol', 'UNKNOWN'),
            type=0 if signal.get('direction') == 'buy' else 1,
            volume=result.get('volume', 0.0),
            price_open=result.get('price', 0.0),
            magic=self.CTHULU_MAGIC,
            adopted=False,
            signal_id=signal.get('signal_id'),
            entry_strategy=signal.get('strategy')
        )
        
        self._positions[ticket] = position
        logger.info(f"Registered trade: {ticket} {position.symbol} {position.direction}")
    
    def scan_for_external_trades(self) -> List[TrackedPosition]:
        """
        Scan MT5 for external trades to adopt.
        
        Returns:
            List of external positions not yet tracked
        """
        if not self.adoption_enabled:
            return []
        
        external_trades = []
        
        try:
            mt5_positions = self.connector.get_positions()
            
            for pos in mt5_positions:
                ticket = pos.ticket
                
                # Skip if already tracked
                if ticket in self._positions:
                    continue
                
                # Skip if it's our own trade
                if pos.magic == self.CTHULU_MAGIC:
                    continue
                
                # Check trade age
                trade_age = time.time() - pos.time
                if trade_age < self.min_trade_age:
                    continue
                
                # This is an external trade
                external = TrackedPosition(
                    ticket=ticket,
                    symbol=pos.symbol,
                    type=pos.type,
                    volume=pos.volume,
                    price_open=pos.price_open,
                    sl=pos.sl if pos.sl != 0 else None,
                    tp=pos.tp if pos.tp != 0 else None,
                    profit=pos.profit,
                    magic=pos.magic,
                    comment=pos.comment,
                    adopted=True,
                    adoption_time=time.time()
                )
                
                external_trades.append(external)
                logger.info(f"Found external trade to adopt: {ticket} {pos.symbol} {'BUY' if pos.type == 0 else 'SELL'}")
        
        except Exception as e:
            logger.error(f"Error scanning for external trades: {e}")
        
        return external_trades
    
    def adopt_trade(self, position: TrackedPosition) -> bool:
        """
        Adopt an external trade into Cthulu's management.
        
        Args:
            position: Position to adopt
            
        Returns:
            True if adoption successful
        """
        ticket = position.ticket
        
        if ticket in self._positions:
            logger.debug(f"Trade {ticket} already adopted")
            return False
        
        self._positions[ticket] = position
        self._adopted_tickets.add(ticket)
        
        logger.info(f"Adopted trade {ticket}: {position.symbol} {position.direction} @ {position.price_open}")
        
        return True
    
    def scan_and_adopt(self) -> int:
        """
        Scan for and adopt external trades.
        
        Returns:
            Number of trades adopted
        """
        logger.info("TradeManager.scan_and_adopt: policy.enabled=" + str(self.adoption_enabled))
        
        external_trades = self.scan_for_external_trades()
        
        logger.info(f"Adoption scan complete: {len(external_trades)} external trades found")
        
        adopted_count = 0
        for position in external_trades:
            if self.adopt_trade(position):
                adopted_count += 1
        
        return adopted_count
    
    def get_position(self, ticket: int) -> Optional[TrackedPosition]:
        """Get a tracked position by ticket."""
        return self._positions.get(ticket)
    
    def get_all_positions(self) -> List[TrackedPosition]:
        """Get all tracked positions."""
        # Refresh from MT5
        self._refresh_positions()
        return list(self._positions.values())
    
    def get_adopted_positions(self) -> List[TrackedPosition]:
        """Get all adopted (external) positions."""
        return [p for p in self._positions.values() if p.adopted]
    
    def get_positions_by_symbol(self, symbol: str) -> List[TrackedPosition]:
        """Get all positions for a symbol."""
        return [p for p in self._positions.values() if p.symbol == symbol]
    
    def _refresh_positions(self):
        """Refresh position data from MT5."""
        try:
            mt5_positions = self.connector.get_positions()
            mt5_tickets = {p.ticket for p in mt5_positions}
            
            # Update existing positions
            for pos in mt5_positions:
                if pos.ticket in self._positions:
                    tracked = self._positions[pos.ticket]
                    tracked.profit = pos.profit
                    tracked.sl = pos.sl if pos.sl != 0 else tracked.sl
                    tracked.tp = pos.tp if pos.tp != 0 else tracked.tp
            
            # Remove closed positions
            closed_tickets = set(self._positions.keys()) - mt5_tickets
            for ticket in closed_tickets:
                logger.info(f"Position {ticket} closed, removing from tracking")
                self._positions.pop(ticket, None)
                self._adopted_tickets.discard(ticket)
        
        except Exception as e:
            logger.error(f"Error refreshing positions: {e}")
    
    def remove_position(self, ticket: int):
        """Remove a position from tracking (called when closed)."""
        self._positions.pop(ticket, None)
        self._adopted_tickets.discard(ticket)
        logger.info(f"Removed position {ticket} from tracking")
    
    def get_position_count(self, symbol: Optional[str] = None) -> int:
        """Get count of open positions, optionally filtered by symbol."""
        if symbol:
            return len(self.get_positions_by_symbol(symbol))
        return len(self._positions)
