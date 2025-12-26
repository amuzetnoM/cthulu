"""
Dynamic Strategy Selector

Intelligently selects and switches between strategies based on market regime,
performance metrics, and real-time conditions. Enables autonomous strategy adaptation.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
import pandas as pd
import numpy as np

from herald.strategy.base import Strategy, Signal


class MarketRegime:
    """Market regime classification."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    CONSOLIDATING = "consolidating"


class StrategyPerformance:
    """Track strategy performance metrics."""
    
    def __init__(self, strategy_name: str, window_size: int = 50):
        self.strategy_name = strategy_name
        self.window_size = window_size
        self.signals_count = 0
        self.wins = 0
        self.losses = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.recent_signals = deque(maxlen=window_size)
        self.last_signal_time = None
        self.confidence_scores = deque(maxlen=window_size)
        
    def add_signal(self, signal: Optional[Signal] = None, outcome: Optional[str] = None, pnl: Optional[float] = None):
        """Record a signal and its outcome."""
        if signal:
            self.signals_count += 1
            self.last_signal_time = datetime.now()
            self.confidence_scores.append(signal.confidence)
        
        if outcome:
            self.recent_signals.append({
                'outcome': outcome,
                'pnl': pnl or 0.0,
                'timestamp': datetime.now()
            })
            
            if outcome == 'win' and pnl:
                self.wins += 1
                self.total_profit += pnl
            elif outcome == 'loss' and pnl:
                self.losses += 1
                self.total_loss += abs(pnl)
                
    @property
    def win_rate(self) -> float:
        """Calculate win rate."""
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0.0
        
    @property
    def profit_factor(self) -> float:
        """Calculate profit factor."""
        return self.total_profit / self.total_loss if self.total_loss > 0 else 0.0
        
    @property
    def avg_confidence(self) -> float:
        """Average confidence of recent signals."""
        return np.mean(self.confidence_scores) if self.confidence_scores else 0.0
        
    @property
    def recent_performance_score(self) -> float:
        """Score based on recent signals (0-1)."""
        if not self.recent_signals:
            return 0.5  # Neutral score with no history
            
        recent_wins = sum(1 for s in self.recent_signals if s['outcome'] == 'win')
        recent_total = len(self.recent_signals)
        
        return recent_wins / recent_total if recent_total > 0 else 0.5


