"""
Trade Adoption Module

Handles detection and adoption of external (manual) trades that were placed
outside of Herald. This allows Cthulu to manage positions that users create
manually in MT5.

Responsibilities:
- Scan for external/manual trades
- Apply Cthulu's exit strategies to external trades
- Policy-based filtering (which trades to adopt)
- Logging and tracking of adoptions

Does NOT:
- Execute new trades (see lifecycle.py)
- Track position state (see tracker.py)
- Make risk decisions (see risk/evaluator.py)
"""

from dataclasses import dataclass
from typing import List, Optional, Set
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class TradeAdoptionPolicy:
    """
    Configuration for trade adoption behavior.
    """
    # Enable/disable adoption
    enabled: bool = True
    
    # Symbol filters
    allowed_symbols: Optional[List[str]] = None  # None = all symbols
    blocked_symbols: List[str] = None  # Symbols to never adopt
    
    # Age filters
    max_age_hours: Optional[float] = None  # Don't adopt trades older than this
    min_age_seconds: float = 60  # Wait this long before adopting (avoid race conditions)
    
    # Size filters
    min_volume: Optional[float] = None
    max_volume: Optional[float] = None
    
    # Magic number filters
    excluded_magic_numbers: Set[int] = None  # Don't adopt these magic numbers
    
    # Safety
    apply_emergency_sl: bool = True  # Add SL if none exists
    emergency_sl_points: float = 100  # Emergency SL distance
    apply_emergency_tp: bool = False  # Add TP if none exists
    emergency_tp_points: float = 100  # Emergency TP distance
    
    # Logging
    log_only: bool = False  # If True, only log orphans without adopting
    
    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.blocked_symbols is None:
            self.blocked_symbols = []
        if self.excluded_magic_numbers is None:
            self.excluded_magic_numbers = set()


