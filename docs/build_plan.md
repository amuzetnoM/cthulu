# Adaptive Trading Intelligence — Build Plan

## File
`/c:/workspace/herald/build_plan.md`

## Summary
A staged, modular implementation plan for a MetaTrader 5 (MT5) trading bot. 
Start with a robust foundation (connection, execution, basic strategy, risk controls), then iteratively add analytical, machine learning, and production features. Emphasize modularity, testability, safety, and observability so new techniques and signals can be integrated without disrupting core behavior.

---

## Goals
- Build a working MT5 bot that can open/close positions and be extended safely.
- Create a clear architecture for incremental feature addition and experimentation.
- Ensure every component is testable, auditable, and deployable.

Non-goals:
- Optimize or tune advanced ML models in phase 1.
- Replace professional risk-management or infrastructure teams.

---

## Table of Contents
1. Architecture overview  
2. Phase-by-phase plan  
3. Component specifications  
4. Interfaces and data contracts  
5. Risk management & safety  
6. Testing & validation strategy  
7. CI/CD, deployment, and observability  
8. Roadmap / Milestones  
9. Quick start snippet (SMA crossover)

---

## 1. Architecture overview
Design principles:
- Single Responsibility: each module has a focused role.
- Clear boundaries: communication via well-defined interfaces/messages.
- Replaceable implementations: e.g., strategy plugins, data sources.
- Event-driven core: signals → trade requests → execution → feedback.

High-level components:
- Connector: MT5 session management, reconnects, rate-limits.
- Data Layer: historical and live market feed, normalization.
- Strategy Layer: pluggable strategies (SMA crossover to start).
- Execution Engine: order placement, modification, cancellation.
- Risk Engine: position sizing, stop loss / take profit enforcement.
- Persistence: trade logs, signals, metrics (SQLite / Postgres).
- Orchestration / Scheduler: manage periodic tasks and backtests.
- Observability: logging, metrics, alerts, dashboards.

Data flow (simplified):
market data -> data layer -> strategy -> signal -> risk check -> execution -> persistence -> monitoring

---

## 2. Phase-by-phase plan

Phase 1 — Foundation (MUST)
- MT5 Connection Module
    - Reliable connect/disconnect, timeout handling, reconnection policy.
    - Session health checks.
- Data ingestion
    - Fetch history, stream ticks and bars, normalization to Pandas.
- Basic Strategy
    - Simple moving average (SMA) crossover strategy on a configurable symbol/timeframe.
- Execution & Risk
    - Open/close logic, stop loss, take profit, position-sizing rule.
- Persistence & Logging
    - Structured logs, action audit trail, simple database schema.
- Local backtest harness for deterministic verification.

Phase 2 — Autonomous Trade Execution (ACTIVE DEVELOPMENT)
OBJECTIVE: Extend Herald from signal generation to full autonomous trading with both entry AND exit execution.

Core Requirements:
- Indicator library integration (RSI, MACD, Bollinger Bands, Stochastic, ADX)
- Position management system (real-time tracking, monitoring, P&L)
- Exit strategy engine (trailing stops, time-based, profit targets, adverse movement)
- Autonomous orchestrator loop (continuous market monitoring and execution)
- Seamless integration with Phase 1 (no breaking changes to existing modules)

Architecture Extensions:
- herald/indicators/ - Technical indicator library with pluggable base class
- herald/position/ - Position tracking and lifecycle management
- herald/exit/ - Exit strategy implementations and detection
- herald/__main__.py - Complete autonomous trading loop

Data Flow (Phase 2 Complete):
market data → indicators → strategy signals → risk approval → execution → 
position tracking → exit detection → position closing → persistence → monitoring

Quality Standards:
- NO stubs, placeholders, or TODOs in production code
- Complete implementations only
- Comprehensive unit and integration tests
- Full documentation with usage examples
- Backward compatible with Phase 1

Phase 3 — Machine Learning Integration
- Offline model evaluation pipeline (scikit-learn/PyTorch).
- Simple supervised models and feature engineering from TA.
- Model serving for inference (local or lightweight REST/gRPC).
- Model training reproducibility and versioning.

Phase 4 — Advanced Intelligence
- Reinforcement learning experiments (DQN/PPO) in sandboxed environments.
- Sentiment and alternative data ingestion (news, social).
- Regime detection and adaptive parameterization.

Phase 5 — Production Features
- Automated backtesting pipeline with walk-forward testing.
- Real-time monitoring dashboard and alerting.
- Safe deployment automation: canary / staging.
- Audit reports and trade-performance analytics.

