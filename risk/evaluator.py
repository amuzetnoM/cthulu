"""
Risk Evaluator - Clean Implementation
Handles trade approval and position sizing.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RiskEvaluator:
    """
    Risk evaluation and position sizing.
    
    Responsibilities:
    - Approve/reject trade signals
    - Calculate position size
    - Check exposure limits
    - Validate against account state
    """
    
    def __init__(self, config: Dict[str, Any], connector):
        """
        Initialize risk evaluator.
        
        Args:
            config: Risk configuration
            connector: MT5 connector
        """
        self.config = config
        self.connector = connector
        self.position_manager = None  # Set later via wire_dependencies
        
        # Risk parameters
        self.max_positions = config.get('max_positions', 3)
        self.max_positions_per_symbol = config.get('max_positions_per_symbol', 3)
        self.max_risk_per_trade = config.get('max_risk_per_trade', 0.02)  # 2%
        self.min_balance_threshold = config.get('min_balance_threshold', 10.0)
        self.default_lot_size = config.get('default_lot_size', 0.1)
        self.max_lot_size = config.get('max_lot_size', 1.0)
        
        logger.info(f"RiskEvaluator initialized: max_positions={self.max_positions}, "
                   f"max_risk={self.max_risk_per_trade*100}%")
    
    def set_position_manager(self, position_manager):
        """Set position manager for exposure checks."""
        self.position_manager = position_manager
    
    def evaluate(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a trade signal for risk approval.
        
        Args:
            signal: Trading signal
            
        Returns:
            {
                'approved': bool,
                'lot_size': float,
                'reason': str,
                'risk_score': float
            }
        """
        symbol = signal.get('symbol', 'UNKNOWN')
        direction = signal.get('direction', 'buy')
        
        # Check account state
        account = self.connector.get_account_info()
        balance = account.get('balance', 0)
        
        if balance < self.min_balance_threshold:
            return {
                'approved': False,
                'lot_size': 0,
                'reason': f'Balance ${balance:.2f} below minimum ${self.min_balance_threshold}',
                'risk_score': 0
            }
        
        # Check total position count
        total_positions = self._get_position_count()
        if total_positions >= self.max_positions:
            return {
                'approved': False,
                'lot_size': 0,
                'reason': f'Maximum positions reached ({total_positions}/{self.max_positions})',
                'risk_score': 0
            }
        
        # Check positions per symbol
        symbol_positions = self._get_position_count(symbol)
        if symbol_positions >= self.max_positions_per_symbol:
            return {
                'approved': False,
                'lot_size': 0,
                'reason': f'Maximum positions per symbol reached ({symbol_positions})',
                'risk_score': 0
            }
        
        # Calculate position size
        lot_size = self._calculate_position_size(signal, balance)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(signal, balance, lot_size)
        
        return {
            'approved': True,
            'lot_size': lot_size,
            'reason': 'Trade approved',
            'risk_score': risk_score
        }
    
    def _get_position_count(self, symbol: Optional[str] = None) -> int:
        """Get current position count."""
        if self.position_manager:
            return self.position_manager.get_position_count(symbol)
        
        # Fallback to connector
        positions = self.connector.get_positions()
        if symbol:
            return len([p for p in positions if p.symbol == symbol])
        return len(positions)
    
    def _calculate_position_size(
        self,
        signal: Dict[str, Any],
        balance: float
    ) -> float:
        """
        Calculate appropriate position size.
        
        Uses risk percentage of account.
        """
        # Risk amount
        risk_amount = balance * self.max_risk_per_trade
        
        # Get ATR-based stop distance from signal
        sl_distance = signal.get('sl_distance', 100)  # Default 100 points
        
        # Very simplified position sizing
        # In reality, this would use pip value calculations
        lot_size = risk_amount / sl_distance / 10  # Simplified
        
        # Clamp to limits
        lot_size = max(0.01, min(self.max_lot_size, lot_size))
        
        # Use default if calculation gives unrealistic value
        if lot_size < 0.01 or lot_size > 10:
            lot_size = self.default_lot_size
        
        return round(lot_size, 2)
    
    def _calculate_risk_score(
        self,
        signal: Dict[str, Any],
        balance: float,
        lot_size: float
    ) -> float:
        """
        Calculate a risk score for the trade.
        
        0 = low risk, 100 = high risk
        """
        score = 50  # Start neutral
        
        # Adjust based on confidence
        confidence = signal.get('confidence', 0.5)
        score -= (confidence - 0.5) * 20  # Higher confidence = lower risk
        
        # Adjust based on lot size relative to max
        lot_ratio = lot_size / self.max_lot_size
        score += lot_ratio * 20  # Bigger size = higher risk
        
        return max(0, min(100, score))
