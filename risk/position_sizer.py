"""
Position Sizing Optimization using Argmax

This module implements argmax-based position sizing selection from discrete
Kelly Criterion variants. Instead of using a single Kelly fraction, it
evaluates multiple size options and selects the optimal one using argmax
over expected utility.

Theoretical Foundation:
- Kelly Criterion: Optimal bet sizing to maximize geometric growth
- Discrete optimization: Evaluate finite set of position sizes
- Utility maximization: Balance return vs risk
- Argmax selection: Choose size with highest expected utility

Key Innovation:
Traditional Kelly uses continuous optimization. We use discrete candidates
and argmax selection, which is:
1. More robust to estimation errors
2. Easier to constrain (min/max sizes)
3. Compatible with bandit-style learning
4. Adaptable to market conditions
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import deque

logger = logging.getLogger("Cthulu.position_sizer")


@dataclass
class PositionSizeCandidate:
    """
    Candidate position size with utility metrics.
    
    Attributes:
        size_pct: Position size as % of capital (e.g., 0.02 = 2%)
        expected_return: Expected return for this size
        expected_risk: Expected risk (variance or std dev)
        utility: Total utility score
        kelly_fraction: Kelly fraction used (if applicable)
        adjustment_factor: Any adjustments applied
        metadata: Additional information
    """
    size_pct: float
    expected_return: float = 0.0
    expected_risk: float = 0.0
    utility: float = 0.0
    kelly_fraction: Optional[float] = None
    adjustment_factor: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class PositionSizingOptimizer:
    """
    Position sizing optimizer using argmax over discrete Kelly variants.
    
    This class implements sophisticated position sizing by:
    1. Calculating Kelly Criterion from win rate and win/loss ratio
    2. Generating discrete size candidates (full Kelly, half Kelly, quarter Kelly, etc.)
    3. Calculating utility for each candidate (return vs risk tradeoff)
    4. Selecting optimal size using argmax over utilities
    
    Kelly Criterion Formula:
        f* = (p * b - q) / b
    
    Where:
        - f*: Optimal fraction of capital to risk
        - p: Win probability
        - q: Loss probability (1 - p)
        - b: Win/loss ratio (avg_win / avg_loss)
    
    Discrete Variants:
        - Full Kelly: f*
        - Half Kelly: f* / 2 (more conservative, less volatility)
        - Quarter Kelly: f* / 4 (very conservative)
        - Fixed sizes: 0.5%, 1%, 2%, 5% (for comparison)
    
    Example Usage:
        optimizer = PositionSizingOptimizer(
            win_rate=0.55,
            avg_win=150.0,
            avg_loss=100.0,
            account_balance=10000.0
        )
        
        # Get optimal position size
        optimal_size = optimizer.select_size(
            signal_confidence=0.8,
            market_volatility=0.02,
            current_exposure=0.05
        )
        
        print(f"Optimal size: {optimal_size.size_pct:.2%}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize position sizing optimizer.
        
        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        
        # Statistical parameters (can be updated)
        self.win_rate = self.config.get('win_rate', 0.5)
        self.avg_win = self.config.get('avg_win', 100.0)
        self.avg_loss = self.config.get('avg_loss', 100.0)
        
        # Risk parameters
        self.max_size = self.config.get('max_size', 0.10)  # 10% max
        self.min_size = self.config.get('min_size', 0.005)  # 0.5% min
        self.risk_aversion = self.config.get('risk_aversion', 2.0)  # Higher = more conservative
        
        # Utility weights
        self.return_weight = self.config.get('return_weight', 0.6)
        self.risk_weight = self.config.get('risk_weight', 0.4)
        
        # Discrete size candidates to evaluate
        self.size_candidates = self._generate_candidates()
        
        # Performance tracking
        self.size_performance: Dict[float, Dict[str, Any]] = {}
        self.selection_history = []
        
        logger.info(
            f"PositionSizingOptimizer initialized: "
            f"win_rate={self.win_rate:.2%}, "
            f"avg_win={self.avg_win:.2f}, "
            f"avg_loss={self.avg_loss:.2f}"
        )
    
    def _generate_candidates(self) -> List[float]:
        """
        Generate discrete position size candidates.
        
        Returns:
            List of position sizes (as fractions of capital)
        """
        candidates = []
        
        # Calculate Kelly fraction
        kelly = self.calculate_kelly()
        
        # Kelly variants
        if kelly > 0:
            candidates.extend([
                kelly,  # Full Kelly
                kelly * 0.75,  # 3/4 Kelly
                kelly * 0.5,  # Half Kelly
                kelly * 0.25,  # Quarter Kelly
            ])
        
        # Fixed sizes
        candidates.extend([
            0.005,  # 0.5%
            0.01,   # 1%
            0.02,   # 2%
            0.05,   # 5%
            0.10,   # 10%
        ])
        
        # Filter by min/max
        candidates = [
            c for c in candidates
            if self.min_size <= c <= self.max_size
        ]
        
        # Remove duplicates and sort
        candidates = sorted(set(candidates))
        
        logger.debug(f"Generated {len(candidates)} size candidates: {candidates}")
        
        return candidates
    
    def calculate_kelly(self) -> float:
        """
        Calculate Kelly Criterion optimal fraction.
        
        Formula:
            f* = (p * b - q) / b
        
        Where:
            - p: win probability
            - q: loss probability (1 - p)
            - b: win/loss ratio
        
        Returns:
            Kelly fraction (0-1)
        """
        if self.avg_loss == 0:
            return 0.0
        
        p = self.win_rate
        q = 1 - p
        b = self.avg_win / self.avg_loss
        
        kelly = (p * b - q) / b
        
        # Kelly can be negative (unfavorable odds) or > 1
        kelly = np.clip(kelly, 0.0, 1.0)
        
        logger.debug(f"Kelly fraction: {kelly:.3f} (p={p:.2f}, b={b:.2f})")
        
        return kelly
    
    def calculate_expected_return(self, size_pct: float) -> float:
        """
        Calculate expected return for a position size.
        
        Expected Return = p * win * size - q * loss * size
        
        Args:
            size_pct: Position size as fraction of capital
            
        Returns:
            Expected return (absolute value)
        """
        p = self.win_rate
        q = 1 - p
        
        expected_return = p * self.avg_win * size_pct - q * self.avg_loss * size_pct
        
        return expected_return
    
    def calculate_expected_risk(self, size_pct: float) -> float:
        """
        Calculate expected risk (variance) for a position size.
        
        Variance = E[X²] - (E[X])²
        
        Where X is the return from a single trade.
        
        Args:
            size_pct: Position size as fraction of capital
            
        Returns:
            Expected risk (variance)
        """
        p = self.win_rate
        q = 1 - p
        
        # Expected value
        ev = self.calculate_expected_return(size_pct)
        
        # E[X²]
        win_squared = (self.avg_win * size_pct) ** 2
        loss_squared = (self.avg_loss * size_pct) ** 2
        e_x_squared = p * win_squared + q * loss_squared
        
        # Variance
        variance = e_x_squared - (ev ** 2)
        
        return max(0, variance)  # Ensure non-negative
    
    def calculate_utility(
        self,
        size_pct: float,
        signal_confidence: float = 0.5,
        market_volatility: float = 0.01,
        current_exposure: float = 0.0
    ) -> float:
        """
        Calculate utility for a position size.
        
        Utility balances expected return against risk, adjusted for
        current market conditions and existing exposure.
        
        Components:
        1. Expected return (positive)
        2. Risk penalty (negative, scaled by risk aversion)
        3. Confidence adjustment
        4. Volatility adjustment
        5. Exposure penalty (avoid over-concentration)
        
        Args:
            size_pct: Position size as fraction
            signal_confidence: Confidence in signal (0-1)
            market_volatility: Current market volatility
            current_exposure: Current total exposure
            
        Returns:
            Total utility score
        """
        # Base components
        expected_return = self.calculate_expected_return(size_pct)
        expected_risk = self.calculate_expected_risk(size_pct)
        
        # Utility = Return - (Risk_Aversion * Risk)
        base_utility = (
            self.return_weight * expected_return -
            self.risk_weight * self.risk_aversion * np.sqrt(expected_risk)
        )
        
        # Confidence adjustment
        # Lower confidence → prefer smaller sizes
        confidence_factor = 0.5 + 0.5 * signal_confidence
        
        # Volatility adjustment
        # Higher volatility → prefer smaller sizes
        vol_factor = 1.0 / (1.0 + 10 * market_volatility)
        
        # Exposure penalty
        # Higher current exposure → prefer smaller additions
        total_exposure = current_exposure + size_pct
        if total_exposure > self.max_size:
            exposure_penalty = -10.0 * (total_exposure - self.max_size)
        else:
            exposure_penalty = 0.0
        
        # Total utility
        utility = base_utility * confidence_factor * vol_factor + exposure_penalty
        
        return utility
    
    def select_size(
        self,
        signal_confidence: float = 0.5,
        market_volatility: float = 0.01,
        current_exposure: float = 0.0,
        market_regime: Optional[str] = None
    ) -> PositionSizeCandidate:
        """
        Select optimal position size using argmax over utilities.
        
        This is the core method that implements argmax-based size selection.
        
        Args:
            signal_confidence: Confidence in trading signal (0-1)
            market_volatility: Current market volatility
            current_exposure: Current total position exposure
            market_regime: Current market regime
            
        Returns:
            Optimal position size candidate
        """
        # Calculate utility for each candidate
        candidates = []
        
        for size in self.size_candidates:
            utility = self.calculate_utility(
                size_pct=size,
                signal_confidence=signal_confidence,
                market_volatility=market_volatility,
                current_exposure=current_exposure
            )
            
            candidate = PositionSizeCandidate(
                size_pct=size,
                expected_return=self.calculate_expected_return(size),
                expected_risk=self.calculate_expected_risk(size),
                utility=utility,
                kelly_fraction=self.calculate_kelly(),
                metadata={
                    'signal_confidence': signal_confidence,
                    'market_volatility': market_volatility,
                    'current_exposure': current_exposure,
                    'market_regime': market_regime
                }
            )
            
            candidates.append(candidate)
            
            logger.debug(
                f"Size {size:.3%}: utility={utility:.3f}, "
                f"return={candidate.expected_return:.2f}, "
                f"risk={candidate.expected_risk:.2f}"
            )
        
        # ARGMAX: Select candidate with highest utility
        optimal = max(candidates, key=lambda c: c.utility)
        
        logger.info(
            f"Selected position size: {optimal.size_pct:.2%} "
            f"(utility={optimal.utility:.3f}, "
            f"kelly={optimal.kelly_fraction:.3f})"
        )
        
        # Record selection
        self.selection_history.append({
            'timestamp': datetime.now(),
            'selected_size': optimal.size_pct,
            'utility': optimal.utility,
            'all_candidates': [(c.size_pct, c.utility) for c in candidates],
            'signal_confidence': signal_confidence,
            'market_volatility': market_volatility
        })
        
        return optimal
    
    def update_statistics(
        self,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None
    ):
        """
        Update statistical parameters based on recent performance.
        
        This should be called periodically to adapt to changing conditions.
        
        Args:
            win_rate: New win rate (if available)
            avg_win: New average win (if available)
            avg_loss: New average loss (if available)
        """
        if win_rate is not None:
            self.win_rate = win_rate
        if avg_win is not None:
            self.avg_win = avg_win
        if avg_loss is not None:
            self.avg_loss = avg_loss
        
        # Regenerate candidates with new parameters
        self.size_candidates = self._generate_candidates()
        
        logger.info(
            f"Updated statistics: win_rate={self.win_rate:.2%}, "
            f"avg_win={self.avg_win:.2f}, avg_loss={self.avg_loss:.2f}"
        )
    
    def update_performance(
        self,
        size_used: float,
        actual_return: float,
        was_win: bool
    ):
        """
        Update performance tracking for a position size.
        
        Args:
            size_used: Position size that was used
            actual_return: Actual return achieved
            was_win: Whether trade was a win
        """
        if size_used not in self.size_performance:
            self.size_performance[size_used] = {
                'uses': 0,
                'wins': 0,
                'total_return': 0.0,
                'returns': deque(maxlen=50)
            }
        
        perf = self.size_performance[size_used]
        perf['uses'] += 1
        if was_win:
            perf['wins'] += 1
        perf['total_return'] += actual_return
        perf['returns'].append(actual_return)
        
        logger.debug(
            f"Updated performance for size {size_used:.2%}: "
            f"win_rate={perf['wins']/perf['uses']:.2%}, "
            f"avg_return={perf['total_return']/perf['uses']:.2f}"
        )
    
    def get_size_rankings(self) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Get position sizes ranked by historical performance.
        
        Returns:
            List of (size, metrics) tuples, sorted by performance
        """
        rankings = []
        
        for size, perf in self.size_performance.items():
            if perf['uses'] == 0:
                continue
            
            win_rate = perf['wins'] / perf['uses']
            avg_return = perf['total_return'] / perf['uses']
            
            # Performance score (combination of win rate and returns)
            score = 0.5 * win_rate + 0.5 * (avg_return / 100.0)  # Normalize return
            
            rankings.append((
                size,
                {
                    'uses': perf['uses'],
                    'win_rate': win_rate,
                    'avg_return': avg_return,
                    'score': score
                }
            ))
        
        # Sort by score descending
        rankings.sort(key=lambda x: x[1]['score'], reverse=True)
        
        return rankings
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive performance report.
        
        Returns:
            Dictionary with detailed statistics
        """
        return {
            'current_parameters': {
                'win_rate': self.win_rate,
                'avg_win': self.avg_win,
                'avg_loss': self.avg_loss,
                'kelly_fraction': self.calculate_kelly()
            },
            'size_candidates': self.size_candidates,
            'size_performance': {
                f"{size:.2%}": {
                    'uses': perf['uses'],
                    'win_rate': perf['wins'] / perf['uses'] if perf['uses'] > 0 else 0,
                    'avg_return': perf['total_return'] / perf['uses'] if perf['uses'] > 0 else 0
                }
                for size, perf in self.size_performance.items()
            },
            'total_selections': len(self.selection_history)
        }


class AdaptivePositionSizer(PositionSizingOptimizer):
    """
    Adaptive position sizer with online learning.
    
    Continuously updates win rate and win/loss ratios based on recent
    performance, using exponential moving average.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Adaptive parameters
        self.alpha = self.config.get('learning_rate', 0.1)  # EMA smoothing
        self.recent_trades = deque(maxlen=100)  # Recent trade outcomes
    
    def record_trade_outcome(
        self,
        size_used: float,
        pnl: float,
        was_win: bool
    ):
        """
        Record trade outcome and update statistics adaptively.
        
        Args:
            size_used: Position size that was used
            pnl: Profit/loss from trade
            was_win: Whether trade was profitable
        """
        # Record trade
        self.recent_trades.append({
            'size': size_used,
            'pnl': pnl,
            'was_win': was_win
        })
        
        # Update parent performance tracking
        self.update_performance(size_used, pnl, was_win)
        
        # Recalculate statistics from recent trades
        if len(self.recent_trades) >= 10:  # Need minimum data
            wins = [t for t in self.recent_trades if t['was_win']]
            losses = [t for t in self.recent_trades if not t['was_win']]
            
            # Update win rate (EMA)
            new_win_rate = len(wins) / len(self.recent_trades)
            self.win_rate = (
                self.alpha * new_win_rate +
                (1 - self.alpha) * self.win_rate
            )
            
            # Update avg win/loss (EMA)
            if wins:
                new_avg_win = np.mean([abs(t['pnl']) for t in wins])
                self.avg_win = (
                    self.alpha * new_avg_win +
                    (1 - self.alpha) * self.avg_win
                )
            
            if losses:
                new_avg_loss = np.mean([abs(t['pnl']) for t in losses])
                self.avg_loss = (
                    self.alpha * new_avg_loss +
                    (1 - self.alpha) * self.avg_loss
                )
            
            # Regenerate candidates with updated stats
            self.size_candidates = self._generate_candidates()
            
            logger.debug(
                f"Adaptive update: win_rate={self.win_rate:.2%}, "
                f"avg_win={self.avg_win:.2f}, avg_loss={self.avg_loss:.2f}"
            )
