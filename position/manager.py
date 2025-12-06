"""
Position Manager Module

Real-time position tracking, monitoring, and lifecycle management per build_plan.md Phase 2.
Integrates with ExecutionEngine for position data and RiskManager for exposure limits.
"""

import MetaTrader5 as mt5
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from execution.engine import ExecutionResult, ExecutionEngine, OrderType, OrderStatus, OrderRequest
from strategy.base import SignalType


@dataclass
class PositionInfo:
    """
    Position tracking structure per build_plan.md specifications.
    
    Attributes:
        ticket: MT5 position ticket
        symbol: Trading symbol
        side: BUY or SELL
        volume: Position size in lots
        open_price: Entry price
        open_time: Position open time
        stop_loss: Stop loss price
        take_profit: Take profit price
        current_price: Current market price
        unrealized_pnl: Current unrealized profit/loss
        realized_pnl: Realized profit/loss (after close)
        commission: Trading commission
        swap: Swap/rollover charges
        magic_number: Bot identifier
        comment: Position comment
        metadata: Additional position data
    """
    ticket: int
    symbol: str
    side: str
    volume: float
    open_price: float
    open_time: datetime
    stop_loss: float
    take_profit: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    magic_number: int = 0
    comment: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_age_seconds(self) -> float:
        """Get position age in seconds."""
        return (datetime.now() - self.open_time).total_seconds()
        
    def get_age_hours(self) -> float:
        """Get position age in hours."""
        return self.get_age_seconds() / 3600.0
        
    def get_pnl_pips(self, pip_value: float) -> float:
        """
        Calculate P&L in pips.
        
        Args:
            pip_value: Value of one pip for the symbol
            
        Returns:
            P&L in pips
        """
        if self.side == "BUY":
            price_diff = self.current_price - self.open_price
        else:  # SELL
            price_diff = self.open_price - self.current_price
            
        return price_diff / pip_value if pip_value > 0 else 0.0