class TradeAdoptionManager:
    """
    Manages adoption of external trades into Cthulu's management system.
    
    This class identifies manual trades placed outside Cthulu and brings them
    under Herald's exit strategy management.
    """
    
    def __init__(self, connector, position_tracker, position_lifecycle, 
                 policy: Optional[TradeAdoptionPolicy] = None):
        """
        Initialize the trade adoption manager.
        
        Args:
            connector: MT5 connector
            position_tracker: PositionTracker instance
            position_lifecycle: PositionLifecycle instance
            policy: TradeAdoptionPolicy configuration
        """
        self.connector = connector
        self.tracker = position_tracker
        self.lifecycle = position_lifecycle
        self.policy = policy or TradeAdoptionPolicy()
        
        # Track which tickets we've already adopted
        self._adopted_tickets: Set[int] = set()
        
        logger.info(f"TradeAdoptionManager initialized (enabled={self.policy.enabled})")
    
    def scan_and_adopt(self) -> int:
        """
        Scan for external trades and adopt them based on policy.
        
        Returns:
            Number of trades adopted in this scan
        """
        if not self.policy.enabled:
            return 0
        
        try:
            # Get all trades identified as external
            external_trades = self._identify_external_trades()
            
            adopted_count = 0
            for trade in external_trades:
                if self._should_adopt(trade):
                    if self._adopt_trade(trade):
                        adopted_count += 1
            
            if adopted_count > 0:
                logger.info(f"Adopted {adopted_count} external trades")
            
            return adopted_count
            
        except Exception as e:
            logger.error(f"Error during trade adoption scan: {e}", exc_info=True)
            return 0
    
    def _identify_external_trades(self) -> List[dict]:
        """
        Identify trades that were not opened by Cthulu.
        
        Returns:
            List of external trade dicts from MT5
        """
        try:
            # Get all open positions from MT5
            all_positions = self.connector.get_open_positions()
            if not all_positions:
                return []
            
            # Filter to find external trades
            external_trades = []
            for position in all_positions:
                ticket = position.get('ticket')
                
                # Skip if already tracking this ticket
                if self.tracker.get_position(ticket):
                    continue
                
                # Skip if already adopted in a previous scan
                if ticket in self._adopted_tickets:
                    continue
                
                # This is an external trade
                external_trades.append(position)
            
            return external_trades
            
        except Exception as e:
            logger.error(f"Error identifying external trades: {e}", exc_info=True)
            return []
    
    def _should_adopt(self, trade: dict) -> bool:
        """
        Determine if a trade should be adopted based on policy.
        
        Args:
            trade: Trade dict from MT5
            
        Returns:
            True if trade should be adopted, False otherwise
        """
        try:
            symbol = trade.get('symbol')
            ticket = trade.get('ticket')
            volume = trade.get('volume', 0.0)
            magic = trade.get('magic', 0)
            open_time = trade.get('time', datetime.now())
            if isinstance(open_time, (int, float)):
                open_time = datetime.fromtimestamp(open_time)
            
            # Check symbol whitelist
            if self.policy.allowed_symbols and symbol not in self.policy.allowed_symbols:
                logger.debug(f"Trade {ticket} symbol {symbol} not in allowed list")
                return False
            
            # Check symbol blacklist
            if symbol in self.policy.blocked_symbols:
                logger.debug(f"Trade {ticket} symbol {symbol} is blocked")
                return False
            
            # Check magic number exclusions
            if magic in self.policy.excluded_magic_numbers:
                logger.debug(f"Trade {ticket} magic {magic} is excluded")
                return False
            
            # Check age limits
            age = datetime.now() - open_time
            if self.policy.max_age_hours and age > timedelta(hours=self.policy.max_age_hours):
                logger.debug(f"Trade {ticket} too old ({age.total_seconds() / 3600:.1f}h)")
                return False
            
            if age < timedelta(seconds=self.policy.min_age_seconds):
                logger.debug(f"Trade {ticket} too new ({age.total_seconds():.0f}s)")
                return False
            
            # Check volume limits
            if self.policy.min_volume and volume < self.policy.min_volume:
                logger.debug(f"Trade {ticket} volume {volume} below minimum")
                return False
            
            if self.policy.max_volume and volume > self.policy.max_volume:
                logger.debug(f"Trade {ticket} volume {volume} above maximum")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking adoption policy: {e}", exc_info=True)
            return False
    
    def _adopt_trade(self, trade: dict) -> bool:
        """
        Adopt an external trade into Cthulu's management.
        
        Args:
            trade: Trade dict from MT5
            
        Returns:
            True if adopted successfully, False otherwise
        """
        try:
            from position.tracker import PositionInfo
            
            ticket = trade.get('ticket')
            symbol = trade.get('symbol')
            trade_type = trade.get('type')  # 0=buy, 1=sell
            volume = trade.get('volume', 0.0)
            open_price = trade.get('price_open', 0.0)
            current_price = trade.get('price_current', 0.0)
            sl = trade.get('sl')
            tp = trade.get('tp')
            profit = trade.get('profit', 0.0)
            open_time = trade.get('time', datetime.now())
            magic = trade.get('magic', 0)
            comment = trade.get('comment', '')
            
            # Convert trade type to string
            type_str = "buy" if trade_type == 0 else "sell"
            
            # Apply emergency SL/TP if configured
            if self.policy.apply_emergency_sl and not sl:
                if type_str == "buy":
                    sl = open_price - self.policy.emergency_sl_points * self.connector.get_point(symbol)
                else:
                    sl = open_price + self.policy.emergency_sl_points * self.connector.get_point(symbol)
                
                # Modify position with emergency SL
                self.lifecycle.modify_position(ticket, sl=sl)
                logger.warning(f"Applied emergency SL to external trade {ticket}")
            
            if self.policy.apply_emergency_tp and not tp:
                if type_str == "buy":
                    tp = open_price + self.policy.emergency_tp_points * self.connector.get_point(symbol)
                else:
                    tp = open_price - self.policy.emergency_tp_points * self.connector.get_point(symbol)
                
                # Modify position with emergency TP
                self.lifecycle.modify_position(ticket, tp=tp)
                logger.warning(f"Applied emergency TP to external trade {ticket}")
            
            # Create PositionInfo for tracking
            position = PositionInfo(
                ticket=ticket,
                symbol=symbol,
                type=type_str,
                volume=volume,
                open_price=open_price,
                current_price=current_price,
                sl=sl,
                tp=tp,
                profit=profit,
                open_time=open_time,
                magic_number=magic,
                comment=f"[ADOPTED] {comment}",
                strategy_name="external",
                entry_reason="Manual trade adopted by Cthulu",
                is_external=True
            )
            
            # Add to tracker
            self.tracker.track_position(position)
            
            # Persist to database
            self.lifecycle.persist_position(position)
            
            # Mark as adopted
            self._adopted_tickets.add(ticket)
            
            logger.info(f"Adopted external trade {ticket}: {symbol} {type_str} {volume}")
            return True
            
        except Exception as e:
            logger.error(f"Error adopting trade {trade.get('ticket')}: {e}", exc_info=True)
            return False
    
    def get_adopted_count(self) -> int:
        """
        Get count of adopted trades.
        
        Returns:
            Number of trades adopted
        """
        return len(self._adopted_tickets)
    
    def get_adoption_statistics(self) -> dict:
        """
        Get adoption statistics.
        
        Returns:
            Dict with adoption metrics
        """
        external_positions = [p for p in self.tracker.get_all_positions() if p.is_external]
        
        return {
            'total_adopted': len(self._adopted_tickets),
            'currently_tracked': len(external_positions),
            'policy_enabled': self.policy.enabled,
            'symbols': list(set(p.symbol for p in external_positions))
        }
    
    def log_external_trade(self, trade: dict) -> None:
        """
        Log details of an external trade for analysis.
        
        Args:
            trade: Trade dict from MT5
        """
        logger.info(
            f"External trade detected: "
            f"Ticket={trade.get('ticket')}, "
            f"Symbol={trade.get('symbol')}, "
            f"Type={trade.get('type')}, "
            f"Volume={trade.get('volume')}, "
            f"Magic={trade.get('magic')}"
        )




