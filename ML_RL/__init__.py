"""
ML/RL Module

Machine Learning and Reinforcement Learning system for Cthulu auto-tuning.
Fully decoupled from main trading loop - runs asynchronously.

Components:
- feature_engineering: Extract features from event streams
- ml_models: Supervised learning with LightGBM, XGBoost, Neural Nets
- reinforcement_learning: Q-Learning and Policy Gradient agents
- orchestrator: Main orchestration system
- instrumentation: Event collection (existing)
"""

from .instrumentation import MLDataCollector
from .feature_engineering import FeatureExtractor, RealtimeFeatureStream, TradeFeatures
from .ml_models import ModelEnsemble, ModelPrediction
from .reinforcement_learning import (
    QLearningAgent,
    PolicyGradientAgent,
    AutoTuner,
    RLState,
    RLAction
)
from .orchestrator import MLRLOrchestrator, TuningRecommendation, create_orchestrator

__all__ = [
    # Instrumentation
    'MLDataCollector',
    
    # Feature Engineering
    'FeatureExtractor',
    'RealtimeFeatureStream',
    'TradeFeatures',
    
    # ML Models
    'ModelEnsemble',
    'ModelPrediction',
    
    # Reinforcement Learning
    'QLearningAgent',
    'PolicyGradientAgent',
    'AutoTuner',
    'RLState',
    'RLAction',
    
    # Orchestration
    'MLRLOrchestrator',
    'TuningRecommendation',
    'create_orchestrator'
]
