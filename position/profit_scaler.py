"""
Profit Scaling Manager - Dynamic Partial Profit Taking System

Implements intelligent profit scaling for micro and standard accounts:
- Tiered profit taking (25%, 35%, 50% at profit milestones)
- Dynamic trailing stop adjustment
- Balance-aware scaling thresholds
- Runner protection with breakeven stops
- ML-powered tier optimization (learns from outcomes)

This is critical for SPARTA mode (micro account battle testing).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import logging
import math

logger = logging.getLogger('Cthulu.profit_scaler')

# ML Tier Optimizer integration
try:
    from cthulu.ML_RL.tier_optimizer import get_tier_optimizer, record_scaling_outcome
    ML_OPTIMIZER_AVAILABLE = True
except ImportError:
    ML_OPTIMIZER_AVAILABLE = False
    logger.info("ML Tier Optimizer not available, using static tiers")


@dataclass
class ScalingTier:
    """Defines a profit-taking tier"""
    profit_threshold_pct: float  # % profit to trigger (e.g., 0.5 = 50% of position value)
    close_pct: float             # % of position to close (e.g., 0.25 = 25%)
    move_sl_to_entry: bool       # Move SL to breakeven after this tier
    trail_pct: float             # Trail SL by this % of profit after taking


@dataclass
class ScalingConfig:
    """Configuration for profit scaling behavior"""
    enabled: bool = True
    
    # Tiers for profit taking (applied in order)
    tiers: List[ScalingTier] = field(default_factory=lambda: [
        ScalingTier(profit_threshold_pct=0.30, close_pct=0.25, move_sl_to_entry=True, trail_pct=0.50),
        ScalingTier(profit_threshold_pct=0.60, close_pct=0.35, move_sl_to_entry=True, trail_pct=0.60),
        ScalingTier(profit_threshold_pct=1.00, close_pct=0.50, move_sl_to_entry=True, trail_pct=0.70),
    ])
    
    # Micro account adjustments (balance < threshold)
    micro_account_threshold: float = 100.0
    micro_tiers: List[ScalingTier] = field(default_factory=lambda: [
        # More aggressive profit taking for micro accounts
        ScalingTier(profit_threshold_pct=0.15, close_pct=0.30, move_sl_to_entry=True, trail_pct=0.40),
        ScalingTier(profit_threshold_pct=0.30, close_pct=0.40, move_sl_to_entry=True, trail_pct=0.50),
        ScalingTier(profit_threshold_pct=0.50, close_pct=0.50, move_sl_to_entry=True, trail_pct=0.60),
    ])
    
    # Minimum profit in account currency to trigger scaling
    min_profit_amount: float = 0.10
    
    # Maximum position age before forced evaluation (hours)
    max_position_age_hours: float = 4.0
    
    # Emergency profit lock threshold (% of balance)
    emergency_lock_threshold_pct: float = 0.10  # Lock profits if > 10% of balance


@dataclass
class PositionScalingState:
    """Tracks scaling state for a position"""
    ticket: int
    symbol: str
    initial_volume: float
    current_volume: float
    entry_price: float
    current_sl: Optional[float]
    current_tp: Optional[float]
    tiers_executed: List[int] = field(default_factory=list)
    total_profit_taken: float = 0.0
    breakeven_set: bool = False
    last_trail_price: Optional[float] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ProfitScaler:
    """
    Dynamic profit scaling manager.
    
    Automatically takes partial profits and adjusts stops to lock gains.
    Designed for both micro accounts (SPARTA mode) and standard accounts.
    Now with ML-powered tier optimization for adaptive learning.
    """
    
    def __init__(self, connector, execution_engine, config: Optional[ScalingConfig] = None, 
                 use_ml_optimizer: bool = True):
        """
        Initialize profit scaler.
        
        Args:
            connector: MT5Connector instance
            execution_engine: ExecutionEngine for order management
            config: Scaling configuration
            use_ml_optimizer: Whether to use ML-based tier optimization
        """
        self.connector = connector
        self.execution_engine = execution_engine
        self.config = config or ScalingConfig()
        self._position_states: Dict[int, PositionScalingState] = {}
        self._scaling_log: List[Dict[str, Any]] = []
        self.use_ml_optimizer = use_ml_optimizer and ML_OPTIMIZER_AVAILABLE
        
        if self.use_ml_optimizer:
            logger.info("ProfitScaler initialized with ML tier optimization enabled")
        
    def get_active_tiers(self, balance: float) -> List[ScalingTier]:
        """Get appropriate tiers based on account balance, optionally ML-optimized"""
        # Try ML-optimized tiers first
        if self.use_ml_optimizer:
            try:
                optimizer = get_tier_optimizer()
                ml_tiers = optimizer.get_optimized_tiers(balance)
                
                if ml_tiers and len(ml_tiers) >= 3:
                    # Convert ML tier format to ScalingTier objects
                    return [
                        ScalingTier(
                            profit_threshold_pct=t['profit_threshold_pct'] / 100,  # Convert from % to ratio
                            close_pct=t['close_pct'] / 100,  # Convert from % to ratio
                            move_sl_to_entry=True,
                            trail_pct=0.50 + (i * 0.10)  # Progressive trailing
                        )
                        for i, t in enumerate(ml_tiers)
                    ]
            except Exception as e:
                logger.warning(f"ML tier optimization failed, using defaults: {e}")
                
        # Fallback to static tiers
        if balance < self.config.micro_account_threshold:
            return self.config.micro_tiers
        return self.config.tiers
    
    def register_position(self, ticket: int, symbol: str, volume: float, 
                         entry_price: float, sl: Optional[float] = None, 
                         tp: Optional[float] = None) -> PositionScalingState:
        """Register a new position for profit scaling"""
        state = PositionScalingState(
            ticket=ticket,
            symbol=symbol,
            initial_volume=volume,
            current_volume=volume,
            entry_price=entry_price,
            current_sl=sl,
            current_tp=tp
        )
        self._position_states[ticket] = state
        logger.info(f"Registered position #{ticket} for profit scaling: {symbol} @ {entry_price}")
        return state
    
    def unregister_position(self, ticket: int) -> None:
        """Remove position from scaling management"""
        if ticket in self._position_states:
            del self._position_states[ticket]
            logger.info(f"Unregistered position #{ticket} from profit scaling")
    
    def evaluate_position(self, ticket: int, current_price: float, 
                         side: str, balance: float) -> List[Dict[str, Any]]:
        """
        Evaluate a position for profit scaling actions.
        
        Args:
            ticket: Position ticket
            current_price: Current market price
            side: 'BUY' or 'SELL'
            balance: Current account balance
            
        Returns:
            List of actions to take (close_partial, modify_sl, etc.)
        """
        if not self.config.enabled:
            return []
            
        state = self._position_states.get(ticket)
        if not state:
            return []
            
        actions = []
        tiers = self.get_active_tiers(balance)
        
        # Calculate current profit
        if side.upper() == 'BUY':
            profit_pips = current_price - state.entry_price
            profit_pct = profit_pips / state.entry_price if state.entry_price > 0 else 0
        else:
            profit_pips = state.entry_price - current_price
            profit_pct = profit_pips / state.entry_price if state.entry_price > 0 else 0
        
        # Estimate profit in currency (rough approximation)
        # For more accuracy, would need pip value calculation per symbol
        profit_amount = profit_pct * state.current_volume * state.entry_price * 100  # Rough estimate
        
        # Check each tier
        for i, tier in enumerate(tiers):
            if i in state.tiers_executed:
                continue
                
            if profit_pct >= tier.profit_threshold_pct:
                # Calculate volume to close
                close_volume = round(state.current_volume * tier.close_pct, 2)
                
                # Ensure minimum lot size
                min_lot = 0.01
                if close_volume < min_lot:
                    close_volume = min_lot
                    
                # Don't close more than we have
                if close_volume > state.current_volume:
                    close_volume = state.current_volume
                
                if close_volume >= min_lot:
                    actions.append({
                        'type': 'close_partial',
                        'ticket': ticket,
                        'volume': close_volume,
                        'tier': i,
                        'reason': f'Tier {i+1} profit target ({tier.profit_threshold_pct*100:.0f}%) reached'
                    })
                    
                # Move SL to breakeven if configured
                if tier.move_sl_to_entry and not state.breakeven_set:
                    actions.append({
                        'type': 'modify_sl',
                        'ticket': ticket,
                        'new_sl': state.entry_price,
                        'reason': 'Breakeven stop after profit tier'
                    })
                    
                # Trail stop if in profit
                if tier.trail_pct > 0 and profit_pct > 0:
                    if side.upper() == 'BUY':
                        trail_sl = state.entry_price + (profit_pips * tier.trail_pct)
                    else:
                        trail_sl = state.entry_price - (profit_pips * tier.trail_pct)
                        
                    if state.current_sl is None or (side.upper() == 'BUY' and trail_sl > state.current_sl) or \
                       (side.upper() == 'SELL' and trail_sl < state.current_sl):
                        actions.append({
                            'type': 'trail_sl',
                            'ticket': ticket,
                            'new_sl': trail_sl,
                            'reason': f'Trailing stop at {tier.trail_pct*100:.0f}% of profit'
                        })
        
        # Emergency profit lock check
        if profit_amount > 0 and balance > 0:
            profit_balance_pct = profit_amount / balance
            if profit_balance_pct >= self.config.emergency_lock_threshold_pct:
                # Lock at least 50% of the position
                if not any(a['type'] == 'close_partial' for a in actions):
                    close_volume = round(state.current_volume * 0.5, 2)
                    if close_volume >= 0.01:
                        actions.append({
                            'type': 'close_partial',
                            'ticket': ticket,
                            'volume': close_volume,
                            'tier': -1,
                            'reason': f'Emergency profit lock ({profit_balance_pct*100:.1f}% of balance)'
                        })
        
        return actions
    
    def execute_actions(self, actions: List[Dict[str, Any]], balance: float = 0.0) -> List[Dict[str, Any]]:
        """
        Execute scaling actions.
        
        Args:
            actions: List of actions from evaluate_position
            balance: Current account balance for ML learning
            
        Returns:
            List of execution results
        """
        results = []
        
        for action in actions:
            try:
                ticket = action['ticket']
                state = self._position_states.get(ticket)
                
                if action['type'] == 'close_partial':
                    result = self._execute_partial_close(ticket, action['volume'])
                    if result.get('success'):
                        profit_captured = result.get('profit', 0)
                        if state:
                            state.current_volume -= action['volume']
                            state.total_profit_taken += profit_captured
                            if 'tier' in action and action['tier'] >= 0:
                                state.tiers_executed.append(action['tier'])
                            state.last_updated = datetime.now(timezone.utc)
                            
                            # Record outcome for ML optimization
                            if self.use_ml_optimizer and 'tier' in action:
                                try:
                                    tier_name = f"tier_{action['tier']+1}" if action['tier'] >= 0 else "emergency"
                                    record_scaling_outcome(
                                        ticket=ticket,
                                        tier=tier_name,
                                        profit_threshold_triggered=action.get('profit_pct', 0),
                                        close_pct=action['volume'] / state.initial_volume * 100 if state.initial_volume > 0 else 0,
                                        profit_captured=profit_captured,
                                        remaining_profit=0,  # Will be updated when position fully closes
                                        account_balance=balance,
                                        symbol=state.symbol
                                    )
                                except Exception as ml_err:
                                    logger.debug(f"ML outcome recording failed: {ml_err}")
                                    
                        self._log_scaling_action(action, result)
                    results.append(result)
                    
                elif action['type'] == 'modify_sl':
                    result = self._execute_sl_modification(ticket, action['new_sl'])
                    if result.get('success') and state:
                        state.current_sl = action['new_sl']
                        state.breakeven_set = True
                        state.last_updated = datetime.now(timezone.utc)
                        self._log_scaling_action(action, result)
                    results.append(result)
                    
                elif action['type'] == 'trail_sl':
                    result = self._execute_sl_modification(ticket, action['new_sl'])
                    if result.get('success') and state:
                        state.current_sl = action['new_sl']
                        state.last_trail_price = action['new_sl']
                        state.last_updated = datetime.now(timezone.utc)
                        self._log_scaling_action(action, result)
                    results.append(result)
                    
            except Exception as e:
                logger.exception(f"Failed to execute scaling action: {action}")
                results.append({'success': False, 'error': str(e), 'action': action})
                
        return results
    
    def _execute_partial_close(self, ticket: int, volume: float) -> Dict[str, Any]:
        """Execute partial position close"""
        try:
            result = self.execution_engine.close_position(ticket, volume=volume)
            if result and result.status.value == 'FILLED':
                profit = result.metadata.get('profit', 0) if result.metadata else 0
                logger.info(f"Partial close #{ticket}: {volume} lots, profit: {profit}")
                return {'success': True, 'profit': profit, 'volume': volume}
            else:
                error = result.error if result else 'Unknown error'
                logger.warning(f"Partial close failed for #{ticket}: {error}")
                return {'success': False, 'error': error}
        except Exception as e:
            logger.exception(f"Partial close error for #{ticket}")
            return {'success': False, 'error': str(e)}
    
    def _execute_sl_modification(self, ticket: int, new_sl: float) -> Dict[str, Any]:
        """Modify position stop loss"""
        try:
            from cthulu.connector.mt5_connector import mt5
            
            # Get current position
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return {'success': False, 'error': 'Position not found'}
                
            pos = positions[0]
            
            # Build modification request
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": pos.tp if hasattr(pos, 'tp') else None,
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"SL modified for #{ticket}: {new_sl}")
                return {'success': True, 'new_sl': new_sl}
            else:
                error = result.comment if result else 'Unknown error'
                logger.warning(f"SL modification failed for #{ticket}: {error}")
                return {'success': False, 'error': error}
                
        except Exception as e:
            logger.exception(f"SL modification error for #{ticket}")
            return {'success': False, 'error': str(e)}
    
    def _log_scaling_action(self, action: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Log scaling action for audit"""
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': action,
            'result': result
        }
        self._scaling_log.append(entry)
        
        # Keep log bounded
        if len(self._scaling_log) > 1000:
            self._scaling_log = self._scaling_log[-500:]
    
    def get_position_state(self, ticket: int) -> Optional[PositionScalingState]:
        """Get scaling state for a position"""
        return self._position_states.get(ticket)
    
    def get_all_states(self) -> Dict[int, PositionScalingState]:
        """Get all position scaling states"""
        return dict(self._position_states)
    
    def get_scaling_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent scaling actions log"""
        return self._scaling_log[-limit:]
    
    def run_scaling_cycle(self, balance: float) -> List[Dict[str, Any]]:
        """
        Run a complete scaling evaluation cycle for all tracked positions.
        
        Args:
            balance: Current account balance
            
        Returns:
            List of all execution results
        """
        if not self.config.enabled:
            return []
            
        all_results = []
        
        try:
            from cthulu.connector.mt5_connector import mt5
            
            # Get all open positions
            positions = mt5.positions_get()
            if not positions:
                return []
                
            for pos in positions:
                ticket = pos.ticket
                
                # Auto-register if not tracked
                if ticket not in self._position_states:
                    side = 'BUY' if pos.type == 0 else 'SELL'
                    self.register_position(
                        ticket=ticket,
                        symbol=pos.symbol,
                        volume=pos.volume,
                        entry_price=pos.price_open,
                        sl=getattr(pos, 'sl', None),
                        tp=getattr(pos, 'tp', None)
                    )
                
                # Evaluate for scaling
                side = 'BUY' if pos.type == 0 else 'SELL'
                actions = self.evaluate_position(
                    ticket=ticket,
                    current_price=pos.price_current,
                    side=side,
                    balance=balance
                )
                
                if actions:
                    # Pass balance for ML learning
                    results = self.execute_actions(actions, balance=balance)
                    all_results.extend(results)
                    
        except Exception as e:
            logger.exception("Scaling cycle error")
            all_results.append({'success': False, 'error': str(e), 'cycle_error': True})
            
        return all_results
    
    def run_ml_optimization(self) -> Dict[str, Any]:
        """
        Trigger ML tier optimization based on collected outcomes.
        
        Returns:
            Optimization results summary
        """
        if not self.use_ml_optimizer:
            return {'error': 'ML optimizer not available'}
            
        try:
            from cthulu.ML_RL.tier_optimizer import run_tier_optimization
            return run_tier_optimization("all")
        except Exception as e:
            logger.exception("ML optimization failed")
            return {'error': str(e)}
    
    def get_ml_stats(self) -> Dict[str, Any]:
        """Get ML optimizer statistics"""
        if not self.use_ml_optimizer:
            return {'available': False}
            
        try:
            optimizer = get_tier_optimizer()
            stats = optimizer.get_stats()
            stats['available'] = True
            return stats
        except Exception as e:
            return {'available': False, 'error': str(e)}
            
        return all_results


# Convenience factory function
def create_profit_scaler(connector, execution_engine, config_dict: Optional[Dict[str, Any]] = None) -> ProfitScaler:
    """
    Create a ProfitScaler with optional configuration.
    
    Args:
        connector: MT5Connector instance
        execution_engine: ExecutionEngine instance
        config_dict: Optional configuration dictionary
        
    Returns:
        Configured ProfitScaler instance
    """
    config = ScalingConfig()
    
    if config_dict:
        if 'enabled' in config_dict:
            config.enabled = bool(config_dict['enabled'])
        if 'micro_account_threshold' in config_dict:
            config.micro_account_threshold = float(config_dict['micro_account_threshold'])
        if 'min_profit_amount' in config_dict:
            config.min_profit_amount = float(config_dict['min_profit_amount'])
        if 'emergency_lock_threshold_pct' in config_dict:
            config.emergency_lock_threshold_pct = float(config_dict['emergency_lock_threshold_pct'])
            
        # Custom tiers if provided
        if 'tiers' in config_dict:
            config.tiers = [
                ScalingTier(**t) for t in config_dict['tiers']
            ]
        if 'micro_tiers' in config_dict:
            config.micro_tiers = [
                ScalingTier(**t) for t in config_dict['micro_tiers']
            ]
    
    return ProfitScaler(connector, execution_engine, config)
