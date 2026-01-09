"""
Adaptive Drawdown Manager - Clean Implementation
Manages position sizing and risk during drawdown periods.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class AdaptiveDrawdownManager:
    """
    Adaptive drawdown and recovery management.
    
    Reduces risk during drawdowns and manages recovery.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize drawdown manager.
        
        Config:
        - trailing_lock_pct: Percentage of profit to lock
        - survival_threshold_pct: Threshold for survival mode
        - recovery_factor: Multiplier for position size during recovery
        """
        config = config or {}
        
        self.trailing_lock_pct = config.get('trailing_lock', 0.5)
        self.survival_threshold = config.get('survival_threshold', 50.0)
        self.recovery_factor = config.get('recovery_factor', 0.5)
        
        # State tracking
        self._peak_balance = 0.0
        self._in_survival_mode = False
        
        logger.info(f"AdaptiveDrawdownManager initialized: trailing_lock={self.trailing_lock_pct}, "
                   f"survival_threshold={self.survival_threshold}%")
    
    def update(self, current_balance: float) -> Dict[str, Any]:
        """
        Update drawdown state with current balance.
        
        Args:
            current_balance: Current account balance
            
        Returns:
            {
                'drawdown_pct': float,
                'survival_mode': bool,
                'size_multiplier': float,
                'recommendation': str
            }
        """
        # Update peak
        if current_balance > self._peak_balance:
            self._peak_balance = current_balance
        
        # Calculate drawdown
        if self._peak_balance > 0:
            drawdown_pct = (self._peak_balance - current_balance) / self._peak_balance * 100
        else:
            drawdown_pct = 0.0
        
        # Check survival mode
        prev_survival = self._in_survival_mode
        self._in_survival_mode = drawdown_pct >= self.survival_threshold
        
        if self._in_survival_mode and not prev_survival:
            logger.warning(f"SURVIVAL MODE activated: {drawdown_pct:.1f}% drawdown")
        elif not self._in_survival_mode and prev_survival:
            logger.info(f"SURVIVAL MODE deactivated: {drawdown_pct:.1f}% drawdown")
        
        # Calculate size multiplier
        if self._in_survival_mode:
            size_multiplier = self.recovery_factor
        elif drawdown_pct > 20:
            # Reduce size during significant drawdown
            size_multiplier = 1.0 - (drawdown_pct - 20) / 100
            size_multiplier = max(0.5, size_multiplier)
        else:
            size_multiplier = 1.0
        
        # Recommendation
        if self._in_survival_mode:
            recommendation = "REDUCE_RISK"
        elif drawdown_pct > 30:
            recommendation = "CAUTION"
        else:
            recommendation = "NORMAL"
        
        return {
            'drawdown_pct': drawdown_pct,
            'survival_mode': self._in_survival_mode,
            'size_multiplier': size_multiplier,
            'recommendation': recommendation
        }
    
    def get_adjusted_lot_size(
        self,
        base_lot_size: float,
        current_balance: float
    ) -> float:
        """
        Get lot size adjusted for current drawdown.
        
        Args:
            base_lot_size: Original calculated lot size
            current_balance: Current account balance
            
        Returns:
            Adjusted lot size
        """
        state = self.update(current_balance)
        adjusted = base_lot_size * state['size_multiplier']
        
        return max(0.01, round(adjusted, 2))
    
    def reset_peak(self, balance: float):
        """Reset peak to current balance (e.g., after deposit)."""
        self._peak_balance = balance
        self._in_survival_mode = False
        logger.info(f"Peak balance reset to ${balance:.2f}")
