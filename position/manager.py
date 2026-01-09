"""
Position Manager - Clean Implementation
Handles position state and exposure tracking.
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PositionState:
    """State tracking for a position."""
    ticket: int
    symbol: str
    unrealized_pnl: float = 0.0
    peak_profit: float = 0.0
    drawdown_from_peak: float = 0.0
    time_in_trade: float = 0.0


class PositionManager:
    """
    Position state and exposure manager.
    
    Responsibilities:
    - Track position P&L and state
    - Calculate exposure per symbol
    - Provide position aggregation
    """
    
    def __init__(self, connector, config: Dict[str, Any]):
        """
        Initialize position manager.
        
        Args:
            connector: MT5 connector
            config: System configuration
        """
        self.connector = connector
        self.config = config
        
        self._position_states: Dict[int, PositionState] = {}
        
        logger.info("PositionManager initialized")
    
    def get_open_positions(self) -> List[Any]:
        """Get all open positions from MT5."""
        return self.connector.get_positions()
    
    def get_position_count(self, symbol: Optional[str] = None) -> int:
        """
        Get count of open positions.
        
        Args:
            symbol: Filter by symbol (None for all)
            
        Returns:
            Number of open positions
        """
        positions = self.get_open_positions()
        
        if symbol:
            return len([p for p in positions if p.symbol == symbol])
        return len(positions)
    
    def get_total_exposure(self, symbol: Optional[str] = None) -> float:
        """
        Get total exposure (sum of volumes).
        
        Args:
            symbol: Filter by symbol (None for all)
            
        Returns:
            Total volume/lots
        """
        positions = self.get_open_positions()
        
        if symbol:
            positions = [p for p in positions if p.symbol == symbol]
        
        return sum(p.volume for p in positions)
    
    def get_total_unrealized_pnl(self, symbol: Optional[str] = None) -> float:
        """
        Get total unrealized P&L.
        
        Args:
            symbol: Filter by symbol (None for all)
            
        Returns:
            Total unrealized profit/loss
        """
        positions = self.get_open_positions()
        
        if symbol:
            positions = [p for p in positions if p.symbol == symbol]
        
        return sum(p.profit for p in positions)
    
    def get_position_by_ticket(self, ticket: int) -> Optional[Any]:
        """Get a specific position by ticket."""
        return self.connector.get_position(ticket)
    
    def update_position_state(self, ticket: int, current_pnl: float):
        """
        Update tracked state for a position.
        
        Args:
            ticket: Position ticket
            current_pnl: Current unrealized P&L
        """
        if ticket not in self._position_states:
            positions = self.get_open_positions()
            for p in positions:
                if p.ticket == ticket:
                    self._position_states[ticket] = PositionState(
                        ticket=ticket,
                        symbol=p.symbol
                    )
                    break
        
        if ticket in self._position_states:
            state = self._position_states[ticket]
            state.unrealized_pnl = current_pnl
            
            if current_pnl > state.peak_profit:
                state.peak_profit = current_pnl
            
            state.drawdown_from_peak = state.peak_profit - current_pnl
    
    def get_position_state(self, ticket: int) -> Optional[PositionState]:
        """Get tracked state for a position."""
        return self._position_states.get(ticket)
    
    def clear_position_state(self, ticket: int):
        """Clear state for a closed position."""
        self._position_states.pop(ticket, None)
    
    def get_symbol_stats(self, symbol: str) -> Dict[str, Any]:
        """
        Get aggregated stats for a symbol.
        
        Returns:
            {
                'position_count': int,
                'total_volume': float,
                'total_pnl': float,
                'long_count': int,
                'short_count': int
            }
        """
        positions = [p for p in self.get_open_positions() if p.symbol == symbol]
        
        return {
            'position_count': len(positions),
            'total_volume': sum(p.volume for p in positions),
            'total_pnl': sum(p.profit for p in positions),
            'long_count': len([p for p in positions if p.type == 0]),
            'short_count': len([p for p in positions if p.type == 1])
        }
