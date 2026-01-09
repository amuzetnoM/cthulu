"""
Exit Strategies Module - Clean Implementation
Handles trailing stops, partial profits, and exit coordination.
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExitSignal:
    """Exit signal with reason and parameters."""
    should_exit: bool
    reason: str
    exit_type: str  # 'full', 'partial'
    exit_portion: float = 1.0  # 1.0 = full, 0.5 = half, etc.


class TrailingStop:
    """
    Trailing Stop Exit Strategy.
    
    Modes:
    - fixed: Trail by fixed points/pips
    - atr: Trail by ATR multiple
    - percentage: Trail by percentage of profit
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize trailing stop.
        
        Config options:
        - mode: 'fixed', 'atr', 'percentage'
        - fixed_points: Points to trail (for fixed mode)
        - atr_multiplier: ATR multiplier (for atr mode)
        - trail_percentage: Percentage to trail (for percentage mode)
        - activation_pips: Pips profit before activation
        """
        self.config = config
        self.mode = config.get('mode', 'atr')
        self.fixed_points = config.get('fixed_points', 50)
        self.atr_multiplier = config.get('atr_multiplier', 1.5)
        self.trail_percentage = config.get('trail_percentage', 0.5)
        self.activation_pips = config.get('activation_pips', 10)
        
        # Track highest profit per position for trailing
        self._high_watermarks: Dict[int, float] = {}
        
        logger.info(f"TrailingStop initialized: mode={self.mode}")
    
    def calculate_trail(
        self,
        ticket: int,
        entry_price: float,
        current_price: float,
        current_sl: float,
        is_buy: bool,
        atr: float = 10.0
    ) -> Dict[str, Any]:
        """
        Calculate trailing stop level.
        
        Args:
            ticket: Position ticket
            entry_price: Entry price
            current_price: Current market price
            current_sl: Current stop loss
            is_buy: True if buy position
            atr: Current ATR value
            
        Returns:
            Dict with 'new_sl' and 'should_update'
        """
        # Calculate current profit in points
        if is_buy:
            profit_points = current_price - entry_price
        else:
            profit_points = entry_price - current_price
        
        # Check if trailing is activated
        if profit_points < self.activation_pips:
            return {'new_sl': current_sl, 'should_update': False, 'reason': 'Not activated'}
        
        # Update high watermark
        current_high = self._high_watermarks.get(ticket, profit_points)
        if profit_points > current_high:
            self._high_watermarks[ticket] = profit_points
            current_high = profit_points
        
        # Calculate trail distance
        if self.mode == 'atr':
            trail_distance = atr * self.atr_multiplier
        elif self.mode == 'percentage':
            trail_distance = current_high * self.trail_percentage
        else:  # fixed
            trail_distance = self.fixed_points
        
        # Calculate new trailing stop
        if is_buy:
            new_sl = current_price - trail_distance
            # Don't move stop backward
            if current_sl and new_sl <= current_sl:
                return {'new_sl': current_sl, 'should_update': False, 'reason': 'No improvement'}
        else:
            new_sl = current_price + trail_distance
            # Don't move stop backward (higher for shorts)
            if current_sl and new_sl >= current_sl:
                return {'new_sl': current_sl, 'should_update': False, 'reason': 'No improvement'}
        
        return {
            'new_sl': new_sl,
            'should_update': True,
            'reason': f'Trail {self.mode}: profit={profit_points:.1f}, trail_dist={trail_distance:.1f}'
        }
    
    def clear_position(self, ticket: int):
        """Clear watermark for closed position."""
        self._high_watermarks.pop(ticket, None)


class PartialProfitExit:
    """
    Partial Profit Exit Strategy.
    
    Takes partial profits at predefined levels.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize partial profit exit.
        
        Config options:
        - levels: List of {profit_pips, exit_portion}
        """
        self.config = config
        self.levels = config.get('levels', [
            {'profit_pips': 20, 'exit_portion': 0.5},  # Take half at 20 pips
            {'profit_pips': 40, 'exit_portion': 0.25}, # Take quarter at 40 pips
        ])
        
        # Track which levels have been hit per position
        self._levels_hit: Dict[int, List[int]] = {}
        
        logger.info(f"PartialProfitExit initialized with {len(self.levels)} levels")
    
    def evaluate(
        self,
        ticket: int,
        entry_price: float,
        current_price: float,
        is_buy: bool
    ) -> Dict[str, Any]:
        """
        Evaluate if partial profit should be taken.
        
        Returns:
            Dict with 'should_exit', 'exit_portion', 'reason'
        """
        # Calculate profit in pips
        if is_buy:
            profit_pips = current_price - entry_price
        else:
            profit_pips = entry_price - current_price
        
        # Get levels hit for this position
        hit_levels = self._levels_hit.get(ticket, [])
        
        for i, level in enumerate(self.levels):
            if i in hit_levels:
                continue
            
            if profit_pips >= level['profit_pips']:
                # Mark level as hit
                if ticket not in self._levels_hit:
                    self._levels_hit[ticket] = []
                self._levels_hit[ticket].append(i)
                
                return {
                    'should_exit': True,
                    'exit_portion': level['exit_portion'],
                    'reason': f"Partial profit at {level['profit_pips']} pips"
                }
        
        return {'should_exit': False, 'exit_portion': 0, 'reason': 'No level hit'}
    
    def clear_position(self, ticket: int):
        """Clear tracking for closed position."""
        self._levels_hit.pop(ticket, None)


class TimeBasedExit:
    """
    Time-based Exit Strategy.
    
    Exits positions based on time criteria.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize time-based exit.
        
        Config options:
        - max_hold_hours: Maximum hold time before forced exit
        - close_before_weekend: Close positions before weekend
        - close_before_news: Close before high-impact news
        """
        self.config = config
        self.max_hold_hours = config.get('max_hold_hours', 24)
        self.close_before_weekend = config.get('close_before_weekend', True)
        
        logger.info(f"TimeBasedExit initialized: max_hold={self.max_hold_hours}h")
    
    def evaluate(self, open_time: float, current_time: float) -> Dict[str, Any]:
        """
        Evaluate if position should be exited based on time.
        
        Args:
            open_time: Position open timestamp
            current_time: Current timestamp
            
        Returns:
            Dict with 'should_exit', 'reason'
        """
        import datetime
        
        # Check max hold time
        hold_hours = (current_time - open_time) / 3600
        if hold_hours >= self.max_hold_hours:
            return {
                'should_exit': True,
                'reason': f'Max hold time reached ({hold_hours:.1f}h)'
            }
        
        # Check weekend - DISABLED for testing
        # if self.close_before_weekend:
        #     dt = datetime.datetime.fromtimestamp(current_time)
        #     # Friday after 20:00 UTC
        #     if dt.weekday() == 4 and dt.hour >= 20:
        #         return {
        #             'should_exit': True,
        #             'reason': 'Weekend approaching'
        #         }
        
        return {'should_exit': False, 'reason': ''}


class ExitCoordinator:
    """
    Coordinates all exit strategies.
    
    Evaluates all exit conditions and returns combined signal.
    """
    
    def __init__(self, config: Dict[str, Any], connector):
        """
        Initialize exit coordinator.
        
        Args:
            config: Exit strategies configuration
            connector: MT5 connector
        """
        self.config = config
        self.connector = connector
        
        # Initialize strategies
        self.trailing_stop = TrailingStop(config.get('trailing_stop', {}))
        self.partial_profit = PartialProfitExit(config.get('partial_profit', {}))
        self.time_based = TimeBasedExit(config.get('time_based', {}))
        
        logger.info("ExitCoordinator initialized")
    
    def evaluate(
        self,
        position,  # TrackedPosition
        current_price: float,
        indicators: Dict[str, Any]
    ) -> ExitSignal:
        """
        Evaluate all exit conditions for a position.
        
        Args:
            position: Position to evaluate
            current_price: Current market price
            indicators: Current indicators
            
        Returns:
            ExitSignal with decision
        """
        import time
        
        atr = indicators.get('ATR', 10.0)
        is_buy = position.type == 0
        
        # Check trailing stop
        trail_result = self.trailing_stop.calculate_trail(
            ticket=position.ticket,
            entry_price=position.price_open,
            current_price=current_price,
            current_sl=position.sl,
            is_buy=is_buy,
            atr=atr
        )
        
        # Note: Trailing stop doesn't exit, it just adjusts SL
        # The actual exit happens when SL is hit by MT5
        
        # Check partial profit
        partial_result = self.partial_profit.evaluate(
            ticket=position.ticket,
            entry_price=position.price_open,
            current_price=current_price,
            is_buy=is_buy
        )
        
        if partial_result['should_exit']:
            return ExitSignal(
                should_exit=True,
                reason=partial_result['reason'],
                exit_type='partial',
                exit_portion=partial_result['exit_portion']
            )
        
        # Check time-based
        open_time = position.adoption_time if position.adoption_time else time.time()
        time_result = self.time_based.evaluate(
            open_time=open_time,
            current_time=time.time()
        )
        
        if time_result['should_exit']:
            return ExitSignal(
                should_exit=True,
                reason=time_result['reason'],
                exit_type='full',
                exit_portion=1.0
            )
        
        return ExitSignal(
            should_exit=False,
            reason='No exit condition met',
            exit_type='none',
            exit_portion=0.0
        )
    
    def get_trailing_update(
        self,
        position,
        current_price: float,
        atr: float
    ) -> Dict[str, Any]:
        """
        Get trailing stop update for position.
        
        Returns:
            Dict with 'new_sl', 'should_update'
        """
        return self.trailing_stop.calculate_trail(
            ticket=position.ticket,
            entry_price=position.price_open,
            current_price=current_price,
            current_sl=position.sl,
            is_buy=position.type == 0,
            atr=atr
        )
    
    def clear_position(self, ticket: int):
        """Clear tracking data for closed position."""
        self.trailing_stop.clear_position(ticket)
        self.partial_profit.clear_position(ticket)
