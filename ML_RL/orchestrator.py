"""
ML/RL Orchestrator

Main orchestration system for ML/RL auto-tuning.
Fully decoupled from main trading loop - runs asynchronously.
Coordinates feature extraction, model training, and RL agents.
"""

import logging
import os
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from threading import Thread, Event
from dataclasses import dataclass

from .feature_engineering import FeatureExtractor, RealtimeFeatureStream
from .ml_models import ModelEnsemble
from .reinforcement_learning import AutoTuner, RLState


@dataclass
class TuningRecommendation:
    """Parameter tuning recommendation."""
    timestamp: datetime
    source: str  # 'ml_ensemble', 'rl_q', 'rl_pg'
    parameters: Dict[str, float]
    confidence: float
    rationale: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'parameters': self.parameters,
            'confidence': self.confidence,
            'rationale': self.rationale
        }


class MLRLOrchestrator:
    """
    Main orchestrator for ML/RL auto-tuning system.
    
    Manages the complete pipeline:
    1. Feature extraction from event streams
    2. Model training (supervised learning)
    3. RL agent training (Q-learning, Policy Gradient)
    4. Parameter recommendations
    
    Fully decoupled - runs in background thread, doesn't affect main loop.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ML/RL orchestrator.
        
        Args:
            config: Configuration parameters
        """
        self.logger = logging.getLogger("Cthulu.ml_rl_orchestrator")
        self.config = config or {}
        
        # Initialize components
        data_dir = self.config.get('data_dir')
        self.feature_extractor = FeatureExtractor(data_dir)
        self.feature_stream = RealtimeFeatureStream(data_dir)
        self.model_ensemble = ModelEnsemble(self.config.get('ml_config', {}))
        self.auto_tuner = AutoTuner(self.config.get('rl_config', {}))
        
        # State
        self.running = False
        self.thread = None
        self.stop_event = Event()
        
        # Training state
        self.last_training = None
        self.training_interval = self.config.get('training_interval_hours', 24)
        self.models_trained = False
        
        # Recommendations
        self.latest_recommendation = None
        self.recommendation_history = []
        
        # Mode
        self.mode = self.config.get('mode', 'supervised')  # 'supervised', 'rl', 'hybrid'
        
        # Paths
        self.output_dir = self.config.get('output_dir', 'ML_RL/models')
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.logger.info(
            f"MLRLOrchestrator initialized in {self.mode} mode"
        )
    
    def start(self):
        """Start orchestrator in background thread."""
        if self.running:
            self.logger.warning("Orchestrator already running")
            return
        
        self.running = True
        self.stop_event.clear()
        
        self.thread = Thread(
            target=self._orchestration_loop,
            name="ml-rl-orchestrator",
            daemon=True
        )
        self.thread.start()
        
        self.logger.info("Orchestrator started in background")
    
    def stop(self, timeout: float = 10.0):
        """Stop orchestrator."""
        if not self.running:
            return
        
        self.logger.info("Stopping orchestrator...")
        self.stop_event.set()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)
        
        self.running = False
        self.logger.info("Orchestrator stopped")
    
    def _orchestration_loop(self):
        """
        Main orchestration loop.
        
        Runs in background thread, fully decoupled from trading.
        """
        self.logger.info("Orchestration loop started")
        
        # Initial training if needed
        if not self.models_trained:
            self._perform_training()
        
        while not self.stop_event.is_set():
            try:
                # Check if retraining needed
                if self._should_retrain():
                    self._perform_training()
                
                # Poll for new events
                new_events = self.feature_stream.poll_new_events()
                
                if new_events:
                    self.logger.debug(f"Polled {len(new_events)} new events")
                    self._process_events(new_events)
                
                # Generate recommendation if needed
                if self._should_recommend():
                    self._generate_recommendation()
                
                # Sleep to avoid busy waiting
                self.stop_event.wait(timeout=60.0)  # Check every minute
            
            except Exception as e:
                self.logger.error(f"Error in orchestration loop: {e}", exc_info=True)
                self.stop_event.wait(timeout=60.0)
        
        self.logger.info("Orchestration loop exited")
    
    def _should_retrain(self) -> bool:
        """Check if models should be retrained."""
        if not self.last_training:
            return True
        
        elapsed = datetime.now() - self.last_training
        return elapsed > timedelta(hours=self.training_interval)
    
    def _should_recommend(self) -> bool:
        """Check if new recommendation should be generated."""
        if not self.latest_recommendation:
            return True
        
        # Generate recommendation every hour
        elapsed = datetime.now() - self.latest_recommendation.timestamp
        return elapsed > timedelta(hours=1)
    
    def _perform_training(self):
        """Perform model training."""
        self.logger.info("Starting model training...")
        
        try:
            # Extract features from all available data
            dataset, _ = self.feature_extractor.create_training_dataset()
            
            if not dataset:
                self.logger.warning("No data available for training")
                return
            
            # Train ensemble
            results = self.model_ensemble.train_ensemble(dataset)
            
            # Save models
            self.model_ensemble.save_models(self.output_dir)
            
            self.models_trained = True
            self.last_training = datetime.now()
            
            self.logger.info(
                f"Training complete: {results.get('n_samples', 0)} samples, "
                f"{len(self.model_ensemble.models)} models trained"
            )
        
        except Exception as e:
            self.logger.error(f"Training failed: {e}", exc_info=True)
    
    def _process_events(self, events: List[Dict[str, Any]]):
        """
        Process new events for online learning.
        
        Args:
            events: New events to process
        """
        # Extract features
        trade_features = self.feature_extractor.extract_trade_features(events)
        
        if not trade_features:
            return
        
        # Update model performance if we have predictions
        for features in trade_features:
            # Check if we have a prediction for this trade
            # (In production, track predictions and outcomes)
            pass
        
        # Update RL agents if in RL mode
        if self.mode in ['rl', 'hybrid']:
            for features in trade_features:
                # Convert to RL format and update
                state = {
                    'volatility_regime': features.market_regime,
                    'trend_regime': features.market_regime,
                    'recent_win_rate': 0.5,  # Would track this
                    'current_drawdown': 0.0
                }
                
                action = {
                    'position_size_multiplier': features.position_size,
                    'risk_per_trade': 0.02,
                    'stop_loss_multiplier': features.stop_loss_pct,
                    'take_profit_multiplier': features.take_profit_pct
                }
                
                reward = features.pnl
                
                next_state = state.copy()
                next_state['recent_win_rate'] = 0.5 + (0.1 if features.was_win else -0.1)
                
                self.auto_tuner.update_from_outcome(state, action, reward, next_state)
    
    def _generate_recommendation(self):
        """Generate parameter tuning recommendation."""
        try:
            # Get current state (would come from monitoring in production)
            current_state = {
                'volatility_regime': 'medium',
                'trend_regime': 'ranging',
                'recent_win_rate': 0.5,
                'current_drawdown': 0.0
            }
            
            if self.mode == 'supervised':
                # Use ML models for prediction
                features = {
                    'hour_of_day': datetime.now().hour,
                    'day_of_week': datetime.now().weekday(),
                    'volatility': 0.01,
                    'trend_strength': 0.5,
                    'signal_confidence': 0.7,
                    'position_size': 1.0,
                    'stop_loss_pct': 0.02,
                    'take_profit_pct': 0.04
                }
                
                prediction = self.model_ensemble.argmax_predict(features)
                
                if prediction:
                    # Convert prediction to parameter recommendation
                    parameters = {
                        'position_size_multiplier': 1.0,
                        'risk_per_trade': 0.02,
                        'expected_pnl': prediction.predicted_pnl
                    }
                    
                    recommendation = TuningRecommendation(
                        timestamp=datetime.now(),
                        source='ml_ensemble',
                        parameters=parameters,
                        confidence=prediction.confidence,
                        rationale=f"Model {prediction.model_name} predicts {prediction.predicted_pnl:.2f}"
                    )
                else:
                    return
            
            elif self.mode == 'rl':
                # Use RL agents
                parameters = self.auto_tuner.suggest_parameters(current_state)
                
                recommendation = TuningRecommendation(
                    timestamp=datetime.now(),
                    source=f'rl_{self.auto_tuner.mode}',
                    parameters=parameters,
                    confidence=0.7,
                    rationale=f"RL agent suggests adjustments"
                )
            
            else:  # hybrid
                # Combine ML and RL
                ml_features = {
                    'hour_of_day': datetime.now().hour,
                    'day_of_week': datetime.now().weekday(),
                    'signal_confidence': 0.7,
                    'position_size': 1.0
                }
                
                ml_pred = self.model_ensemble.argmax_predict(ml_features)
                rl_params = self.auto_tuner.suggest_parameters(current_state)
                
                # Combine recommendations
                parameters = rl_params.copy()
                if ml_pred:
                    parameters['expected_pnl'] = ml_pred.predicted_pnl
                
                recommendation = TuningRecommendation(
                    timestamp=datetime.now(),
                    source='hybrid',
                    parameters=parameters,
                    confidence=0.75,
                    rationale="Combined ML prediction and RL optimization"
                )
            
            self.latest_recommendation = recommendation
            self.recommendation_history.append(recommendation)
            
            # Save recommendation
            self._save_recommendation(recommendation)
            
            self.logger.info(
                f"Generated recommendation from {recommendation.source}: "
                f"{recommendation.parameters}"
            )
        
        except Exception as e:
            self.logger.error(f"Failed to generate recommendation: {e}", exc_info=True)
    
    def _save_recommendation(self, recommendation: TuningRecommendation):
        """Save recommendation to disk."""
        try:
            filepath = os.path.join(
                self.output_dir,
                f"recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(filepath, 'w') as f:
                json.dump(recommendation.to_dict(), f, indent=2)
            
            # Also update latest.json
            latest_path = os.path.join(self.output_dir, 'latest_recommendation.json')
            with open(latest_path, 'w') as f:
                json.dump(recommendation.to_dict(), f, indent=2)
        
        except Exception as e:
            self.logger.warning(f"Failed to save recommendation: {e}")
    
    def train_supervised(self) -> Dict[str, Any]:
        """
        Trigger supervised training manually.
        
        Returns:
            Training results
        """
        self.logger.info("Manual supervised training triggered")
        
        dataset, _ = self.feature_extractor.create_training_dataset()
        
        if not dataset:
            return {'error': 'no_data'}
        
        results = self.model_ensemble.train_ensemble(dataset)
        self.model_ensemble.save_models(self.output_dir)
        
        self.models_trained = True
        self.last_training = datetime.now()
        
        return results
    
    def get_latest_recommendation(self) -> Optional[TuningRecommendation]:
        """Get latest tuning recommendation."""
        return self.latest_recommendation
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            'running': self.running,
            'mode': self.mode,
            'models_trained': self.models_trained,
            'last_training': self.last_training.isoformat() if self.last_training else None,
            'recommendations_generated': len(self.recommendation_history),
            'latest_recommendation': self.latest_recommendation.to_dict() if self.latest_recommendation else None,
            'ml_ensemble': {
                'models_loaded': list(self.model_ensemble.models.keys()),
                'model_scores': self.model_ensemble.model_scores
            },
            'auto_tuner': self.auto_tuner.get_statistics()
        }


def create_orchestrator(config: Optional[Dict[str, Any]] = None) -> MLRLOrchestrator:
    """
    Factory function to create orchestrator.
    
    Args:
        config: Configuration parameters
        
    Returns:
        Initialized orchestrator
    """
    return MLRLOrchestrator(config)
