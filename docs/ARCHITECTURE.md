---
title: Architecture Overview
description: Technical architecture and system design of the Cthulu multi-strategy autonomous trading platform
tags: [architecture, system-design, technical-overview]
slug: /docs/architecture
sidebar_position: 3
---

## System Architecture

<a href="https://artifact-virtual.gitbook.io/Cthulu"><img alt="Version" src="https://img.shields.io/badge/version-5.1.0-blue?style=flat-square" /></a>

### High-Level System Overview

```mermaid
graph TB
    subgraph "User Interface Layer"
        GUI[Desktop GUI<br/>Tkinter Dashboard]
        RPC[RPC Server<br/>HTTP API]
    end
    
    subgraph "Core Trading Engine"
        ORCH[Multi-Strategy<br/>Orchestrator]
        STRAT[Strategy Engine<br/>6 Strategies]
        EXEC[Execution Engine<br/>Order Management]
    end
    
    subgraph "Intelligence Layer"
        IND[Indicator Library<br/>12 Indicators]
        REGIME[Regime Detection<br/>10 States]
        NEWS[News Integration<br/>FRED, TradingEconomics]
    end
    
    subgraph "Data & Persistence"
        DATA[Data Layer<br/>OHLCV Processing]
        DB[SQLite Database<br/>Trade History]
        CACHE[Cache Layer<br/>Performance]
    end
    
    subgraph "Risk & Position Management"
        RISK[Risk Manager<br/>Position Sizing]
        POS[Position Manager<br/>Lifecycle]
        EXIT[Exit Strategies<br/>4 Types]
    end
    
    subgraph "External Services"
        MT5[MetaTrader 5<br/>Broker]
        PROM[Prometheus<br/>Metrics]
    end
    
    GUI --> ORCH
    RPC --> ORCH
    ORCH --> REGIME
    REGIME --> STRAT
    STRAT --> IND
    STRAT --> NEWS
    STRAT --> EXEC
    EXEC --> RISK
    RISK --> MT5
    EXEC --> POS
    POS --> EXIT
    EXIT --> MT5
    DATA --> MT5
    IND --> DATA
    POS --> DB
    EXEC --> DB
    ORCH --> PROM
    DATA --> CACHE
    
    style ORCH fill:#00ff88,stroke:#00cc6a,color:#000
    style MT5 fill:#00aaff,stroke:#0088cc,color:#000
    style DB fill:#ffaa00,stroke:#dd8800,color:#000
```

### Component Architecture (ASCII for compatibility)

