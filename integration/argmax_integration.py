"""
Argmax Integration Layer

This module provides a unified interface for integrating all argmax-based
optimization components into the Cthulu trading system. It replaces legacy
logic while maintaining backward compatibility and zero-error status.

Components integrated:
1. BanditSelector - Replaces weighted strategy selection
2. DynamicExitSelector - Replaces fixed-priority exits
3. SignalAggregator - Replaces simple indicator voting
4. PositionSizingOptimizer - Replaces fixed position sizing
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Import argmax components
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.bandit_selector import BanditSelector
from exit.dynamic_selector import DynamicExitSelector, ExitUtility
from indicators.signal_aggregator import SignalAggregator, IndicatorSignal, AdaptiveSignalAggregator
from risk.position_sizer import PositionSizingOptimizer, AdaptivePositionSizer
from strategy.base import Strategy, Signal

logger = logging.getLogger("Cthulu.argmax_integration")


class ArgmaxTradingEngine:
    """
    Unified argmax-based trading engine.
    
    This class integrates all four argmax components and provides a single
    interface for the trading system. It manages the complete decision pipeline:
    
    1. Signal Generation → SignalAggregator
    2. Strategy Selection → BanditSelector
    3. Position Sizing → PositionSizingOptimizer
    4. Exit Management → DynamicExitSelector
    
    Maintains comprehensive metrics for monitoring and observability.
    """
    
    def __init__(
        self,
        strategies: List[Strategy],
        exit_strategies: List[Any],
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize argmax trading engine.
        
        Args:
            strategies: Available trading strategies
            exit_strategies: Available exit strategies
            config: Configuration parameters
        """
        self.config = config or {}
        self.logger = logging.getLogger("Cthulu.argmax_engine")
        
        # Initialize components
        self.strategy_selector = BanditSelector(
            strategies=strategies,
            algorithm=self.config.get('bandit_algorithm', 'ucb'),
            config=self.config.get('bandit_config', {})
        )
        
        self.signal_aggregator = AdaptiveSignalAggregator(
            config=self.config.get('aggregator_config', {})
        )
        
        self.position_sizer = AdaptivePositionSizer(
            config=self.config.get('sizing_config', {})
        )
        
        self.exit_selector = DynamicExitSelector(
            exit_strategies=exit_strategies,
            config=self.config.get('exit_config', {})
        )
        
        # Metrics tracking
        self.metrics = {
            'total_decisions': 0,
            'strategy_selections': {},
            'exit_selections': {},
            'signal_aggregations': 0,
            'position_sizes': [],
            'last_update': datetime.now()
        }
        
        self.logger.info("ArgmaxTradingEngine initialized with all components")
    
    def generate_trading_signal(
        self,
        indicator_signals: List[IndicatorSignal],
        market_data: Dict[str, Any],
        market_regime: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate trading signal using argmax-based decision pipeline.
        
        Pipeline:
        1. Aggregate indicator signals using argmax
        2. Select strategy using multi-armed bandit
        3. Calculate optimal position size using argmax over Kelly variants
        
        Args:
            indicator_signals: Signals from technical indicators
            market_data: Current market data
            market_regime: Current market regime
            
        Returns:
            Dictionary with signal, strategy, and position size, or None
        """
        # Step 1: Aggregate signals
        for signal in indicator_signals:
            self.signal_aggregator.add_signal(signal)
        
        consensus_signal = self.signal_aggregator.aggregate(
            method='argmax_weighted',
            market_regime=market_regime
        )
        
        if not consensus_signal:
            self.logger.debug("No consensus signal from aggregation")
            return None
        
        self.metrics['signal_aggregations'] += 1
        
        # Step 2: Select strategy
        strategy = self.strategy_selector.select_strategy(
            context={'regime': market_regime}
        )
        
        strategy_name = strategy.name
        self.metrics['strategy_selections'][strategy_name] = \
            self.metrics['strategy_selections'].get(strategy_name, 0) + 1
        
        # Step 3: Calculate position size
        volatility = market_data.get('atr', 0) / market_data.get('close', 1)
        current_exposure = market_data.get('current_exposure', 0.0)
        
        optimal_size = self.position_sizer.select_size(
            signal_confidence=consensus_signal.confidence,
            market_volatility=volatility,
            current_exposure=current_exposure,
            market_regime=market_regime
        )
        
        self.metrics['position_sizes'].append(optimal_size.size_pct)
        self.metrics['total_decisions'] += 1
        
        return {
            'signal': consensus_signal,
            'strategy': strategy,
            'strategy_name': strategy_name,
            'position_size': optimal_size.size_pct,
            'position_utility': optimal_size.utility,
            'kelly_fraction': optimal_size.kelly_fraction,
            'indicators_used': [s.indicator_name for s in indicator_signals],
            'aggregation_method': consensus_signal.metadata.get('aggregation_method'),
            'timestamp': datetime.now()
        }
    
    def evaluate_exit(
        self,
        position: Any,
        market_ctx: Any,
        position_ctx: Any,
        current_data: Dict[str, Any]
    ) -> Optional[Tuple[Any, ExitUtility]]:
        """
        Evaluate if position should be exited using dynamic argmax selection.
        
        Args:
            position: Position information
            market_ctx: Market context
            position_ctx: Position context
            current_data: Current market data
            
        Returns:
            Tuple of (exit_strategy, utility) or None if hold
        """
        result = self.exit_selector.select_exit(
            position=position,
            market_ctx=market_ctx,
            position_ctx=position_ctx,
            current_data=current_data
        )
        
        if result:
            exit_strategy, utility = result
            exit_name = exit_strategy.name
            self.metrics['exit_selections'][exit_name] = \
                self.metrics['exit_selections'].get(exit_name, 0) + 1
            
            self.logger.info(
                f"Exit selected: {exit_name} (utility={utility.total_utility:.3f})"
            )
        
        return result
    
    def update_after_trade(
        self,
        strategy_name: str,
        pnl: float,
        success: bool,
        signal_type: Any,
        indicators_used: List[str],
        position_size: float,
        market_regime: str
    ):
        """
        Update all components with trade outcome.
        
        This is critical for learning - must be called after each trade.
        
        Args:
            strategy_name: Strategy that was used
            pnl: Trade profit/loss
            success: Whether trade was profitable
            signal_type: Type of signal (LONG/SHORT)
            indicators_used: List of indicators that contributed
            position_size: Position size that was used
            market_regime: Market regime during trade
        """
        # Update strategy selector
        self.strategy_selector.update_reward(
            strategy_name=strategy_name,
            reward=pnl,
            success=success
        )
        
        # Update signal aggregator
        for indicator in indicators_used:
            self.signal_aggregator.update_performance(
                indicator_name=indicator,
                signal_type=signal_type,
                was_correct=success,
                market_regime=market_regime
            )
        
        # Update position sizer
        self.position_sizer.record_trade_outcome(
            size_used=position_size,
            pnl=pnl,
            was_win=success
        )
        
        self.logger.info(
            f"Updated all components: strategy={strategy_name}, "
            f"pnl={pnl:.2f}, success={success}"
        )
    
    def update_exit_performance(
        self,
        exit_name: str,
        was_beneficial: bool,
        pnl_improvement: float,
        regime: str
    ):
        """
        Update exit selector performance.
        
        Args:
            exit_name: Exit strategy that was used
            was_beneficial: Whether exit improved outcome
            pnl_improvement: How much P&L improved
            regime: Market regime during exit
        """
        self.exit_selector.update_performance(
            strategy_name=exit_name,
            was_beneficial=was_beneficial,
            pnl_improvement=pnl_improvement,
            regime=regime
        )
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics from all argmax components.
        
        Returns metrics suitable for monitoring/observability systems.
        
        Returns:
            Dictionary with detailed metrics
        """
        metrics = {
            'engine': {
                'total_decisions': self.metrics['total_decisions'],
                'signal_aggregations': self.metrics['signal_aggregations'],
                'strategy_selections': self.metrics['strategy_selections'],
                'exit_selections': self.metrics['exit_selections'],
                'avg_position_size': sum(self.metrics['position_sizes']) / len(self.metrics['position_sizes']) 
                    if self.metrics['position_sizes'] else 0.0,
                'last_update': self.metrics['last_update'].isoformat()
            },
            'bandit_selector': self.strategy_selector.get_statistics(),
            'signal_aggregator': self.signal_aggregator.get_performance_report(),
            'position_sizer': self.position_sizer.get_performance_report(),
            'exit_selector': self.exit_selector.get_performance_report()
        }
        
        return metrics
    
    def get_csv_row(self) -> Dict[str, Any]:
        """
        Get current state as CSV row for metrics.csv.
        
        Returns:
            Dictionary suitable for CSV export
        """
        stats = self.strategy_selector.get_statistics()
        best_strategy, best_reward = self.strategy_selector.get_best_strategy()
        
        size_perf = self.position_sizer.get_performance_report()
        kelly = size_perf['current_parameters']['kelly_fraction']
        
        # Get indicator rankings
        indicator_rankings = self.signal_aggregator.get_indicator_rankings()
        best_indicator = indicator_rankings[0][0] if indicator_rankings else 'none'
        best_indicator_score = indicator_rankings[0][1] if indicator_rankings else 0.0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_decisions': self.metrics['total_decisions'],
            'best_strategy': best_strategy or 'none',
            'best_strategy_reward': best_reward,
            'bandit_algorithm': stats['algorithm'],
            'bandit_total_pulls': stats['total_pulls'],
            'kelly_fraction': kelly,
            'avg_position_size': sum(self.metrics['position_sizes'][-50:]) / min(50, len(self.metrics['position_sizes'])) 
                if self.metrics['position_sizes'] else 0.0,
            'best_indicator': best_indicator,
            'best_indicator_score': best_indicator_score,
            'signal_aggregations': self.metrics['signal_aggregations']
        }
