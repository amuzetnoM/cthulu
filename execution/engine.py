"""
Execution Engine

Handles order placement, modification, and reconciliation.
Supports market/limit orders with idempotent submission and external reconciliation.
"""

from herald.connector.mt5_connector import mt5
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from herald.strategy.base import Signal, SignalType
from herald.position import risk_manager
from herald import constants


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
    Order request structure.
    
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
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """
    Execution result structure.
    
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
    metadata: Dict[str, Any] = field(default_factory=dict)
    # position_ticket (MT5 position ticket if determinable) — order tickets and position tickets differ
    position_ticket: Optional[int] = None

    # Backwards-compatible aliases expected by other modules
    @property
    def fill_price(self) -> Optional[float]:
        return self.executed_price

    @property
    def filled_volume(self) -> Optional[float]:
        return self.executed_volume

    @property
    def commission(self) -> float:
        return float(self.metadata.get('commission', 0.0))

    @property
    def message(self) -> Optional[str]:
        return self.error


class ExecutionEngine:
    """
    Order execution and management engine.
    
    Responsibilities:
    - Place market and limit orders
    - Handle partial fills
    - Idempotent order submission
    - External reconciliation
    - Order modification and cancellation
    """
    
    def __init__(self, connector, magic_number: int = None, slippage: int = 10, risk_config: Optional[Dict[str, Any]] = None, metrics=None):
        """
        Initialize execution engine.
        
        Args:
            connector: MT5Connector instance
            magic_number: Unique identifier for bot orders (if None, use DEFAULT_MAGIC)
            slippage: Maximum allowed slippage in points
        """
        self.connector = connector
        # Use provided magic number or fall back to centralized DEFAULT_MAGIC
        self.magic_number = magic_number if magic_number is not None else constants.DEFAULT_MAGIC
        self.slippage = slippage
        # Optional risk configuration overrides (from app config)
        self.risk_config = risk_config or {}
        self.logger = logging.getLogger("herald.execution")
        # Optional metrics collector (MetricsCollector)
        self.metrics = metrics
        
        # Order tracking for idempotency
        self._submitted_orders: Dict[str, int] = {}
        # Max size to avoid unbounded growth; old entries will be pruned
        self._idempotency_max = 1000
        
    def place_order(self, order_req: OrderRequest) -> ExecutionResult:
        """
        Place order with idempotency check.
        
        Args:
            order_req: Order request
            
        Returns:
            ExecutionResult with order outcome
        """
        # Ensure metadata present
        if order_req.metadata is None:
            order_req.metadata = {}

        # If client_tag not provided, generate a deterministic tag based on order content
        if not order_req.client_tag:
            try:
                import hashlib, json
                canonical = json.dumps({
                    'signal_id': order_req.signal_id,
                    'symbol': order_req.symbol,
                    'side': order_req.side,
                    'volume': order_req.volume,
                    'order_type': order_req.order_type.value if hasattr(order_req.order_type, 'value') else str(order_req.order_type),
                    'price': order_req.price,
                    'sl': order_req.sl,
                    'tp': order_req.tp
                }, sort_keys=True, default=str)
                order_req.client_tag = hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:16]
                self.logger.debug(f"Autogenerated client_tag: {order_req.client_tag}")
            except Exception as _:
                from datetime import datetime as _dt
                order_req.client_tag = f"autogen:{int(_dt.now().timestamp())}"

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
                
            # Check if trading is allowed - ensure account is permitted before processing result
            account_info = self.connector.get_account_info()
            if account_info is None or not account_info.get('trade_allowed', False):
                self.logger.error("Trading not allowed on the connected account")
                return ExecutionResult(
                    order_id=None,
                    status=OrderStatus.REJECTED,
                    executed_price=None,
                    executed_volume=None,
                    timestamp=datetime.now(),
                    error="Trade not allowed on account",
                    metadata={'trade_allowed': False}
                )

            # Check result
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                # Track for idempotency
                if order_req.client_tag:
                    # Prune oldest entries if necessary
                    if len(self._submitted_orders) >= self._idempotency_max:
                        oldest = next(iter(self._submitted_orders))
                        try:
                            del self._submitted_orders[oldest]
                        except Exception:
                            pass
                    self._submitted_orders[order_req.client_tag] = result.order
                    
                self.logger.info(
                    f"Order executed: Ticket #{result.order} | "
                    f"Price: {result.price:.5f} | Volume: {result.volume}"
                )
                
                # Gather metadata including commission if present
                md = {
                    'bid': getattr(result, 'bid', None),
                    'ask': getattr(result, 'ask', None),
                    'comment': getattr(result, 'comment', None)
                }
                if hasattr(result, 'commission'):
                    md['commission'] = getattr(result, 'commission')

                # Try to resolve the resulting position ticket (MT5 differentiates orders and positions)
                position_ticket = None
                try:
                    positions = mt5.positions_get()
                    if positions:
                        # Filter by symbol
                        candidates = [p for p in positions if getattr(p, 'symbol', None) == order_req.symbol]
                        # Prefer matching magic
                        magic_matches = [p for p in candidates if getattr(p, 'magic', None) == self.magic_number]
                        candidates = magic_matches or candidates
                        # Prefer most recent positions
                        candidates = sorted(candidates, key=lambda x: getattr(x, 'time', 0), reverse=True)
                        for p in candidates:
                            try:
                                if abs(getattr(p, 'volume', 0) - result.volume) < 0.0001:
                                    position_ticket = getattr(p, 'ticket', None)
                                    break
                            except Exception:
                                continue
                except Exception:
                    position_ticket = None

                return ExecutionResult(
                    order_id=result.order,
                    position_ticket=position_ticket,
                    status=OrderStatus.FILLED,
                    executed_price=result.price,
                    executed_volume=result.volume,
                    timestamp=datetime.now(),
                    metadata=md
                )
            else:
                self.logger.error(f"Order rejected: {result.retcode} - {result.comment}")
                return ExecutionResult(
                    order_id=None,
                    status=OrderStatus.REJECTED,
                    executed_price=None,
                    executed_volume=None,
                    timestamp=datetime.now(),
                    error=f"{result.retcode}: {getattr(result, 'comment', None)}",
                    metadata={'retcode': getattr(result, 'retcode', None), 'comment': getattr(result, 'comment', None)}
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
                    metadata={'profit': result.profit, 'commission': getattr(result, 'commission', 0.0)}
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
        # If no SL provided, ask risk manager for a suggested default based on balance
        if not order_req.sl:
            try:
                acct = self.connector.get_account_info()
                balance = float(acct.get('balance')) if acct and acct.get('balance') is not None else None
            except Exception:
                balance = None

            if balance is not None and price is not None:
                # Pass risk_config thresholds to the risk manager if provided
                thresholds = None
                breakpoints = None
                try:
                    thresholds = self.risk_config.get('sl_balance_thresholds')
                    breakpoints = self.risk_config.get('sl_balance_breakpoints')
                except Exception:
                    thresholds = None
                    breakpoints = None

                suggestion = risk_manager.suggest_sl_adjustment(
                    order_req.symbol,
                    balance,
                    float(price),
                    float(price),
                    side=order_req.side.upper(),
                    thresholds=self.risk_config.get('sl_balance_thresholds') if isinstance(self.risk_config, dict) else None,
                    breakpoints=self.risk_config.get('sl_balance_breakpoints') if isinstance(self.risk_config, dict) else None,
                )
                # If suggestion indicates within threshold, it returns adjusted_sl=None
                adj = suggestion.get('adjusted_sl')
                if adj is not None:
                    order_req.metadata.setdefault('risk_suggestion', suggestion)
                    order_req.sl = adj
                    self.logger.info(f"Risk-managed SL for {order_req.symbol}: {order_req.sl} (balance={balance})")

        if order_req.sl:
            request["sl"] = order_req.sl
        if order_req.tp:
            request["tp"] = order_req.tp
            
        return request