```
┌─────────────────────────────────────────────────────────────────────┐
│                 Multi-Strategy Orchestrator                         │
│                         (__main__.py)                               │
│  11-step trading loop: Connect → Detect Regime → Select Strategy → │
│  Analyze → Decide → Execute → Track → Exit → Learn → Monitor       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
                ▼                                 ▼
    ┌───────────────────┐           ┌───────────────────┐
    │   Configuration   │           │   Logging System  │
    │   (config/)       │           │  (observability/) │
    │   Wizard + Schema │           │  JSON + Metrics   │
    └───────────────────┘           └───────────────────┘
                │                                 │
                └──────────┬──────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼
┌─────────────────┐                 ┌─────────────────┐
│  MT5 Connector  │                 │  Risk Manager   │
│ (connector/)    │                 │  (risk/)        │
│                 │                 │                 │
│ - Reconnection  │                 │ - Position size │
│ - Rate limiting │                 │ - Daily limits  │
│ - Health check  │                 │ - Approval      │
│ - Session mgmt  │                 │ - Kelly sizing  │
└────────┬────────┘                 └────────┬────────┘
         │                                   │
         └──────────┬────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌─────────────────┐   ┌─────────────────────┐
│   Data Layer    │   │  Indicator Library  │
│   (data/)       │   │  (indicators/)      │
│                 │   │                     │
│ - OHLCV norm    │   │ - RSI, MACD, BB, Stoch │
│ - Indicators    │   │ - ADX, Supertrend, VWAP │
│ - Caching       │   │ - VPT, Vol Osc, PVT, ATR │
│ - Resampling    │   │ - Williams %R, Anchored VWAP │
└────────┬────────┘   └─────────┬──────────┘
         │                       │
         └──────────┬────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌─────────────────┐   ┌─────────────────────┐
│ Strategy Engine │   │  Execution Engine   │
│ (strategy/)     │   │  (execution/)       │
│                 │   │                     │
│ - 6 Strategies  │   │ - Idempotent orders │
│ - 10 Regime Detect │   │ - ML instrumentation│
│ - Performance   │   │ - Reconciliation    │
│ - Selection     │   │ - Error recovery    │
└────────┬────────┘   └─────────┬──────────┘
         │                       │
         └──────────┬────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌─────────────────┐   ┌─────────────────────┐
│ Position Mgmt   │   │  Exit Strategies    │
│ (position/)     │   │  (exit/)           │
│                 │   │                     │
│ - Tracking      │   │ - Trailing stop     │
│ - Adoption      │   │ - Time-based        │
│ - Reconciliation│   │ - Profit target     │
│ - P&L calc      │   │ - Adverse movement  │
└────────┬────────┘   └─────────┬──────────┘
         │                       │
         └──────────┬────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌─────────────────┐   ┌─────────────────────┐
│   Persistence   │   │   Observability     │
│   (database/)   │   │  (monitoring/)      │
│                 │   │                     │
│ - SQLite trades │   │ - Trade monitor     │
│ - Signals       │   │ - Health checks     │
│ - Metrics       │   │ - GUI integration   │
│ - Export        │   │ - Prometheus hooks  │
└────────┬────────┘   └─────────┬──────────┘
         │                       │
         └──────────┬────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌─────────────────┐   ┌─────────────────────┐
│   Desktop GUI   │   │     RPC Server      │
│   (ui/)         │   │   (rpc/)           │
│                 │   │                     │
│ - Trade history │   │ - HTTP API          │
│ - Live monitor  │   │ - Manual trading    │
│ - Metrics dash  │   │ - External access   │
│ - Manual orders │   │ - REST endpoints    │
└─────────────────┘   └─────────────────────┘
```
         │            │ - ATR               │
         │            └──────────┬──────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   Strategy Engine    │
          │   (strategy/)        │
          │                      │
          │ - Signal generation  │
          │ - SMA crossover      │
          │ - Indicator fusion   │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  Execution Engine    │
          │  (execution/)        │
          │                      │
          │ - Order submission   │
          │ - Idempotency        │
          │ - Fill tracking      │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │ Position Manager     │
          │  (position/)         │
          │                      │
          │ - Track positions    │
          │ - Calculate P&L      │
          │ - Sync with MT5      │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  Exit Strategies     │
          │  (exit/)             │
          │                      │
          │ - Stop Loss (P1)     │
          │ - Take Profit (P2)   │
          │ - Trailing Stop (P3) │
          │ - Time-based (P4)    │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   Persistence Layer  │
          │  (persistence/)      │
          │                      │
          │ - Signal storage     │
          │ - Order history      │
          │ - Trade records      │
          │ - P&L tracking       │
          └──────────────────────┘
```

## Autonomous Trading Flow

### Trading Loop Sequence

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant MT5
    participant Strategy
    participant Risk
    participant Execution
    participant Position
    
    User->>Orchestrator: Start Trading
    
    loop Every Trading Cycle
        Orchestrator->>MT5: Check Connection
        MT5-->>Orchestrator: Status OK
        
        Orchestrator->>MT5: Fetch Market Data
        MT5-->>Orchestrator: OHLCV Data
        
        Orchestrator->>Strategy: Detect Market Regime
        Strategy-->>Orchestrator: Regime Classification
        
        Orchestrator->>Strategy: Analyze & Generate Signal
        Strategy-->>Orchestrator: Trade Signal (BUY/SELL/HOLD)
        
        alt Signal is BUY or SELL
            Orchestrator->>Risk: Validate Trade
            Risk-->>Orchestrator: Risk Approved + Position Size
            
            Orchestrator->>Execution: Execute Order
            Execution->>MT5: Place Order
            MT5-->>Execution: Order Filled
            Execution-->>Orchestrator: Execution Result
            
            Orchestrator->>Position: Track New Position
            Position-->>Orchestrator: Position Registered
        end
        
        Orchestrator->>Position: Check Existing Positions
        Position->>Position: Evaluate Exit Conditions
        
        alt Exit Condition Met
            Position->>Execution: Close Position
            Execution->>MT5: Close Order
            MT5-->>Execution: Position Closed
        end
        
        Orchestrator->>Orchestrator: Update Metrics
        Orchestrator->>User: Log Status
    end
```

