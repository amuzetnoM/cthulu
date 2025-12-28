"""
Risk Evaluator Module

Unified risk management system consolidating all risk evaluation logic.
This is the single source of truth for all risk-related decisions in Herald.

Responsibilities:
- Position sizing (fixed, percent, volatility-adjusted, Kelly criterion)
- Trade approval with comprehensive checks
- Exposure management (per-symbol, total)
- Daily loss limits with emergency shutdown
- Spread checking
- Risk/reward ratio validation
- Confidence threshold enforcement
- Stop-loss adjustment recommendations
- Balance-based scaling
- Timeframe/mindset recommendations

Consolidates:
- risk/manager.py (trade approval, position sizing, limits)
- position/risk_manager.py (SL adjustment, balance scaling)
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


@dataclass
class RiskLimits:
    """Configuration for risk limits and thresholds."""
    # Position sizing
    max_position_size_percent: float = 2.0  # Max % of balance per position
    max_total_exposure_percent: float = 10.0  # Max % of balance in all positions
    
    # Per-symbol limits
    max_positions_per_symbol: int = 3
    max_exposure_per_symbol_percent: float = 5.0
    
    # Daily limits
    max_daily_loss: float = 500.0  # Max loss per day in account currency
    max_daily_trades: int = 50
    
    # Risk/reward
    min_risk_reward_ratio: float = 1.5  # Minimum R:R ratio
    
    # Spread limits
    max_spread_points: float = 10.0  # Max spread in points
    
    # Confidence
    min_confidence: float = 0.0  # Minimum signal confidence (0.0 = no filter)
    
    # Emergency
    emergency_shutdown_enabled: bool = True


class DailyRiskTracker:
    """Tracks daily P&L and trading activity for limit enforcement."""
    
    def __init__(self):
        """Initialize daily risk tracker."""
        self.reset_daily_tracking()
    
    def reset_daily_tracking(self):
        """Reset daily counters (called at start of each trading day)."""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.last_reset = datetime.now().date()
        logger.info("Daily risk tracking reset")
    
    def check_and_reset_if_new_day(self):
        """Check if it's a new day and reset if needed."""
        today = datetime.now().date()
        if today > self.last_reset:
            self.reset_daily_tracking()
    
    def update_pnl(self, pnl: float):
        """Update daily P&L."""
        self.check_and_reset_if_new_day()
        self.daily_pnl += pnl
    
    def increment_trades(self):
        """Increment daily trade counter."""
        self.check_and_reset_if_new_day()
        self.daily_trades += 1
    
    def get_daily_pnl(self) -> float:
        """Get current daily P&L."""
        self.check_and_reset_if_new_day()
        return self.daily_pnl
    
    def get_daily_trades(self) -> int:
        """Get count of trades today."""
        self.check_and_reset_if_new_day()
        return self.daily_trades


