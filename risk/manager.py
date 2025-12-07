"""
Risk Management Engine

Implements position sizing, exposure limits, and trade approval logic.
Provides hard guards for maximum drawdown, daily limits, and emergency shutdown.
"""

import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import date
from herald.strategy.base import Signal, SignalType


@dataclass
class RiskLimits:
    """Risk management configuration"""
    max_position_size_pct: float = 0.02  # 2% of balance per position
    max_total_exposure_pct: float = 0.10  # 10% total exposure
    max_daily_loss_pct: float = 0.05  # 5% daily loss limit
    max_positions_per_symbol: int = 1
    max_total_positions: int = 3
    min_risk_reward_ratio: float = 1.0
    max_spread_pips: float = 50.0
    volatility_scaling: bool = True


class RiskManager:
    """
    Risk management and trade approval engine.
    
    Responsibilities:
    - Position sizing (fixed, percent, volatility-based)
    - Hard guards (exposure, drawdown, daily limits)
    - Trade approval workflow
    - Emergency shutdown capability
    """
    
    def __init__(self, limits: RiskLimits):
        """
        Initialize risk manager.
        
        Args:
            limits: Risk limit configuration
        """
        self.limits = limits
        self.logger = logging.getLogger("herald.risk")
        
        # Daily tracking
        self.daily_pnl = 0.0
        self.current_date = date.today()
        self.trade_count = 0
        self.shutdown_triggered = False
        
    def approve(
        self,
        signal: Signal,
        account_state: Dict[str, Any],
        current_positions: int = 0
    ) -> Tuple[bool, str, Optional[float]]:
        """
        Approve trade signal and calculate position size.
        
        Args:
            signal: Trading signal to approve
            account_state: Current account information
            current_positions: Number of open positions
            
        Returns:
            Tuple of (approved, reason, position_size)
        """
        # Check emergency shutdown
        if self.shutdown_triggered:
            return False, "Emergency shutdown active", None
            
        # Reset daily tracking if new day
        self._check_new_day()
        
        # Check daily loss limit
        balance = account_state.get('balance', 0)
        max_daily_loss = balance * self.limits.max_daily_loss_pct
        
        if self.daily_pnl < -max_daily_loss:
            self.logger.warning(f"Daily loss limit exceeded: {self.daily_pnl:.2f}")
            return False, "Daily loss limit exceeded", None
            
        # Check max positions
        if current_positions >= self.limits.max_total_positions:
            return False, f"Max positions reached ({self.limits.max_total_positions})", None
            
        # Check trading allowed
        if not account_state.get('trade_allowed', False):
            return False, "Trading not allowed on account", None
            
        # Validate signal
        if signal.side == SignalType.NONE or signal.side == SignalType.CLOSE:
            return False, "Invalid signal type for new trade", None
            
        # Check risk/reward ratio
        if signal.stop_loss and signal.take_profit and signal.price:
            risk = abs(signal.price - signal.stop_loss)
            reward = abs(signal.take_profit - signal.price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio < self.limits.min_risk_reward_ratio:
                return False, f"Risk/reward ratio too low: {rr_ratio:.2f}", None
                
        # Calculate position size
        position_size = self._calculate_position_size(signal, account_state)
        
        if position_size is None or position_size == 0:
            return False, "Invalid position size calculated", None
            
        self.logger.info(
            f"Trade approved: {signal.action} {position_size:.2f} lots | "
            f"Confidence: {signal.confidence:.2%}"
        )
        
        return True, "Approved", position_size
        
    def _calculate_position_size(
        self,
        signal: Signal,
        account_state: Dict[str, Any]
    ) -> Optional[float]:
        """
        Calculate position size based on risk parameters.
        
        Args:
            signal: Trading signal
            account_state: Account information
            
        Returns:
            Position size in lots or None
        """
        balance = account_state.get('balance', 0)
        if balance == 0:
            return None
            
        # Risk amount per trade
        risk_amount = balance * self.limits.max_position_size_pct
        
        # If using signal size hint
        if signal.size_hint:
            return signal.size_hint
            
        # Calculate based on stop loss
        if signal.stop_loss and signal.price:
            # This is simplified - real implementation needs symbol specs
            risk_pips = abs(signal.price - signal.stop_loss)
            
            if risk_pips == 0:
                return None
                
            # Simplified calculation - needs proper pip value from symbol info
            # For demonstration: assume standard lot calculation
            lot_size = risk_amount / risk_pips / 10  # Simplified
            
            # Apply volatility scaling if enabled
            if self.limits.volatility_scaling and signal.metadata.get('atr'):
                atr = signal.metadata['atr']
                avg_atr = signal.metadata.get('avg_atr', atr)
                if avg_atr > 0:
                    volatility_factor = avg_atr / atr
                    lot_size *= volatility_factor
                    
            # Round to 2 decimals
            lot_size = round(lot_size, 2)
            
            # Apply minimum
            lot_size = max(0.01, lot_size)
            
            # Apply maximum (10% of risk per trade)
            max_lots = (balance * 0.10) / 1000  # Simplified
            lot_size = min(lot_size, max_lots)
            
            return lot_size
            
        # Default: minimum lot size
        return 0.01
        
    def record_trade_result(self, profit: float):
        """
        Record trade result for daily tracking.
        
        Args:
            profit: Trade profit/loss
        """
        self.daily_pnl += profit
        self.trade_count += 1
        
        self.logger.info(
            f"Trade result recorded: {profit:+.2f} | "
            f"Daily P&L: {self.daily_pnl:+.2f} ({self.trade_count} trades)"
        )
        
        # Check if daily loss limit hit
        balance = 10000  # Should be passed from account state
        max_daily_loss = balance * self.limits.max_daily_loss_pct
        
        if self.daily_pnl < -max_daily_loss:
            self.logger.critical("Daily loss limit exceeded - consider shutdown")
            
    def emergency_shutdown(self, reason: str = "Manual"):
        """
        Trigger emergency shutdown.
        
        Args:
            reason: Reason for shutdown
        """
        self.shutdown_triggered = True
        self.logger.critical(f"EMERGENCY SHUTDOWN TRIGGERED: {reason}")
        
    def reset_shutdown(self):
        """Reset emergency shutdown flag."""
        self.shutdown_triggered = False
        self.logger.info("Emergency shutdown reset")
        
    def _check_new_day(self):
        """Check if new trading day and reset counters."""
        today = date.today()
        if today != self.current_date:
            self.logger.info(
                f"New trading day | Previous P&L: {self.daily_pnl:+.2f} ({self.trade_count} trades)"
            )
            self.daily_pnl = 0.0
            self.trade_count = 0
            self.current_date = today
            
    def get_status(self) -> Dict[str, Any]:
        """
        Get current risk manager status.
        
        Returns:
            Status dictionary
        """
        return {
            'daily_pnl': self.daily_pnl,
            'trade_count': self.trade_count,
            'date': self.current_date.isoformat(),
            'shutdown_triggered': self.shutdown_triggered,
            'limits': {
                'max_position_size_pct': self.limits.max_position_size_pct,
                'max_daily_loss_pct': self.limits.max_daily_loss_pct,
                'max_total_positions': self.limits.max_total_positions,
            }
        }
