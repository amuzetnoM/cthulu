"""Position manager and PositionInfo dataclass.

Provides a lightweight in-memory position manager used for tracking open positions,
calculating unrealized P&L, and simple reconciliation helpers. Designed to be
thread-safe for basic operations.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import threading


@dataclass
class PositionInfo:
    ticket: int
    symbol: str
    volume: float
    open_price: float = 0.0
    current_price: float = 0.0
    open_time: Optional[datetime] = None
    side: str = "BUY"
    metadata: dict = field(default_factory=dict)

    def __init__(self, ticket: int, symbol: str, volume: float, open_price: Optional[float] = None,
                 current_price: Optional[float] = None, open_time: Optional[datetime] = None,
                 side: Optional[str] = None, _legacy_entry_price: Optional[float] = None,
                 _legacy_position_type: Optional[str] = None, stop_loss: Optional[float] = None,
                 take_profit: Optional[float] = None, **kwargs):
        # Backwards-compatible legacy mapping
        if _legacy_entry_price is not None and open_price is None:
            open_price = _legacy_entry_price
        if _legacy_position_type is not None and side is None:
            side = _legacy_position_type

        self.ticket = ticket
        self.symbol = symbol
        self.volume = float(volume)
        self.open_price = float(open_price) if open_price is not None else 0.0
        self.current_price = float(current_price) if current_price is not None else (self.open_price or 0.0)
        self.open_time = open_time or datetime.utcnow()
        self.side = (side or 'BUY').upper()
        self.metadata = kwargs.get('metadata', {}) or {}
        # Optional exit fields
        self.stop_loss = stop_loss if 'stop_loss' in kwargs or stop_loss is not None else kwargs.get('stop_loss')
        self.take_profit = take_profit if 'take_profit' in kwargs or take_profit is not None else kwargs.get('take_profit')

    def get_age_hours(self) -> float:
        try:
            dt = self.open_time
            if dt is None:
                return 0.0
            from datetime import datetime, timezone
            now_utc = datetime.now(tz=timezone.utc)
            # Handle naive datetimes consistently with system local time
            if dt.tzinfo is None:
                now = datetime.now()
                return (now - dt).total_seconds() / 3600.0
            else:
                return (now_utc - dt).total_seconds() / 3600.0
        except Exception:
            return 0.0

    @property
    def unrealized_pnl(self) -> float:
        return self.calculate_unrealized_pnl()

    @property
    def entry_price(self) -> float:
        return self.open_price

    @property
    def position_type(self) -> str:
        return self.side

    def calculate_unrealized_pnl(self) -> float:
        try:
            # Simplified P&L: (current - entry) * volume for BUY, reversed for SELL
            if self.side == 'BUY':
                return (self.current_price - self.open_price) * self.volume
            else:
                return (self.open_price - self.current_price) * self.volume
        except Exception:
            return 0.0


class PositionManager:
    """In-memory position manager used by trading logic and tests."""

    def __init__(self, connector=None, execution_engine=None):
        self._positions: Dict[int, PositionInfo] = {}
        self._lock = threading.RLock()
        # Optional integration references
        self.connector = connector
        self.execution_engine = execution_engine

    def add_position(self, pos: PositionInfo) -> None:
        with self._lock:
            self._positions[pos.ticket] = pos

    def remove_position(self, ticket: int) -> None:
        with self._lock:
            if ticket in self._positions:
                del self._positions[ticket]

    def update_position(self, ticket: int, **kwargs) -> Optional[PositionInfo]:
        with self._lock:
            p = self._positions.get(ticket)
            if not p:
                return None
            for k, v in kwargs.items():
                if hasattr(p, k):
                    setattr(p, k, v)
                else:
                    p.metadata[k] = v
            return p

    def get_position(self, ticket: int) -> Optional[PositionInfo]:
        with self._lock:
            return self._positions.get(ticket)

    def get_all_positions(self) -> Dict[int, PositionInfo]:
        with self._lock:
            return dict(self._positions)

    def get_positions_by_symbol(self, symbol: str) -> List[PositionInfo]:
        with self._lock:
            return [p for p in self._positions.values() if p.symbol == symbol]

    # Compatibility alias used elsewhere
    def get_positions(self, symbol: Optional[str] = None) -> List[PositionInfo]:
        if symbol:
            return self.get_positions_by_symbol(symbol)
        return list(self.get_all_positions().values())

    def calculate_total_pnl(self) -> float:
        with self._lock:
            total = 0.0
            for p in self._positions.values():
                total += p.calculate_unrealized_pnl()
            return total

    # Additional helpers that the trading loop expects
    def track_position(self, execution_result, signal_metadata: dict = None) -> None:
        """Create a PositionInfo from an execution result (best-effort)."""
        try:
            ticket = getattr(execution_result, 'order_id', None) or getattr(execution_result, 'position_ticket', None)
            symbol = signal_metadata.get('symbol') if signal_metadata and 'symbol' in signal_metadata else getattr(execution_result, 'metadata', {}).get('symbol') if getattr(execution_result, 'metadata', None) else None
            # Fallback: if symbol missing, leave unknown
            pos = PositionInfo(
                ticket=int(ticket or 0),
                symbol=symbol or 'UNKNOWN',
                volume=getattr(execution_result, 'executed_volume', getattr(execution_result, 'volume', 0.0)) or 0.0,
                open_price=getattr(execution_result, 'executed_price', None) or 0.0,
                current_price=getattr(execution_result, 'executed_price', None) or 0.0,
                side=signal_metadata.get('side') if signal_metadata and 'side' in signal_metadata else 'BUY'
            )
            self.add_position(pos)
        except Exception:
            pass

    def monitor_positions(self) -> List[PositionInfo]:
        """Return currently tracked positions for monitoring."""
        with self._lock:
            return list(self._positions.values())

    def reconcile_positions(self) -> int:
        """Reconcile internal position tracking with MT5 live positions.
        
        Queries MT5 for actual open positions and syncs internal state.
        Returns the count of reconciled positions.
        """
        try:
            import MetaTrader5 as mt5
            if not mt5.initialize():
                # MT5 not available, return current count
                with self._lock:
                    return len(self._positions)
            
            positions = mt5.positions_get()
            if positions is None:
                positions = []
            
            with self._lock:
                # Get current MT5 tickets
                mt5_tickets = {p.ticket for p in positions}
                internal_tickets = set(self._positions.keys())
                
                # Remove positions that are no longer open in MT5
                for ticket in internal_tickets - mt5_tickets:
                    del self._positions[ticket]
                
                # Add/update positions from MT5
                for pos in positions:
                    existing = self._positions.get(pos.ticket)
                    if existing:
                        # Update current price and other fields
                        existing.current_price = pos.price_current
                        existing.volume = pos.volume
                    else:
                        # Add new position from MT5
                        self._positions[pos.ticket] = PositionInfo(
                            ticket=pos.ticket,
                            symbol=pos.symbol,
                            volume=pos.volume,
                            open_price=pos.price_open,
                            current_price=pos.price_current,
                            open_time=None,  # MT5 provides timestamp differently
                            side='BUY' if pos.type == 0 else 'SELL'
                        )
                
                return len(self._positions)
        except ImportError:
            # MT5 not installed
            with self._lock:
                return len(self._positions)
        except Exception:
            # Any error - return current count
            with self._lock:
                return len(self._positions)

    def get_statistics(self) -> dict:
        """Get position statistics, reconciling with MT5 first."""
        self.reconcile_positions()  # Sync with MT5 before reporting
        with self._lock:
            total_pnl = 0.0
            for p in self._positions.values():
                total_pnl += p.calculate_unrealized_pnl()
            return {'open_positions': len(self._positions), 'total_unrealized_pnl': total_pnl}

    def get_position_summary_by_symbol(self) -> dict:
        out = {}
        with self._lock:
            for p in self._positions.values():
                out.setdefault(p.symbol, {'count': 0, 'volume': 0.0})
                out[p.symbol]['count'] += 1
                out[p.symbol]['volume'] += p.volume
        return out

    def close_position(self, ticket: int, reason: str = "", partial_volume: Optional[float] = None):
        """Close a position via execution engine.
        
        Args:
            ticket: Position ticket to close
            reason: Reason for closing
            partial_volume: Optional partial close volume
            
        Returns:
            ExecutionResult from the close order
        """
        from cthulu.execution.engine import OrderRequest, OrderType
        
        position = self.get_position(ticket)
        if not position:
            # Position not tracked locally - try to close via MT5 directly
            import MetaTrader5 as mt5
            mt5_pos = mt5.positions_get(ticket=ticket)
            if not mt5_pos:
                from cthulu.execution.engine import ExecutionResult, OrderStatus
                return ExecutionResult(
                    status=OrderStatus.REJECTED,
                    message=f"Position {ticket} not found"
                )
            position = PositionInfo(
                ticket=mt5_pos[0].ticket,
                symbol=mt5_pos[0].symbol,
                volume=mt5_pos[0].volume,
                open_price=mt5_pos[0].price_open,
                side='BUY' if mt5_pos[0].type == 0 else 'SELL'
            )
        
        close_volume = partial_volume if partial_volume and partial_volume < position.volume else position.volume
        
        # Create close order
        close_side = 'SELL' if position.side.upper() == 'BUY' else 'BUY'
        order_req = OrderRequest(
            symbol=position.symbol,
            order_type=OrderType.MARKET,
            side=close_side,
            volume=close_volume,
            comment=f"CLOSE:{reason[:20]}" if reason else "CLOSE",
            metadata={'closing_ticket': ticket, 'reason': reason}
        )
        
        # Execute close via execution engine
        result = self.execution_engine.place_order(order_req)
        
        # If successful, remove from tracking
        if hasattr(result, 'status') and str(result.status).upper() in ('FILLED', 'ORDERSTATUS.FILLED'):
            if close_volume >= position.volume:
                self.remove_position(ticket)
            else:
                # Partial close - update volume
                self.update_position(ticket, volume=position.volume - close_volume)
        
        return result