### Detailed Trading Flow (Text-based for compatibility)

```
1. Initialization (Orchestrator)
   └─> Load config.json or .env
   └─> Setup structured logging
   └─> Initialize MT5 connector
   └─> Initialize all components:
       ├─> DataLayer
       ├─> RiskManager
       ├─> ExecutionEngine
       ├─> PositionManager
       └─> ExitStrategyManager

2. Main Loop (10-Step Cycle)
   
   Step 1: Connection Health
   └─> Check MT5 connection
   └─> Reconnect if needed
   
   Step 2: Position Synchronization
   └─> Sync positions from MT5
   └─> Update PositionManager state
   
   Step 3: Market Data Fetch
   └─> Get OHLCV data for symbol
   └─> Normalize to DataFrame
   
   Step 4: Indicator Calculation
   └─> Calculate RSI, MACD, Bollinger
   └─> Calculate Stochastic, ADX, ATR
   
   Step 5: Entry Signal Generation
   └─> Run strategy analysis
   └─> Generate entry signal (if any)
   
   Step 6: Risk Approval (Entry)
   └─> Position sizing calculation
   └─> Check daily loss limits
   └─> Approve or reject signal
   
   Step 7: Entry Execution
   └─> Submit order to MT5
   └─> Track order status
   └─> Update PositionManager
   
   Step 8: Exit Signal Generation
   └─> Check all open positions
   └─> Run exit strategies (priority order):
       ├─> P1: Stop Loss Exit
       ├─> P2: Take Profit Exit
       ├─> P3: Trailing Stop Exit
       └─> P4: Time-based Exit
   
   Step 9: Exit Execution
   └─> Submit close orders
   └─> Track fill status
   └─> Update P&L records
   
   Step 10: Persistence & Logging
   └─> Save signals to database
   └─> Log trade history
   └─> Update metrics
   
   └─> Sleep interval (e.g., 60s)
   └─> Repeat
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

## Data Flow

```
MT5 Terminal
    │
    │ (Historical Data)
    ▼
Strategy.get_candles()
```

---

## Monitoring & Deployment Recommendations

**Short-term (30-60 min validation)**
- Run Cthulu locally in a terminal using the aggressive mindset config and `--log-level DEBUG`:

```bash
python -m Cthulu --config configs/mindsets/aggressive/config_aggressive_h1.json --symbol "GOLD#m" --skip-setup --no-prompt --log-level DEBUG
```

- Tail logs (e.g., `tail -f Cthulu.log`) and watch for these messages:
  - `Adopted trade:` — adoption events
  - `Set SL/TP for #` — confirmed SL/TP set on broker
  - `SL/TP verification failed` — broker refused modification (investigate immediately)
  - `Failed to select symbol` — symbol visibility issue in MT5 Market Watch

**Production (recommended)**
- Containerize with Docker and expose Prometheus metrics via simple endpoint (use `observability/prometheus.py` and a tiny metrics HTTP server).
- Use an orchestrator (Docker Compose or Kubernetes) and set restart policies, resource limits, and liveness/readiness probes.
- Centralized logging + alerting (Prometheus + Alertmanager; PagerDuty/Slack integration for critical alerts):
  - Alert on any `Cthulu_sl_tp_failure_total > 0` within a 1-minute window
  - Alert on `Cthulu_mt5_connected == 0` for 2 consecutive checks
  - Alert on repeated adoption failures or repeated market data absence

**Monitoring approach choice**
- Terminal monitoring: fast, low-friction for smoke tests and short runs (30–60 min). I can run and monitor logs and report back.
- Containerized monitoring: recommended for production — reproducible, easier integration with metrics and alerting, and safer for long-term uptime.

Let me know if you want me to: **(A)** run a 30–60 minute live terminal monitoring session now, or **(B)** start containerizing Cthulu and add Prometheus HTTP exposure + alert rules (I can start with a Dockerfile and a metrics endpoint).
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

## Component Responsibilities

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

## Safety Features

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

## Extensibility Points

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

## Testing Strategy

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

## Deployment Architecture

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

## Future Architecture Evolution

### Phase 2: Multi-Strategy
```
Cthulu Bot
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
Cthulu Bot
├── Feature Engine
├── ML Model Manager
│   ├── Random Forest
│   ├── Gradient Boosting
│   └── Ensemble
└── Prediction Service
```