class StrategySelector:
    """
    Dynamic strategy selector that chooses the best strategy based on:
    - Market regime detection
    - Individual strategy performance
    - Market conditions (volatility, trend strength)
    - Strategy confidence scores
    """
    
    def __init__(self, strategies: List[Strategy], config: Dict[str, Any] = None):
        """
        Initialize strategy selector.
        
        Args:
            strategies: List of available strategies
            config: Configuration parameters
        """
        self.strategies = {s.name: s for s in strategies}
        self.config = config or {}
        self.logger = logging.getLogger("herald.strategy_selector")
        
        # Performance tracking
        self.performance = {
            name: StrategyPerformance(name) 
            for name in self.strategies.keys()
        }
        
        # Current state
        self.current_strategy = None
        self.current_regime = MarketRegime.RANGING
        self.last_regime_check = None
        self.regime_history = deque(maxlen=20)
        
        # Configuration
        self.regime_check_interval = config.get('regime_check_interval', 300)  # 5 minutes
        self.min_strategy_signals = config.get('min_strategy_signals', 5)
        self.performance_weight = config.get('performance_weight', 0.4)
        self.regime_weight = config.get('regime_weight', 0.4)
        self.confidence_weight = config.get('confidence_weight', 0.2)
        
        # Strategy-regime affinity (which strategies work best in which regimes)
        self.strategy_affinity = {
            'sma_crossover': {
                MarketRegime.TRENDING_UP: 0.9,
                MarketRegime.TRENDING_DOWN: 0.9,
                MarketRegime.RANGING: 0.3,
                MarketRegime.VOLATILE: 0.5,
                MarketRegime.CONSOLIDATING: 0.4
            },
            'ema_crossover': {
                MarketRegime.TRENDING_UP: 0.95,
                MarketRegime.TRENDING_DOWN: 0.95,
                MarketRegime.RANGING: 0.4,
                MarketRegime.VOLATILE: 0.6,
                MarketRegime.CONSOLIDATING: 0.5
            },
            'momentum_breakout': {
                MarketRegime.TRENDING_UP: 0.8,
                MarketRegime.TRENDING_DOWN: 0.8,
                MarketRegime.RANGING: 0.5,
                MarketRegime.VOLATILE: 0.9,
                MarketRegime.CONSOLIDATING: 0.3
            },
            'scalping': {
                MarketRegime.TRENDING_UP: 0.6,
                MarketRegime.TRENDING_DOWN: 0.6,
                MarketRegime.RANGING: 0.9,
                MarketRegime.VOLATILE: 0.4,
                MarketRegime.CONSOLIDATING: 0.7
            }
        }
        
        self.logger.info(f"StrategySelector initialized with {len(strategies)} strategies")
        
    def detect_market_regime(self, data: pd.DataFrame) -> str:
        """
        Detect current market regime from price data.
        
        Args:
            data: DataFrame with OHLCV and indicators
            
        Returns:
            Market regime classification
        """
        if len(data) < 50:
            return MarketRegime.RANGING
            
        # Calculate trend indicators
        if 'adx' in data.columns:
            adx = data['adx'].iloc[-1]
            adx_threshold_strong = 25
            adx_threshold_weak = 20
        else:
            adx = None
            
        # Calculate price momentum
        returns = data['close'].pct_change(20).iloc[-1]
        
        # Calculate volatility (ATR ratio)
        if 'atr' in data.columns:
            atr = data['atr'].iloc[-1]
            atr_avg = data['atr'].rolling(50).mean().iloc[-1]
            volatility_ratio = atr / atr_avg if atr_avg > 0 else 1.0
        else:
            volatility_ratio = 1.0
            
        # Calculate Bollinger Band width (if available)
        bb_width_ratio = 1.0
        if 'bb_upper' in data.columns and 'bb_lower' in data.columns:
            bb_width = data['bb_upper'].iloc[-1] - data['bb_lower'].iloc[-1]
            bb_width_avg = (data['bb_upper'] - data['bb_lower']).rolling(50).mean().iloc[-1]
            bb_width_ratio = bb_width / bb_width_avg if bb_width_avg > 0 else 1.0
        
        # Regime detection logic
        regime = MarketRegime.RANGING  # Default
        
        # High volatility regime
        if volatility_ratio > 1.5 or bb_width_ratio > 1.5:
            regime = MarketRegime.VOLATILE
            
        # Trending regimes
        elif adx and adx > adx_threshold_strong:
            if returns > 0.02:
                regime = MarketRegime.TRENDING_UP
            elif returns < -0.02:
                regime = MarketRegime.TRENDING_DOWN
            else:
                regime = MarketRegime.RANGING
                
        # Consolidation
        elif bb_width_ratio < 0.7 and (not adx or adx < adx_threshold_weak):
            regime = MarketRegime.CONSOLIDATING
            
        # Ranging (default for weak trends)
        else:
            regime = MarketRegime.RANGING
            
        self.regime_history.append({
            'regime': regime,
            'timestamp': datetime.now(),
            'adx': adx,
            'returns': returns,
            'volatility_ratio': volatility_ratio
        })
        
        self.logger.info(f"Market regime detected: {regime} (ADX={adx:.1f if adx else 'N/A'}, "
                        f"Returns={returns*100:.2f}%, Vol={volatility_ratio:.2f})")
        
        return regime
        
    def select_strategy(self, data: pd.DataFrame) -> Strategy:
        """
        Select the best strategy for current conditions.
        
        Args:
            data: Market data with indicators
            
        Returns:
            Selected strategy instance
        """
        # Update market regime if needed
        now = datetime.now()
        if (self.last_regime_check is None or 
            (now - self.last_regime_check).total_seconds() > self.regime_check_interval):
            
            self.current_regime = self.detect_market_regime(data)
            self.last_regime_check = now
            
        # Calculate scores for each strategy
        scores = {}
        
        for name, strategy in self.strategies.items():
            perf = self.performance[name]
            
            # Performance score
            if perf.signals_count >= self.min_strategy_signals:
                perf_score = (perf.win_rate * 0.5 + 
                             min(perf.profit_factor / 2.0, 1.0) * 0.3 +
                             perf.recent_performance_score * 0.2)
            else:
                perf_score = 0.5  # Neutral for untested strategies
                
            # Regime affinity score
            affinity = self.strategy_affinity.get(name, {})
            regime_score = affinity.get(self.current_regime, 0.5)
            
            # Confidence score
            confidence_score = perf.avg_confidence if perf.confidence_scores else 0.5
            
            # Combined weighted score
            total_score = (perf_score * self.performance_weight +
                          regime_score * self.regime_weight +
                          confidence_score * self.confidence_weight)
                          
            scores[name] = {
                'total': total_score,
                'performance': perf_score,
                'regime': regime_score,
                'confidence': confidence_score
            }
            
        # Select strategy with highest score
        best_strategy_name = max(scores.keys(), key=lambda k: scores[k]['total'])
        best_score = scores[best_strategy_name]
        
        # Log selection reasoning
        self.logger.info(
            f"Selected strategy: {best_strategy_name} "
            f"(score={best_score['total']:.3f}, perf={best_score['performance']:.3f}, "
            f"regime={best_score['regime']:.3f}, conf={best_score['confidence']:.3f})"
        )
        
        # Log all scores for transparency
        for name, score in scores.items():
            if name != best_strategy_name:
                self.logger.debug(
                    f"  {name}: total={score['total']:.3f}, "
                    f"perf={score['performance']:.3f}, "
                    f"regime={score['regime']:.3f}"
                )
        
        self.current_strategy = self.strategies[best_strategy_name]
        return self.current_strategy
        
    def generate_signal(self, data: pd.DataFrame, bar: pd.Series) -> Optional[Signal]:
        """
        Generate signal using selected strategy.
        
        Args:
            data: Full market data
            bar: Latest bar
            
        Returns:
            Signal from selected strategy
        """
        # Select best strategy
        strategy = self.select_strategy(data)
        
        # Generate signal
        signal = strategy.on_bar(bar)
        
        # Track signal for performance monitoring
        if signal:
            self.performance[strategy.name].add_signal(signal)
            
        return signal
        
    def record_outcome(self, strategy_name: str, outcome: str, pnl: float):
        """
        Record the outcome of a signal.
        
        Args:
            strategy_name: Name of strategy that generated the signal
            outcome: 'win' or 'loss'
            pnl: Profit/loss amount
        """
        if strategy_name in self.performance:
            # Update the most recent signal with outcome
            self.performance[strategy_name].add_signal(
                None,  # No new signal, just updating outcome
                outcome=outcome,
                pnl=pnl
            )
            
            self.logger.info(
                f"Recorded {outcome} for {strategy_name}: "
                f"${pnl:.2f} (WinRate={self.performance[strategy_name].win_rate:.2%})"
            )
            
    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report for all strategies."""
        report = {
            'current_regime': self.current_regime,
            'current_strategy': self.current_strategy.name if self.current_strategy else None,
            'strategies': {}
        }
        
        for name, perf in self.performance.items():
            report['strategies'][name] = {
                'signals_count': perf.signals_count,
                'win_rate': perf.win_rate,
                'profit_factor': perf.profit_factor,
                'avg_confidence': perf.avg_confidence,
                'recent_performance': perf.recent_performance_score,
                'total_profit': perf.total_profit,
                'total_loss': perf.total_loss
            }
            
        return report
