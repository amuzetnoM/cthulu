# Herald Architecture Overview

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Herald Bot                           │
│                         (main.py)                           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
    ┌───────────────────┐       ┌───────────────────┐
    │   Configuration   │       │   Logging System  │
    │   (utils/config)  │       │  (utils/logger)   │
    └───────────────────┘       └───────────────────┘
                │                           │
                └─────────┬─────────────────┘
                          │
                ┌─────────┴─────────┐
                │                   │
                ▼                   ▼
    ┌───────────────────┐   ┌──────────────────┐
    │  MT5 Connection   │   │  Risk Manager    │
    │ (core/connection) │   │(core/risk_manager│
    │                   │   │                  │
    │ - Connect/reconnect│   │ - Position sizing│
    │ - Health checks    │   │ - SL/TP calc     │
    │ - Account info    │   │ - Margin checks  │
    │ - Symbol info     │   │ - Daily P&L      │
    └─────────┬─────────┘   └────────┬─────────┘
              │                      │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Trade Manager      │
              │ (core/trade_manager) │
              │                      │
              │ - Open position      │
              │ - Close position     │
              │ - Modify SL/TP       │
              │ - Get positions      │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Base Strategy      │
              │(strategies/base)     │
              │                      │
              │ - Get candles        │
              │ - Calculate ATR      │
              │ - Execute signals    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  MA Cross Strategy   │
              │(strategies/         │
              │ simple_ma_cross)     │
              │                      │
              │ - Analyze market     │
              │ - Generate signals   │
              │ - Manage positions   │
              └──────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   MetaTrader 5       │
              │      Terminal        │
              │                      │
              │ - Execute orders     │
              │ - Provide data       │
              │ - Manage positions   │
              └──────────────────────┘
```

## 🔄 Trading Flow

```
1. Bot Initialization
   └─> Load configuration
   └─> Setup logging
   └─> Connect to MT5
   └─> Initialize components
   └─> Load strategy

2. Main Loop (every 60 seconds)
   └─> Check MT5 connection
       │
       ├─> Fetch market data
       │   └─> Get historical candles
       │   └─> Calculate indicators
       │
       ├─> Strategy Analysis
       │   └─> MA crossover detection
       │   └─> Apply filters
       │   └─> Generate signal
       │
       ├─> Position Management
       │   └─> Check existing positions
       │   └─> Evaluate exit conditions
       │   └─> Close if needed
       │
       └─> Signal Execution
           └─> Risk checks
           └─> Position sizing
           └─> SL/TP calculation
           └─> Order placement
           └─> Update tracking

3. Shutdown
   └─> Close connections
   └─> Save logs
   └─> Exit gracefully
```

## 📊 Data Flow

```
MT5 Terminal
    │
    │ (Historical Data)
    ▼
Strategy.get_candles()
    │
    │ (OHLCV DataFrame)
    ▼
Strategy.analyze()
    │
    │ (Calculate Indicators)
    ├─> Moving Averages
    ├─> ATR
    └─> Filters
    │
    │ (Signal)
    ▼
TradeManager.open_position()
    │
    │ (Risk Validation)
    ▼
RiskManager.can_open_trade()
RiskManager.calculate_position_size()
RiskManager.calculate_stop_loss()
RiskManager.calculate_take_profit()
    │
    │ (Order Details)
    ▼
MT5 Terminal
    │
    │ (Execution Result)
    ▼
Logger.trade_opened()
RiskManager.update_daily_pnl()
```

## 🎯 Component Responsibilities

### Core Components

**MT5Connection** (`core/connection.py`)
- Establish and maintain MT5 terminal connection
- Handle reconnection logic
- Provide account and terminal information
- Manage symbol data access
- Health monitoring

**RiskManager** (`core/risk_manager.py`)
- Calculate position sizes based on risk percentage
- Compute stop loss and take profit levels
- Enforce trading limits (max positions, daily loss)
- Track daily P&L
- Validate margin requirements

**TradeManager** (`core/trade_manager.py`)
- Execute market orders (buy/sell)
- Close existing positions
- Modify position SL/TP
- Track all bot positions
- Handle order errors and retries

### Strategy Components

**BaseStrategy** (`strategies/base_strategy.py`)
- Abstract base class for all strategies
- Common functionality (data fetching, ATR calculation)
- Strategy execution framework
- Signal management

**SimpleMovingAverageCross** (`strategies/simple_ma_cross.py`)
- MA crossover signal detection
- Entry/exit logic
- Filter application
- Position management

### Utility Components

**Config** (`utils/config.py`)
- Load YAML configuration
- Access configuration values
- Validate settings
- Save configuration changes

**Logger** (`utils/logger.py`)
- Console and file logging
- Color-coded output
- Trade-specific logging
- Error tracking

## 🔐 Safety Features

### Multi-Layer Risk Protection

1. **Configuration Level**
   - Risk per trade limit (default: 1%)
   - Max concurrent positions (default: 3)
   - Max daily loss (default: 5%)

2. **Pre-Trade Checks**
   - Connection validation
   - Trading hours filter
   - Spread limit check
   - Margin sufficiency
   - Account trading status

3. **Position Level**
   - Automatic stop loss on every trade
   - Take profit for profit targets
   - ATR-based SL sizing
   - Risk/reward ratio enforcement

4. **Daily Tracking**
   - Daily P&L monitoring
   - Automatic trading halt at loss limit
   - Position count enforcement

## 📈 Extensibility Points

### Adding New Strategies

```python
from strategies.base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def analyze(self, df):
        # Your analysis logic
        return signal_dict
    
    def should_close_position(self, position, df):
        # Your exit logic
        return (should_close, reason)
```

### Adding New Indicators

```python
# indicators/custom.py
def my_indicator(df, period=14):
    # Calculate indicator
    return indicator_values
```

### Integration Points

1. **gold_standard Integration**
   - Import signals from analysis database
   - Use regime detection
   - Filter by economic calendar

2. **External Data Sources**
   - Sentiment analysis
   - News feeds
   - Alternative data

3. **Machine Learning**
   - Feature extraction from indicators
   - Model prediction integration
   - Confidence-based filtering

## 🧪 Testing Strategy

### Unit Tests
- Component isolation testing
- Mock MT5 API responses
- Risk calculation verification

### Integration Tests
- Full strategy execution
- Multi-component interaction
- Error handling scenarios

### Backtesting
- Historical data replay
- Performance metrics
- Optimization runs

## 📦 Deployment Architecture

```
Development Environment
├── Local Python venv
├── Demo MT5 account
├── File-based configuration
└── Console logging

Production Environment (Future)
├── Dedicated server/VPS
├── Live MT5 account
├── Database configuration
├── Remote logging (e.g., Elasticsearch)
├── Monitoring dashboard
└── Alert system
```

## 🔄 Future Architecture Evolution

### Phase 2: Multi-Strategy
```
Herald Bot
├── Strategy Manager
│   ├── MA Crossover
│   ├── RSI + MACD
│   ├── Bollinger Breakout
│   └── Pattern Recognition
└── Regime Detector
    └── Strategy Router
```

### Phase 3: ML Integration
```
Herald Bot
├── Feature Engine
├── ML Model Manager
│   ├── Random Forest
│   ├── Gradient Boosting
│   └── Ensemble
└── Prediction Service
```

### Phase 4: Multi-Asset
```
Herald Bot
├── Asset Manager
│   ├── XAUUSD (Gold)
│   ├── EURUSD (Forex)
│   └── BTCUSD (Crypto)
├── Portfolio Manager
└── Correlation Engine
```

---

**Current Status:** Phase 1 Complete - Foundation  
**Architecture:** Modular, extensible, production-ready foundation  
**Next Steps:** Deploy Phase 2 enhancements
