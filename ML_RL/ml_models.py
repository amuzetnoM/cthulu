"""
ML Model Training Module

Trains supervised learning models to predict trade outcomes and optimize parameters.
Supports LightGBM, XGBoost, and Neural Networks with argmax model selection.
Fully decoupled from main trading loop.
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import numpy as np


@dataclass
class ModelPrediction:
    """Prediction from a trained model."""
    model_name: str
    predicted_pnl: float
    predicted_win_prob: float
    confidence: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'model_name': self.model_name,
            'predicted_pnl': self.predicted_pnl,
            'predicted_win_prob': self.predicted_win_prob,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat()
        }


class ModelEnsemble:
    """
    Ensemble of ML models with argmax selection.
    
    Trains multiple models and uses argmax to select the best prediction.
    Supports LightGBM, XGBoost, and simple neural networks.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize model ensemble.
        
        Args:
            config: Configuration parameters
        """
        self.logger = logging.getLogger("Cthulu.ml_ensemble")
        self.config = config or {}
        
        # Model performance tracking
        self.model_scores = {
            'lightgbm': {'predictions': 0, 'mae': 0.0, 'accuracy': 0.0},
            'xgboost': {'predictions': 0, 'mae': 0.0, 'accuracy': 0.0},
            'neural_net': {'predictions': 0, 'mae': 0.0, 'accuracy': 0.0}
        }
        
        # Trained models (placeholder - will be populated during training)
        self.models = {}
        
        self.logger.info("ModelEnsemble initialized")
    
    def train_lightgbm(
        self,
        features: np.ndarray,
        targets: np.ndarray,
        feature_names: List[str]
    ) -> Any:
        """
        Train LightGBM model.
        
        Args:
            features: Feature matrix (N x D)
            targets: Target values (N,)
            feature_names: Feature names
            
        Returns:
            Trained model
        """
        try:
            import lightgbm as lgb
            
            # Create dataset
            train_data = lgb.Dataset(features, label=targets, feature_name=feature_names)
            
            # Parameters
            params = {
                'objective': 'regression',
                'metric': 'mae',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.9,
                'verbose': -1
            }
            
            # Train
            model = lgb.train(
                params,
                train_data,
                num_boost_round=100,
                valid_sets=[train_data],
                callbacks=[lgb.log_evaluation(period=0)]  # Silent
            )
            
            self.logger.info("LightGBM model trained successfully")
            return model
        
        except ImportError:
            self.logger.warning("LightGBM not installed, skipping")
            return None
        except Exception as e:
            self.logger.error(f"Failed to train LightGBM: {e}")
            return None
    
    def train_xgboost(
        self,
        features: np.ndarray,
        targets: np.ndarray,
        feature_names: List[str]
    ) -> Any:
        """
        Train XGBoost model.
        
        Args:
            features: Feature matrix
            targets: Target values
            feature_names: Feature names
            
        Returns:
            Trained model
        """
        try:
            import xgboost as xgb
            
            # Create DMatrix
            dtrain = xgb.DMatrix(features, label=targets, feature_names=feature_names)
            
            # Parameters
            params = {
                'objective': 'reg:squarederror',
                'eval_metric': 'mae',
                'max_depth': 6,
                'learning_rate': 0.05,
                'subsample': 0.9,
                'colsample_bytree': 0.9,
                'verbosity': 0
            }
            
            # Train
            model = xgb.train(
                params,
                dtrain,
                num_boost_round=100,
                evals=[(dtrain, 'train')],
                verbose_eval=False
            )
            
            self.logger.info("XGBoost model trained successfully")
            return model
        
        except ImportError:
            self.logger.warning("XGBoost not installed, skipping")
            return None
        except Exception as e:
            self.logger.error(f"Failed to train XGBoost: {e}")
            return None
    
    def train_neural_net(
        self,
        features: np.ndarray,
        targets: np.ndarray
    ) -> Any:
        """
        Train simple neural network.
        
        Args:
            features: Feature matrix
            targets: Target values
            
        Returns:
            Trained model (dict with weights)
        """
        # Simple feedforward network using numpy
        # This is a placeholder - in production, use PyTorch/TensorFlow
        
        n_features = features.shape[1]
        n_hidden = 32
        
        # Initialize weights
        np.random.seed(42)
        W1 = np.random.randn(n_features, n_hidden) * 0.01
        b1 = np.zeros((1, n_hidden))
        W2 = np.random.randn(n_hidden, 1) * 0.01
        b2 = np.zeros((1, 1))
        
        # Simple training loop (very basic)
        learning_rate = 0.001
        n_epochs = 50
        
        for epoch in range(n_epochs):
            # Forward pass
            z1 = np.dot(features, W1) + b1
            a1 = np.maximum(0, z1)  # ReLU
            z2 = np.dot(a1, W2) + b2
            predictions = z2.flatten()
            
            # Loss (MSE)
            loss = np.mean((predictions - targets) ** 2)
            
            # Backward pass (simplified)
            d_loss = 2 * (predictions - targets) / len(targets)
            d_z2 = d_loss.reshape(-1, 1)
            d_W2 = np.dot(a1.T, d_z2)
            d_b2 = np.sum(d_z2, axis=0, keepdims=True)
            d_a1 = np.dot(d_z2, W2.T)
            d_z1 = d_a1 * (z1 > 0)  # ReLU derivative
            d_W1 = np.dot(features.T, d_z1)
            d_b1 = np.sum(d_z1, axis=0, keepdims=True)
            
            # Update weights
            W1 -= learning_rate * d_W1
            b1 -= learning_rate * d_b1
            W2 -= learning_rate * d_W2
            b2 -= learning_rate * d_b2
        
        model = {
            'W1': W1,
            'b1': b1,
            'W2': W2,
            'b2': b2
        }
        
        self.logger.info("Neural network trained successfully")
        return model
    
    def train_ensemble(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Train all models in the ensemble.
        
        Args:
            dataset: Training dataset
            
        Returns:
            Training results
        """
        if not dataset:
            self.logger.warning("Empty dataset, cannot train")
            return {'error': 'empty_dataset'}
        
        self.logger.info(f"Training ensemble on {len(dataset)} samples")
        
        # Extract features and targets
        feature_names = [
            'hour_of_day', 'day_of_week', 'volatility', 'trend_strength',
            'signal_confidence', 'position_size', 'stop_loss_pct', 'take_profit_pct'
        ]
        
        features = []
        targets = []
        
        for sample in dataset:
            # Extract feature values
            feature_vec = []
            for fname in feature_names:
                val = sample.get(fname, 0.0)
                # Handle non-numeric values
                if isinstance(val, (int, float)):
                    feature_vec.append(float(val))
                else:
                    feature_vec.append(0.0)
            
            features.append(feature_vec)
            targets.append(sample.get('pnl', 0.0))
        
        features = np.array(features)
        targets = np.array(targets)
        
        # Train each model
        results = {}
        
        # LightGBM
        lgb_model = self.train_lightgbm(features, targets, feature_names)
        if lgb_model:
            self.models['lightgbm'] = lgb_model
            results['lightgbm'] = 'trained'
        
        # XGBoost
        xgb_model = self.train_xgboost(features, targets, feature_names)
        if xgb_model:
            self.models['xgboost'] = xgb_model
            results['xgboost'] = 'trained'
        
        # Neural Network
        nn_model = self.train_neural_net(features, targets)
        if nn_model:
            self.models['neural_net'] = nn_model
            results['neural_net'] = 'trained'
        
        results['n_samples'] = len(dataset)
        results['feature_names'] = feature_names
        
        self.logger.info(f"Ensemble training complete: {results}")
        return results
    
    def predict_ensemble(self, features: Dict[str, float]) -> List[ModelPrediction]:
        """
        Get predictions from all models.
        
        Args:
            features: Feature dictionary
            
        Returns:
            List of predictions from each model
        """
        predictions = []
        timestamp = datetime.now()
        
        # Extract feature vector
        feature_names = [
            'hour_of_day', 'day_of_week', 'volatility', 'trend_strength',
            'signal_confidence', 'position_size', 'stop_loss_pct', 'take_profit_pct'
        ]
        
        feature_vec = np.array([[features.get(fname, 0.0) for fname in feature_names]])
        
        # LightGBM prediction
        if 'lightgbm' in self.models:
            try:
                pred = self.models['lightgbm'].predict(feature_vec)[0]
                predictions.append(ModelPrediction(
                    model_name='lightgbm',
                    predicted_pnl=pred,
                    predicted_win_prob=1.0 / (1.0 + np.exp(-pred)),  # Sigmoid
                    confidence=0.8,
                    timestamp=timestamp
                ))
            except Exception as e:
                self.logger.warning(f"LightGBM prediction failed: {e}")
        
        # XGBoost prediction
        if 'xgboost' in self.models:
            try:
                import xgboost as xgb
                dtest = xgb.DMatrix(feature_vec, feature_names=feature_names)
                pred = self.models['xgboost'].predict(dtest)[0]
                predictions.append(ModelPrediction(
                    model_name='xgboost',
                    predicted_pnl=pred,
                    predicted_win_prob=1.0 / (1.0 + np.exp(-pred)),
                    confidence=0.8,
                    timestamp=timestamp
                ))
            except Exception as e:
                self.logger.warning(f"XGBoost prediction failed: {e}")
        
        # Neural Network prediction
        if 'neural_net' in self.models:
            try:
                model = self.models['neural_net']
                z1 = np.dot(feature_vec, model['W1']) + model['b1']
                a1 = np.maximum(0, z1)
                z2 = np.dot(a1, model['W2']) + model['b2']
                pred = z2[0, 0]
                predictions.append(ModelPrediction(
                    model_name='neural_net',
                    predicted_pnl=pred,
                    predicted_win_prob=1.0 / (1.0 + np.exp(-pred)),
                    confidence=0.7,
                    timestamp=timestamp
                ))
            except Exception as e:
                self.logger.warning(f"Neural net prediction failed: {e}")
        
        return predictions
    
    def argmax_predict(self, features: Dict[str, float]) -> Optional[ModelPrediction]:
        """
        Use argmax to select best model prediction.
        
        Selects the model with highest historical accuracy.
        
        Args:
            features: Feature dictionary
            
        Returns:
            Best prediction
        """
        predictions = self.predict_ensemble(features)
        
        if not predictions:
            return None
        
        # Use argmax over model scores (accuracy)
        best_model = max(
            self.model_scores.items(),
            key=lambda x: x[1]['accuracy']
        )[0]
        
        # Find prediction from best model
        for pred in predictions:
            if pred.model_name == best_model:
                self.logger.info(
                    f"Argmax selected {best_model}: pnl={pred.predicted_pnl:.2f}"
                )
                return pred
        
        # Fallback to first prediction
        return predictions[0]
    
    def update_model_performance(
        self,
        model_name: str,
        predicted_pnl: float,
        actual_pnl: float
    ):
        """
        Update model performance tracking.
        
        Args:
            model_name: Name of model
            predicted_pnl: Predicted P&L
            actual_pnl: Actual P&L
        """
        if model_name not in self.model_scores:
            return
        
        scores = self.model_scores[model_name]
        n = scores['predictions']
        
        # Update MAE (moving average)
        error = abs(predicted_pnl - actual_pnl)
        scores['mae'] = (scores['mae'] * n + error) / (n + 1)
        
        # Update accuracy (correct sign prediction)
        correct = (predicted_pnl > 0) == (actual_pnl > 0)
        scores['accuracy'] = (scores['accuracy'] * n + (1.0 if correct else 0.0)) / (n + 1)
        
        scores['predictions'] = n + 1
        
        self.logger.debug(
            f"Updated {model_name}: mae={scores['mae']:.3f}, "
            f"accuracy={scores['accuracy']:.2%}"
        )
    
    def save_models(self, output_dir: str):
        """
        Save trained models to disk.
        
        Args:
            output_dir: Directory to save models
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Save LightGBM
        if 'lightgbm' in self.models:
            try:
                path = os.path.join(output_dir, 'lightgbm_model.txt')
                self.models['lightgbm'].save_model(path)
                self.logger.info(f"Saved LightGBM to {path}")
            except Exception as e:
                self.logger.error(f"Failed to save LightGBM: {e}")
        
        # Save XGBoost
        if 'xgboost' in self.models:
            try:
                path = os.path.join(output_dir, 'xgboost_model.json')
                self.models['xgboost'].save_model(path)
                self.logger.info(f"Saved XGBoost to {path}")
            except Exception as e:
                self.logger.error(f"Failed to save XGBoost: {e}")
        
        # Save Neural Network
        if 'neural_net' in self.models:
            try:
                path = os.path.join(output_dir, 'neural_net_weights.json')
                # Convert numpy arrays to lists
                weights = {
                    k: v.tolist() for k, v in self.models['neural_net'].items()
                }
                with open(path, 'w') as f:
                    json.dump(weights, f)
                self.logger.info(f"Saved Neural Net to {path}")
            except Exception as e:
                self.logger.error(f"Failed to save Neural Net: {e}")
        
        # Save performance scores
        try:
            scores_path = os.path.join(output_dir, 'model_scores.json')
            with open(scores_path, 'w') as f:
                json.dump(self.model_scores, f, indent=2)
            self.logger.info(f"Saved model scores to {scores_path}")
        except Exception as e:
            self.logger.error(f"Failed to save scores: {e}")
    
    def load_models(self, input_dir: str):
        """
        Load trained models from disk.
        
        Args:
            input_dir: Directory containing saved models
        """
        # Load LightGBM
        try:
            import lightgbm as lgb
            path = os.path.join(input_dir, 'lightgbm_model.txt')
            if os.path.exists(path):
                self.models['lightgbm'] = lgb.Booster(model_file=path)
                self.logger.info("Loaded LightGBM model")
        except Exception as e:
            self.logger.warning(f"Failed to load LightGBM: {e}")
        
        # Load XGBoost
        try:
            import xgboost as xgb
            path = os.path.join(input_dir, 'xgboost_model.json')
            if os.path.exists(path):
                model = xgb.Booster()
                model.load_model(path)
                self.models['xgboost'] = model
                self.logger.info("Loaded XGBoost model")
        except Exception as e:
            self.logger.warning(f"Failed to load XGBoost: {e}")
        
        # Load Neural Network
        try:
            path = os.path.join(input_dir, 'neural_net_weights.json')
            if os.path.exists(path):
                with open(path, 'r') as f:
                    weights = json.load(f)
                # Convert lists back to numpy arrays
                self.models['neural_net'] = {
                    k: np.array(v) for k, v in weights.items()
                }
                self.logger.info("Loaded Neural Net model")
        except Exception as e:
            self.logger.warning(f"Failed to load Neural Net: {e}")
        
        # Load performance scores
        try:
            scores_path = os.path.join(input_dir, 'model_scores.json')
            if os.path.exists(scores_path):
                with open(scores_path, 'r') as f:
                    self.model_scores = json.load(f)
                self.logger.info("Loaded model scores")
        except Exception as e:
            self.logger.warning(f"Failed to load scores: {e}")