### Phase 4: Multi-Asset
```
Cthulu Bot
├── Asset Manager
│   ├── XAUUSD (Gold)
│   ├── EURUSD (Forex)
│   └── BTCUSD (Crypto)
├── Portfolio Manager
└── Correlation Engine
```

---

```mermaid

flowchart TD
    subgraph Orchestration
        O1["__main__.py loop"]
    end

    A["MT5 Connector<br/>(MT5Connector / mt5)"]
    B["Data Layer<br/>(DataLayer.normalize_rates)"]
    C["Indicators<br/>(RSI, MACD, Bollinger, Stochastic, ADX)"]
    D["Strategy<br/>(SmaCrossover / Strategy.on_bar)"]
    E["Risk Manager<br/>(RiskManager.approve)"]
    F["Execution Engine<br/>(ExecutionEngine.place_order)"]
    G["MT5<br/>(order_send) & Order Result"]
    H["Position Manager<br/>(PositionManager.track_position / monitor_positions)"]
    I["Exit Strategies<br/>(Adverse, TimeBased, ProfitTarget, TrailingStop)"]
    J["Persistence<br/>(Database.record_trade, record_signal, update_trade_exit)"]
    K["Metrics<br/>(MetricsCollector)"]
    L["Health & Reconnect checks<br/>(MT5Connector.is_connected, reconnect)"]
    M["Trade Adoption<br/>(TradeManager.scan_and_adopt → PositionManager.add_position)"]

    O1 --> A
    O1 --> B
    O1 --> C
    O1 --> D
    O1 --> E
    O1 --> F
    O1 --> H
    O1 --> I
    O1 --> J
    O1 --> K
    O1 --> L
    O1 --> M

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I -- "Position close" --> F
    H --> J
    F --> J
    H --> K
    J --> K
    A --> L
    L --> H
    A --> M
```

---


**Current Status:** Complete - Production-Ready Enterprise Trading System  
**Architecture:** Fully modular, extensible, enterprise-grade with 6 strategies and 12 indicators  
**Next Steps:** Performance optimization and advanced monitoring enhancements

### Strategy Selection Logic

```mermaid
flowchart TD
    Start([Start Trading Cycle]) --> FetchData[Fetch Market Data]
    FetchData --> CalcIndicators[Calculate Indicators]
    CalcIndicators --> DetectRegime{Detect Market<br/>Regime}
    
    DetectRegime -->|Trending Up Strong| TrendFollow[Trend Following<br/>Strategy]
    DetectRegime -->|Trending Down Strong| TrendFollow
    DetectRegime -->|Ranging Tight| MeanReversion[Mean Reversion<br/>Strategy]
    DetectRegime -->|Ranging Wide| MeanReversion
    DetectRegime -->|Volatile Breakout| MomentumBreakout[Momentum Breakout<br/>Strategy]
    DetectRegime -->|Consolidating| Scalping[Scalping<br/>Strategy]
    
    TrendFollow --> GenerateSignal[Generate Trade Signal]
    MeanReversion --> GenerateSignal
    MomentumBreakout --> GenerateSignal
    Scalping --> GenerateSignal
    
    GenerateSignal --> CheckSignal{Signal<br/>Type?}
    CheckSignal -->|BUY/SELL| RiskCheck[Risk Manager<br/>Validation]
    CheckSignal -->|HOLD| WaitNext[Wait for Next Cycle]
    
    RiskCheck --> RiskPass{Risk<br/>Approved?}
    RiskPass -->|Yes| Execute[Execute Order]
    RiskPass -->|No| WaitNext
    
    Execute --> TrackPosition[Track Position]
    TrackPosition --> MonitorExits[Monitor Exit<br/>Conditions]
    
    MonitorExits --> ExitCheck{Exit<br/>Triggered?}
    ExitCheck -->|Yes| ClosePosition[Close Position]
    ExitCheck -->|No| WaitNext
    
    ClosePosition --> UpdateMetrics[Update Performance<br/>Metrics]
    WaitNext --> UpdateMetrics
    UpdateMetrics --> End([End Cycle])
    
    style Start fill:#00ff88,stroke:#00cc6a
    style Execute fill:#ffaa00,stroke:#dd8800
    style ClosePosition fill:#ff4444,stroke:#cc3333
    style End fill:#00ff88,stroke:#00cc6a
```





