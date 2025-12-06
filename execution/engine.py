"""
Execution Engine

Handles order placement, modification, and reconciliation per build_plan.md.
Supports market/limit orders with idempotent submission and external reconciliation.
"""

import MetaTrader5 as mt5
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from strategy.base import Signal, SignalType


class OrderType(Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


@dataclass
class OrderRequest:
    """
    Order request structure per build_plan.md.
    
    Attributes:
        signal_id: Originating signal ID
        symbol: Trading symbol
        side: BUY or SELL
        volume: Position size in lots
        order_type: MARKET, LIMIT, or STOP
        price: Limit/stop price (None for market)
        sl: Stop loss price
        tp: Take profit price
        client_tag: Client order identifier
        metadata: Additional order data
    """
    signal_id: str
    symbol: str
    side: str
    volume: float
    order_type: OrderType
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    client_tag: str = ""
    metadata: Dict[str, Any] = None


@dataclass
class ExecutionResult:
    """
    Execution result structure per build_plan.md.
    
    Attributes:
        order_id: MT5 order ticket
        status: Execution status
        executed_price: Filled price
        executed_volume: Filled volume
        timestamp: Execution time
        error: Error message if failed
        metadata: Additional execution data
    """
    order_id: Optional[int]
    status: OrderStatus
    executed_price: Optional[float]
    executed_volume: Optional[float]
    timestamp: datetime
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class ExecutionEngine:
    """
    Order execution and management engine.
    
    Responsibilities per build_plan.md:
    - Place market and limit orders
    - Handle partial fills
    - Idempotent order submission
    - External reconciliation
    - Order modification and cancellation
    """
    
    def __init__(self, connector, magic_number: int = 20241206, slippage: int = 10):
        """
        Initialize execution engine.
        
        Args:
            connector: MT5Connector instance
            magic_number: Unique identifier for bot orders
            slippage: Maximum allowed slippage in points
        """
        self.connector = connector
        self.magic_number = magic_number
        self.slippage = slippage
        self.logger = logging.getLogger("herald.execution")
        
        # Order tracking for idempotency
        self._submitted_orders: Dict[str, int] = {}
        
    def place_order(self, order_req: OrderRequest) -> ExecutionResult:
        """
        Place order with idempotency check.
        
        Args:
            order_req: Order request
            
        Returns:
            ExecutionResult with order outcome
        """
        # Check if already submitted (idempotency)
        if order_req.client_tag in self._submitted_orders:
            existing_ticket = self._submitted_orders[order_req.client_tag]
            self.logger.warning(f"Order {order_req.client_tag} already submitted as ticket #{existing_ticket}")
            return ExecutionResult(
                order_id=existing_ticket,
                status=OrderStatus.PENDING,
                executed_price=None,
                executed_volume=None,
                timestamp=datetime.now(),
                error="Duplicate order submission"
            )
            
        # Validate connection
        if not self.connector.is_connected():
            self.logger.error("Not connected to MT5")
            return ExecutionResult(
                order_id=None,
                status=OrderStatus.REJECTED,
                executed_price=None,
                executed_volume=None,
                timestamp=datetime.now(),
                error="MT5 not connected"
            )
            
        try:
            # Prepare MT5 order request
            request = self._build_mt5_request(order_req)
            
            # Submit order
            self.logger.info(
                f"Placing {order_req.order_type.value} order: "
                f"{order_req.side} {order_req.volume} {order_req.symbol}"
            )
            
            result = mt5.order_send(request)
            
            if result is None:
                error = mt5.last_error()
                self.logger.error(f"Order submission failed: {error}")
                return ExecutionResult(
                    order_id=None,
                    status=OrderStatus.REJECTED,
                    executed_price=None,
                    executed_volume=None,
                    timestamp=datetime.now(),
                    error=str(error)
                )
                
            # Check result
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                # Track for idempotency
                if order_req.client_tag:
                    self._submitted_orders[order_req.client_tag] = result.order
                    
                self.logger.info(
                    f"Order executed: Ticket #{result.order} | "
                    f"Price: {result.price:.5f} | Volume: {result.volume}"
                )
                
                return ExecutionResult(
                    order_id=result.order,
                    status=OrderStatus.FILLED,
                    executed_price=result.price,
                    executed_volume=result.volume,
                    timestamp=datetime.now(),
                    metadata={
                        'bid': result.bid,
                        'ask': result.ask,
                        'comment': result.comment
                    }
                )
            else:
                self.logger.error(f"Order rejected: {result.retcode} - {result.comment}")
                return ExecutionResult(
                    order_id=None,
                    status=OrderStatus.REJECTED,
                    executed_price=None,
                    executed_volume=None,
                    timestamp=datetime.now(),
                    error=f"{result.retcode}: {result.comment}"
                )
                
        except Exception as e:
            self.logger.error(f"Order execution error: {e}", exc_info=True)
            return ExecutionResult(
                order_id=None,
                status=OrderStatus.REJECTED,
                executed_price=None,
                executed_volume=None,
                timestamp=datetime.now(),
                error=str(e)
            )
            
    def close_position(self, ticket: int, volume: Optional[float] = None) -> ExecutionResult:
        """
        Close an existing position.
        
        Args:
            ticket: Position ticket number
            volume: Volume to close (None = full position)
            
        Returns:
            ExecutionResult with close outcome
        """
        try:
            # Get position
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return ExecutionResult(
                    order_id=None,
                    status=OrderStatus.REJECTED,
                    executed_price=None,
                    executed_volume=None,
                    timestamp=datetime.now(),
                    error=f"Position #{ticket} not found"
                )
                
            position = position[0]
            
            # Determine close parameters
            close_volume = volume if volume else position.volume
            
            if position.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(position.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(position.symbol).ask
                
            # Build close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": close_volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": self.slippage,
                "magic": self.magic_number,
                "comment": "Herald close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Submit close order
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"Position closed: #{ticket} | Profit: {result.profit:.2f}")
                return ExecutionResult(
                    order_id=result.order,
                    status=OrderStatus.FILLED,
                    executed_price=result.price,
                    executed_volume=result.volume,
                    timestamp=datetime.now(),
                    metadata={'profit': result.profit}
                )
            else:
                error = result.comment if result else "Unknown error"
                return ExecutionResult(
                    order_id=None,
                    status=OrderStatus.REJECTED,
                    executed_price=None,
                    executed_volume=None,
                    timestamp=datetime.now(),
                    error=error
                )
                
        except Exception as e:
            self.logger.error(f"Position close error: {e}")
            return ExecutionResult(
                order_id=None,
                status=OrderStatus.REJECTED,
                executed_price=None,
                executed_volume=None,
                timestamp=datetime.now(),
                error=str(e)
            )
            
    def _build_mt5_request(self, order_req: OrderRequest) -> Dict[str, Any]:
        """Build MT5 order request dictionary."""
        # Determine MT5 order type
        if order_req.side.upper() == 'BUY':
            mt5_type = mt5.ORDER_TYPE_BUY
        else:
            mt5_type = mt5.ORDER_TYPE_SELL
            
        # Get current price if market order
        if order_req.order_type == OrderType.MARKET:
            symbol_info = self.connector.get_symbol_info(order_req.symbol)
            if order_req.side.upper() == 'BUY':
                price = symbol_info['ask']
            else:
                price = symbol_info['bid']
        else:
            price = order_req.price
            
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": order_req.symbol,
            "volume": order_req.volume,
            "type": mt5_type,
            "price": price,
            "deviation": self.slippage,
            "magic": self.magic_number,
            "comment": order_req.client_tag or "Herald",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Add SL/TP if specified
        if order_req.sl:
            request["sl"] = order_req.sl
        if order_req.tp:
            request["tp"] = order_req.tp
            
        return request