---

## 3A. Phase 2 Component Specifications (Autonomous Trading)

### Indicator Library (herald/indicators/)

Base Indicator Interface:
```python
class Indicator(ABC):
    """Abstract base class for technical indicators"""
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """Calculate indicator values"""
        pass
    
    def reset(self):
        """Reset indicator state"""
        pass
    
    def state(self) -> Dict[str, Any]:
        """Get indicator internal state"""
        pass
```

Required Indicators:
- RSI (Relative Strength Index)
  - Configurable period (default: 14)
  - Returns: RSI value (0-100)
  - Signals: Overbought (>70), Oversold (<30)
  
- MACD (Moving Average Convergence Divergence)
  - Configurable: fast (12), slow (26), signal (9)
  - Returns: MACD line, signal line, histogram
  - Signals: Bullish crossover (MACD > signal), Bearish crossover (MACD < signal)
  
- Bollinger Bands
  - Configurable: period (20), std_dev (2)
  - Returns: upper band, middle band (SMA), lower band
  - Signals: Price breakout above/below bands
  
- Stochastic Oscillator
  - Configurable: %K period (14), %D period (3)
  - Returns: %K line, %D line
  - Signals: Overbought (>80), Oversold (<20)
  
- ADX (Average Directional Index)
  - Configurable: period (14)
  - Returns: ADX value, +DI, -DI
  - Signals: Trend strength (ADX >25 = trending, <20 = ranging)

Integration Contract:
- All indicators accept DataFrame with OHLCV columns
- Return pandas Series or DataFrame with indicator values indexed by timestamp
- Include metadata: indicator_name, parameters, calculation_timestamp
- Thread-safe for concurrent calculation
- Cacheable results for backtesting

### Position Manager (herald/position/)

PositionManager Class:
```python
@dataclass
class PositionInfo:
    """Position tracking structure"""
    ticket: int
    symbol: str
    side: str  # BUY or SELL
    volume: float
    open_price: float
    open_time: datetime
    stop_loss: float
    take_profit: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    metadata: Dict[str, Any]

class PositionManager:
    """Real-time position tracking and monitoring"""
    
    def track_position(self, execution_result: ExecutionResult) -> PositionInfo:
        """Add new position to tracking"""
        pass
    
    def monitor_positions(self) -> List[PositionInfo]:
        """Update all position metrics with current prices"""
        pass
    
    def check_exits(self, exit_strategies: List[ExitStrategy]) -> List[ExitSignal]:
        """Check all positions against exit conditions"""
        pass
    
    def close_position(self, ticket: int, reason: str) -> ExecutionResult:
        """Execute position close"""
        pass
    
    def get_position_metrics(self, ticket: int) -> Dict[str, float]:
        """Get detailed position analytics"""
        pass
```

Responsibilities:
- Maintain real-time position registry synced with MT5
- Calculate unrealized P&L continuously
- Detect position modifications (SL/TP changes)
- Track position age and exposure time
- Integrate with RiskManager for exposure limits
- Reconcile with MT5 positions on reconnect

### Exit Strategy Engine (herald/exit/)

Base Exit Strategy Interface:
```python
@dataclass
class ExitSignal:
    """Exit signal structure"""
    ticket: int
    reason: str
    price: Optional[float]
    timestamp: datetime
    strategy_name: str
    confidence: float
    metadata: Dict[str, Any]

class ExitStrategy(ABC):
    """Abstract exit strategy base class"""
    
    @abstractmethod
    def should_exit(self, position: PositionInfo, current_data: Dict[str, Any]) -> Optional[ExitSignal]:
        """Determine if position should be exited"""
        pass
    
    def configure(self, params: Dict[str, Any]):
        """Update strategy parameters"""
        pass
```

Required Exit Strategies:

1. Trailing Stop Strategy
   - Dynamic stop loss following price movement
   - Configurable: trail_distance (pips or ATR multiplier), activation_profit (min profit to activate)
   - ATR-based: adjusts trail distance based on volatility
   - Never moves against profit direction

2. Time-Based Exit Strategy
   - Close positions after configured duration
   - Configurable: max_hold_time (hours), market_close_offset (minutes before session end)
   - Prevents overnight exposure if configured
   - Weekend/holiday awareness

3. Profit Target Exit Strategy
   - Close at predetermined profit levels
   - Configurable: target_pct (% profit), target_pips (absolute), partial_close (close portion at target)
   - Multiple target levels supported
   - Scales out positions incrementally

