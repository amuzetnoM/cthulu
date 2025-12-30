# ML/RL Auto-Tuning System for Cthulu

## Overview

Fully decoupled Machine Learning and Reinforcement Learning system for autonomous parameter tuning and optimization. Runs independently from the main trading loop with zero performance impact.

## Quick Start

```python
from ML_RL import create_orchestrator

# Create orchestrator with hybrid mode (ML + RL)
config = {
    'mode': 'hybrid',
    'training_interval_hours': 24
}

orchestrator = create_orchestrator(config)
orchestrator.start()  # Runs in background thread

# Get latest recommendation
recommendation = orchestrator.get_latest_recommendation()
print(f"Suggested parameters: {recommendation.parameters}")
```

## Architecture

The system is fully decoupled from the main trading loop:

1. **Main Loop** writes events to `ML_RL/data/raw/*.jsonl.gz`
2. **Orchestrator** reads events asynchronously in background
3. **Models** train on historical data periodically
4. **Recommendations** written to `ML_RL/models/latest_recommendation.json`

**Zero impact on main loop performance.**

## Components

### 1. Feature Engineering
- Extracts features from event streams
- Real-time and batch processing
- 18+ features per trade

### 2. ML Models (Supervised Learning)
- **LightGBM**: Gradient boosting
- **XGBoost**: Extreme gradient boosting  
- **Neural Net**: Feedforward network
- **Argmax Selection**: Best model by accuracy

### 3. Reinforcement Learning
- **Q-Learning**: Argmax action selection, epsilon-greedy exploration
- **Policy Gradient**: Softmax policy, REINFORCE algorithm
- **Auto-Tuner**: Combined parameter optimization

### 4. Orchestrator
- Background thread coordination
- Periodic training (default: 24h)
- Hourly recommendations
- Model persistence

## Argmax Integration

### ML Ensemble with Argmax
```python
prediction = ensemble.argmax_predict(features)
# Selects model with highest historical accuracy
```

### Q-Learning with Argmax
```python
action = agent.select_action(state, mode='greedy')
# action = argmax_a Q(state, a)
```

### Policy Gradient with Softmax
```python
action = agent.select_action(state)
# π(a|s) = softmax(θ(s,a))
```

## Usage Modes

### Supervised Training
Train on historical data:
```python
config = {'mode': 'supervised'}
orchestrator = create_orchestrator(config)
results = orchestrator.train_supervised()
```

### Reinforcement Learning
Online parameter tuning:
```python
config = {'mode': 'rl', 'rl_config': {'mode': 'rl_q'}}
orchestrator = create_orchestrator(config)
orchestrator.start()
```

### Hybrid (Recommended)
Combine ML + RL:
```python
config = {'mode': 'hybrid'}
orchestrator = create_orchestrator(config)
orchestrator.start()
```

## Integration

### Read Recommendations
```python
import json

with open('ML_RL/models/latest_recommendation.json', 'r') as f:
    rec = json.load(f)

# Apply recommended parameters
position_size = rec['parameters']['position_size_multiplier']
risk = rec['parameters']['risk_per_trade']
```

### Optional Auto-Application
```python
# In trading loop (optional)
if config.get('ml_rl_auto_apply', False):
    try:
        rec = load_latest_recommendation()
        self.apply_parameters(rec['parameters'])
    except Exception as e:
        logger.warning(f"ML/RL auto-apply failed: {e}")
```

## Installation

```bash
# Core (required)
pip install numpy

# Optional (for full ML)
pip install lightgbm xgboost scipy scikit-learn pandas
```

## File Structure

```
ML_RL/
├── __init__.py                    # Module exports
├── instrumentation.py             # Event collection
├── feature_engineering.py         # Feature extraction
├── ml_models.py                   # ML models
├── reinforcement_learning.py      # RL agents
├── orchestrator.py                # Main orchestrator
├── ARGMAX_RL_INTEGRATION.md      # Integration roadmap
├── README.md                      # This file
├── data/raw/                      # Event data
└── models/                        # Trained models + recommendations
```

## Monitoring

```python
stats = orchestrator.get_statistics()
print(f"Models trained: {stats['models_trained']}")
print(f"Recommendations: {stats['recommendations_generated']}")
print(f"Mode: {stats['mode']}")
```

## Best Practices

1. **Start Supervised**: Train on historical data first
2. **Graduate to RL**: After 1000+ trades
3. **Use Hybrid**: Best for production
4. **Regular Retraining**: Daily recommended
5. **Validate First**: Review before auto-applying

## Performance

- **Decoupled**: Zero impact on main loop
- **Async**: Background thread processing
- **Efficient**: Event streaming, not polling
- **Scalable**: Handles millions of events

## Status

✅ Production-Ready  
✅ Zero Main Loop Impact  
✅ Argmax Integration Complete  
✅ Fully Documented

For detailed documentation, see inline docstrings and `ARGMAX_RL_INTEGRATION.md`.
