"""
Signal Aggregation using Argmax

This module implements argmax-based signal aggregation from multiple technical
indicators. Instead of naive averaging or simple voting, it uses sophisticated
confidence weighting and argmax selection to identify the most reliable signal.

Theoretical Foundation:
- Treat each indicator as an "expert" with varying reliability
- Weight signals by historical accuracy in current market regime
- Use argmax to select the strongest/most confident indicator
- Optional: Use softmax for probabilistic consensus

Key Advantages over Simple Averaging:
1. Adaptive weighting based on performance
2. Regime-aware indicator selection
3. Noise reduction by selecting best signal
4. Learning from outcomes
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict, deque

from cthulu.strategy.base import Signal, SignalType


logger = logging.getLogger("Cthulu.signal_aggregator")


@dataclass
class IndicatorSignal:
    """
    Signal from a single technical indicator.
    
    Attributes:
        indicator_name: Name of the indicator (RSI, MACD, etc.)
        signal_type: LONG, SHORT, or HOLD
        confidence: Confidence score (0-1)
        strength: Signal strength/magnitude
        timestamp: When signal was generated
        metadata: Additional information
    """
    indicator_name: str
    signal_type: SignalType
    confidence: float
    strength: float = 0.0
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class IndicatorPerformance:
    """Track performance of an indicator over time."""
    name: str
    total_signals: int = 0
    correct_signals: int = 0
    total_strength: float = 0.0
    recent_accuracy: deque = None  # Recent accuracy (binary)
    by_regime: Dict[str, Dict[str, float]] = None
    by_signal_type: Dict[SignalType, Dict[str, float]] = None
    
    def __post_init__(self):
        if self.recent_accuracy is None:
            self.recent_accuracy = deque(maxlen=50)  # Last 50 signals
        if self.by_regime is None:
            self.by_regime = defaultdict(lambda: {'total': 0, 'correct': 0})
        if self.by_signal_type is None:
            self.by_signal_type = defaultdict(lambda: {'total': 0, 'correct': 0})
    
    @property
    def accuracy(self) -> float:
        """Overall accuracy."""
        return self.correct_signals / self.total_signals if self.total_signals > 0 else 0.5
    
    @property
    def recent_accuracy_score(self) -> float:
        """Recent accuracy (sliding window)."""
        return sum(self.recent_accuracy) / len(self.recent_accuracy) if self.recent_accuracy else 0.5
    
    @property
    def avg_strength(self) -> float:
        """Average signal strength."""
        return self.total_strength / self.total_signals if self.total_signals > 0 else 0.0


class SignalAggregator:
    """
    Aggregates signals from multiple indicators using argmax-based selection.
    
    This class implements three aggregation strategies:
    
    1. **Argmax by Confidence**: Select indicator with highest confidence
    2. **Argmax by Weighted Score**: Weight confidence by historical accuracy
    3. **Softmax Consensus**: Probabilistic combination of all signals
    
    The aggregator learns from outcomes and adapts weights over time.
    
    Example Usage:
        aggregator = SignalAggregator()
        
        # Add signals from indicators
        aggregator.add_signal(IndicatorSignal(
            indicator_name='RSI',
            signal_type=SignalType.LONG,
            confidence=0.8,
            strength=25.0  # RSI=25 (oversold)
        ))
        
        aggregator.add_signal(IndicatorSignal(
            indicator_name='MACD',
            signal_type=SignalType.LONG,
            confidence=0.6,
            strength=0.05
        ))
        
        # Get aggregated signal using argmax
        final_signal = aggregator.aggregate(
            method='argmax_weighted',
            market_regime='trending'
        )
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize signal aggregator.
        
        Args:
            config: Configuration parameters
        """
        self.config = config or {}
        
        # Indicator performance tracking
        self.performance: Dict[str, IndicatorPerformance] = {}
        
        # Current signals (cleared each aggregation cycle)
        self.current_signals: List[IndicatorSignal] = []
        
        # Configuration
        self.min_confidence_threshold = self.config.get('min_confidence', 0.5)
        self.consensus_threshold = self.config.get('consensus_threshold', 0.7)
        self.learning_rate = self.config.get('learning_rate', 0.1)
        
        # Aggregation history
        self.aggregation_history = []
        
        logger.info("SignalAggregator initialized")
    
    def add_signal(self, signal: IndicatorSignal):
        """
        Add a signal from an indicator.
        
        Args:
            signal: Indicator signal to add
        """
        # Initialize performance tracking if new indicator
        if signal.indicator_name not in self.performance:
            self.performance[signal.indicator_name] = IndicatorPerformance(
                name=signal.indicator_name
            )
        
        self.current_signals.append(signal)
        
        logger.debug(
            f"Added signal from {signal.indicator_name}: "
            f"type={signal.signal_type}, conf={signal.confidence:.2f}"
        )
    
    def aggregate(
        self,
        method: str = 'argmax_weighted',
        market_regime: Optional[str] = None
    ) -> Optional[Signal]:
        """
        Aggregate all current signals into a single signal.
        
        Args:
            method: Aggregation method ('argmax_simple', 'argmax_weighted', 'softmax')
            market_regime: Current market regime (for regime-aware selection)
            
        Returns:
            Aggregated signal or None if no consensus
        """
        if not self.current_signals:
            logger.warning("No signals to aggregate")
            return None
        
        # Select aggregation method
        if method == 'argmax_simple':
            result = self._argmax_by_confidence()
        elif method == 'argmax_weighted':
            result = self._argmax_by_weighted_score(market_regime)
        elif method == 'softmax':
            result = self._softmax_consensus(market_regime)
        else:
            raise ValueError(f"Unknown aggregation method: {method}")
        
        # Record aggregation
        self.aggregation_history.append({
            'timestamp': datetime.now(),
            'method': method,
            'num_signals': len(self.current_signals),
            'result': result,
            'signals': self.current_signals.copy()
        })
        
        # Clear current signals
        self.current_signals.clear()
        
        return result
    
    def _argmax_by_confidence(self) -> Optional[Signal]:
        """
        Simple argmax: Select indicator with highest confidence.
        
        This is the most straightforward approach - just pick the indicator
        that is most confident about its signal.
        
        Returns:
            Signal from most confident indicator
        """
        # Filter by minimum confidence
        valid_signals = [
            s for s in self.current_signals
            if s.confidence >= self.min_confidence_threshold
        ]
        
        if not valid_signals:
            logger.debug("No signals meet confidence threshold")
            return None
        
        # ARGMAX: Select signal with highest confidence
        best_signal = max(valid_signals, key=lambda s: s.confidence)
        
        logger.info(
            f"Argmax (simple): Selected {best_signal.indicator_name} "
            f"with confidence {best_signal.confidence:.2f}"
        )
        
        return self._create_output_signal(best_signal, method='argmax_simple')
    
    def _argmax_by_weighted_score(
        self,
        market_regime: Optional[str] = None
    ) -> Optional[Signal]:
        """
        Weighted argmax: Weight confidence by historical accuracy.
        
        Formula:
            weighted_score = confidence * historical_accuracy * regime_factor
        
        Select signal with highest weighted score using argmax.
        
        Args:
            market_regime: Current market regime
            
        Returns:
            Signal with highest weighted score
        """
        # Calculate weighted scores
        scored_signals = []
        
        for signal in self.current_signals:
            # Base confidence
            confidence = signal.confidence
            
            # Historical accuracy weight
            perf = self.performance.get(signal.indicator_name)
            if perf:
                # Use recent accuracy (more responsive to changes)
                accuracy_weight = perf.recent_accuracy_score
                
                # Regime-specific accuracy if available
                if market_regime and market_regime in perf.by_regime:
                    regime_perf = perf.by_regime[market_regime]
                    if regime_perf['total'] > 5:  # Sufficient data
                        regime_accuracy = regime_perf['correct'] / regime_perf['total']
                        accuracy_weight = 0.5 * accuracy_weight + 0.5 * regime_accuracy
            else:
                accuracy_weight = 0.5  # Neutral for new indicators
            
            # Signal type-specific accuracy
            signal_type_perf = perf.by_signal_type.get(signal.signal_type, {}) if perf else {}
            if signal_type_perf.get('total', 0) > 5:
                type_accuracy = signal_type_perf['correct'] / signal_type_perf['total']
                accuracy_weight = 0.7 * accuracy_weight + 0.3 * type_accuracy
            
            # Weighted score
            weighted_score = confidence * accuracy_weight
            
            scored_signals.append({
                'signal': signal,
                'score': weighted_score,
                'confidence': confidence,
                'accuracy_weight': accuracy_weight
            })
            
            logger.debug(
                f"{signal.indicator_name}: conf={confidence:.2f}, "
                f"acc_weight={accuracy_weight:.2f}, score={weighted_score:.2f}"
            )
        
        if not scored_signals:
            return None
        
        # ARGMAX: Select signal with highest weighted score
        best = max(scored_signals, key=lambda x: x['score'])
        
        logger.info(
            f"Argmax (weighted): Selected {best['signal'].indicator_name} "
            f"with score {best['score']:.2f} "
            f"(conf={best['confidence']:.2f}, acc={best['accuracy_weight']:.2f})"
        )
        
        return self._create_output_signal(best['signal'], method='argmax_weighted')
    
    def _softmax_consensus(
        self,
        market_regime: Optional[str] = None
    ) -> Optional[Signal]:
        """
        Softmax consensus: Probabilistic combination of all signals.
        
        Uses softmax to convert weighted scores to probabilities, then
        creates a consensus signal based on probability-weighted average.
        
        Formula:
            P(indicator_i) = exp(score_i / τ) / Σ exp(score_j / τ)
        
        Where τ (temperature) controls confidence spread.
        
        Args:
            market_regime: Current market regime
            
        Returns:
            Consensus signal
        """
        temperature = self.config.get('softmax_temperature', 0.1)
        
        # Calculate weighted scores (same as weighted argmax)
        scored_signals = []
        
        for signal in self.current_signals:
            confidence = signal.confidence
            perf = self.performance.get(signal.indicator_name)
            accuracy_weight = perf.recent_accuracy_score if perf else 0.5
            
            weighted_score = confidence * accuracy_weight
            scored_signals.append({
                'signal': signal,
                'score': weighted_score
            })
        
        if not scored_signals:
            return None
        
        # Apply softmax to get probabilities
        scores = np.array([s['score'] for s in scored_signals])
        exp_scores = np.exp(scores / temperature)
        probabilities = exp_scores / np.sum(exp_scores)
        
        # Count votes by signal type (weighted by probability)
        votes = {
            SignalType.LONG: 0.0,
            SignalType.SHORT: 0.0,
            SignalType.HOLD: 0.0
        }
        
        weighted_confidence = 0.0
        weighted_strength = 0.0
        
        for prob, item in zip(probabilities, scored_signals):
            signal = item['signal']
            votes[signal.signal_type] += prob
            weighted_confidence += prob * signal.confidence
            weighted_strength += prob * signal.strength
        
        # Determine consensus signal type
        consensus_type = max(votes.keys(), key=lambda k: votes[k])
        consensus_strength = votes[consensus_type]
        
        logger.info(
            f"Softmax consensus: {consensus_type} "
            f"(strength={consensus_strength:.2%}, "
            f"votes={dict(votes)})"
        )
        
        # Only return signal if consensus is strong enough
        if consensus_strength < self.consensus_threshold:
            logger.debug(
                f"Consensus too weak: {consensus_strength:.2%} < "
                f"{self.consensus_threshold:.2%}"
            )
            return None
        
        # Create consensus signal
        return Signal(
            symbol="CONSENSUS",  # To be overridden by caller
            side=consensus_type,
            confidence=weighted_confidence,
            entry_price=0.0,  # To be filled by caller
            stop_loss=0.0,
            take_profit=0.0,
            metadata={
                'aggregation_method': 'softmax',
                'num_indicators': len(scored_signals),
                'consensus_strength': consensus_strength,
                'votes': dict(votes),
                'probabilities': probabilities.tolist(),
                'indicators': [s['signal'].indicator_name for s in scored_signals]
            }
        )
    
    def _create_output_signal(
        self,
        indicator_signal: IndicatorSignal,
        method: str
    ) -> Signal:
        """
        Convert IndicatorSignal to output Signal format.
        
        Args:
            indicator_signal: Selected indicator signal
            method: Aggregation method used
            
        Returns:
            Formatted Signal object
        """
        return Signal(
            symbol="CONSENSUS",  # To be overridden
            side=indicator_signal.signal_type,
            confidence=indicator_signal.confidence,
            entry_price=0.0,  # To be filled
            stop_loss=0.0,
            take_profit=0.0,
            metadata={
                'aggregation_method': method,
                'selected_indicator': indicator_signal.indicator_name,
                'num_indicators': len(self.current_signals),
                'signal_strength': indicator_signal.strength,
                'indicator_metadata': indicator_signal.metadata
            }
        )
    
    def update_performance(
        self,
        indicator_name: str,
        signal_type: SignalType,
        was_correct: bool,
        market_regime: Optional[str] = None
    ):
        """
        Update indicator performance after outcome is known.
        
        This is crucial for learning - must be called after each trade
        to update accuracy weights.
        
        Args:
            indicator_name: Name of indicator that generated signal
            signal_type: Type of signal (LONG/SHORT/HOLD)
            was_correct: Whether the signal led to profitable trade
            market_regime: Market regime during signal
        """
        if indicator_name not in self.performance:
            self.performance[indicator_name] = IndicatorPerformance(
                name=indicator_name
            )
        
        perf = self.performance[indicator_name]
        
        # Update overall stats
        perf.total_signals += 1
        if was_correct:
            perf.correct_signals += 1
        
        # Update recent accuracy
        perf.recent_accuracy.append(1.0 if was_correct else 0.0)
        
        # Update regime-specific stats
        if market_regime:
            regime_perf = perf.by_regime[market_regime]
            regime_perf['total'] += 1
            if was_correct:
                regime_perf['correct'] += 1
        
        # Update signal type-specific stats
        type_perf = perf.by_signal_type[signal_type]
        type_perf['total'] += 1
        if was_correct:
            type_perf['correct'] += 1
        
        logger.info(
            f"Updated {indicator_name}: "
            f"accuracy={perf.accuracy:.2%}, "
            f"recent={perf.recent_accuracy_score:.2%}"
        )
    
    def get_indicator_rankings(
        self,
        market_regime: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Get indicators ranked by performance.
        
        Args:
            market_regime: Optional regime to get regime-specific rankings
            
        Returns:
            List of (indicator_name, score) tuples, sorted by score descending
        """
        rankings = []
        
        for name, perf in self.performance.items():
            if market_regime and market_regime in perf.by_regime:
                # Regime-specific score
                regime_perf = perf.by_regime[market_regime]
                if regime_perf['total'] > 0:
                    score = regime_perf['correct'] / regime_perf['total']
                else:
                    score = perf.accuracy
            else:
                # Overall score
                score = perf.recent_accuracy_score
            
            rankings.append((name, score))
        
        # Sort by score descending
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        return rankings
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive performance report.
        
        Returns:
            Dictionary with detailed statistics
        """
        report = {}
        
        for name, perf in self.performance.items():
            report[name] = {
                'total_signals': perf.total_signals,
                'accuracy': perf.accuracy,
                'recent_accuracy': perf.recent_accuracy_score,
                'by_regime': {},
                'by_signal_type': {}
            }
            
            # Regime performance
            for regime, regime_perf in perf.by_regime.items():
                if regime_perf['total'] > 0:
                    report[name]['by_regime'][regime] = {
                        'total': regime_perf['total'],
                        'accuracy': regime_perf['correct'] / regime_perf['total']
                    }
            
            # Signal type performance
            for sig_type, type_perf in perf.by_signal_type.items():
                if type_perf['total'] > 0:
                    report[name]['by_signal_type'][sig_type.name] = {
                        'total': type_perf['total'],
                        'accuracy': type_perf['correct'] / type_perf['total']
                    }
        
        return report
    
    def reset_performance(self):
        """Reset all performance statistics."""
        self.performance.clear()
        self.aggregation_history.clear()
        logger.info("Performance statistics reset")


class AdaptiveSignalAggregator(SignalAggregator):
    """
    Extended aggregator with adaptive learning.
    
    Automatically adjusts indicator weights based on recent performance
    using exponential moving average.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Adaptive weights (learned)
        self.adaptive_weights: Dict[str, float] = {}
        self.weight_decay = self.config.get('weight_decay', 0.95)
    
    def update_performance(
        self,
        indicator_name: str,
        signal_type: SignalType,
        was_correct: bool,
        market_regime: Optional[str] = None
    ):
        """Update performance and adaptive weights."""
        # Call parent update
        super().update_performance(indicator_name, signal_type, was_correct, market_regime)
        
        # Update adaptive weights using exponential moving average
        if indicator_name not in self.adaptive_weights:
            self.adaptive_weights[indicator_name] = 0.5  # Initial
        
        current_weight = self.adaptive_weights[indicator_name]
        target = 1.0 if was_correct else 0.0
        
        # EMA update
        new_weight = (
            self.weight_decay * current_weight +
            (1 - self.weight_decay) * target
        )
        
        self.adaptive_weights[indicator_name] = new_weight
        
        logger.debug(
            f"Adaptive weight for {indicator_name}: {new_weight:.3f}"
        )