4. Adverse Movement Exit Strategy
   - Detect rapid price movement against position
   - Configurable: movement_threshold (pips), time_window (seconds), volatility_filter (ignore during high volatility)
   - Protects against flash crashes and news events
   - Integrates with risk manager circuit breaker

Exit Strategy Priority:
1. Adverse movement (highest priority - emergency exit)
2. Time-based (session close protection)
3. Profit target (take profits)
4. Trailing stop (protect profits)

### Autonomous Orchestrator (herald/__main__.py)

Main Trading Loop Structure:
```python
def main():
    # 1. Initialize all modules
    config = load_config(args.config)
    connector = MT5Connector(ConnectionConfig(**config['mt5']))
    data_layer = DataLayer(cache_enabled=True)
    risk_manager = RiskManager(RiskLimits(**config['risk']))
    execution_engine = ExecutionEngine(connector)
    position_manager = PositionManager(connector, execution_engine)
    
    # 2. Load indicators and strategies
    indicators = load_indicators(config['indicators'])
    strategy = load_strategy(config['strategy'])
    exit_strategies = load_exit_strategies(config['exits'])
    
    # 3. Connect and health check
    if not connector.connect():
        logger.error("Failed to connect to MT5")
        return 1
    
    logger.info("Herald autonomous trading started")
    
    try:
        while True:
            # 4. Market data ingestion
            rates = connector.get_rates(
                symbol=config['trading']['symbol'],
                timeframe=mt5.TIMEFRAME_H1,
                count=500
            )
            df = data_layer.normalize_rates(rates, symbol=config['trading']['symbol'])
            
            # 5. Calculate indicators
            for indicator in indicators:
                indicator_data = indicator.calculate(df)
                df = pd.concat([df, indicator_data], axis=1)
            
            # 6. Generate strategy signals
            signal = strategy.on_bar(df.iloc[-1])
            
            # 7. Process entry signals
            if signal and signal.side in [SignalType.LONG, SignalType.SHORT]:
                account_info = connector.get_account_info()
                approved, reason, size = risk_manager.approve(
                    signal,
                    account_info,
                    current_positions=len(position_manager.get_positions())
                )
                
                if approved:
                    # Execute order
                    order_req = OrderRequest(
                        signal_id=signal.id,
                        symbol=signal.symbol,
                        side="BUY" if signal.side == SignalType.LONG else "SELL",
                        volume=size,
                        order_type=OrderType.MARKET,
                        sl=signal.stop_loss,
                        tp=signal.take_profit
                    )
                    result = execution_engine.place_order(order_req)
                    
                    if result.status == OrderStatus.FILLED:
                        position_manager.track_position(result)
                        persistence.record_trade(signal, result)
            
            # 8. Monitor positions and check exits
            positions = position_manager.monitor_positions()
            
            for position in positions:
                # Check all exit strategies
                for exit_strategy in exit_strategies:
                    exit_signal = exit_strategy.should_exit(position, {
                        'current_data': df.iloc[-1],
                        'account_info': connector.get_account_info()
                    })
                    
                    if exit_signal:
                        logger.info(f"Exit triggered: {exit_signal.reason}")
                        close_result = position_manager.close_position(
                            position.ticket,
                            exit_signal.reason
                        )
                        
                        if close_result.status == OrderStatus.FILLED:
                            persistence.record_exit(exit_signal, close_result)
                            risk_manager.record_trade_result(position.realized_pnl)
                        
                        break  # Exit after first strategy triggers
            
            # 9. Health monitoring
            if not connector.is_connected():
                logger.warning("Connection lost, attempting reconnect...")
                if not connector.reconnect():
                    logger.error("Reconnection failed")
                    break
            
            # 10. Wait for next cycle
            time.sleep(config['trading']['poll_interval'])
            
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        # Cleanup
        position_manager.close_all_positions("Shutdown")
        connector.disconnect()
        persistence.close()
        logger.info("Herald stopped")
    
    return 0
```

Critical Safeguards:
- Connection loss: automatic reconnection with position reconciliation
- Exception handling: log and continue (no crash on single error)
- Emergency shutdown: close all positions on fatal error
- State persistence: save positions and state on shutdown
- Health checks: verify connection before each operation

Integration Points:
- Connector: market data, account info, connection health
- DataLayer: OHLCV normalization, indicator integration
- Indicators: calculated values added to DataFrame
- Strategy: generates entry signals from enriched data
- RiskManager: approves trades, tracks daily P&L
- ExecutionEngine: places orders, handles fills
- PositionManager: tracks positions, monitors P&L
- ExitStrategies: detect exit conditions
- Persistence: record all trades, signals, exits