class PositionManager:
    """
    Real-time position tracking and monitoring engine.
    
    Responsibilities per build_plan.md:
    - Maintain real-time position registry synced with MT5
    - Calculate unrealized P&L continuously
    - Detect position modifications (SL/TP changes)
    - Track position age and exposure time
    - Integrate with RiskManager for exposure limits
    - Reconcile with MT5 positions on reconnect
    """
    
    def __init__(self, connector, execution_engine: ExecutionEngine):
        """
        Initialize position manager.
        
        Args:
            connector: MT5Connector instance
            execution_engine: ExecutionEngine instance
        """
        self.connector = connector
        self.execution_engine = execution_engine
        self.logger = logging.getLogger("herald.position")
        
        # Position registry
        self._positions: Dict[int, PositionInfo] = {}
        
        # Statistics
        self._total_positions_opened = 0
        self._total_positions_closed = 0
        
    def track_position(self, execution_result: ExecutionResult, signal_metadata: Dict[str, Any] = None) -> Optional[PositionInfo]:
        """
        Add new position to tracking registry.
        
        Args:
            execution_result: Execution result from order placement
            signal_metadata: Optional metadata from originating signal
            
        Returns:
            PositionInfo object or None if tracking failed
        """
        if execution_result.status != OrderStatus.FILLED:
            self.logger.warning(f"Cannot track unfilled order: {execution_result.status}")
            return None
            
        if execution_result.order_id is None:
            self.logger.error("Cannot track position without order ID")
            return None
            
        try:
            # Get position details from MT5
            position = mt5.positions_get(ticket=execution_result.order_id)
            
            if position is None or len(position) == 0:
                self.logger.error(f"Position not found in MT5: ticket #{execution_result.order_id}")
                return None
                
            pos = position[0]
            
            # Create PositionInfo
            position_info = PositionInfo(
                ticket=pos.ticket,
                symbol=pos.symbol,
                side="BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                volume=pos.volume,
                open_price=pos.price_open,
                open_time=datetime.fromtimestamp(pos.time),
                stop_loss=pos.sl if pos.sl > 0 else 0.0,
                take_profit=pos.tp if pos.tp > 0 else 0.0,
                current_price=pos.price_current,
                unrealized_pnl=pos.profit,
                commission=pos.commission if hasattr(pos, 'commission') else 0.0,
                swap=pos.swap if hasattr(pos, 'swap') else 0.0,
                magic_number=pos.magic,
                comment=pos.comment if hasattr(pos, 'comment') else "",
                metadata=signal_metadata or {}
            )
            
            # Add to registry
            self._positions[position_info.ticket] = position_info
            self._total_positions_opened += 1
            
            self.logger.info(
                f"Position tracked: #{position_info.ticket} | "
                f"{position_info.symbol} {position_info.side} {position_info.volume:.2f} @ {position_info.open_price:.5f}"
            )
            
            return position_info
            
        except Exception as e:
            self.logger.error(f"Failed to track position: {e}", exc_info=True)
            return None
            
    def monitor_positions(self) -> List[PositionInfo]:
        """
        Update all tracked positions with current prices and P&L.
        
        Returns:
            List of updated PositionInfo objects
        """
        if not self.connector.is_connected():
            self.logger.warning("Cannot monitor positions: not connected to MT5")
            return list(self._positions.values())
            
        try:
            # Get all MT5 positions for this bot
            mt5_positions = mt5.positions_get()
            
            if mt5_positions is None:
                mt5_positions = []
                
            # Update existing positions
            mt5_tickets = {pos.ticket for pos in mt5_positions}
            
            for ticket in list(self._positions.keys()):
                if ticket in mt5_tickets:
                    # Position still open - update it
                    mt5_pos = next(p for p in mt5_positions if p.ticket == ticket)
                    
                    position_info = self._positions[ticket]
                    position_info.current_price = mt5_pos.price_current
                    position_info.unrealized_pnl = mt5_pos.profit
                    position_info.swap = mt5_pos.swap if hasattr(mt5_pos, 'swap') else 0.0
                    position_info.stop_loss = mt5_pos.sl if mt5_pos.sl > 0 else 0.0
                    position_info.take_profit = mt5_pos.tp if mt5_pos.tp > 0 else 0.0
                    
                else:
                    # Position closed externally - remove from tracking
                    self.logger.info(f"Position #{ticket} closed externally")
                    del self._positions[ticket]
                    self._total_positions_closed += 1
                    
            return list(self._positions.values())
            
        except Exception as e:
            self.logger.error(f"Failed to monitor positions: {e}", exc_info=True)
            return list(self._positions.values())
            
    def get_position(self, ticket: int) -> Optional[PositionInfo]:
        """
        Get specific position by ticket.
        
        Args:
            ticket: Position ticket number
            
        Returns:
            PositionInfo or None if not found
        """
        return self._positions.get(ticket)
        
    def get_positions(self, symbol: Optional[str] = None) -> List[PositionInfo]:
        """
        Get all tracked positions, optionally filtered by symbol.
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of PositionInfo objects
        """
        if symbol:
            return [p for p in self._positions.values() if p.symbol == symbol]
        return list(self._positions.values())
        
    def close_position(
        self,
        ticket: int,
        reason: str,
        partial_volume: Optional[float] = None
    ) -> Optional[ExecutionResult]:
        """
        Close position (full or partial).
        
        Args:
            ticket: Position ticket to close
            reason: Reason for closing
            partial_volume: Optional volume for partial close
            
        Returns:
            ExecutionResult or None if failed
        """
        position_info = self._positions.get(ticket)
        if not position_info:
            self.logger.error(f"Cannot close position #{ticket}: not tracked")
            return None
            
        try:
            # Get current price
            if position_info.side == "BUY":
                close_price = mt5.symbol_info_tick(position_info.symbol).bid
                order_type = mt5.ORDER_TYPE_SELL
            else:
                close_price = mt5.symbol_info_tick(position_info.symbol).ask
                order_type = mt5.ORDER_TYPE_BUY
                
            # Determine volume
            close_volume = partial_volume if partial_volume else position_info.volume
            
            # Create close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position_info.symbol,
                "volume": close_volume,
                "type": order_type,
                "position": ticket,
                "price": close_price,
                "deviation": 10,
                "magic": self.execution_engine.magic_number,
                "comment": f"Close: {reason}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            # Send close order
            result = mt5.order_send(request)
            
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                error = mt5.last_error() if result is None else f"{result.retcode}: {result.comment}"
                self.logger.error(f"Failed to close position #{ticket}: {error}")
                return ExecutionResult(
                    order_id=None,
                    status=OrderStatus.REJECTED,
                    executed_price=None,
                    executed_volume=None,
                    timestamp=datetime.now(),
                    error=str(error)
                )
                
            # Calculate realized P&L
            realized_pnl = position_info.unrealized_pnl
            
            # Remove from tracking if fully closed
            if close_volume >= position_info.volume:
                del self._positions[ticket]
                self._total_positions_closed += 1
            else:
                # Update remaining volume for partial close
                position_info.volume -= close_volume
                
            self.logger.info(
                f"Position closed: #{ticket} | "
                f"Volume: {close_volume:.2f} | "
                f"Price: {close_price:.5f} | "
                f"P&L: {realized_pnl:+.2f} | "
                f"Reason: {reason}"
            )
            
            return ExecutionResult(
                order_id=result.order,
                status=OrderStatus.FILLED,
                executed_price=result.price,
                executed_volume=result.volume,
                timestamp=datetime.now(),
                metadata={
                    'reason': reason,
                    'realized_pnl': realized_pnl,
                    'ticket_closed': ticket
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to close position #{ticket}: {e}", exc_info=True)
            return None
            
    def close_all_positions(self, reason: str = "Close all") -> List[ExecutionResult]:
        """
        Close all tracked positions.
        
        Args:
            reason: Reason for closing all positions
            
        Returns:
            List of ExecutionResult objects
        """
        results = []
        
        for ticket in list(self._positions.keys()):
            result = self.close_position(ticket, reason)
            if result:
                results.append(result)
                
        return results
        
    def get_total_exposure(self) -> float:
        """
        Calculate total exposure across all positions.
        
        Returns:
            Total exposure in account currency
        """
        return sum(abs(p.unrealized_pnl) for p in self._positions.values())
        
    def get_total_unrealized_pnl(self) -> float:
        """
        Calculate total unrealized P&L.
        
        Returns:
            Total unrealized P&L
        """
        return sum(p.unrealized_pnl for p in self._positions.values())
        
    def get_position_metrics(self, ticket: int) -> Dict[str, Any]:
        """
        Get detailed position analytics.
        
        Args:
            ticket: Position ticket
            
        Returns:
            Dictionary with position metrics
        """
        position = self._positions.get(ticket)
        if not position:
            return {}
            
        return {
            'ticket': position.ticket,
            'symbol': position.symbol,
            'side': position.side,
            'volume': position.volume,
            'open_price': position.open_price,
            'current_price': position.current_price,
            'unrealized_pnl': position.unrealized_pnl,
            'age_hours': position.get_age_hours(),
            'stop_loss': position.stop_loss,
            'take_profit': position.take_profit,
            'commission': position.commission,
            'swap': position.swap
        }
        
    def reconcile_positions(self) -> int:
        """
        Reconcile tracked positions with MT5 after reconnection.
        
        Returns:
            Number of positions reconciled
        """
        if not self.connector.is_connected():
            self.logger.warning("Cannot reconcile: not connected to MT5")
            return 0
            
        try:
            # Get all MT5 positions
            mt5_positions = mt5.positions_get(group=f"*{self.execution_engine.magic_number}*")
            
            if mt5_positions is None:
                mt5_positions = []
                
            reconciled = 0
            
            for mt5_pos in mt5_positions:
                if mt5_pos.ticket not in self._positions:
                    # Track missing position
                    position_info = PositionInfo(
                        ticket=mt5_pos.ticket,
                        symbol=mt5_pos.symbol,
                        side="BUY" if mt5_pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                        volume=mt5_pos.volume,
                        open_price=mt5_pos.price_open,
                        open_time=datetime.fromtimestamp(mt5_pos.time),
                        stop_loss=mt5_pos.sl if mt5_pos.sl > 0 else 0.0,
                        take_profit=mt5_pos.tp if mt5_pos.tp > 0 else 0.0,
                        current_price=mt5_pos.price_current,
                        unrealized_pnl=mt5_pos.profit,
                        magic_number=mt5_pos.magic
                    )
                    self._positions[position_info.ticket] = position_info
                    reconciled += 1
                    
            if reconciled > 0:
                self.logger.info(f"Reconciled {reconciled} positions with MT5")
                
            return reconciled
            
        except Exception as e:
            self.logger.error(f"Failed to reconcile positions: {e}", exc_info=True)
            return 0
            
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get position management statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'active_positions': len(self._positions),
            'total_opened': self._total_positions_opened,
            'total_closed': self._total_positions_closed,
            'total_unrealized_pnl': self.get_total_unrealized_pnl(),
            'total_exposure': self.get_total_exposure()
        }
