"""
Dynamic SL/TP Manager - Clean Implementation
Handles ATR-based SL/TP calculation, breakeven, and trailing stops.

Modes:
- NORMAL: Initial SL/TP based on ATR
- BREAKEVEN: Move SL to entry when in profit
- TRAILING: Lock profits by trailing SL
"""
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SLTPMode(Enum):
    """Position management mode."""
    NORMAL = "normal"
    BREAKEVEN = "breakeven"
    TRAILING = "trailing"


@dataclass
class SLTPResult:
    """Result of SL/TP calculation."""
    update_sl: bool = False
    update_tp: bool = False
    new_sl: float = 0.0
    new_tp: float = 0.0
    action: str = "none"
    reasoning: str = ""
    mode: SLTPMode = SLTPMode.NORMAL


class DynamicSLTPManager:
    """
    Dynamic Stop Loss / Take Profit Manager.
    
    Flow:
    1. Calculate initial SL/TP based on ATR
    2. Monitor position profit
    3. When profit > breakeven_threshold: move SL to breakeven
    4. When profit > trailing_trigger: start trailing SL
    5. Trailing SL locks a percentage of profit
    """
    
    def __init__(self, config: Dict[str, Any], connector=None):
        """
        Initialize Dynamic SLTP Manager.
        
        Config options:
        - base_sl_atr: ATR multiplier for SL (default: 2.0)
        - base_tp_atr: ATR multiplier for TP (default: 4.0)
        - breakeven_pips: Profit pips to trigger breakeven (default: 10)
        - trailing_trigger_pips: Profit pips to start trailing (default: 20)
        - trailing_lock_pct: Percentage of profit to lock (default: 0.5)
        """
        self.config = config
        self.connector = connector
        
        # Configuration
        self.base_sl_atr = config.get('base_sl_atr', 2.0)
        self.base_tp_atr = config.get('base_tp_atr', 4.0)
        self.breakeven_pips = config.get('breakeven_pips', 10)
        self.trailing_trigger_pips = config.get('trailing_trigger_pips', 20)
        self.trailing_lock_pct = config.get('trailing_lock_pct', 0.5)
        
        # Position tracking
        self._position_modes: Dict[int, SLTPMode] = {}
        self._trailing_highs: Dict[int, float] = {}  # Highest profit reached
        
        logger.info(f"DynamicSLTPManager initialized: base_sl_atr={self.base_sl_atr}, "
                   f"base_tp_atr={self.base_tp_atr}")
    
    def set_trade_manager(self, trade_manager):
        """Set trade manager reference for position tracking."""
        self.trade_manager = trade_manager
    
    def calculate_initial_sltp(
        self,
        ticket: int,
        direction: str,
        entry_price: float,
        atr: float
    ) -> Dict[str, float]:
        """
        Calculate initial SL and TP based on ATR.
        
        Args:
            ticket: Position ticket
            direction: 'buy' or 'sell'
            entry_price: Trade entry price
            atr: Current ATR value
            
        Returns:
            Dict with 'sl' and 'tp' prices
        """
        sl_distance = atr * self.base_sl_atr
        tp_distance = atr * self.base_tp_atr
        
        if direction == 'buy':
            sl = entry_price - sl_distance
            tp = entry_price + tp_distance
        else:  # sell
            sl = entry_price + sl_distance
            tp = entry_price - tp_distance
        
        # Initialize position mode
        self._position_modes[ticket] = SLTPMode.NORMAL
        self._trailing_highs[ticket] = 0.0
        
        logger.info(f"Initial SLTP for {ticket}: SL={sl:.2f}, TP={tp:.2f} (ATR={atr:.2f})")
        
        return {'sl': sl, 'tp': tp}
    
    def update_position_sltp(
        self,
        position: Any,
        current_price: float,
        atr: float
    ) -> Dict[str, Any]:
        """
        Update SL/TP for an existing position.
        
        Logic:
        1. Calculate profit in pips
        2. Determine mode: NORMAL -> BREAKEVEN -> TRAILING
        3. Calculate new SL/TP if mode requires update
        4. Return update instructions
        
        Args:
            position: Position object with ticket, type, price_open, sl, tp, profit
            current_price: Current market price
            atr: Current ATR value
            
        Returns:
            SLTPResult dict with update instructions
        """
        ticket = position.ticket
        is_buy = position.type == 0
        entry_price = position.price_open
        current_sl = position.sl or 0
        current_tp = position.tp or 0
        profit = position.profit
        
        # Get pip value (simplified)
        pip_value = self._get_pip_value(position.symbol)
        
        # Calculate profit in pips
        if is_buy:
            profit_pips = (current_price - entry_price) / pip_value
        else:
            profit_pips = (entry_price - current_price) / pip_value
        
        # Update trailing high
        if ticket not in self._trailing_highs:
            self._trailing_highs[ticket] = profit_pips
        else:
            self._trailing_highs[ticket] = max(self._trailing_highs[ticket], profit_pips)
        
        # Determine mode
        current_mode = self._position_modes.get(ticket, SLTPMode.NORMAL)
        new_mode = self._determine_mode(profit_pips, current_mode)
        self._position_modes[ticket] = new_mode
        
        # Calculate new SL/TP based on mode
        result = self._calculate_updates(
            position=position,
            current_price=current_price,
            entry_price=entry_price,
            current_sl=current_sl,
            current_tp=current_tp,
            profit_pips=profit_pips,
            mode=new_mode,
            atr=atr,
            pip_value=pip_value,
            is_buy=is_buy
        )
        
        return result
    
    def _determine_mode(self, profit_pips: float, current_mode: SLTPMode) -> SLTPMode:
        """Determine the current management mode based on profit."""
        # Mode can only advance, never go back
        if current_mode == SLTPMode.TRAILING:
            return SLTPMode.TRAILING
        
        if profit_pips >= self.trailing_trigger_pips:
            return SLTPMode.TRAILING
        
        if current_mode == SLTPMode.BREAKEVEN:
            return SLTPMode.BREAKEVEN
        
        if profit_pips >= self.breakeven_pips:
            return SLTPMode.BREAKEVEN
        
        return SLTPMode.NORMAL
    
    def _calculate_updates(
        self,
        position: Any,
        current_price: float,
        entry_price: float,
        current_sl: float,
        current_tp: float,
        profit_pips: float,
        mode: SLTPMode,
        atr: float,
        pip_value: float,
        is_buy: bool
    ) -> Dict[str, Any]:
        """Calculate SL/TP updates based on mode."""
        
        result = {
            'update_sl': False,
            'update_tp': False,
            'new_sl': current_sl,
            'new_tp': current_tp,
            'action': 'none',
            'reasoning': f'No adjustment needed - Mode: {mode.value}',
            'mode': mode
        }
        
        # Handle no initial SL/TP
        if current_sl == 0 or current_tp == 0:
            initial = self.calculate_initial_sltp(
                ticket=position.ticket,
                direction='buy' if is_buy else 'sell',
                entry_price=entry_price,
                atr=atr
            )
            result['update_sl'] = current_sl == 0
            result['update_tp'] = current_tp == 0
            result['new_sl'] = initial['sl'] if current_sl == 0 else current_sl
            result['new_tp'] = initial['tp'] if current_tp == 0 else current_tp
            result['action'] = 'initial_sltp'
            result['reasoning'] = 'Applied initial SL/TP'
            return result
        
        if mode == SLTPMode.NORMAL:
            # In normal mode, keep existing SL/TP
            return result
        
        elif mode == SLTPMode.BREAKEVEN:
            # Move SL to breakeven (entry price + small buffer)
            buffer = pip_value * 2  # 2 pip buffer
            
            if is_buy:
                breakeven_sl = entry_price + buffer
                if current_sl < breakeven_sl:
                    result['update_sl'] = True
                    result['new_sl'] = breakeven_sl
                    result['action'] = 'breakeven'
                    result['reasoning'] = f'Moved SL to breakeven at {breakeven_sl:.2f}'
            else:
                breakeven_sl = entry_price - buffer
                if current_sl > breakeven_sl or current_sl == 0:
                    result['update_sl'] = True
                    result['new_sl'] = breakeven_sl
                    result['action'] = 'breakeven'
                    result['reasoning'] = f'Moved SL to breakeven at {breakeven_sl:.2f}'
        
        elif mode == SLTPMode.TRAILING:
            # Trail SL to lock profits
            locked_profit_pips = self._trailing_highs.get(position.ticket, profit_pips) * self.trailing_lock_pct
            trail_distance = locked_profit_pips * pip_value
            
            if is_buy:
                trailing_sl = current_price - trail_distance
                # Only move SL up, never down
                if trailing_sl > current_sl:
                    result['update_sl'] = True
                    result['new_sl'] = trailing_sl
                    result['action'] = 'trailing'
                    result['reasoning'] = f'Trailing SL to {trailing_sl:.2f} (locking {self.trailing_lock_pct*100:.0f}% of profit)'
            else:
                trailing_sl = current_price + trail_distance
                # Only move SL down, never up
                if trailing_sl < current_sl or current_sl == 0:
                    result['update_sl'] = True
                    result['new_sl'] = trailing_sl
                    result['action'] = 'trailing'
                    result['reasoning'] = f'Trailing SL to {trailing_sl:.2f} (locking {self.trailing_lock_pct*100:.0f}% of profit)'
        
        return result
    
    def _get_pip_value(self, symbol: str) -> float:
        """Get pip value for a symbol."""
        symbol_upper = symbol.upper()
        
        # Gold/XAU
        if 'GOLD' in symbol_upper or 'XAU' in symbol_upper:
            return 0.1  # 0.1 for gold
        
        # Bitcoin
        if 'BTC' in symbol_upper:
            return 1.0  # 1 dollar for BTC
        
        # Forex majors
        if 'JPY' in symbol_upper:
            return 0.01  # 0.01 for JPY pairs
        
        return 0.0001  # Default for forex
    
    def cleanup_position(self, ticket: int):
        """Clean up tracking data for a closed position."""
        self._position_modes.pop(ticket, None)
        self._trailing_highs.pop(ticket, None)
