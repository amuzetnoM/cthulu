"""
Trailing Stop Exit Strategy - Standalone Module
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TrailingStop:
    """
    Trailing Stop Manager - ensures profits are protected.
    
    Modes:
    - aggressive: Tight trail, locks in more profit but may get stopped out
    - protective: Moderate trail, balance between protection and room to breathe  
    - conservative: Loose trail, gives trade room but protects less
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize trailing stop.
        
        Config:
        - mode: 'aggressive', 'protective', 'conservative'
        - atr_multiplier: Base ATR multiplier for trail distance
        - activation_profit_pips: Profit (in pips) before trailing activates
        - min_trail_distance: Minimum trail distance in points
        """
        config = config or {}
        
        self.mode = config.get('mode', 'protective')
        self.base_atr_mult = config.get('atr_multiplier', 1.5)
        self.activation_profit = config.get('activation_profit_pips', 10)
        self.min_trail_distance = config.get('min_trail_distance', 5)
        
        # Mode multipliers
        self.mode_multipliers = {
            'aggressive': 0.75,    # Tighter trail
            'protective': 1.0,     # Normal
            'conservative': 1.5    # Looser trail
        }
        
        # High watermarks for each position
        self._watermarks: Dict[int, float] = {}
        
        logger.info(f"TrailingStop initialized: mode={self.mode}, atr_mult={self.base_atr_mult}")
    
    def calculate_trailing_stop(
        self,
        ticket: int,
        entry_price: float,
        current_price: float,
        current_sl: float,
        is_buy: bool,
        atr: float
    ) -> Dict[str, Any]:
        """
        Calculate new trailing stop level.
        
        Args:
            ticket: Position ticket
            entry_price: Entry price
            current_price: Current market price
            current_sl: Current SL
            is_buy: True if long position
            atr: Current ATR value
            
        Returns:
            {
                'new_sl': float,
                'should_update': bool,
                'activated': bool,
                'reason': str
            }
        """
        # Calculate profit in price units
        if is_buy:
            profit = current_price - entry_price
        else:
            profit = entry_price - current_price
        
        result = {
            'new_sl': current_sl,
            'should_update': False,
            'activated': False,
            'reason': ''
        }
        
        # Check if trailing is activated
        if profit < self.activation_profit:
            result['reason'] = f'Profit {profit:.2f} < activation {self.activation_profit}'
            return result
        
        result['activated'] = True
        
        # Update watermark
        prev_watermark = self._watermarks.get(ticket, profit)
        if profit > prev_watermark:
            self._watermarks[ticket] = profit
            prev_watermark = profit
        
        # Calculate trail distance
        mode_mult = self.mode_multipliers.get(self.mode, 1.0)
        trail_distance = max(atr * self.base_atr_mult * mode_mult, self.min_trail_distance)
        
        # Calculate new SL
        if is_buy:
            new_sl = current_price - trail_distance
            # Only move SL up, never down
            if current_sl and new_sl <= current_sl:
                result['reason'] = f'New SL {new_sl:.2f} not better than current {current_sl:.2f}'
                return result
            # Must be above entry for trailing
            if new_sl < entry_price:
                result['reason'] = f'New SL {new_sl:.2f} below entry {entry_price:.2f}'
                return result
        else:
            new_sl = current_price + trail_distance
            # Only move SL down, never up
            if current_sl and new_sl >= current_sl:
                result['reason'] = f'New SL {new_sl:.2f} not better than current {current_sl:.2f}'
                return result
            # Must be below entry for trailing
            if new_sl > entry_price:
                result['reason'] = f'New SL {new_sl:.2f} above entry {entry_price:.2f}'
                return result
        
        result['new_sl'] = new_sl
        result['should_update'] = True
        result['reason'] = f'Trail: profit={profit:.2f}, trail_dist={trail_distance:.2f}'
        
        logger.info(f"Trailing {ticket}: {result['reason']}")
        
        return result
    
    def clear_position(self, ticket: int):
        """Remove tracking data for closed position."""
        self._watermarks.pop(ticket, None)
    
    def get_watermark(self, ticket: int) -> float:
        """Get current watermark for position."""
        return self._watermarks.get(ticket, 0.0)
