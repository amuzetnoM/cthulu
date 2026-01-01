# Cthulu Cognition: AI/ML/RL Integration Proposal

<div align="center">

![APEX](https://img.shields.io/badge/APEX-v5.1.0-4B0082?style=flat-square)
![Status](https://img.shields.io/badge/Status-Proposal-orange?style=flat-square)
![Priority](https://img.shields.io/badge/Priority-High-red?style=flat-square)

**The Soul of the System**

</div>

---

## Executive Summary

This proposal outlines a comprehensive AI/ML/RL integration strategy for Cthulu, transforming it from a rule-based trading system into an adaptive, self-improving market predator. The goal is to complement (not replace) the robust rule-based foundation with intelligent decision-making capabilities.

---

## 1. Market Regime Classifier

### Purpose
Detect current market conditions to adapt trading behavior dynamically.

### Implementation

```python
class MarketRegimeClassifier:
    """
    Classifies market into: BULL, BEAR, SIDEWAYS, VOLATILE, CHOPPY
    Uses softmax for probability distribution across regimes.
    """
    
    REGIMES = ['BULL', 'BEAR', 'SIDEWAYS', 'VOLATILE', 'CHOPPY']
    
    def __init__(self):
        self.features = [
            'trend_strength',      # ADX value
            'price_momentum',      # ROC/momentum
            'volatility_ratio',    # ATR/price
            'volume_trend',        # Volume MA ratio
            'higher_highs_count',  # Trend structure
            'lower_lows_count',    # Trend structure
            'range_bound_score',   # Bollinger %B variance
        ]
    
    def classify(self, market_data: pd.DataFrame) -> Dict[str, float]:
        """
        Returns softmax probabilities for each regime.
        
        Example output:
        {
            'BULL': 0.65,
            'BEAR': 0.05,
            'SIDEWAYS': 0.15,
            'VOLATILE': 0.10,
            'CHOPPY': 0.05
        }
        """
        features = self._extract_features(market_data)
        logits = self._compute_logits(features)
        return self._softmax(logits)
    
    def _softmax(self, logits: np.ndarray) -> Dict[str, float]:
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / exp_logits.sum()
        return dict(zip(self.REGIMES, probs))
```

### Integration Points
- **Signal Generator**: Adjust confidence based on favorable regime
- **Risk Manager**: Tighten/loosen based on volatility regime
- **Strategy Selector**: Weight strategies by regime compatibility

---

## 2. Price Predictor (Softmax/Argmax)

### Purpose
Predict next-bar direction with probability distribution.

### Architecture

```
Input Features (60 bars)
         │
    ┌────┴────┐
    │ LSTM    │  Temporal patterns
    │ Layer   │
    └────┬────┘
         │
    ┌────┴────┐
    │ Attention│  Focus on key bars
    │ Layer   │
    └────┬────┘
         │
    ┌────┴────┐
    │ Dense   │  Feature compression
    │ Layers  │
    └────┬────┘
         │
    ┌────┴────┐
    │ Softmax │  Direction probabilities
    │ Output  │
    └────┴────┘
         │
    [UP: 0.65, DOWN: 0.20, NEUTRAL: 0.15]
```

### Implementation

```python
class PricePredictor:
    """
    Softmax-based direction predictor.
    Outputs probability distribution over {UP, DOWN, NEUTRAL}
    Argmax selects the most likely direction.
    """
    
    DIRECTIONS = ['UP', 'DOWN', 'NEUTRAL']
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = self._load_or_create_model(model_path)
        self.scaler = StandardScaler()
        self.lookback = 60
        self.confidence_threshold = 0.60
    
    def predict(self, ohlcv: pd.DataFrame) -> Dict:
        """
        Returns:
        {
            'direction': 'UP',           # argmax result
            'confidence': 0.65,          # max probability
            'probabilities': {           # softmax output
                'UP': 0.65,
                'DOWN': 0.20,
                'NEUTRAL': 0.15
            },
            'actionable': True           # confidence > threshold
        }
        """
        features = self._prepare_features(ohlcv)
        probs = self.model.predict(features)
        
        direction_idx = np.argmax(probs)
        confidence = probs[direction_idx]
        
        return {
            'direction': self.DIRECTIONS[direction_idx],
            'confidence': float(confidence),
            'probabilities': dict(zip(self.DIRECTIONS, probs.tolist())),
            'actionable': confidence >= self.confidence_threshold
        }
    
    def _prepare_features(self, ohlcv: pd.DataFrame) -> np.ndarray:
        """
        Feature engineering for prediction:
        - Price changes (returns)
        - Technical indicators
        - Volume patterns
        - Volatility measures
        """
        features = []
        
        # Price-based features
        features.extend([
            ohlcv['close'].pct_change(),
            ohlcv['high'] - ohlcv['low'],  # Range
            (ohlcv['close'] - ohlcv['open']) / ohlcv['open'],  # Body
        ])
        
        # Technical indicators (already calculated by Cthulu)
        # RSI, MACD, Bollinger, ATR, etc.
        
        return self.scaler.fit_transform(np.array(features).T)
```

### Training Data Requirements
- Minimum 2 years of historical OHLCV data
- Labels: Next bar direction (UP if close > open + threshold, etc.)
- Walk-forward validation to prevent lookahead bias

---

## 3. Exit Oracle Enhancement

### Purpose
High-confluence exit signals using reverse indicator detection.

### Architecture

```python
class ExitOracle:
    """
    Generates exit signals based on:
    1. Reversal indicator confluence
    2. Profit target achievement
    3. Risk threshold breach
    4. Time-based exits
    """
    
    def __init__(self, position_tracker: PositionTracker):
        self.positions = position_tracker
        self.reversal_detectors = [
            RSIReversalDetector(),
            MACDCrossoverDetector(),
            BollingerBandBreachDetector(),
            CandlePatternDetector(),
            VolumeClimaxDetector(),
        ]
        self.confluence_threshold = 3  # Minimum signals for exit
    
    def evaluate_exits(self) -> List[ExitSignal]:
        """
        Evaluate all positions for exit conditions.
        Returns high-confidence exit signals.
        """
        exit_signals = []
        
        for position in self.positions.get_active():
            reversal_score = self._calculate_reversal_score(position)
            profit_status = self._evaluate_profit_status(position)
            risk_status = self._evaluate_risk_status(position)
            
            # Confluence check
            signals_triggered = sum([
                reversal_score >= self.confluence_threshold,
                profit_status['target_hit'],
                risk_status['stop_triggered'],
            ])
            
            if signals_triggered >= 1:
                exit_signals.append(ExitSignal(
                    ticket=position.ticket,
                    reason=self._determine_exit_reason(
                        reversal_score, profit_status, risk_status
                    ),
                    confidence=self._calculate_exit_confidence(
                        reversal_score, profit_status, risk_status
                    ),
                    urgency=self._calculate_urgency(position)
                ))
        
        return exit_signals
    
    def _calculate_reversal_score(self, position) -> int:
        """
        Count how many reversal detectors are signaling.
        """
        score = 0
        for detector in self.reversal_detectors:
            if detector.is_signaling(position.symbol, position.direction):
                score += 1
        return score
```

### Reversal Detection Signals

| Detector | LONG Exit Signal | SHORT Exit Signal |
|----------|------------------|-------------------|
| RSI | RSI > 70 and falling | RSI < 30 and rising |
| MACD | MACD crosses below signal | MACD crosses above signal |
| Bollinger | Price touches upper band | Price touches lower band |
| Candle | Bearish engulfing | Bullish engulfing |
| Volume | Climax volume + reversal | Climax volume + reversal |

---

## 4. Sentiment Analyzer

### Purpose
Incorporate news and social sentiment into trading decisions.

### Data Sources
1. **Financial News APIs**: Reuters, Bloomberg, Alpha Vantage
2. **Social Media**: Twitter/X sentiment via API
3. **Economic Calendar**: High-impact events
4. **Market Fear Indices**: VIX, Fear & Greed Index

### Implementation

```python
class SentimentAnalyzer:
    """
    Aggregates sentiment from multiple sources.
    Outputs normalized sentiment score [-1, +1]
    """
    
    def __init__(self):
        self.news_analyzer = NewsAnalyzer()
        self.social_analyzer = SocialAnalyzer()
        self.calendar_analyzer = EconomicCalendar()
        
        # Source weights
        self.weights = {
            'news': 0.40,
            'social': 0.25,
            'calendar': 0.35
        }
    
    def get_sentiment(self, symbol: str) -> Dict:
        """
        Returns:
        {
            'score': 0.35,           # Weighted average [-1, +1]
            'direction': 'BULLISH',  # BULLISH, BEARISH, NEUTRAL
            'confidence': 0.72,      # Agreement across sources
            'components': {
                'news': 0.45,
                'social': 0.20,
                'calendar': 0.40
            },
            'events': [
                {'type': 'FOMC', 'impact': 'HIGH', 'time': '14:00 UTC'}
            ]
        }
        """
        news_score = self.news_analyzer.analyze(symbol)
        social_score = self.social_analyzer.analyze(symbol)
        calendar_impact = self.calendar_analyzer.get_upcoming(symbol)
        
        weighted_score = (
            news_score * self.weights['news'] +
            social_score * self.weights['social'] +
            calendar_impact * self.weights['calendar']
        )
        
        return {
            'score': weighted_score,
            'direction': self._score_to_direction(weighted_score),
            'confidence': self._calculate_confidence(
                news_score, social_score, calendar_impact
            ),
            'components': {
                'news': news_score,
                'social': social_score,
                'calendar': calendar_impact
            }
        }
```

---

## 5. Adaptive Loss Curve (Softmax-based)

### Purpose
Dynamic loss tolerance based on account size using non-linear scaling.

### Mathematical Foundation

```
Traditional Linear: loss_tolerance = balance * risk_pct

Adaptive Curve: loss_tolerance = base_risk * softmax_scale(balance)

Where softmax_scale applies temperature-adjusted scaling:
- Small accounts: Tighter tolerance (protective)
- Medium accounts: Balanced tolerance
- Large accounts: Can absorb more but still controlled
```

### Implementation

```python
class AdaptiveLossCurve:
    """
    Non-linear loss tolerance scaling using softmax-inspired curves.
    """
    
    def __init__(self):
        self.balance_tiers = [5, 50, 500, 5000, 50000]
        self.risk_tiers = [0.005, 0.01, 0.015, 0.02, 0.025]
        self.temperature = 2.0  # Controls curve steepness
    
    def get_max_loss(self, balance: float, trade_risk: float) -> float:
        """
        Calculate maximum acceptable loss for this balance.
        
        Examples:
        - $5 balance → $0.025 max loss (0.5%)
        - $50 balance → $0.50 max loss (1.0%)
        - $500 balance → $7.50 max loss (1.5%)
        - $5000 balance → $100 max loss (2.0%)
        """
        # Interpolate risk percentage based on balance
        risk_pct = self._interpolate_risk(balance)
        
        # Apply softmax scaling for smooth transition
        scaled_risk = self._softmax_scale(risk_pct, balance)
        
        return balance * scaled_risk
    
    def _softmax_scale(self, base_risk: float, balance: float) -> float:
        """
        Apply temperature-controlled softmax scaling.
        Lower temperature = sharper transitions
        Higher temperature = smoother curve
        """
        # Normalize balance to [0, 1] range
        norm_balance = np.clip(balance / 50000, 0, 1)
        
        # Softmax-inspired scaling
        scale = 1 / (1 + np.exp(-self.temperature * (norm_balance - 0.5)))
        
        return base_risk * (0.5 + scale)
```

---

## 6. Reinforcement Learning Position Manager

### Purpose
Learn optimal position sizing, entry timing, and exit strategies through experience.

### Architecture

```
State Space:
├── Market State (regime, volatility, trend)
├── Position State (open trades, P&L, exposure)
├── Account State (balance, margin, drawdown)
└── Signal State (confidence, confluence)

Action Space:
├── Position Size: [0.0, 0.25, 0.5, 0.75, 1.0] of max
├── Entry: [SKIP, ENTER, SCALE_IN]
├── Exit: [HOLD, PARTIAL_25, PARTIAL_50, FULL_EXIT]
└── Stop Adjustment: [TIGHTEN, HOLD, WIDEN]

Reward Function:
├── Realized P&L (primary)
├── Risk-adjusted returns (Sharpe)
├── Drawdown penalty
└── Consistency bonus
```

### Implementation Approach

```python
class RLPositionManager:
    """
    DQN-based position management with experience replay.
    """
    
    def __init__(self):
        self.state_dim = 32  # Flattened state features
        self.action_dim = 20  # Discrete action combinations
        self.memory = ReplayBuffer(capacity=100000)
        self.model = self._build_network()
        self.target_model = self._build_network()
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01
    
    def decide(self, state: np.ndarray) -> int:
        """
        Epsilon-greedy action selection.
        """
        if np.random.random() < self.epsilon:
            return np.random.randint(self.action_dim)
        
        q_values = self.model.predict(state.reshape(1, -1))
        return np.argmax(q_values[0])
    
    def train(self, batch_size: int = 64):
        """
        Train on mini-batch from replay buffer.
        """
        if len(self.memory) < batch_size:
            return
        
        batch = self.memory.sample(batch_size)
        states, actions, rewards, next_states, dones = batch
        
        # Bellman equation update
        targets = self.model.predict(states)
        next_q = self.target_model.predict(next_states)
        
        for i in range(batch_size):
            if dones[i]:
                targets[i][actions[i]] = rewards[i]
            else:
                targets[i][actions[i]] = rewards[i] + 0.99 * np.max(next_q[i])
        
        self.model.fit(states, targets, epochs=1, verbose=0)
        
        # Decay exploration
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Market Regime Classifier (rule-based first, ML later)
- [ ] Adaptive Loss Curve implementation
- [ ] Exit Oracle enhancement with confluence scoring

### Phase 2: Prediction (Week 3-4)
- [ ] Price Predictor with softmax output
- [ ] Historical data pipeline for training
- [ ] Shadow mode testing

### Phase 3: Sentiment (Week 5-6)
- [ ] News API integration
- [ ] Economic calendar integration
- [ ] Sentiment scoring pipeline

### Phase 4: RL (Week 7-8)
- [ ] RL Position Manager prototype
- [ ] Simulation environment
- [ ] Initial training on historical data

### Phase 5: Integration (Week 9-10)
- [ ] Full integration with Cthulu core
- [ ] A/B testing framework
- [ ] Production deployment

---

## 8. Risk Considerations

### Model Risk
- Overfitting to historical data
- Regime changes invalidating learned patterns
- Black-box decision making

### Mitigations
1. **Ensemble approach**: Multiple models with voting
2. **Confidence thresholds**: Only act on high-confidence signals
3. **Kill switch**: Rule-based overrides for ML decisions
4. **Continuous monitoring**: Drift detection and model health
5. **Explainability**: Feature importance tracking

---

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Prediction Accuracy | > 55% | Directional accuracy |
| Sharpe Ratio Improvement | > 0.2 | vs rule-based only |
| Drawdown Reduction | > 15% | Max drawdown decrease |
| Win Rate | > 52% | Profitable trades |
| Profit Factor | > 1.5 | Gross profit / gross loss |

---

## 10. Exodus Integration Patterns

Based on review of the Exodus brokerage platform, key patterns to adopt:

### Event-Sourced Trade Tape
- Immutable audit trail for all decisions
- Replay capability for debugging
- Compliance-ready logging

### MT5 Bridge Pattern
- WebRequest-based orchestration
- Heartbeat monitoring
- Position synchronization

### Dual Dashboard Approach
- Service dashboard for ops/dev
- Trading dashboard for performance
- Real-time metrics streaming

---

## 11. References

### Papers
- "Deep Reinforcement Learning for Automated Stock Trading" (2020)
- "Attention-based LSTM for Financial Time Series" (2019)
- "Market Regime Detection using Hidden Markov Models" (2018)

### Libraries
- **PyTorch/TensorFlow**: Deep learning models
- **Stable-Baselines3**: RL implementations
- **LightGBM/XGBoost**: Gradient boosting for regime classification
- **Transformers**: Sentiment analysis from news

---

<div align="center">

**Cognition: The Soul of Cthulu**

*"Intelligence is the ability to adapt to change."* - Stephen Hawking

</div>
