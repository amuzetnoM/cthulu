"""
Cthulu Cognition Engine - The Soul of the System

Central AI/ML integration layer that coordinates:
- Market Regime Classification
- Price Direction Prediction
- Sentiment Analysis
- Enhanced Exit Signals

Part of Cthulu v5.1.0 APEX
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import json
import os

from .regime_classifier import (
    MarketRegimeClassifier, RegimeState, MarketRegime,
    get_regime_classifier, classify_regime
)
from .price_predictor import (
    PricePredictor, PricePrediction, PredictionDirection,
    get_price_predictor, predict_direction
)
from .sentiment_analyzer import (
    SentimentAnalyzer, SentimentScore, SentimentDirection,
    get_sentiment_analyzer, get_sentiment
)
from .exit_oracle import (
    ExitOracle, ExitSignal, ExitUrgency, PositionContext,
    get_exit_oracle, evaluate_exits
)

logger = logging.getLogger("Cthulu.cognition")


@dataclass
class CognitionState:
    """Combined state of all cognition modules."""
    regime: RegimeState
    prediction: PricePrediction
    sentiment: SentimentScore
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def combined_confidence(self) -> float:
        """Overall confidence from all modules."""
        weights = {'regime': 0.35, 'prediction': 0.40, 'sentiment': 0.25}
        return (
            self.regime.confidence * weights['regime'] +
            self.prediction.confidence * weights['prediction'] +
            self.sentiment.confidence * weights['sentiment']
        )
    
    @property
    def directional_consensus(self) -> str:
        """Check if modules agree on direction."""
        bullish_count = 0
        bearish_count = 0
        
        # Regime
        if self.regime.regime in (MarketRegime.BULL,):
            bullish_count += 1
        elif self.regime.regime in (MarketRegime.BEAR,):
            bearish_count += 1
        
        # Prediction
        if self.prediction.direction == PredictionDirection.LONG:
            bullish_count += 1
        elif self.prediction.direction == PredictionDirection.SHORT:
            bearish_count += 1
        
        # Sentiment
        if self.sentiment.direction == SentimentDirection.BULLISH:
            bullish_count += 1
        elif self.sentiment.direction == SentimentDirection.BEARISH:
            bearish_count += 1
        
        if bullish_count >= 2:
            return "BULLISH"
        elif bearish_count >= 2:
            return "BEARISH"
        else:
            return "MIXED"
    
    @property
    def trade_allowed(self) -> bool:
        """Check if conditions are favorable for trading."""
        # Avoid choppy markets with low prediction confidence
        if self.regime.regime == MarketRegime.CHOPPY and self.prediction.confidence < 0.6:
            return False
        
        # Avoid trading against strong sentiment
        if self.sentiment.suggests_caution:
            return False
        
        return True


@dataclass
class SignalEnhancement:
    """Enhancement/adjustment for trading signals."""
    confidence_multiplier: float  # Multiply signal confidence
    size_multiplier: float  # Multiply position size
    reasons: List[str]
    warnings: List[str]
    
    @property
    def is_favorable(self) -> bool:
        return self.confidence_multiplier >= 1.0 and not self.warnings


class CognitionEngine:
    """
    Central AI/ML integration layer for Cthulu.
    
    Coordinates all cognition modules:
    - Market Regime Classifier: Bull/Bear/Sideways/Volatile/Choppy
    - Price Predictor: Direction probabilities for next N bars
    - Sentiment Analyzer: News/calendar/fear-greed integration
    - Exit Oracle: High-confluence exit signals
    
    Provides:
    - Signal enhancement (boost/reduce confidence)
    - Exit signal generation
    - Risk adjustment recommendations
    - Market condition awareness
    """
    
    def __init__(
        self,
        enable_regime: bool = True,
        enable_prediction: bool = True,
        enable_sentiment: bool = True,
        enable_exit_oracle: bool = True,
        model_dir: Optional[str] = None
    ):
        self.enable_regime = enable_regime
        self.enable_prediction = enable_prediction
        self.enable_sentiment = enable_sentiment
        self.enable_exit_oracle = enable_exit_oracle
        
        self.model_dir = model_dir or os.path.join(
            os.path.dirname(__file__), 'data', 'models'
        )
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Initialize modules
        self._regime_classifier: Optional[MarketRegimeClassifier] = None
        self._price_predictor: Optional[PricePredictor] = None
        self._sentiment_analyzer: Optional[SentimentAnalyzer] = None
        self._exit_oracle: Optional[ExitOracle] = None
        
        # State tracking
        self._last_state: Optional[CognitionState] = None
        self._state_history: List[CognitionState] = []
        
        # Initialize enabled modules
        self._initialize_modules()
        
        logger.info(f"CognitionEngine initialized: regime={enable_regime}, "
                   f"prediction={enable_prediction}, sentiment={enable_sentiment}, "
                   f"exit_oracle={enable_exit_oracle}")
    
    def _initialize_modules(self):
        """Initialize enabled cognition modules."""
        if self.enable_regime:
            self._regime_classifier = get_regime_classifier()
        
        if self.enable_prediction:
            model_path = os.path.join(self.model_dir, 'price_predictor.json')
            self._price_predictor = get_price_predictor(
                model_path=model_path if os.path.exists(model_path) else None
            )
        
        if self.enable_sentiment:
            self._sentiment_analyzer = get_sentiment_analyzer()
        
        if self.enable_exit_oracle:
            self._exit_oracle = get_exit_oracle()
            # Integrate cognition into exit oracle
            self._exit_oracle.integrate_cognition(
                regime_classifier=self._regime_classifier,
                price_predictor=self._price_predictor,
                sentiment_analyzer=self._sentiment_analyzer
            )
    
    def analyze(self, symbol: str, market_data: pd.DataFrame) -> CognitionState:
        """
        Perform full cognition analysis.
        
        Args:
            symbol: Trading symbol
            market_data: OHLCV DataFrame
            
        Returns:
            CognitionState with all module outputs
        """
        # Regime classification
        if self._regime_classifier and len(market_data) >= 50:
            regime = self._regime_classifier.classify(market_data)
        else:
            regime = RegimeState(
                regime=MarketRegime.UNKNOWN,
                confidence=0.0,
                probabilities={},
                features={}
            )
        
        # Price prediction
        if self._price_predictor and len(market_data) >= self._price_predictor.lookback_bars:
            prediction = self._price_predictor.predict(market_data)
        else:
            prediction = PricePrediction(
                direction=PredictionDirection.NEUTRAL,
                confidence=0.33,
                probabilities={},
                expected_move_pct=0.0,
                horizon_bars=5,
                features_used=0
            )
        
        # Sentiment
        if self._sentiment_analyzer:
            sentiment = self._sentiment_analyzer.get_sentiment(symbol)
        else:
            sentiment = SentimentScore(
                score=0.0,
                direction=SentimentDirection.NEUTRAL,
                confidence=0.5,
                components={},
                events=[]
            )
        
        state = CognitionState(
            regime=regime,
            prediction=prediction,
            sentiment=sentiment
        )
        
        self._last_state = state
        self._state_history.append(state)
        
        # Trim history
        if len(self._state_history) > 100:
            self._state_history = self._state_history[-50:]
        
        logger.debug(f"Cognition analysis: regime={regime.regime.value}, "
                    f"prediction={prediction.direction.value}, "
                    f"sentiment={sentiment.direction.value}")
        
        return state
    
    def enhance_signal(
        self,
        signal_direction: str,  # 'long' or 'short'
        signal_confidence: float,
        symbol: str,
        market_data: pd.DataFrame
    ) -> SignalEnhancement:
        """
        Enhance or adjust a trading signal based on cognition.
        
        Args:
            signal_direction: Signal direction ('long' or 'short')
            signal_confidence: Original signal confidence
            symbol: Trading symbol
            market_data: OHLCV DataFrame
            
        Returns:
            SignalEnhancement with multipliers and reasons
        """
        # Get or refresh state
        if self._last_state is None or (datetime.utcnow() - self._last_state.timestamp).seconds > 60:
            self.analyze(symbol, market_data)
        
        state = self._last_state
        if state is None:
            return SignalEnhancement(1.0, 1.0, [], [])
        
        confidence_mult = 1.0
        size_mult = 1.0
        reasons = []
        warnings = []
        
        # Regime alignment
        if state.regime.regime != MarketRegime.UNKNOWN:
            regime_val = state.regime.regime.value
            
            if signal_direction == 'long':
                if regime_val == 'bull':
                    confidence_mult *= 1.15
                    reasons.append(f"Bullish regime (+15% conf)")
                elif regime_val == 'bear':
                    confidence_mult *= 0.75
                    warnings.append(f"Bearish regime (-25% conf)")
                elif regime_val == 'sideways':
                    size_mult *= 0.8
                    warnings.append(f"Sideways regime (-20% size)")
                elif regime_val in ('choppy', 'volatile'):
                    confidence_mult *= 0.85
                    size_mult *= 0.7
                    warnings.append(f"{regime_val.title()} market (-15% conf, -30% size)")
            
            elif signal_direction == 'short':
                if regime_val == 'bear':
                    confidence_mult *= 1.15
                    reasons.append(f"Bearish regime (+15% conf)")
                elif regime_val == 'bull':
                    confidence_mult *= 0.75
                    warnings.append(f"Bullish regime (-25% conf)")
        
        # Prediction alignment
        if state.prediction.direction != PredictionDirection.NEUTRAL:
            pred_dir = state.prediction.direction.value
            pred_conf = state.prediction.confidence
            
            if (signal_direction == 'long' and pred_dir == 'long') or \
               (signal_direction == 'short' and pred_dir == 'short'):
                boost = 1 + (pred_conf - 0.5) * 0.3  # Up to +15% at 100% conf
                confidence_mult *= boost
                reasons.append(f"Prediction aligned ({pred_conf:.0%} conf)")
            elif pred_conf > 0.65:
                # Strong prediction against signal
                confidence_mult *= 0.8
                warnings.append(f"Prediction against signal ({pred_conf:.0%})")
        
        # Sentiment alignment
        if state.sentiment.direction != SentimentDirection.NEUTRAL:
            sent_dir = state.sentiment.direction.value
            sent_conf = state.sentiment.confidence
            
            if (signal_direction == 'long' and sent_dir == 'bullish') or \
               (signal_direction == 'short' and sent_dir == 'bearish'):
                boost = 1 + (sent_conf - 0.5) * 0.2
                confidence_mult *= boost
                reasons.append(f"Sentiment aligned ({sent_dir})")
            elif sent_conf > 0.6:
                confidence_mult *= 0.9
                warnings.append(f"Sentiment against ({sent_dir})")
        
        # Caution flag
        if state.sentiment.suggests_caution:
            size_mult *= 0.5
            warnings.append("Sentiment suggests caution (-50% size)")
        
        # Consensus bonus
        if state.directional_consensus == signal_direction.upper():
            confidence_mult *= 1.1
            reasons.append("Full consensus (+10% conf)")
        
        return SignalEnhancement(
            confidence_multiplier=confidence_mult,
            size_multiplier=size_mult,
            reasons=reasons,
            warnings=warnings
        )
    
    def get_exit_signals(
        self,
        positions: List[Dict[str, Any]],
        market_data: pd.DataFrame,
        indicators: Dict[str, float]
    ) -> List[ExitSignal]:
        """
        Get exit signals for active positions.
        
        Args:
            positions: List of position dictionaries
            market_data: OHLCV DataFrame
            indicators: Current indicator values
            
        Returns:
            List of exit signals
        """
        if not self._exit_oracle:
            return []
        
        # Convert to PositionContext
        contexts = []
        for pos in positions:
            try:
                ctx = PositionContext(
                    ticket=pos.get('ticket', 0),
                    symbol=pos.get('symbol', ''),
                    direction='long' if pos.get('type', 0) == 0 else 'short',
                    entry_price=pos.get('price_open', 0),
                    current_price=pos.get('price_current', 0),
                    volume=pos.get('volume', 0),
                    unrealized_pnl=pos.get('profit', 0),
                    entry_time=pos.get('time', datetime.utcnow())
                )
                contexts.append(ctx)
            except Exception as e:
                logger.warning(f"Error creating PositionContext: {e}")
        
        return self._exit_oracle.evaluate_exits(contexts, market_data, indicators)
    
    def get_strategy_affinity(self, strategy_name: str) -> float:
        """
        Get affinity score for a strategy based on current regime.
        
        Args:
            strategy_name: Name of strategy
            
        Returns:
            Affinity score 0-1
        """
        if self._regime_classifier:
            return self._regime_classifier.get_regime_affinity(strategy_name)
        return 0.5
    
    def should_trade(self, symbol: str, market_data: pd.DataFrame) -> Tuple[bool, str]:
        """
        Check if trading is advisable.
        
        Args:
            symbol: Trading symbol
            market_data: OHLCV DataFrame
            
        Returns:
            (should_trade, reason)
        """
        if self._last_state is None or (datetime.utcnow() - self._last_state.timestamp).seconds > 60:
            self.analyze(symbol, market_data)
        
        state = self._last_state
        if state is None:
            return True, "No cognition data"
        
        # Check trade allowed
        if not state.trade_allowed:
            if state.regime.regime == MarketRegime.CHOPPY:
                return False, f"Choppy market with low prediction confidence"
            if state.sentiment.suggests_caution:
                return False, f"Sentiment suggests caution"
        
        # Check sentiment for upcoming events
        if self._sentiment_analyzer:
            avoid, reason = self._sentiment_analyzer.should_avoid_trading(symbol)
            if avoid:
                return False, reason
        
        return True, "Trading conditions acceptable"
    
    def train_predictor(
        self,
        market_data: pd.DataFrame,
        epochs: int = 100,
        **kwargs
    ):
        """Train the price predictor on historical data."""
        if not self._price_predictor:
            logger.warning("Price predictor not enabled")
            return None
        
        result = self._price_predictor.train(market_data, epochs=epochs, **kwargs)
        
        # Save model
        model_path = os.path.join(self.model_dir, 'price_predictor.json')
        self._price_predictor.save(model_path)
        
        return result
    
    def add_news(self, headline: str, source: str, symbols: List[str]):
        """Add news item to sentiment analyzer."""
        if self._sentiment_analyzer:
            self._sentiment_analyzer.add_news(headline, source, symbols)
    
    def add_economic_event(self, **kwargs):
        """Add economic event to sentiment analyzer."""
        if self._sentiment_analyzer:
            self._sentiment_analyzer.add_event(**kwargs)
    
    def get_state(self) -> Optional[CognitionState]:
        """Get last cognition state."""
        return self._last_state
    
    def to_dict(self) -> Dict[str, Any]:
        """Export current state as dictionary."""
        result = {
            'enabled_modules': {
                'regime': self.enable_regime,
                'prediction': self.enable_prediction,
                'sentiment': self.enable_sentiment,
                'exit_oracle': self.enable_exit_oracle
            },
            'state_history_length': len(self._state_history)
        }
        
        if self._last_state:
            result['last_state'] = {
                'regime': self._last_state.regime.regime.value,
                'regime_confidence': self._last_state.regime.confidence,
                'prediction': self._last_state.prediction.direction.value,
                'prediction_confidence': self._last_state.prediction.confidence,
                'sentiment': self._last_state.sentiment.direction.value,
                'sentiment_score': self._last_state.sentiment.score,
                'consensus': self._last_state.directional_consensus,
                'combined_confidence': self._last_state.combined_confidence,
                'trade_allowed': self._last_state.trade_allowed
            }
        
        if self._regime_classifier:
            result['regime_classifier'] = self._regime_classifier.to_dict()
        
        if self._price_predictor:
            result['price_predictor'] = self._price_predictor.to_dict()
        
        if self._sentiment_analyzer:
            result['sentiment_analyzer'] = self._sentiment_analyzer.to_dict()
        
        if self._exit_oracle:
            result['exit_oracle'] = self._exit_oracle.to_dict()
        
        return result


# Module-level singleton
_engine: Optional[CognitionEngine] = None


def get_cognition_engine(**kwargs) -> CognitionEngine:
    """Get or create the cognition engine singleton."""
    global _engine
    if _engine is None:
        _engine = CognitionEngine(**kwargs)
    return _engine


def analyze_market(symbol: str, market_data: pd.DataFrame) -> CognitionState:
    """Convenience function to analyze market."""
    return get_cognition_engine().analyze(symbol, market_data)


def enhance_signal(
    signal_direction: str,
    signal_confidence: float,
    symbol: str,
    market_data: pd.DataFrame
) -> SignalEnhancement:
    """Convenience function to enhance signal."""
    return get_cognition_engine().enhance_signal(
        signal_direction, signal_confidence, symbol, market_data
    )
