"""
Trade Manager

Manages external trades not placed by Herald, allowing the bot
to adopt and manage manual/external trades with its exit strategies.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field

from herald.connector.mt5_connector import mt5
from herald.position.manager import PositionInfo, PositionManager


@dataclass
class TradeAdoptionPolicy:
    """
    Policy configuration for adopting external trades.
    
    Attributes:
        enabled: Whether to adopt external trades
        adopt_symbols: List of symbols to adopt (empty = all symbols)
        ignore_symbols: List of symbols to never adopt
        apply_exit_strategies: Whether to apply exit strategies to adopted trades
        apply_trailing_stop: Whether to apply trailing stops
        apply_time_based_exit: Whether to apply time-based exits
        max_adoption_age_hours: Max age of trade to adopt (0 = any age)
        log_only: If True, only log external trades without adopting
    """
    enabled: bool = True
    adopt_symbols: List[str] = field(default_factory=list)
    ignore_symbols: List[str] = field(default_factory=list)
    apply_exit_strategies: bool = True
    apply_trailing_stop: bool = True
    apply_time_based_exit: bool = True
    max_adoption_age_hours: float = 0.0  # 0 = no limit
    log_only: bool = False


# Backwards compatibility alias
OrphanPolicy = TradeAdoptionPolicy


class TradeManager:
    """
    Manages detection and adoption of trades not placed by Herald.
    
    This allows Herald to:
    1. Detect manual trades placed directly in MT5
    2. Detect trades from other EAs/bots
    3. Apply Herald's exit strategies to these external trades
    4. Track and log adopted trade performance
    """
    
    # Herald's magic number (trades placed by Herald have this)
    HERALD_MAGIC = 123456
    
    def __init__(
        self,
        position_manager: PositionManager,
        policy: Optional[TradeAdoptionPolicy] = None,
        magic_number: int = HERALD_MAGIC,
        default_stop_pct: float = 8.0,
        default_rr: float = 2.0,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize trade manager.

        Args:
            position_manager: Herald's position manager
            policy: Trade adoption policy
            magic_number: Herald's magic number for identifying its own trades
            default_stop_pct: Default emergency stop percent to apply when adopting
            default_rr: Default risk:reward ratio to set TP when adopting
            config: Optional full configuration dict used to derive exit/risk defaults
        """
        """Initialize trade manager.

        Args:
            position_manager: Herald's position manager
            policy: Trade adoption policy
            magic_number: Herald's magic number for identifying its own trades
            default_stop_pct: Default emergency stop percent to apply when adopting
            default_rr: Default risk:reward ratio to set TP when adopting
        """
        """
        Initialize trade manager.
        
        Args:
            position_manager: Herald's position manager
            policy: Trade adoption policy
            magic_number: Herald's magic number for identifying its own trades
        """
        self.position_manager = position_manager
        self.policy = policy or TradeAdoptionPolicy()
        self.magic_number = magic_number
        self.default_stop_pct = default_stop_pct
        self.default_rr = default_rr
        self.logger = logging.getLogger("herald.trade_manager")
        
        # Track adopted trades
        self._adopted_tickets: Set[int] = set()
        self._adoption_log: List[Dict[str, Any]] = []
        self.config = config or {}
        
    def scan_for_external_trades(self) -> List[PositionInfo]:
        """
        Scan MT5 for trades not placed by Herald.
        
        Returns:
            List of external trade PositionInfo objects
        """
        if not self.policy.enabled:
            return []
            
        try:
            # Get all MT5 positions
            mt5_positions = mt5.positions_get()
            
            if mt5_positions is None:
                return []
                
            external_trades = []
            
            for pos in mt5_positions:
                # Skip if already tracked by Herald
                if pos.ticket in self.position_manager._positions:
                    continue
                    
                # Skip if already adopted
                if pos.ticket in self._adopted_tickets:
                    continue
                    
                # Check if this is Herald's own trade
                if pos.magic == self.magic_number:
                    # Herald trade not in registry - should reconcile
                    self.logger.warning(
                        f"Herald trade #{pos.ticket} not in registry, reconciling"
                    )
                    continue
                    
                # This is an external trade - check adoption policy
                if self._should_adopt(pos):
                    trade_info = self._create_position_info(pos)
                    external_trades.append(trade_info)
                    
            return external_trades
            
        except Exception as e:
            self.logger.error(f"Error scanning for external trades: {e}", exc_info=True)
            return []
            
    def _should_adopt(self, pos) -> bool:
        """
        Check if a position should be adopted based on policy.
        
        Args:
            pos: MT5 position object
            
        Returns:
            True if position should be adopted
        """
        # Check symbol filters
        if self.policy.adopt_symbols:
            if pos.symbol not in self.policy.adopt_symbols:
                return False
                
        if self.policy.ignore_symbols:
            if pos.symbol in self.policy.ignore_symbols:
                return False
                
        # Check age limit
        if self.policy.max_adoption_age_hours > 0:
            age_hours = (datetime.now().timestamp() - pos.time) / 3600.0
            if age_hours > self.policy.max_adoption_age_hours:
                self.logger.debug(
                    f"Skipping trade #{pos.ticket}: too old ({age_hours:.1f}h)"
                )
                return False
                
        return True
        
    def _create_position_info(self, pos) -> PositionInfo:
        """
        Create PositionInfo from MT5 position object.
        
        Args:
            pos: MT5 position object
            
        Returns:
            PositionInfo object
        """
        return PositionInfo(
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
            commission=getattr(pos, 'commission', 0.0),
            swap=getattr(pos, 'swap', 0.0),
            magic_number=pos.magic,
            comment=getattr(pos, 'comment', ''),
            metadata={
                'adopted': True,
                'adoption_time': datetime.now().isoformat(),
                'original_magic': pos.magic
            }
        )
        
    def adopt_trades(self, trades: List[PositionInfo]) -> int:
        """
        Adopt external trades into Herald's position manager and apply protective SL/TP.

        Returns:
            Number of trades adopted
        """
        if self.policy.log_only:
            for trade in trades:
                self.logger.info(
                    f"[LOG ONLY] Detected external trade: #{trade.ticket} "
                    f"{trade.symbol} {trade.side} {trade.volume:.2f} lots, "
                    f"P&L: ${trade.unrealized_pnl:.2f}"
                )
            return 0

        adopted_count = 0

        for trade in trades:
            try:
                # Add to position manager registry
                self.position_manager.add_position(trade)
                self._adopted_tickets.add(trade.ticket)

                # Log adoption
                self._adoption_log.append({
                    'ticket': trade.ticket,
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'volume': trade.volume,
                    'adoption_time': datetime.now().isoformat(),
                    'original_magic': trade.magic_number,
                    'pnl_at_adoption': trade.unrealized_pnl
                })

                self.logger.info(
                    f"Adopted trade: #{trade.ticket} | "
                    f"{trade.symbol} {trade.side} {trade.volume:.2f} lots @ {trade.open_price:.5f}, "
                    f"Current P&L: ${trade.unrealized_pnl:.2f}"
                )

                # Apply protective SL/TP if configured to do so
                try:
                    if self.policy.apply_exit_strategies:
                        # Prefer config values if available
                        pct = None
                        rr = None
                        try:
                            pct = float(self.config.get('risk', {}).get('emergency_stop_loss_pct'))
                        except Exception:
                            pct = getattr(self, 'default_stop_pct', 8.0)
                        try:
                            rr = float(self.config.get('strategy', {}).get('params', {}).get('risk_reward_ratio'))
                        except Exception:
                            rr = getattr(self, 'default_rr', 2.0)

                        entry = trade.open_price
                        if trade.side == 'BUY':
                            sl = round(entry * (1.0 - pct / 100.0), 5)
                            tp = round(entry + (entry - sl) * rr, 5)
                        else:
                            sl = round(entry * (1.0 + pct / 100.0), 5)
                            tp = round(entry - (sl - entry) * rr, 5)

                        # Only set if not already present
                        _pos = self.position_manager.get_position(trade.ticket)
                        if _pos and ((_pos.stop_loss == 0.0 and sl) or (_pos.take_profit == 0.0 and tp)):
                            success = self.position_manager.set_sl_tp(trade.ticket, sl=sl, tp=tp)
                            if success:
                                self.logger.info(f"Applied protective SL/TP to adopted trade #{trade.ticket}: SL={sl:.5f}, TP={tp:.5f}")
                            else:
                                self.logger.warning(f"Failed to apply SL/TP to adopted trade #{trade.ticket}")

                except Exception as e:
                    self.logger.error(f"Error applying SL/TP to adopted trade #{trade.ticket}: {e}")

                adopted_count += 1

            except Exception as e:
                self.logger.error(
                    f"Failed to adopt trade #{trade.ticket}: {e}"
                )

        return adopted_count
        
    def scan_and_adopt(self) -> int:
        """
        Convenience method: scan for external trades and adopt them.
        
        Returns:
            Number of trades adopted
        """
        trades = self.scan_for_external_trades()
        
        if trades:
            self.logger.info(f"Found {len(trades)} external trades")
            return self.adopt_trades(trades)
            
        return 0
        
    def get_adopted_count(self) -> int:
        """Get total number of adopted trades."""
        return len(self._adopted_tickets)
        
    def get_adoption_log(self) -> List[Dict[str, Any]]:
        """Get log of all adopted trades."""
        return self._adoption_log.copy()
        
    def is_adopted(self, ticket: int) -> bool:
        """Check if a ticket was adopted."""
        return ticket in self._adopted_tickets


# Backwards compatibility alias
OrphanTradeManager = TradeManager
