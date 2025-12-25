"""
Position Manager Module

Real-time position tracking, monitoring, and lifecycle management.
Integrates with ExecutionEngine for position data and RiskManager for exposure limits.
"""

from herald.connector.mt5_connector import mt5
import re
import time
from herald.position import risk_manager
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from herald.execution.engine import ExecutionResult, ExecutionEngine, OrderType, OrderStatus, OrderRequest
from herald.strategy.base import SignalType


@dataclass
class PositionInfo:
    """
    Position tracking structure.
    
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
    volume: float
    open_time: datetime
    open_price: Optional[float] = None
    stop_loss: float = 0.0
    take_profit: float = 0.0
    side: Optional[str] = None
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    magic_number: int = 0
    comment: str = ""
    # Backwards compatible fields (constructor friendly) - keep after non-defaults
    _legacy_entry_price: Optional[float] = None
    _legacy_position_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_age_seconds(self) -> float:
        """Get position age in seconds."""
        return (datetime.now() - self.open_time).total_seconds()
        
    def get_age_hours(self) -> float:
        """Get position age in hours."""
        return self.get_age_seconds() / 3600.0
        
    def get_pnl_pips(self, pip_value: float = 0.0001) -> float:
        """
        Calculate P&L in pips.
        
        Args:
            pip_value: Value of one pip for the symbol (default: 0.0001 for forex)
            
        Returns:
            P&L in pips
        """
        if self.open_price is None or self.open_price == 0:
            return 0.0
            
        if self.side == "BUY":
            price_diff = self.current_price - self.open_price
        else:  # SELL
            price_diff = self.open_price - self.current_price
            
        return price_diff / pip_value if pip_value > 0 else 0.0

    # Do not create constructor fields for legacy aliases to avoid dataclass/property conflicts

    # Backward compatibility: alias entry_price <-> open_price
    @property
    def entry_price(self) -> Optional[float]:
        return self.open_price

    @entry_price.setter
    def entry_price(self, price: Optional[float]):
        if price is not None:
            self.open_price = price

    # Backward compatibility: alias position_type <-> side
    @property
    def position_type(self) -> Optional[str]:
        return self.side

    @position_type.setter
    def position_type(self, pt: Optional[str]):
        if pt is not None:
            self.side = pt

    def calculate_unrealized_pnl(self) -> float:
        """Backward-compatible helper: compute unrealized profit/loss (basic)."""
        if self.side == "BUY":
            return (self.current_price - self.open_price) * self.volume
        else:
            return (self.open_price - self.current_price) * self.volume

    def __post_init__(self):
        # If legacy alias fields were used (entry_price/position_type), map them
        # Map explicit legacy fields first
        if getattr(self, 'entry_price', None) is not None and (self.open_price is None or self.open_price == 0.0):
            self.open_price = getattr(self, 'entry_price')
        if getattr(self, 'position_type', None) and not self.side:
            self.side = getattr(self, 'position_type')

        # Back-compat: map constructor-only legacy fields (prefixed with _legacy_)
        if getattr(self, '_legacy_entry_price', None) is not None and (self.open_price is None or self.open_price == 0.0):
            self.open_price = getattr(self, '_legacy_entry_price')
            logging.getLogger("herald.position").warning("_legacy_entry_price used: prefer `open_price` in new code")
        if getattr(self, '_legacy_position_type', None) and not self.side:
            self.side = getattr(self, '_legacy_position_type')
            logging.getLogger("herald.position").warning("_legacy_position_type used: prefer `side` in new code")


class PositionManager:
    """
    Real-time position tracking and monitoring engine.
    
    Responsibilities:
    - Maintain real-time position registry synced with MT5
    - Calculate unrealized P&L continuously
    - Detect position modifications (SL/TP changes)
    - Track position age and exposure time
    - Integrate with RiskManager for exposure limits
    - Reconcile with MT5 positions on reconnect
    """
    
    def __init__(self, connector=None, execution_engine: Optional[ExecutionEngine]=None):
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

        # Prefer explicit position_ticket when available (order id != position ticket in MT5)
        ticket_to_query = getattr(execution_result, 'position_ticket', None) or execution_result.order_id

        if ticket_to_query is None:
            self.logger.error("Cannot track position without order/position ID")
            return None

        try:
            # Try to get position by ticket first
            position = mt5.positions_get(ticket=ticket_to_query)

            # If not found and we were given an order_id, try to find a matching position by symbol/volume
            if (position is None or len(position) == 0) and execution_result.order_id is not None:
                positions = mt5.positions_get() or []
                # find candidate by order symbol and volume
                candidates = [p for p in positions if getattr(p, 'symbol', None) == getattr(execution_result, 'metadata', {}).get('symbol', None) or getattr(p, 'symbol', None)]
                # prefer same magic as the engine if available
                candidates = sorted(candidates, key=lambda x: getattr(x, 'time', 0), reverse=True)
                position = None
                for p in candidates:
                    try:
                        if abs(getattr(p, 'volume', 0) - (execution_result.executed_volume or 0)) < 0.0001:
                            position = [p]
                            break
                    except Exception:
                        continue

            if position is None or len(position) == 0:
                self.logger.error(f"Position not found in MT5: ticket #{ticket_to_query}")
                return None

            pos = position[0]
            
            # Create PositionInfo
            position_info = PositionInfo(
                ticket=pos.ticket,
                symbol=pos.symbol,
                side="BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                _legacy_position_type="BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                volume=pos.volume,
                open_price=pos.price_open,
                _legacy_entry_price=pos.price_open,
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

            # Record opened position in metrics collector if available
            try:
                if getattr(self, 'execution_engine', None) and getattr(self.execution_engine, 'metrics', None):
                    try:
                        self.execution_engine.metrics.record_position_opened()
                    except Exception:
                        pass
            except Exception:
                pass
            
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
                        entry_price=pos.price_open,
        
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
                    # Fast dynamic management: evaluate and optionally adjust SL/TP
                    try:
                        from herald.position.dynamic_manager import evaluate as dynamic_evaluate
                        suggestion = dynamic_evaluate(position_info, self.connector, getattr(self, 'config', {}))
                        if suggestion and suggestion.get('adjust_sl') is not None:
                            new_sl = suggestion['adjust_sl']
                            # Respect simple rate-limit: only attempt if last change > 30s
                            last_change = position_info.metadata.get('last_sl_change_ts')
                            now_ts = datetime.now().timestamp()
                            if not last_change or (now_ts - float(last_change)) > float(getattr(self, 'sl_change_cooldown', 30)):
                                ok = self.set_sl_tp(position_info.ticket, sl=new_sl)
                                if ok:
                                    position_info.metadata['last_sl_change_ts'] = now_ts
                                    position_info.metadata.setdefault('dynamic_actions', []).append({'ts': now_ts, 'action': 'tighten_sl', 'reason': suggestion.get('reason')})
                    except Exception:
                        # Keep monitoring robust; log at debug level
                        self.logger.debug('Dynamic manager evaluation failed', exc_info=True)

                    # If a tracked position is missing SL/TP, attempt to apply a conservative default
                    try:
                        if (position_info.stop_loss is None or float(position_info.stop_loss) == 0.0) and getattr(self, 'connector', None) and self.connector.is_connected():
                            # Avoid rapid repeated attempts per position
                            last_attempt = position_info.metadata.get('sl_set_attempt_ts')
                            now_ts = datetime.now().timestamp()
                            cooldown = float(getattr(self, 'sl_set_cooldown', 60))
                            if not last_attempt or (now_ts - float(last_attempt)) > cooldown:
                                try:
                                    acct = self.connector.get_account_info()
                                    balance = float(acct.get('balance')) if acct and acct.get('balance') is not None else None
                                except Exception:
                                    balance = None

                                if balance and position_info.open_price:
                                    from herald.position.risk_manager import _threshold_from_config, suggest_sl_adjustment
                                    threshold = _threshold_from_config(balance, None, None)
                                    if position_info.side == 'BUY':
                                        proposed_sl = float(position_info.open_price) * (1.0 - threshold)
                                    else:
                                        proposed_sl = float(position_info.open_price) * (1.0 + threshold)

                                    suggestion = suggest_sl_adjustment(position_info.symbol, balance, float(position_info.open_price), float(proposed_sl), side=position_info.side)
                                    adj = suggestion.get('adjusted_sl') or proposed_sl

                                    # Compute TP using RR 2.0 by default
                                    rr = 2.0
                                    if position_info.side == 'BUY':
                                        tp = float(position_info.open_price) + (float(position_info.open_price) - float(adj)) * rr
                                    else:
                                        tp = float(position_info.open_price) - (float(adj) - float(position_info.open_price)) * rr

                                    ok = self.set_sl_tp(position_info.ticket, sl=adj, tp=tp)
                                    position_info.metadata['sl_set_attempt_ts'] = now_ts
                                    position_info.metadata.setdefault('dynamic_actions', []).append({'ts': now_ts, 'action': 'apply_default_sl_tp', 'sl': adj, 'tp': tp, 'reason': suggestion.get('reason')})
                                    if ok:
                                        self.logger.info(f"Applied default SL/TP to position #{position_info.ticket}: sl={adj}, tp={tp}")
                    except Exception:
                        self.logger.exception('Failed to apply default SL/TP to tracked position')
                    
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

    # Backwards compatible API: keep old method name used by tests
    def get_positions_by_symbol(self, symbol: Optional[str] = None) -> List[PositionInfo]:
        return self.get_positions(symbol)

    def calculate_total_pnl(self) -> float:
        """Return total unrealized P&L across all tracked positions."""
        return sum(p.calculate_unrealized_pnl() for p in self._positions.values())

    # Backwards-compatible helper methods for legacy tests or external code
    def add_position(self, position: PositionInfo):
        """Add a position to the manager (compat shim)."""
        self._positions[position.ticket] = position
        self._total_positions_opened += 1
        # Record opened position in metrics collector if available
        try:
            if getattr(self, 'execution_engine', None) and getattr(self.execution_engine, 'metrics', None):
                try:
                    self.execution_engine.metrics.record_position_opened()
                except Exception:
                    pass
        except Exception:
            pass

    def remove_position(self, ticket: int):
        """Remove a position from the manager (compat shim)."""
        if ticket in self._positions:
            del self._positions[ticket]
            self._total_positions_closed += 1

    def get_all_positions(self) -> List[int]:
        """Return a list of tracked position tickets for compatibility with legacy tests."""
        return list(self._positions.keys())

    def update_position(self, ticket: int, current_price: float = None):
        """Update position fields (compat shim)."""
        pos = self._positions.get(ticket)
        if pos and current_price is not None:
            pos.current_price = current_price
        
    def set_sl_tp(self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None) -> bool:
        """Set stop loss and/or take profit for an existing position.

        Returns True if modified successfully, False otherwise.
        """
        position_info = self._positions.get(ticket)
        if not position_info:
            self.logger.error(f"Cannot modify SL/TP for position #{ticket}: not tracked")
            return False
        try:
            # If an SL is proposed, ask the risk manager for an adjustment
            if sl is not None:
                try:
                    acct = mt5.account_info()
                    balance = acct.balance if acct is not None else None
                except Exception:
                    balance = None

                # Prefer tracked current price, fall back to open price
                current_price = position_info.current_price or position_info.open_price

                if balance is not None and current_price is not None:
                    suggestion = risk_manager.suggest_sl_adjustment(
                        position_info.symbol,
                        float(balance),
                        float(current_price),
                        float(sl),
                        side=position_info.side or "BUY",
                        thresholds=(self.execution_engine.risk_config.get('sl_balance_thresholds') if getattr(self, 'execution_engine', None) and isinstance(self.execution_engine.risk_config, dict) else None),
                        breakpoints=(self.execution_engine.risk_config.get('sl_balance_breakpoints') if getattr(self, 'execution_engine', None) and isinstance(self.execution_engine.risk_config, dict) else None),
                    )
                    # If the risk manager recommends a narrower SL, apply it
                    adj = suggestion.get("adjusted_sl")
                    if adj is not None and adj != sl:
                        self.logger.warning(
                            f"Adjusting proposed SL for #{ticket} from {sl} -> {adj} based on balance={balance}: {suggestion.get('reason')}"
                        )
                        position_info.metadata.setdefault("risk_suggestions", []).append(suggestion)
                        sl = adj

            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "symbol": position_info.symbol,
            }
            if sl is not None:
                request["sl"] = sl
            if tp is not None:
                request["tp"] = tp
            # Log outgoing SL/TP request for observability
            try:
                self.logger.info(f"Outgoing SL/TP request for #{ticket}: {request}")
            except Exception:
                pass

            result = mt5.order_send(request)

            # Log result for debugging broker responses
            try:
                self.logger.info(f"SL/TP order_send result for #{ticket}: retcode={getattr(result,'retcode',None)} comment={getattr(result,'comment',None)}")
            except Exception:
                pass

            if result is None or getattr(result, 'retcode', None) != mt5.TRADE_RETCODE_DONE:
                err = getattr(result, 'comment', None) if result else "Unknown"
                self.logger.error(f"Failed to set SL/TP for #{ticket}: {err}")
                return False

            # Verify by reading back the position to ensure broker accepted the SL/TP
            verified = False
            for attempt in range(6):  # small wait-and-retry to allow terminal update
                try:
                    time.sleep(0.5)
                    positions = mt5.positions_get(ticket=ticket)
                    if positions:
                        p = positions[0]
                        # Compare sl/tp with tolerance for broker rounding and symbol digits
                        sl_ok = True
                        tp_ok = True
                        try:
                            sym_info = mt5.symbol_info(position_info.symbol)
                            digits = getattr(sym_info, 'digits', 5) if sym_info is not None else 5
                            # tolerance: at least 1e-5, but scale with symbol digits (e.g., 0.01 for 2 digits)
                            tol = max(10 ** -digits, 1e-5)
                        except Exception:
                            tol = 1e-5

                        if sl is not None:
                            sl_ok = abs((p.sl or 0.0) - sl) <= tol
                        if tp is not None:
                            tp_ok = abs((p.tp or 0.0) - tp) <= tol
                        if sl_ok and tp_ok:
                            verified = True
                            break
                    else:
                        self.logger.debug(f"Verification attempt {attempt+1}: position #{ticket} not found")
                except Exception as e:
                    self.logger.debug(f"Verification attempt {attempt+1} error for #{ticket}: {e}")

            if not verified:
                # Retrieve last error for more context
                err = mt5.last_error()
                err_msg = str(err) if err else 'unknown error'
                self.logger.error(f"SL/TP verification failed for #{ticket} after update (error: {err_msg})")
                # ML instrumentation: record SL/TP failure (best-effort)
                try:
                    if getattr(self, 'execution_engine', None) and getattr(self.execution_engine, 'ml_collector', None):
                        payload = {
                            'ticket': ticket,
                            'symbol': position_info.symbol,
                            'sl': sl,
                            'tp': tp,
                            'status': 'FAILED',
                            'error': err_msg
                        }
                        try:
                            self.execution_engine.ml_collector.record_execution(payload)
                        except Exception:
                            self.logger.exception('ML collector failed')
                except Exception:
                    pass
                # Publish a Prometheus metric if exporter exists (best-effort)
                try:
                    from herald.observability import PrometheusExporter
                    # This will only increment the metric if an exporter instance is used in main; otherwise it's safe.
                    exporter = PrometheusExporter()
                    exporter.record_sl_tp_failure(ticket=ticket, symbol=position_info.symbol)
                except Exception:
                    pass
                return False

            # Update tracked position fields
            if sl is not None:
                position_info.stop_loss = sl
            if tp is not None:
                position_info.take_profit = tp

            self.logger.info(f"Set SL/TP for #{ticket}: SL={position_info.stop_loss}, TP={position_info.take_profit}")
            # ML instrumentation: record SL/TP update if collector available (best-effort)
            try:
                if getattr(self, 'execution_engine', None) and getattr(self.execution_engine, 'ml_collector', None):
                    payload = {
                        'ticket': ticket,
                        'symbol': position_info.symbol,
                        'sl': position_info.stop_loss,
                        'tp': position_info.take_profit,
                        'status': 'SET'
                    }
                    try:
                        self.execution_engine.ml_collector.record_execution(payload)
                    except Exception:
                        self.logger.exception('ML collector failed')
            except Exception:
                pass
            return True
        except Exception as e:
            self.logger.error(f"Error setting SL/TP for #{ticket}: {e}", exc_info=True)
            return False

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
            
            # Create close request (strict MT5 comment sanitization)
            raw_comment = f"Close: {reason}"
            # Collapse whitespace/newlines and keep only printable ASCII (0x20-0x7E)
            try:
                cleaned = re.sub(r"[\r\n\t]+", ' ', raw_comment)
                cleaned = re.sub(r"\s+", ' ', cleaned).strip()
                cleaned = ''.join(ch for ch in cleaned if 32 <= ord(ch) <= 126)
                # MT5 comment limit is 31 characters; enforce strict truncation
                if len(cleaned) > 31:
                    cleaned = cleaned[:31]
            except Exception:
                cleaned = ''

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position_info.symbol,
                "volume": close_volume,
                "type": order_type,
                "position": ticket,
                "price": close_price,
                "deviation": 10,
                "magic": self.execution_engine.magic_number,
                "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Only include `comment` when it is non-empty and <=31 chars (MT5 requirement).
            if cleaned:
                request["comment"] = cleaned

            # Log outgoing close request payload at INFO so it appears in current logs
            try:
                self.logger.info(
                    f"Outgoing close request #{ticket}: raw_comment='{raw_comment}' sanitized_comment='{cleaned}'"
                )
                self.logger.info(f"Outgoing close request payload: {request}")
            except Exception:
                pass
            
            # Send close order
            result = mt5.order_send(request)

            # If broker rejects due to invalid comment or unsupported filling mode, attempt robust fallbacks
            if result is None or getattr(result, 'retcode', None) != mt5.TRADE_RETCODE_DONE:
                # Build an error message for logging/inspection
                error_msg = None
                try:
                    if result is None:
                        last = mt5.last_error()
                        error_msg = str(last) if last else 'Unknown'
                    else:
                        error_msg = f"{getattr(result,'retcode', None)}: {getattr(result,'comment', None)}"
                except Exception:
                    error_msg = 'unknown error'

                # Try to detect known rejection causes and retry with fallbacks
                try:
                    comment_text = getattr(result, 'comment', '') if result is not None else ''

                    # 1) If broker rejects comment, retry without comment
                    if (comment_text and 'Invalid "comment" argument' in comment_text) or (isinstance(error_msg, str) and 'Invalid "comment" argument' in error_msg) or (getattr(result, 'retcode', None) == -2):
                        self.logger.warning(f"Broker rejected close for #{ticket} due to comment; retrying without comment (was: '{request.get('comment', '')}')")
                        request_no_comment = {k: v for k, v in request.items() if k != 'comment'}
                        retry = mt5.order_send(request_no_comment)
                        if retry is not None and getattr(retry, 'retcode', None) == mt5.TRADE_RETCODE_DONE:
                            result = retry
                        else:
                            final_err = getattr(retry, 'comment', None) if retry is not None else mt5.last_error()
                            self.logger.error(f"Retry without comment failed for #{ticket}: {final_err}")
                            # continue to try other fallbacks below

                    # 2) If unsupported filling mode is reported or we still have a non-DONE result, try alternative filling modes
                    if (isinstance(error_msg, str) and 'Unsupported filling mode' in error_msg) or (getattr(result, 'retcode', None) not in (None, mt5.TRADE_RETCODE_DONE)):
                        # Try ORDER_FILLING_FOK then no type_filling
                        tried = []
                        try_modes = []
                        try:
                            try_modes.append(('FOK', mt5.ORDER_FILLING_FOK))
                        except Exception:
                            pass
                        # Also try removing the type_filling entirely
                        try_modes.append(('NO_FILLING', None))

                        attempted_success = False
                        for mode_name, mode_val in try_modes:
                            self.logger.info(f"Attempting close retry #{mode_name} for #{ticket}")
                            request_retry = request.copy()
                            if mode_val is None:
                                request_retry.pop('type_filling', None)
                            else:
                                request_retry['type_filling'] = mode_val
                            retry2 = mt5.order_send(request_retry)
                            if retry2 is not None and getattr(retry2, 'retcode', None) == mt5.TRADE_RETCODE_DONE:
                                result = retry2
                                attempted_success = True
                                break
                            else:
                                tried.append((mode_name, getattr(retry2, 'retcode', None), getattr(retry2, 'comment', None)))

                        if not attempted_success:
                            self.logger.error(f"All filling mode fallbacks failed for #{ticket}: {tried}")
                            return ExecutionResult(
                                order_id=None,
                                status=OrderStatus.REJECTED,
                                executed_price=None,
                                executed_volume=None,
                                timestamp=datetime.now(),
                                error=str(error_msg)
                            )

                    # If we have not returned yet and result still indicates failure, return an error
                    if result is None or getattr(result, 'retcode', None) != mt5.TRADE_RETCODE_DONE:
                        self.logger.error(f"Failed to close position #{ticket}: {error_msg}")
                        return ExecutionResult(
                            order_id=None,
                            status=OrderStatus.REJECTED,
                            executed_price=None,
                            executed_volume=None,
                            timestamp=datetime.now(),
                            error=str(error_msg)
                        )
                except Exception as e:
                    self.logger.error(f"Error handling failed close for #{ticket}: {e}", exc_info=True)
                    return ExecutionResult(
                        order_id=None,
                        status=OrderStatus.REJECTED,
                        executed_price=None,
                        executed_volume=None,
                        timestamp=datetime.now(),
                        error=str(e)
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

            # Record trade result in metrics collector if available
            try:
                if getattr(self, 'execution_engine', None) and getattr(self.execution_engine, 'metrics', None):
                    self.execution_engine.metrics.record_trade(float(realized_pnl), position_info.symbol)
            except Exception:
                self.logger.debug('Failed to record trade in metrics collector', exc_info=True)
            
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
        
    def reconcile_positions(self, magic_number: int = None) -> int:
        """
        Reconcile tracked positions with MT5 after reconnection or at startup.
        
        Args:
            magic_number: Herald's magic number to filter positions (defaults to central DEFAULT_MAGIC)
        
        Returns:
            Number of positions reconciled
        """
        if magic_number is None:
            try:
                from herald import constants
                magic_number = constants.DEFAULT_MAGIC
            except Exception:
                magic_number = 0

        if not self.connector.is_connected():
            self.logger.warning("Cannot reconcile: not connected to MT5")
            return 0
            
        try:
            # Get all MT5 positions
            mt5_positions = mt5.positions_get()
            
            if mt5_positions is None:
                mt5_positions = []
                
            reconciled = 0
            
            for mt5_pos in mt5_positions:
                # Only reconcile Herald's own trades (matching magic number)
                if mt5_pos.magic != magic_number:
                    continue
                    
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
