"""
Dynamic Exit Strategy Selection using Argmax

This module implements utility-based exit strategy selection, where each exit
strategy is evaluated based on current position state and market conditions,
and the strategy with highest utility is selected using argmax.

Theoretical Foundation:
- Utility theory: Assign numerical value (utility) to each exit option
- Argmax selection: Choose exit with maximum expected utility
- Multi-objective optimization: Balance profit, risk, time, and opportunity cost

Key Innovation:
Instead of fixed priority (80, 70, 60, 50), dynamically calculate utility scores
based on real-time conditions and select optimal exit via argmax.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from cthulu.exit.coordinator import ExitCoordinator, MarketContext, PositionContext
from cthulu.exit.base import ExitStrategy
from cthulu.exit.exit_manager import ExitDecision


logger = logging.getLogger("Cthulu.dynamic_exit")


@dataclass
class ExitUtility:
    """
    Utility components for exit strategy evaluation.
    
    Each component contributes to overall utility:
    - pnl_component: Potential profit/loss improvement
    - risk_component: Risk reduction (drawdown protection)
    - time_component: Opportunity cost of capital
    - regime_component: Market condition alignment
    - confidence_component: Historical effectiveness
    """
    strategy_name: str
    pnl_component: float = 0.0
    risk_component: float = 0.0
    time_component: float = 0.0
    regime_component: float = 0.0
    confidence_component: float = 0.0
    total_utility: float = 0.0
    
    def calculate_total(self, weights: Dict[str, float]) -> float:
        """
        Calculate weighted total utility.
        
        Args:
            weights: Weight for each component
            
        Returns:
            Total weighted utility
        """
        self.total_utility = (
            weights.get('pnl', 0.3) * self.pnl_component +
            weights.get('risk', 0.3) * self.risk_component +
            weights.get('time', 0.2) * self.time_component +
            weights.get('regime', 0.1) * self.regime_component +
            weights.get('confidence', 0.1) * self.confidence_component
        )
        return self.total_utility


class DynamicExitSelector:
    """
    Dynamic exit strategy selector using argmax over utility scores.
    
    This class evaluates all available exit strategies and selects the one
    with highest utility using argmax, providing dynamic and context-aware
    exit decisions.
    
    Components of Utility:
    
    1. **P&L Component**: Expected profit/loss improvement
       - Positive P&L → higher utility for profit-taking exits
       - Negative P&L → higher utility for stop-loss exits
       - Near target → very high utility for profit target
    
    2. **Risk Component**: Risk reduction potential
       - High unrealized loss → higher utility for stops
       - Low drawdown exposure → lower utility for exits
       - Trailing stop locks in profits → high risk utility
    
    3. **Time Component**: Opportunity cost
       - Long holding time → higher utility for exits
       - Quick moves → lower utility (let it run)
       - Market close approaching → higher utility
    
    4. **Regime Component**: Market condition alignment
       - Volatile markets → favor stops and adverse movement
       - Trending markets → favor trailing stops
       - Ranging markets → favor profit targets
    
    5. **Confidence Component**: Historical effectiveness
       - Track which exits work best in similar conditions
       - Learn from past outcomes
       - Update based on realized results
    
    Example:
        selector = DynamicExitSelector(exit_strategies)
        
        # Evaluate all exits
        best_exit = selector.select_exit(
            position=position_info,
            market_ctx=market_context,
            position_ctx=position_context
        )
        
        if best_exit:
            execute_exit(best_exit)
    """
    
    def __init__(
        self,
        exit_strategies: List[ExitStrategy],
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize dynamic exit selector.
        
        Args:
            exit_strategies: Available exit strategies
            config: Configuration parameters
        """
        self.strategies = {s.name: s for s in exit_strategies}
        self.config = config or {}
        
        # Utility weights
        self.weights = {
            'pnl': self.config.get('pnl_weight', 0.3),
            'risk': self.config.get('risk_weight', 0.3),
            'time': self.config.get('time_weight', 0.2),
            'regime': self.config.get('regime_weight', 0.1),
            'confidence': self.config.get('confidence_weight', 0.1)
        }
        
        # Normalize weights to sum to 1
        weight_sum = sum(self.weights.values())
        self.weights = {k: v/weight_sum for k, v in self.weights.items()}
        
        # Historical performance tracking for confidence
        self.strategy_performance = {
            name: {
                'executions': 0,
                'successes': 0,  # Exit was beneficial
                'total_improvement': 0.0,  # P&L improvement from exit
                'by_regime': {}  # Performance per market regime
            }
            for name in self.strategies.keys()
        }
        
        # Regime-strategy affinity (can be learned or preset)
        self.regime_affinity = self._initialize_regime_affinity()
        
        # Metrics
        self.selection_history = []
        
        logger.info(
            f"DynamicExitSelector initialized: {len(self.strategies)} strategies, "
            f"weights={self.weights}"
        )
    
    def _initialize_regime_affinity(self) -> Dict[str, Dict[str, float]]:
        """
        Initialize strategy-regime affinity scores.
        
        These represent how well each exit strategy performs in different
        market regimes. Can be preset based on domain knowledge or learned
        from data.
        
        Returns:
            Dictionary mapping strategy -> regime -> affinity score
        """
        return {
            'StopLoss': {
                'trending': 0.6,
                'ranging': 0.7,
                'volatile': 0.9,  # Very important in volatile markets
                'consolidating': 0.5,
            },
            'TrailingStop': {
                'trending': 0.95,  # Excellent for trends
                'ranging': 0.4,
                'volatile': 0.6,
                'consolidating': 0.3,
            },
            'TakeProfit': {
                'trending': 0.5,
                'ranging': 0.9,  # Great for range-bound
                'volatile': 0.7,
                'consolidating': 0.8,
            },
            'TimeBasedExit': {
                'trending': 0.4,
                'ranging': 0.6,
                'volatile': 0.5,
                'consolidating': 0.7,
            },
            'ProfitTargetExit': {
                'trending': 0.6,
                'ranging': 0.9,
                'volatile': 0.7,
                'consolidating': 0.8,
            },
            'AdverseMovementExit': {
                'trending': 0.5,
                'ranging': 0.6,
                'volatile': 0.95,  # Critical for adverse moves
                'consolidating': 0.4,
            }
        }
    
    def calculate_utility(
        self,
        strategy: ExitStrategy,
        position_ctx: PositionContext,
        market_ctx: MarketContext,
        current_data: Dict[str, Any]
    ) -> ExitUtility:
        """
        Calculate utility components for an exit strategy.
        
        Args:
            strategy: Exit strategy to evaluate
            position_ctx: Current position state
            market_ctx: Current market conditions
            current_data: Current market data
            
        Returns:
            ExitUtility with all components calculated
        """
        utility = ExitUtility(strategy_name=strategy.name)
        
        # 1. P&L Component
        utility.pnl_component = self._calculate_pnl_utility(
            strategy, position_ctx, current_data
        )
        
        # 2. Risk Component
        utility.risk_component = self._calculate_risk_utility(
            strategy, position_ctx, market_ctx
        )
        
        # 3. Time Component
        utility.time_component = self._calculate_time_utility(
            strategy, position_ctx, market_ctx
        )
        
        # 4. Regime Component
        utility.regime_component = self._calculate_regime_utility(
            strategy, market_ctx
        )
        
        # 5. Confidence Component
        utility.confidence_component = self._calculate_confidence_utility(
            strategy, market_ctx
        )
        
        # Calculate total weighted utility
        utility.calculate_total(self.weights)
        
        return utility
    
    def _calculate_pnl_utility(
        self,
        strategy: ExitStrategy,
        position_ctx: PositionContext,
        current_data: Dict[str, Any]
    ) -> float:
        """
        Calculate P&L-based utility.
        
        Logic:
        - In profit: Favor profit-taking exits (trailing stop, profit target)
        - In loss: Favor protective exits (stop loss, adverse movement)
        - Near targets: Very high utility for target exits
        
        Returns:
            P&L utility score (0-1)
        """
        pnl_pct = position_ctx.unrealized_pnl_percent
        
        # Profit-taking strategies
        if 'profit' in strategy.name.lower() or 'trailing' in strategy.name.lower():
            if pnl_pct > 0:
                # Higher profit → higher utility
                utility = min(1.0, (pnl_pct / 5.0))  # Scale to 0-1 (5% = max)
                
                # Bonus if near maximum favorable excursion
                if position_ctx.max_favorable_excursion > 0:
                    current_ratio = pnl_pct / position_ctx.max_favorable_excursion
                    if current_ratio < 0.8:  # Retreating from peak
                        utility += 0.3  # Urgency to lock in profits
                
                return np.clip(utility, 0.0, 1.0)
            else:
                return 0.1  # Low utility when in loss
        
        # Loss-cutting strategies
        elif 'stop' in strategy.name.lower() or 'adverse' in strategy.name.lower():
            if pnl_pct < 0:
                # Higher loss → higher utility
                utility = min(1.0, abs(pnl_pct) / 5.0)
                
                # Bonus if loss is significant
                if pnl_pct < -2.0:
                    utility += 0.2
                
                return np.clip(utility, 0.0, 1.0)
            else:
                return 0.2  # Some utility even in profit (protection)
        
        # Time-based or other
        else:
            # Moderate utility, slightly favor exits when in profit
            return 0.5 + 0.1 * np.sign(pnl_pct)
    
    def _calculate_risk_utility(
        self,
        strategy: ExitStrategy,
        position_ctx: PositionContext,
        market_ctx: MarketContext
    ) -> float:
        """
        Calculate risk-based utility.
        
        Logic:
        - High volatility → higher utility for protective stops
        - Near stop loss → very high utility for exits
        - Trailing stops lock in profits → high risk utility
        
        Returns:
            Risk utility score (0-1)
        """
        utility = 0.5  # Base
        
        # Volatility factor
        if market_ctx.volatility > 0.02:  # High volatility
            if 'stop' in strategy.name.lower():
                utility += 0.3
        
        # Drawdown exposure
        if position_ctx.max_adverse_excursion > 0:
            drawdown_ratio = abs(position_ctx.max_adverse_excursion) / 100  # Normalize
            
            if 'stop' in strategy.name.lower() or 'adverse' in strategy.name.lower():
                utility += min(0.4, drawdown_ratio * 2.0)
        
        # Trailing stop special case (locks in profits)
        if 'trailing' in strategy.name.lower() and position_ctx.is_in_profit:
            utility += 0.3
        
        # News event or market close
        if market_ctx.is_news_event or market_ctx.is_market_close:
            utility += 0.2  # Higher utility for any exit
        
        return np.clip(utility, 0.0, 1.0)
    
    def _calculate_time_utility(
        self,
        strategy: ExitStrategy,
        position_ctx: PositionContext,
        market_ctx: MarketContext
    ) -> float:
        """
        Calculate time-based utility (opportunity cost).
        
        Logic:
        - Longer holding time → higher utility for time-based exits
        - Quick moves → lower utility (let winners run)
        - Market session changes → moderate utility
        
        Returns:
            Time utility score (0-1)
        """
        holding_hours = position_ctx.holding_time_minutes / 60.0
        
        # Time-based exit strategies
        if 'time' in strategy.name.lower():
            # Linear increase with holding time
            utility = min(1.0, holding_hours / 24.0)  # Max at 24 hours
            
            # Bonus for very long holds
            if holding_hours > 48:
                utility += 0.2
            
            return np.clip(utility, 0.0, 1.0)
        
        # Other strategies: moderate time penalty
        else:
            # Slight increase with time for all exits
            time_penalty = min(0.3, holding_hours / 48.0)
            
            # But decrease if position is moving favorably quickly
            if position_ctx.unrealized_pnl_percent > 0 and holding_hours < 2:
                time_penalty -= 0.2  # Let winners run
            
            return np.clip(0.5 + time_penalty, 0.0, 1.0)
    
    def _calculate_regime_utility(
        self,
        strategy: ExitStrategy,
        market_ctx: MarketContext
    ) -> float:
        """
        Calculate market regime-based utility.
        
        Uses pre-defined (or learned) affinity scores for each
        strategy-regime combination.
        
        Returns:
            Regime utility score (0-1)
        """
        # Determine regime (simplified)
        if market_ctx.trend_strength > 0.7:
            regime = 'trending'
        elif market_ctx.trend_strength < 0.3:
            regime = 'ranging'
        elif market_ctx.volatility > 0.02:
            regime = 'volatile'
        else:
            regime = 'consolidating'
        
        # Get affinity score
        strategy_affinities = self.regime_affinity.get(strategy.name, {})
        affinity = strategy_affinities.get(regime, 0.5)  # Default: neutral
        
        return affinity
    
    def _calculate_confidence_utility(
        self,
        strategy: ExitStrategy,
        market_ctx: MarketContext
    ) -> float:
        """
        Calculate confidence-based utility from historical performance.
        
        Learns which exit strategies have been most effective in similar
        conditions.
        
        Returns:
            Confidence utility score (0-1)
        """
        perf = self.strategy_performance.get(strategy.name, {})
        
        if perf['executions'] == 0:
            return 0.5  # Neutral for untested
        
        # Overall success rate
        success_rate = perf['successes'] / perf['executions']
        
        # Average improvement from this exit
        avg_improvement = perf['total_improvement'] / perf['executions']
        
        # Combine (favor success rate more)
        confidence = 0.7 * success_rate + 0.3 * min(1.0, avg_improvement / 2.0)
        
        return np.clip(confidence, 0.0, 1.0)
    
    def select_exit(
        self,
        position: Any,  # PositionInfo
        market_ctx: MarketContext,
        position_ctx: PositionContext,
        current_data: Dict[str, Any]
    ) -> Optional[Tuple[ExitStrategy, ExitUtility]]:
        """
        Select best exit strategy using argmax over utility scores.
        
        This is the core method that implements argmax-based exit selection.
        
        Args:
            position: Position information
            market_ctx: Market context
            position_ctx: Position context
            current_data: Current market data
            
        Returns:
            Tuple of (selected_strategy, utility) or None if no exit warranted
        """
        # Calculate utilities for all strategies
        utilities = {}
        
        for name, strategy in self.strategies.items():
            utility = self.calculate_utility(
                strategy=strategy,
                position_ctx=position_ctx,
                market_ctx=market_ctx,
                current_data=current_data
            )
            utilities[name] = utility
        
        # ARGMAX: Select strategy with highest utility
        best_strategy_name = max(
            utilities.keys(),
            key=lambda name: utilities[name].total_utility
        )
        
        best_utility = utilities[best_strategy_name]
        best_strategy = self.strategies[best_strategy_name]
        
        # Log selection reasoning
        logger.info(
            f"Exit selection (argmax): {best_strategy_name} "
            f"(utility={best_utility.total_utility:.3f}, "
            f"pnl={best_utility.pnl_component:.3f}, "
            f"risk={best_utility.risk_component:.3f}, "
            f"time={best_utility.time_component:.3f})"
        )
        
        # Log other options for transparency
        for name, util in sorted(
            utilities.items(),
            key=lambda x: x[1].total_utility,
            reverse=True
        )[1:]:  # Skip best (already logged)
            logger.debug(
                f"  {name}: utility={util.total_utility:.3f}"
            )
        
        # Record selection
        self.selection_history.append({
            'timestamp': datetime.now(),
            'selected_strategy': best_strategy_name,
            'utility': best_utility.total_utility,
            'all_utilities': {name: u.total_utility for name, u in utilities.items()},
            'position_pnl': position_ctx.unrealized_pnl_percent
        })
        
        # Only execute if utility exceeds threshold
        min_utility_threshold = self.config.get('min_utility_threshold', 0.6)
        
        if best_utility.total_utility >= min_utility_threshold:
            return best_strategy, best_utility
        else:
            logger.debug(
                f"No exit: best utility {best_utility.total_utility:.3f} "
                f"below threshold {min_utility_threshold}"
            )
            return None
    
    def update_performance(
        self,
        strategy_name: str,
        was_beneficial: bool,
        pnl_improvement: float,
        regime: str
    ):
        """
        Update historical performance after exit execution.
        
        Args:
            strategy_name: Name of exit strategy used
            was_beneficial: Whether the exit improved outcome
            pnl_improvement: How much P&L improved (or worsened)
            regime: Market regime during exit
        """
        if strategy_name not in self.strategy_performance:
            return
        
        perf = self.strategy_performance[strategy_name]
        
        # Update overall stats
        perf['executions'] += 1
        if was_beneficial:
            perf['successes'] += 1
        perf['total_improvement'] += pnl_improvement
        
        # Update regime-specific stats
        if regime not in perf['by_regime']:
            perf['by_regime'][regime] = {
                'executions': 0,
                'successes': 0,
                'total_improvement': 0.0
            }
        
        regime_perf = perf['by_regime'][regime]
        regime_perf['executions'] += 1
        if was_beneficial:
            regime_perf['successes'] += 1
        regime_perf['total_improvement'] += pnl_improvement
        
        logger.info(
            f"Updated {strategy_name} performance: "
            f"success_rate={perf['successes']/perf['executions']:.2%}, "
            f"avg_improvement={perf['total_improvement']/perf['executions']:.2f}"
        )
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get detailed performance report for all exit strategies.
        
        Returns:
            Dictionary with performance metrics
        """
        report = {}
        
        for name, perf in self.strategy_performance.items():
            if perf['executions'] == 0:
                continue
            
            report[name] = {
                'executions': perf['executions'],
                'success_rate': perf['successes'] / perf['executions'],
                'avg_improvement': perf['total_improvement'] / perf['executions'],
                'by_regime': {}
            }
            
            for regime, regime_perf in perf['by_regime'].items():
                if regime_perf['executions'] > 0:
                    report[name]['by_regime'][regime] = {
                        'executions': regime_perf['executions'],
                        'success_rate': regime_perf['successes'] / regime_perf['executions'],
                        'avg_improvement': regime_perf['total_improvement'] / regime_perf['executions']
                    }
        
        return report
