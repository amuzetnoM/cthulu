"""
Position Lifecycle Module

Handles all position operations including opening, closing, modification,
and exit strategy application. This module contains execution logic that
changes position state.

Responsibilities:
- Open positions via ExecutionEngine
- Close positions (market, limit orders)
- Modify stop-loss and take-profit
- Apply exit strategies (trailing, time-based, profit-target, drawdown)
- Refresh position data from MT5
- Persist position data to database

Does NOT:
- Track position state (see tracker.py)
- Make risk decisions (see risk/evaluator.py)
- Handle external trade adoption (see adoption.py)
"""

from typing import Optional, List, Dict, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PositionLifecycle:
    """
    Manages the complete lifecycle of trading positions.
    
    This class handles all operations that change position state,
    from opening to closing, including modifications and exit strategy application.
    """
    
    def __init__(self, connector, execution_engine, position_tracker, db_handler):
        """
        Initialize the position lifecycle manager.
        
        Args:
            connector: MT5 connector for market operations
            execution_engine: ExecutionEngine for order placement
            position_tracker: PositionTracker for state management
            db_handler: Database handler for persistence
        """
        self.connector = connector
        self.execution_engine = execution_engine
        self.tracker = position_tracker
        self.db = db_handler
        logger.info("PositionLifecycle initialized")
    
    def open_position(self, symbol: str, order_type: str, volume: float,
                     sl: Optional[float] = None, tp: Optional[float] = None,
                     comment: str = "", magic_number: int = 0,
                     strategy_name: Optional[str] = None) -> Optional[int]:
        """
        Open a new position via ExecutionEngine.
        
        Args:
            symbol: Trading symbol
            order_type: "buy" or "sell"
            volume: Position size
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
            magic_number: Magic number for identification
            strategy_name: Name of strategy placing order
            
        Returns:
            Position ticket number if successful, None otherwise
        """
        try:
            # Use execution engine to place order
            ticket = self.execution_engine.execute_order(
                symbol=symbol,
                order_type=order_type,
                volume=volume,
                sl=sl,
                tp=tp,
                comment=comment,
                magic_number=magic_number
            )
            
            if ticket:
                # Get position info from MT5
                position_info = self.connector.get_position_by_ticket(ticket)
                if position_info:
                    # Import PositionInfo here to avoid circular import
                    from position.tracker import PositionInfo
                    
                    # Create tracked position
                    tracked_pos = PositionInfo(
                        ticket=ticket,
                        symbol=symbol,
                        type=order_type,
                        volume=volume,
                        open_price=position_info.get('price_open', 0.0),
                        current_price=position_info.get('price_current', 0.0),
                        sl=sl,
                        tp=tp,
                        profit=position_info.get('profit', 0.0),
                        open_time=datetime.now(),
                        magic_number=magic_number,
                        comment=comment,
                        strategy_name=strategy_name
                    )
                    
                    # Add to tracker
                    self.tracker.track_position(tracked_pos)
                    
                    # Persist to database
                    self.persist_position(tracked_pos)
                    
                    logger.info(f"Opened position {ticket}: {symbol} {order_type} {volume}")
                    return ticket
            
            logger.error(f"Failed to open position: {symbol} {order_type}")
            return None
            
        except Exception as e:
            logger.error(f"Error opening position: {e}", exc_info=True)
            return None
    
    def close_position(self, ticket: int, reason: str = "") -> bool:
        """
        Close a position by ticket number.
        
        Args:
            ticket: Position ticket to close
            reason: Reason for closure (for logging)
            
        Returns:
            True if closed successfully, False otherwise
        """
        try:
            # Get position from tracker
            position = self.tracker.get_position(ticket)
            if not position:
                logger.warning(f"Position {ticket} not found in tracker")
                return False
            
            # Close via execution engine
            result = self.execution_engine.close_position(ticket)

            # Support both legacy boolean return values and ExecutionResult objects
            success = False
            try:
                # If engine returned an ExecutionResult-like object, inspect status
                if hasattr(result, 'status'):
                    from herald.execution.engine import OrderStatus
                    success = (getattr(result, 'status', None) == OrderStatus.FILLED)
                else:
                    # Fallback: truthiness for legacy boolean API
                    success = bool(result)
            except Exception:
                success = False
            if success:
                # Remove from tracker
                self.tracker.remove_position(ticket)
                
                # Update database
                self.db.update_position_status(ticket, 'closed', reason)
                
                logger.info(f"Closed position {ticket}: {reason}")
                return True
            else:
                logger.error(f"Failed to close position {ticket}")
                return False
                
        except Exception as e:
            logger.error(f"Error closing position {ticket}: {e}", exc_info=True)
            return False
    
    def close_all_positions(self, symbol: Optional[str] = None) -> int:
        """
        Close all open positions, optionally filtered by symbol.
        
        Args:
            symbol: If provided, only close positions for this symbol
            
        Returns:
            Number of positions closed
        """
        try:
            positions = self.tracker.get_all_positions()
            if symbol:
                positions = [p for p in positions if p.symbol == symbol]
            
            closed_count = 0
            for position in positions:
                if self.close_position(position.ticket, "Close all"):
                    closed_count += 1
            
            logger.info(f"Closed {closed_count} positions")
            return closed_count
            
        except Exception as e:
            logger.error(f"Error closing all positions: {e}", exc_info=True)
            return 0
    
    def close_positions_by_symbol(self, symbol: str) -> int:
        """Close all positions for a specific symbol."""
        return self.close_all_positions(symbol=symbol)
    
    def modify_position(self, ticket: int, sl: Optional[float] = None,
                       tp: Optional[float] = None) -> bool:
        """
        Modify stop-loss and/or take-profit for a position.
        
        Args:
            ticket: Position ticket to modify
            sl: New stop loss (None to keep current)
            tp: New take profit (None to keep current)
            
        Returns:
            True if modified successfully, False otherwise
        """
        try:
            position = self.tracker.get_position(ticket)
            if not position:
                logger.warning(f"Position {ticket} not found")
                return False
            
            # Use execution engine to modify
            success = self.execution_engine.modify_position(ticket, sl, tp)
            
            if success:
                # Update tracker
                if sl is not None:
                    position.sl = sl
                if tp is not None:
                    position.tp = tp
                
                logger.info(f"Modified position {ticket}: SL={sl}, TP={tp}")
                return True
            else:
                logger.error(f"Failed to modify position {ticket}")
                return False
                
        except Exception as e:
            logger.error(f"Error modifying position {ticket}: {e}", exc_info=True)
            return False
    
    def apply_trailing_stop(self, ticket: int, trail_points: float) -> bool:
        """
        Apply trailing stop logic to a position.
        
        Args:
            ticket: Position ticket
            trail_points: Number of points to trail by
            
        Returns:
            True if trailing stop applied successfully
        """
        try:
            position = self.tracker.get_position(ticket)
            if not position:
                return False
            
            # Calculate new SL based on current price and trail points
            if position.type == "buy":
                new_sl = position.current_price - trail_points
                if position.sl is None or new_sl > position.sl:
                    return self.modify_position(ticket, sl=new_sl)
            else:  # sell
                new_sl = position.current_price + trail_points
                if position.sl is None or new_sl < position.sl:
                    return self.modify_position(ticket, sl=new_sl)
            
            return False
            
        except Exception as e:
            logger.error(f"Error applying trailing stop to {ticket}: {e}", exc_info=True)
            return False
    
    def apply_time_based_exit(self, ticket: int, max_age_hours: float) -> bool:
        """
        Close position if it exceeds maximum age.
        
        Args:
            ticket: Position ticket
            max_age_hours: Maximum age in hours
            
        Returns:
            True if position was closed, False otherwise
        """
        try:
            position = self.tracker.get_position(ticket)
            if not position:
                return False
            
            age = datetime.now() - position.open_time
            if age > timedelta(hours=max_age_hours):
                return self.close_position(ticket, f"Time-based exit ({max_age_hours}h)")
            
            return False
            
        except Exception as e:
            logger.error(f"Error applying time-based exit to {ticket}: {e}", exc_info=True)
            return False
    
    def apply_profit_target(self, ticket: int, target_profit: float) -> bool:
        """
        Close position if profit target is reached.
        
        Args:
            ticket: Position ticket
            target_profit: Profit target in account currency
            
        Returns:
            True if position was closed, False otherwise
        """
        try:
            position = self.tracker.get_position(ticket)
            if not position and position.profit >= target_profit:
                return self.close_position(ticket, f"Profit target ({target_profit})")
            
            return False
            
        except Exception as e:
            logger.error(f"Error applying profit target to {ticket}: {e}", exc_info=True)
            return False
    
    def apply_drawdown_protection(self, ticket: int, max_drawdown: float) -> bool:
        """
        Close position if drawdown exceeds limit.
        
        Args:
            ticket: Position ticket
            max_drawdown: Maximum allowed drawdown (negative value)
            
        Returns:
            True if position was closed, False otherwise
        """
        try:
            position = self.tracker.get_position(ticket)
            if not position:
                return False
            
            if position.profit <= max_drawdown:
                return self.close_position(ticket, f"Drawdown protection ({max_drawdown})")
            
            return False
            
        except Exception as e:
            logger.error(f"Error applying drawdown protection to {ticket}: {e}", exc_info=True)
            return False
    
    def refresh_positions(self) -> None:
        """
        Refresh all tracked positions with latest data from MT5.
        """
        try:
            for position in self.tracker.get_all_positions():
                mt5_position = self.connector.get_position_by_ticket(position.ticket)
                if mt5_position:
                    # Update tracker with fresh data
                    self.tracker.update_position(
                        position.ticket,
                        mt5_position.get('price_current', position.current_price),
                        mt5_position.get('profit', position.profit)
                    )
                else:
                    # Position no longer exists in MT5 - remove from tracker
                    logger.warning(f"Position {position.ticket} not found in MT5, removing from tracker")
                    self.tracker.remove_position(position.ticket)
                    
        except Exception as e:
            logger.error(f"Error refreshing positions: {e}", exc_info=True)
    
    def persist_position(self, position) -> None:
        """
        Save position to database.
        
        Args:
            position: PositionInfo object to persist
        """
        try:
            self.db.save_position(
                ticket=position.ticket,
                symbol=position.symbol,
                type=position.type,
                volume=position.volume,
                open_price=position.open_price,
                sl=position.sl,
                tp=position.tp,
                open_time=position.open_time,
                magic_number=position.magic_number,
                comment=position.comment,
                strategy_name=position.strategy_name
            )
        except Exception as e:
            logger.error(f"Error persisting position {position.ticket}: {e}", exc_info=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get position statistics.
        
        Returns:
            Dict with position metrics
        """
        positions = self.tracker.get_all_positions()
        
        return {
            'total_positions': len(positions),
            'total_profit': sum(p.profit for p in positions),
            'total_exposure': sum(abs(p.volume) for p in positions),
            'long_positions': len([p for p in positions if p.type == "buy"]),
            'short_positions': len([p for p in positions if p.type == "sell"]),
            'external_positions': len([p for p in positions if p.is_external]),
            'symbols': list(set(p.symbol for p in positions))
        }
    
    def is_healthy(self) -> bool:
        """
        Check if position lifecycle is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Check connector
            if not self.connector.is_connected():
                logger.error("MT5 connector not connected")
                return False
            
            # Check execution engine
            if not hasattr(self.execution_engine, 'execute_order'):
                logger.error("Execution engine missing execute_order method")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking position lifecycle health: {e}", exc_info=True)
            return False