---


Connector (MT5)
- Exposes: connect(), disconnect(), is_connected(), get_rates(symbol, timeframe, n), subscribe_ticks(symbols)
- Handles: login config, retries, exception consolidation

Data Layer
- Normalizes to DataFrame with timestamp index, OHLCV, volume.
- Stores raw and resampled series.
- Caching layer for repeated backtests.

Strategy Interface (example)
- Methods: on_bar(bar), on_tick(tick), configure(params), state()
- Returns: Signal objects {type: LONG/SHORT/CLOSE, confidence, reason}

Execution Engine
- Receives Signal => makes OrderRequest after risk approval.
- Supports market/limit orders, partial fills handling.
- Idempotent order submission and external reconciliation.

Risk Engine
- Position sizing: fixed lots, percent of balance, volatility-based sizing.
- Hard guards: max exposure per-symbol, max total drawdown, daily stop-loss.
- Emergency shutdown API.

Persistence
- Schemas: trades, orders, positions, signals, metrics.
- Historical retention plan and export capability.

Observability
- Structured JSON logs, metrics (Prometheus), trace spans for critical ops.
- Alerting for connection loss, order failures, guard triggers.

---

## 4. Interfaces and data contracts
- Signal JSON:
    - {id, timestamp, symbol, timeframe, side, action, size_hint, price, stop_loss, take_profit, metadata}
- OrderRequest:
    - {signal_id, symbol, side, volume, order_type, price, sl, tp, client_tag}
- ExecutionResult:
    - {order_id, status, executed_price, executed_volume, timestamp, error (optional)}

Ensure all modules validate and log both requests and responses.

---

## 5. Risk management & safety
Mandatory runtime checks:
- Max position size per symbol and overall exposure.
- Per-day maximum loss limit and auto-pause behavior.
- Slippage and spread thresholds (reject trades if abnormal).
- Simulated mode toggle to test logic without real orders.
- Manual kill switch accessible via CLI or dashboard.

---

## 6. Testing & validation
- Unit tests for each pure module (indicators, position sizing).
- Integration tests: connector + execution in demo accounts or simulator.
- Deterministic backtests with seeded RNG and retained environments.
- Regression tests for historical trade-results comparison.
- Continuous metrics: PnL, Sharpe, max drawdown, win rate.

---

## 7. CI/CD, deployment, and observability
- CI: run lint, unit tests, static analysis, minimal backtest on PRs.
- CD: artifact build (Docker), staged deployment (canary on demo account), rollback path.
- Secrets: store credentials in secure vault; avoid committing keys.
- Monitoring: logs to central store, key metrics to Prometheus/Grafana, alerts via email/Slack.

---

## 8. Roadmap / Milestones (example timeline)
- Week 1–2: Connector, data ingestion, SMA strategy, basic execution.
- Week 3: Persistence, logging, simple backtest harness.
- Week 4: Risk engine, simulated run on demo account, first integration tests.
- Month 2–3: TA indicator suite, multi-timeframe aggregation.
- Month 3–6: ML experiments and model inference pipeline.
- Ongoing: hardening, dashboards, and production rollout.

---

## 9. Quick start: SMA crossover (pseudocode)
```python
# high-level pseudocode
from mt5_connector import MT5Connector
from strategy import SmaCrossover
from execution import ExecutionEngine
from risk import RiskEngine
from persistence import DB

mt5 = MT5Connector(config)
mt5.connect()

data = mt5.get_rates("EURUSD", timeframe="H1", n=500)
strategy = SmaCrossover(short_window=20, long_window=50)
signal = strategy.generate_signal(data)

if signal:
        order = RiskEngine.approve(signal, account_state=mt5.account_info())
        if order.approved:
                result = ExecutionEngine.place_order(order)
                DB.record(result)
```

---

## Appendix: Initial checklist
- [ ] Add config schema and secrets handling
- [ ] Implement MT5 connector with health checks
- [ ] Implement Data Layer and SMA strategy
- [ ] Implement Execution Engine and Risk Engine basic guards
- [ ] Add persistence and structured logging
- [ ] Run integration test on demo account

---

This plan focuses on a safe, incremental path from a functional SMA-based MT5 bot to a research-friendly, production-capable platform with clear extension points for indicators and ML models.
## 3. Component specifications