class RiskEvaluator:
    """
    Unified risk evaluation system - single source of truth for all risk logic.
    
    This class consolidates risk management functionality from multiple
    previous managers into one cohesive system.
    """
    
    def __init__(self, connector, position_tracker, limits: Optional[RiskLimits] = None):
        """
        Initialize the risk evaluator.
        
        Args:
            connector: MT5 connector
            position_tracker: PositionTracker instance
            limits: RiskLimits configuration
        """
        self.connector = connector
        self.tracker = position_tracker
        self.limits = limits or RiskLimits()
        self.daily_tracker = DailyRiskTracker()
        self.emergency_shutdown_triggered = False
        
        logger.info("RiskEvaluator initialized")
    
    def approve(self, signal, account_info, current_positions) -> tuple[bool, str, float]:
        """
        Approve a trading signal and calculate position size.
        
        Args:
            signal: Trading signal object
            account_info: MT5 account info (dict or object)
            current_positions: Number of current positions for this symbol
            
        Returns:
            tuple: (approved: bool, reason: str, position_size: float)
        """
        try:
            # Handle both dict and object formats for account_info
            if isinstance(account_info, dict):
                balance = account_info.get('balance') or account_info.get('Balance') or 0.0
            else:
                balance = getattr(account_info, 'balance', getattr(account_info, 'Balance', 0.0))
            symbol = signal.symbol
            
            # Calculate position size
            position_size = self.calculate_position_size(
                symbol=symbol,
                balance=balance,
                method="percent",
                risk_percent=self.limits.max_position_size_percent
            )
            
            # Check if we can open more positions
            if current_positions >= self.limits.max_positions_per_symbol:
                return False, f"Maximum positions per symbol reached ({self.limits.max_positions_per_symbol})", 0.0
            
            # Check total exposure
            total_exposure = sum(p.volume for p in self.tracker.get_positions())
            max_total = balance * self.limits.max_total_exposure_percent / 100
            if total_exposure + position_size > max_total:
                return False, f"Total exposure limit exceeded ({self.limits.max_total_exposure_percent}%)", 0.0
            
            # Approve the trade
            approved, reason = self.approve_trade(
                symbol=symbol,
                volume=position_size,
                entry_price=signal.price,
                sl=signal.stop_loss,
                tp=signal.take_profit,
                confidence=signal.confidence
            )
            
            if approved:
                return True, reason, position_size
            else:
                return False, reason, 0.0
                
        except Exception as e:
            logger.error(f"Error in signal approval: {e}", exc_info=True)
            return False, f"Approval error: {str(e)}", 0.0
    
    def approve_trade(self, symbol: str, volume: float, entry_price: float,
                     sl: Optional[float] = None, tp: Optional[float] = None,
                     confidence: float = 1.0) -> tuple[bool, str]:
        """
        Master trade approval method - checks all risk constraints.
        
        Args:
            symbol: Trading symbol
            volume: Proposed position size
            entry_price: Entry price
            sl: Stop loss price
            tp: Take profit price
            confidence: Signal confidence (0.0-1.0)
            
        Returns:
            Tuple of (approved: bool, reason: str)
        """
        try:
            # Check emergency shutdown
            if self.emergency_shutdown_triggered:
                return False, "Emergency shutdown active"
            
            # Check daily loss limit
            if not self.check_daily_limits()[0]:
                return False, "Daily loss limit exceeded"
            
            # Check daily trade limit
            if self.daily_tracker.get_daily_trades() >= self.limits.max_daily_trades:
                return False, f"Daily trade limit ({self.limits.max_daily_trades}) reached"
            
            # Check confidence threshold
            if confidence < self.limits.min_confidence:
                return False, f"Confidence {confidence:.2f} below threshold {self.limits.min_confidence}"
            
            # Check spread
            spread_ok, spread_msg = self.check_spread(symbol)
            if not spread_ok:
                return False, spread_msg
            
            # Check exposure limits
            exposure_ok, exposure_msg = self.check_exposure_limits(symbol, volume)
            if not exposure_ok:
                return False, exposure_msg
            
            # Check risk/reward ratio
            if sl and tp:
                rr_ok, rr_msg = self.validate_risk_reward(entry_price, sl, tp)
                if not rr_ok:
                    return False, rr_msg
            
            # All checks passed
            return True, "Trade approved"
            
        except Exception as e:
            logger.error(f"Error in trade approval: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    def calculate_position_size(self, symbol: str, balance: float, 
                               method: str = "percent", 
                               risk_percent: float = 2.0,
                               sl_points: Optional[float] = None,
                               atr: Optional[float] = None,
                               win_rate: Optional[float] = None) -> float:
        """
        Calculate position size using various methods.
        
        Args:
            symbol: Trading symbol
            balance: Account balance
            method: Sizing method ("fixed", "percent", "volatility", "kelly")
            risk_percent: Risk percentage for percent method
            sl_points: Stop loss distance in points (for volatility method)
            atr: Average True Range (for volatility method)
            win_rate: Historical win rate (for Kelly criterion)
            
        Returns:
            Position size in lots
        """
        try:
            if method == "fixed":
                # Fixed lot size
                return 0.01
            
            elif method == "percent":
                # Risk percentage of balance
                risk_amount = balance * (risk_percent / 100.0)
                point_value = self.connector.get_point_value(symbol)
                
                if sl_points and point_value:
                    volume = risk_amount / (sl_points * point_value)
                    # Round to valid lot size
                    min_lot = self.connector.get_min_lot(symbol)
                    volume = max(min_lot, round(volume / min_lot) * min_lot)
                    return volume
                else:
                    # Default to small size if no SL info
                    return 0.01
            
            elif method == "volatility":
                # Volatility-adjusted sizing
                if not atr:
                    logger.warning("ATR not provided for volatility sizing, using percent method")
                    return self.calculate_position_size(symbol, balance, "percent", risk_percent)
                
                # Adjust position size inversely to volatility
                # Higher volatility = smaller position
                point_value = self.connector.get_point_value(symbol)
                risk_amount = balance * (risk_percent / 100.0)
                volume = risk_amount / (atr * point_value)
                
                min_lot = self.connector.get_min_lot(symbol)
                volume = max(min_lot, round(volume / min_lot) * min_lot)
                return volume
            
            elif method == "kelly":
                # Kelly Criterion sizing
                if not win_rate:
                    logger.warning("Win rate not provided for Kelly sizing, using percent method")
                    return self.calculate_position_size(symbol, balance, "percent", risk_percent)
                
                # Kelly formula: f* = (bp - q) / b
                # where b = odds received, p = win probability, q = loss probability
                avg_win = 2.0  # Assume 2:1 average win
                avg_loss = 1.0
                
                kelly_fraction = (avg_win * win_rate - (1 - win_rate)) / avg_win
                kelly_fraction = max(0.0, min(kelly_fraction, 0.25))  # Cap at 25%
                
                # Use Kelly fraction as risk percent
                return self.calculate_position_size(symbol, balance, "percent", kelly_fraction * 100)
            
            else:
                logger.warning(f"Unknown sizing method '{method}', using percent")
                return self.calculate_position_size(symbol, balance, "percent", risk_percent)
                
        except Exception as e:
            logger.error(f"Error calculating position size: {e}", exc_info=True)
            return 0.01  # Safe default
    
    def check_exposure_limits(self, symbol: str, additional_volume: float) -> tuple[bool, str]:
        """
        Check if adding a position would exceed exposure limits.
        
        Args:
            symbol: Trading symbol
            additional_volume: Volume to add
            
        Returns:
            Tuple of (within_limits: bool, reason: str)
        """
        try:
            # Check total exposure
            current_exposure = self.tracker.calculate_total_exposure()
            balance = self.connector.get_balance()
            
            if balance > 0:
                exposure_percent = (current_exposure / balance) * 100
                new_exposure_percent = ((current_exposure + additional_volume) / balance) * 100
                
                if new_exposure_percent > self.limits.max_total_exposure_percent:
                    return False, f"Would exceed total exposure limit ({self.limits.max_total_exposure_percent}%)"
            
            # Check per-symbol exposure
            symbol_positions = self.tracker.get_positions_by_symbol(symbol)
            symbol_exposure = sum(abs(p.volume) for p in symbol_positions)
            
            if balance > 0:
                symbol_exposure_percent = ((symbol_exposure + additional_volume) / balance) * 100
                
                if symbol_exposure_percent > self.limits.max_exposure_per_symbol_percent:
                    return False, f"Would exceed {symbol} exposure limit ({self.limits.max_exposure_per_symbol_percent}%)"
            
            # Check position count per symbol
            if len(symbol_positions) >= self.limits.max_positions_per_symbol:
                return False, f"Maximum positions for {symbol} ({self.limits.max_positions_per_symbol}) reached"
            
            return True, "Exposure within limits"
            
        except Exception as e:
            logger.error(f"Error checking exposure limits: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    def check_daily_limits(self) -> tuple[bool, str]:
        """
        Check if daily loss limit has been exceeded.
        
        Returns:
            Tuple of (within_limits: bool, reason: str)
        """
        try:
            daily_pnl = self.daily_tracker.get_daily_pnl()
            
            if daily_pnl <= -self.limits.max_daily_loss:
                if self.limits.emergency_shutdown_enabled:
                    self.trigger_emergency_shutdown()
                return False, f"Daily loss limit ({self.limits.max_daily_loss}) exceeded: {daily_pnl:.2f}"
            
            return True, "Within daily limits"
            
        except Exception as e:
            logger.error(f"Error checking daily limits: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    def validate_risk_reward(self, entry: float, sl: float, tp: float) -> tuple[bool, str]:
        """
        Validate risk/reward ratio meets minimum requirements.
        
        Args:
            entry: Entry price
            sl: Stop loss price
            tp: Take profit price
            
        Returns:
            Tuple of (valid: bool, reason: str)
        """
        try:
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            
            if risk == 0:
                return False, "Risk is zero (invalid SL)"
            
            rr_ratio = reward / risk
            
            if rr_ratio < self.limits.min_risk_reward_ratio:
                return False, f"R:R ratio {rr_ratio:.2f} below minimum {self.limits.min_risk_reward_ratio}"
            
            return True, f"R:R ratio {rr_ratio:.2f} acceptable"
            
        except Exception as e:
            logger.error(f"Error validating risk/reward: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    def check_spread(self, symbol: str) -> tuple[bool, str]:
        """
        Check if current spread is acceptable.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Tuple of (acceptable: bool, reason: str)
        """
        try:
            spread = self.connector.get_spread(symbol)
            
            if spread > self.limits.max_spread_points:
                return False, f"Spread {spread} exceeds limit {self.limits.max_spread_points}"
            
            return True, f"Spread {spread} acceptable"
            
        except Exception as e:
            logger.error(f"Error checking spread: {e}", exc_info=True)
            return True, "Spread check skipped (error)"  # Don't block on error
    
    def update_daily_pnl(self, pnl: float):
        """Update daily P&L tracking."""
        self.daily_tracker.update_pnl(pnl)
        
        # Check if limit exceeded
        self.check_daily_limits()
    
    def reset_daily_tracking(self):
        """Reset daily counters (called at start of trading day)."""
        self.daily_tracker.reset_daily_tracking()
        self.emergency_shutdown_triggered = False
    
    def trigger_emergency_shutdown(self):
        """Trigger emergency shutdown due to excessive losses."""
        self.emergency_shutdown_triggered = True
        logger.critical("EMERGENCY SHUTDOWN TRIGGERED - Daily loss limit exceeded!")
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        Get current risk metrics and status.
        
        Returns:
            Dict with risk metrics
        """
        return {
            'daily_pnl': self.daily_tracker.get_daily_pnl(),
            'daily_trades': self.daily_tracker.get_daily_trades(),
            'total_exposure': self.tracker.calculate_total_exposure(),
            'position_count': self.tracker.get_position_count(),
            'emergency_shutdown': self.emergency_shutdown_triggered,
            'exposure_by_symbol': self.tracker.get_exposure_by_symbol()
        }
    
    def suggest_sl_adjustment(self, balance: float, timeframe: str = "M5") -> float:
        """
        Suggest stop-loss distance based on balance and timeframe.
        
        Consolidated from position/risk_manager.py
        
        Args:
            balance: Account balance
            timeframe: Trading timeframe
            
        Returns:
            Suggested SL distance in points
        """
        try:
            # Base SL by balance tier
            if balance < 500:
                base_sl = 30
            elif balance < 1000:
                base_sl = 50
            elif balance < 5000:
                base_sl = 100
            else:
                base_sl = 150
            
            # Adjust by timeframe
            timeframe_multipliers = {
                "M1": 0.5,
                "M5": 1.0,
                "M15": 1.5,
                "M30": 2.0,
                "H1": 3.0,
                "H4": 5.0,
                "D1": 10.0
            }
            
            multiplier = timeframe_multipliers.get(timeframe, 1.0)
            adjusted_sl = base_sl * multiplier
            
            return adjusted_sl
            
        except Exception as e:
            logger.error(f"Error suggesting SL adjustment: {e}", exc_info=True)
            return 50.0  # Safe default
    
    def recommend_settings(self, balance: float) -> Dict[str, Any]:
        """
        Recommend risk settings based on account balance.
        
        Consolidated from position/risk_manager.py
        
        Args:
            balance: Account balance
            
        Returns:
            Dict with recommended settings
        """
        try:
            if balance < 500:
                return {
                    'mindset': 'conservative',
                    'max_positions': 2,
                    'risk_percent': 1.0,
                    'timeframes': ['M5', 'M15']
                }
            elif balance < 1000:
                return {
                    'mindset': 'balanced',
                    'max_positions': 3,
                    'risk_percent': 2.0,
                    'timeframes': ['M5', 'M15', 'M30']
                }
            elif balance < 5000:
                return {
                    'mindset': 'aggressive',
                    'max_positions': 5,
                    'risk_percent': 3.0,
                    'timeframes': ['M5', 'M15', 'M30', 'H1']
                }
            else:
                return {
                    'mindset': 'ultra_aggressive',
                    'max_positions': 10,
                    'risk_percent': 5.0,
                    'timeframes': ['M1', 'M5', 'M15', 'M30', 'H1']
                }
                
        except Exception as e:
            logger.error(f"Error recommending settings: {e}", exc_info=True)
            return {
                'mindset': 'conservative',
                'max_positions': 2,
                'risk_percent': 1.0,
                'timeframes': ['M15']
            }




