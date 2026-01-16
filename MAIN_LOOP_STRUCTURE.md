# Cthulu Trading System - Main Loop Structure Analysis

## Overview

The Cthulu trading system follows a modular architecture with a clear separation of concerns. The main trading loop orchestrates data ingestion, signal generation, risk management, and position monitoring in a continuous cycle.

---

## 1. System Architecture & Flow

### Entry Point: `cthulu/__main__.py`

The trading system follows a 4-phase startup sequence:

```
Phase 1: Bootstrap System
├── Singleton lock check (prevent multiple instances via cthulu.lock)
├── Argument parsing (--config, --mindset, --dry-run, etc.)
├── Logger setup (logs/Cthulu.log)
└── Signal handlers (SIGINT, SIGTERM)

Phase 2: Initialize Components (via core/bootstrap.py)
├── MT5Connector: MetaTrader 5 connection & market data
├── DataLayer: Rate normalization & caching
├── Strategy: Signal generation (SMA, EMA, Scalping, etc.)
├── RiskEvaluator: Position sizing & approval
├── ExecutionEngine: Order placement & management
├── PositionTracker: Low-level position state
├── PositionManager: High-level position monitoring
├── PositionLifecycle: Position operations (modify, close)
├── TradeAdoptionManager: Orphaned trade adoption
├── ExitCoordinator: Exit strategy coordination
├── Database: Trade & signal persistence
├── MetricsCollector: Performance tracking
├── DynamicSLTPManager: Adaptive stop-loss/take-profit
├── ProfitScaler: Partial profit taking
└── Optional: Hektor (semantic memory), Cognition Engine (AI/ML)

Phase 3: Run Trading Loop (core/trading_loop.py)
└── TradingLoop.run() - main execution loop

Phase 4: Graceful Shutdown (core/shutdown.py)
├── Close Hektor semantic memory connection
├── Persist final metrics
├── Close database connections
├── Shutdown MT5 connector
└── Cleanup lock file
```

---

## 2. Core Bootstrap Components (`core/bootstrap.py`)

**CthuluBootstrap** initializes all system components in dependency order:

| Component | Module | Purpose |
|-----------|--------|---------|
| **MT5Connector** | `connector/mt5_connector.py` | Market data, order execution, account info |
| **DataLayer** | `data/layer.py` | Rate normalization, symbol mapping, caching |
| **RiskEvaluator** | `risk/evaluator.py` | Position sizing, risk approval, drawdown limits |
| **ExecutionEngine** | `execution/engine.py` | Order placement, status tracking |
| **PositionTracker** | `position/tracker.py` | Low-level position state tracking |
| **PositionManager** | `position/manager.py` | High-level position monitoring for trading loop |
| **PositionLifecycle** | `position/lifecycle.py` | Position opening/closing/modification |
| **TradeAdoptionManager** | `position/adoption.py` | Adopt external trades with matching policy |
| **Database** | `persistence/database.py` | SQLite persistence for trades & signals |
| **MetricsCollector** | `observability/metrics.py` | Performance metrics aggregation |
| **DynamicSLTPManager** | `risk/dynamic_sltp_manager.py` | ATR-based trailing stops |
| **ProfitScaler** | `position/profit_scaler.py` | Partial profit taking at levels |
| **AdaptiveAccountManager** | `risk/adaptive_account_manager.py` | Phase-based risk scaling |
| **IndicatorCollector** | `monitoring/indicator_collector.py` | Real-time indicator snapshots |
| **ComprehensiveCollector** | `observability/comprehensive_collector.py` | Full system metrics |
| **HektorAdapter** | `integrations/hektor/adapter.py` | Vector Studio semantic memory |

**Configuration Flow:**
1. Load `config.json` or specified config file
2. Apply mindset overlays (conservative/balanced/aggressive/ultra_aggressive)
3. Validate schema via `config_schema.py`
4. Initialize components with config sections

---

## 3. Main Trading Loop (`core/trading_loop.py`)

### TradingLoop Class Structure

```python
class TradingLoop:
    def __init__(self, context: TradingLoopContext):
        """Initialize with dependency injection via context object"""
        self.ctx = context  # Contains all dependencies
        self.loop_count = 0
        self._shutdown_requested = False
        
        # Trade cooldown tracking
        self._last_trade_time = None
        self._min_trade_interval_seconds = 60  # Configurable
        
    def run(self) -> int:
        """Main execution loop"""
        while not self._shutdown_requested:
            self.loop_count += 1
            self._execute_loop_iteration()
            time.sleep(poll_interval)
```

### Loop Iteration Flow (`_execute_loop_iteration()`)

Each loop cycle executes **9 sequential steps**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRADING LOOP ITERATION                       │
└─────────────────────────────────────────────────────────────────┘

1. MARKET DATA INGESTION (_ingest_market_data)
   ├─ Fetch OHLCV bars from MT5 via connector.get_rates()
   │  Parameters: symbol, timeframe, lookback_bars (default 100)
   ├─ Convert MT5 numpy array to Python dictionaries
   └─ Normalize to pandas DataFrame via DataLayer
   
2. INDICATOR CALCULATION (_calculate_indicators)
   ├─ Calculate SMA periods (strategy-dependent: e.g., 20, 50)
   ├─ Compute EMA columns (strategy-dependent: e.g., 5, 10, 21)
   ├─ Ensure runtime indicators via ensure_runtime_indicators():
   │  ├─ RSI (default period 14, strategy-specific overrides)
   │  ├─ ATR (default period 14, for stop-loss sizing)
   │  ├─ ADX (for regime detection in dynamic strategies)
   │  └─ Optional: MACD, Bollinger Bands, Stochastic, Supertrend, VWAP
   ├─ Calculate configured indicators from config.json
   ├─ Create friendly aliases (rsi, atr, adx) for strategy access
   ├─ Fallback indicator computation if missing
   └─ Feed real-time data to IndicatorCollector & ComprehensiveCollector
   
3. PENDING ENTRY CHECKS (_check_pending_entries)
   ├─ Query Entry Confluence Filter for queued signals
   ├─ Check if optimal entry price reached
   ├─ Create synthetic signal for ready entries
   └─ Process pending signal if conditions met
   
4. SIGNAL GENERATION (_generate_signal)
   ├─ Call strategy.on_bar(current_bar) or generate_signal(df, bar)
   │  Strategies: SMA Crossover, EMA Crossover, Scalping, Momentum Breakout
   ├─ Apply Cognition Engine enhancement (if enabled):
   │  ├─ Confidence multiplier (boost/reduce signal confidence)
   │  ├─ Size multiplier (increase/decrease position size)
   │  ├─ Warning signals (market regime, volatility concerns)
   │  └─ Trading advisability check (should_trade gate)
   └─ Return Signal object or None
   
5. ENTRY SIGNAL PROCESSING (_process_entry_signal)
   ├─ Trade cooldown check (prevent rapid-fire entries)
   ├─ Check for opposite direction positions (block BUY if SELL exists)
   ├─ Entry Confluence Filter (quality gate):
   │  ├─ Analyze market regime (trending vs ranging)
   │  ├─ Check indicator alignment (RSI, ADX, trend indicators)
   │  ├─ Calculate quality score (EXCELLENT/GOOD/FAIR/POOR)
   │  ├─ Queue signal if "wait for better" conditions apply
   │  └─ Apply position size multiplier based on quality
   ├─ Risk approval via RiskEvaluator.approve():
   │  ├─ Balance protection checks
   │  ├─ Position size calculation
   │  ├─ Daily loss limit enforcement
   │  ├─ Spread validation
   │  └─ Risk/reward ratio check
   ├─ Apply size multipliers:
   │  ├─ Entry quality multiplier
   │  ├─ Adaptive loss curve adjustment
   │  └─ Cognition size multiplier
   └─ Execute order or record advisory/ghost signal
   
6. EXTERNAL TRADE ADOPTION (_adopt_external_trades)
   ├─ Scan MT5 for positions not tracked by system
   ├─ Check TradeAdoptionPolicy (enabled, magic number filter)
   ├─ Adopt qualifying positions into PositionManager
   └─ Apply SL/TP if configured in adoption policy
   
7. POSITION MONITORING (_monitor_positions)
   ├─ Get all open positions via PositionManager.monitor_positions()
   ├─ Profit Scaling (ProfitScaler.run_scaling_cycle):
   │  ├─ Check each position against profit levels
   │  ├─ Execute partial closes at configured thresholds
   │  └─ Respect minimum lot constraints
   ├─ Cognition Exit Signals (if enabled):
   │  ├─ Get AI/ML enhanced exit recommendations
   │  ├─ Consider urgency levels (IMMEDIATE/HIGH/NORMAL/LOW)
   │  └─ Flag positions for priority exit
   ├─ Dynamic SL/TP Management (_apply_dynamic_sltp):
   │  ├─ ATR-based trailing stop calculation
   │  ├─ Drawdown-aware tightening
   │  ├─ Broker minimum distance validation
   │  └─ Position modification via PositionLifecycle
   └─ Exit Strategy Evaluation (priority-sorted):
      ├─ Check each exit strategy (Stop Loss, Take Profit, Trailing Stop, Time-based)
      ├─ Process first triggering exit signal
      └─ Close position and update database
   
8. CONNECTION HEALTH CHECK (_check_connection_health)
   ├─ Verify MT5 connection via connector.is_connected()
   ├─ Attempt reconnection if disconnected
   └─ Reconcile positions after successful reconnect
   
9. PERFORMANCE REPORTING (_report_performance_metrics)
   ├─ Every 10 loops: publish metrics to Prometheus
   ├─ Sync position summary into MetricsCollector
   ├─ Write metrics to textfile for node_exporter
   └─ Log position statistics (open count, total P&L)
```

---

## 4. MT5 Connector & Symbol Handling (`connector/mt5_connector.py`)

### MT5Connector Responsibilities

```python
class MT5Connector:
    """MetaTrader 5 connection manager with health checks"""
    
    # Core Methods
    def connect() -> bool
        """Establish MT5 session with retry logic"""
    
    def get_rates(symbol, timeframe, count) -> List[Dict]
        """Fetch OHLCV historical data"""
    
    def get_account_info() -> Dict
        """Balance, equity, margin, leverage"""
    
    def get_symbol_info(symbol) -> Dict
        """Bid/ask, point size, min lot, stops level"""
    
    def get_position_by_ticket(ticket) -> Dict
        """Fetch single position details"""
    
    def get_open_positions() -> List[Dict]
        """Get all positions from MT5"""
    
    # Symbol Selection
    def ensure_symbol_selected(symbol) -> Optional[str]
        """Flexible symbol matching with variant support"""
    
    # Health & Reconnection
    def is_connected() -> bool
        """Check connection status"""
    
    def reconnect() -> bool
        """Reconnect after connection loss"""
```

### Symbol Handling Strategy

**Configuration:**
- Primary symbol from `config.json`: `config['trading']['symbol']` (e.g., 'EURUSD')
- Passed to TradingLoopContext at initialization
- Used for all rate fetching and position filtering

**Flexible Symbol Matching:**
The connector implements intelligent symbol matching to handle broker variations:

1. **Exact normalized match**: `GOLD` → `GOLD`
2. **Token equality**: Handles multi-word symbol names
3. **Prefix match with short suffix**: `GOLD` → `GOLDm`, `GOLD` → `GOLD#`
4. **Fallback substring**: For longer queries only

**Symbol Variants:**
- Automatically tries common variations: `#m` ↔ `m#`
- Removes special characters if needed: `GOLD#` → `GOLD`
- Validates tradability (checks for point, volume_min)

**Key Symbol Info:**
- `point`: Minimum price increment (e.g., 0.00001 for EURUSD)
- `volume_min`: Minimum tradable lot (default 0.01, broker-specific)
- `volume_step`: Lot increment (usually 0.01)
- `trade_stops_level`: Minimum distance for SL/TP in points

---

## 5. Risk Evaluation & Position Management

### RiskEvaluator Flow (`risk/evaluator.py`)

```python
RiskEvaluator.approve(signal, account_info, current_positions):
│
├─ 1. Balance Protection Checks
│  ├─ Negative balance detection → HALT
│  ├─ Balance below minimum threshold → REJECT
│  ├─ Negative equity → EMERGENCY CLOSE ALL
│  ├─ Margin call detection → REDUCE/HALT
│  └─ Excessive drawdown → HALT/REDUCE
│
├─ 2. Daily Limit Checks
│  ├─ Daily loss limit enforcement
│  ├─ Daily trade count limit
│  └─ Reset tracking at day boundary
│
├─ 3. Position Size Calculation
│  ├─ Base calculation:
│  │  - Fixed lot size, OR
│  │  - Risk percentage (e.g., 1% of balance), OR
│  │  - Volatility-adjusted (ATR-based), OR
│  │  - Kelly criterion (optimal growth)
│  ├─ Constraints:
│  │  ├─ Minimum lot (from symbol info)
│  │  ├─ Maximum lot (from symbol info)
│  │  └─ Round to volume_step
│  └─ Apply balance scaling factor
│
├─ 4. Risk/Reward Validation
│  ├─ Calculate expected R:R from signal SL/TP
│  ├─ Compare against min_risk_reward_ratio (default 1.5)
│  └─ Reject if insufficient R:R
│
├─ 5. Spread Validation
│  ├─ Get current spread from MT5
│  ├─ Check against max_spread_points (5000 default)
│  ├─ Check against max_spread_pct (5% default)
│  └─ Reject if spread too wide
│
├─ 6. Per-Symbol Limits
│  ├─ Count existing positions for this symbol
│  ├─ Check max_positions_per_symbol (default 3)
│  └─ Check max_exposure_per_symbol_percent (default 5%)
│
├─ 7. Confidence Threshold
│  ├─ Compare signal.confidence against min_confidence
│  └─ Reject if below threshold
│
└─ Return: (approved: bool, reason: str, position_size: float)
```

### Position Management Stack

```
┌──────────────────────────────────────────────────────────────┐
│                    Position Management Layers                │
└──────────────────────────────────────────────────────────────┘

Layer 1: PositionManager (High-level - for Trading Loop)
├─ monitor_positions() → List[PositionInfo]
│  └─ Fetches positions, calculates unrealized P&L
├─ close_position(ticket, reason, partial_volume=None)
│  └─ Creates CLOSE order via ExecutionEngine
├─ track_position(order_result, signal_metadata)
│  └─ Records new position in tracker
├─ reconcile_positions()
│  └─ Syncs tracker state with MT5 after reconnect
└─ get_statistics() → Dict
   └─ Win rate, average win/loss, Sharpe ratio, etc.

Layer 2: PositionLifecycle (Mid-level - Operations)
├─ modify_position(ticket, sl=None, tp=None) → bool
│  ├─ Validates minimum distance to current price
│  ├─ Creates MODIFY request via ExecutionEngine
│  └─ Updates tracker on success
├─ refresh_positions()
│  └─ Fetches latest state from MT5
└─ reconcile_positions()
   └─ Adds missing positions, removes closed ones

Layer 3: PositionTracker (Low-level - State)
├─ get_position(ticket) → Optional[PositionInfo]
├─ get_all_positions() → List[PositionInfo]
├─ add_position(position_info)
├─ update_position(ticket, **kwargs)
└─ remove_position(ticket)
```

### Advanced Position Management Features

**1. Dynamic SL/TP Management** (`risk/dynamic_sltp_manager.py`):
```python
- ATR-based trailing stops (move SL as price moves favorably)
- Drawdown-aware tightening (reduce risk during drawdown)
- Phase-based adjustment (aggressive in growth, conservative in recovery)
- Broker minimum distance validation
- Sanity checks (prevent SL too close to current price)
```

**2. Profit Scaling** (`position/profit_scaler.py`):
```python
- Partial profit taking at configured levels (e.g., 50%, 75%, 100%)
- Risk reduction: Close 50% at +2R, let rest run with BE stop
- Account phase awareness: More aggressive scaling in growth phase
- Minimum lot protection: Don't scale if position at minimum
- Cooldown between scaling actions
```

**3. Adaptive Drawdown Management** (`risk/adaptive_drawdown_manager.py`):
```python
- Tracks peak balance and current drawdown
- Survival threshold (halt trading at 40% DD)
- Trailing lock-in (protect gains by moving peak forward)
- Position reduction on moderate drawdown
- Emergency close on critical drawdown
```

**4. Adaptive Account Manager** (`risk/adaptive_account_manager.py`):
```python
Phases:
- GROWTH: Account growing, allow max risk
- RECOVERY: Account recovering from DD, moderate risk
- SURVIVAL: Account in danger, minimal risk

Dynamic Timeframe:
- Growth phase: Can use lower timeframes (M15, M30)
- Recovery phase: Stick to configured timeframe
- Survival phase: Move to higher timeframes (H4, D1)
```

---

## 6. Data Flow Through System

```
┌─────────────────────────────────────────────────────────────────┐
│                   COMPLETE DATA FLOW PIPELINE                   │
└─────────────────────────────────────────────────────────────────┘

MARKET DATA INGESTION
│
MT5 Terminal
├─ Real-time rates (OHLCV bars)
├─ Current positions
├─ Account information (balance, equity, margin)
└─ Symbol specifications
      │
      ▼
MT5Connector (connector/mt5_connector.py)
├─ get_rates(symbol, timeframe, count)
├─ get_account_info()
├─ get_position_by_ticket(ticket)
├─ get_symbol_info(symbol)
      │
      ▼
DataLayer (data/layer.py)
├─ normalize_rates(rates, symbol)
├─ cache management
├─ symbol normalization
      │
      ▼
TradingLoop._ingest_market_data()
└─ Returns: pandas DataFrame with OHLCV data

─────────────────────────────────────────────────────────────────

INDICATOR CALCULATION
│
TradingLoop._calculate_indicators(df)
├─ Calculate SMA (strategy-dependent periods)
├─ Calculate EMA (strategy-dependent periods)
├─ Ensure runtime indicators:
│  ├─ RSI (from indicators/rsi.py)
│  ├─ ATR (from indicators/atr.py)
│  ├─ ADX (from indicators/adx.py)
│  └─ Optional: MACD, Bollinger, Stochastic, etc.
├─ Create friendly aliases (rsi, atr, adx)
├─ Feed to IndicatorCollector (real-time snapshots)
└─ Feed to ComprehensiveCollector (full metrics)

─────────────────────────────────────────────────────────────────

SIGNAL GENERATION
│
TradingLoop._generate_signal(df)
├─ Current bar extraction: df.iloc[-1]
├─ Strategy signal generation:
│  ├─ SMA Crossover: short_sma crosses long_sma
│  ├─ EMA Crossover: fast_ema crosses slow_ema
│  ├─ Scalping: EMA + RSI + ADX combination
│  ├─ Momentum Breakout: Price breaks high/low + volume confirm
│  └─ Dynamic Selector: Auto-selects best strategy per regime
├─ Cognition Engine enhancement (optional):
│  ├─ Confidence adjustment (boost/reduce)
│  ├─ Size multiplier calculation
│  └─ Trading advisability check
└─ Returns: Signal object or None

─────────────────────────────────────────────────────────────────

ENTRY DECISION
│
TradingLoop._process_entry_signal(signal)
├─ Trade cooldown check (60s minimum interval)
├─ Opposite direction prevention (no BUY if SELL exists)
├─ Entry Confluence Filter (cognition/entry_confluence.py):
│  ├─ Market regime analysis (trending/ranging)
│  ├─ Indicator alignment check
│  ├─ Quality score calculation (EXCELLENT/GOOD/FAIR/POOR)
│  ├─ Queue for better entry if needed
│  └─ Position size multiplier (0.5x for FAIR, 1.0x for GOOD)
├─ Risk approval (risk/evaluator.py):
│  ├─ Balance protection
│  ├─ Position size calculation
│  ├─ Daily limits
│  ├─ Spread validation
│  └─ Risk/reward check
├─ Apply size adjustments:
│  ├─ Entry quality multiplier
│  ├─ Adaptive loss curve
│  └─ Cognition multiplier
└─ Execute order or record advisory

─────────────────────────────────────────────────────────────────

ORDER EXECUTION
│
TradingLoop._execute_order(signal, position_size)
├─ Create OrderRequest (execution/engine.py):
│  ├─ signal_id: Unique identifier
│  ├─ symbol: Trading symbol
│  ├─ side: BUY or SELL
│  ├─ volume: Approved lot size
│  ├─ order_type: MARKET (immediate)
│  ├─ sl: Stop loss price
│  └─ tp: Take profit price
├─ Advisory decision (if enabled):
│  ├─ EXECUTE: Real trade
│  ├─ ADVISORY: Log signal only
│  └─ GHOST: Micro lot test trade
├─ ExecutionEngine.place_order(order_req):
│  ├─ Build MT5 trade request
│  ├─ Send order to terminal
│  ├─ Wait for result (with timeout)
│  └─ Return OrderResult (FILLED/REJECTED/...)
├─ Track position (position/manager.py):
│  └─ PositionManager.track_position(result, metadata)
├─ Record in database (persistence/database.py):
│  ├─ SignalRecord (strategy, confidence, indicators)
│  └─ TradeRecord (entry price, SL, TP, timestamp)
└─ Store in Hektor semantic memory (optional)

─────────────────────────────────────────────────────────────────

POSITION MONITORING
│
TradingLoop._monitor_positions(df)
├─ Get all positions: PositionManager.monitor_positions()
├─ Profit scaling (position/profit_scaler.py):
│  ├─ Check profit levels (e.g., +1R, +2R, +3R)
│  ├─ Execute partial closes at thresholds
│  └─ Move to breakeven after first scale
├─ Cognition exit signals (cognition/exit_oracle.py):
│  ├─ AI/ML enhanced exit analysis
│  ├─ Urgency levels (IMMEDIATE/HIGH/NORMAL/LOW)
│  └─ Exit reasons (profit target reached, trend reversal, etc.)
├─ Dynamic SL/TP (risk/dynamic_sltp_manager.py):
│  ├─ ATR-based trailing calculation
│  ├─ Drawdown-aware tightening
│  ├─ Modify position via PositionLifecycle
│  └─ Update tracker on success
└─ Exit strategy evaluation (exit/*.py):
   ├─ Stop Loss: Hard stop hit
   ├─ Take Profit: Target reached
   ├─ Trailing Stop: Price retraces from peak
   ├─ Time-based: Max duration or weekend protection
   ├─ Multi-RRR: Scale out at multiple R:R levels
   └─ Process first triggering exit (priority order)

─────────────────────────────────────────────────────────────────

POSITION CLOSE
│
TradingLoop._process_exit_signal(position, exit_signal)
├─ Log exit reason
├─ Close position (position/manager.py):
│  ├─ PositionManager.close_position(ticket, reason, partial_volume)
│  ├─ Create CLOSE order via ExecutionEngine
│  └─ Wait for confirmation
├─ Update database (persistence/database.py):
│  └─ update_trade_exit(order_id, exit_price, profit, reason)
├─ Store outcome in Hektor (optional):
│  └─ Trade result, P&L, exit reason for pattern learning
├─ Record metrics:
│  ├─ MetricsCollector.record_position_closed(symbol)
│  └─ Update win/loss statistics
└─ Risk manager update:
   └─ RiskEvaluator.record_trade_result(pnl)

─────────────────────────────────────────────────────────────────

OBSERVABILITY
│
Continuous Monitoring (every loop iteration)
├─ IndicatorCollector.update_snapshot():
│  ├─ RSI value, overbought/oversold
│  ├─ ADX value, trend strength
│  ├─ ATR value
│  └─ Current price, volume
├─ ComprehensiveCollector updates:
│  ├─ Account metrics (balance, equity, margin)
│  ├─ Position metrics (count, unrealized P&L)
│  └─ Price metrics (current price, symbol)
├─ SystemHealthCollector (separate process):
│  ├─ CPU, memory usage
│  ├─ Disk space
│  └─ Network latency
└─ Prometheus export (every 10 loops):
   ├─ MetricsCollector.publish_to_prometheus(exporter)
   ├─ Write to textfile (for node_exporter)
   └─ Serve HTTP /metrics endpoint (port 8181)
```

---

## 7. Critical Safety Mechanisms

### Trade Sequencing & Cooldown

```python
# Prevent rapid-fire entries
_last_trade_time: Optional[datetime] = None
_min_trade_interval_seconds: int = 60  # Configurable

def _check_trade_cooldown(signal) -> bool:
    """Returns True if OK to trade, False if in cooldown"""
    if self._last_trade_time is None:
        return True
    
    elapsed = (datetime.now() - self._last_trade_time).total_seconds()
    if elapsed < self._min_trade_interval_seconds:
        logger.info(f"Trade cooldown: {elapsed}s / {self._min_trade_interval_seconds}s")
        return False
    
    return True
```

### Opposite Direction Prevention

```python
# Block BUY signal if SELL positions exist (and vice versa)
mt5_positions = mt5.positions_get(symbol=symbol)
if mt5_positions:
    existing_directions = set()
    for pos in mt5_positions:
        pos_dir = 'LONG' if pos.type == 0 else 'SHORT'
        existing_directions.add(pos_dir)
    
    signal_direction = 'LONG' if signal.side == SignalType.LONG else 'SHORT'
    opposite_direction = 'SHORT' if signal_direction == 'LONG' else 'LONG'
    
    if opposite_direction in existing_directions:
        logger.warning(f"BLOCKED: {signal_direction} signal while {opposite_direction} exists")
        return  # Reject signal
```

### Entry Quality Gate (Entry Confluence Filter)

```python
from cognition.entry_confluence import get_entry_confluence_filter

confluence_filter = get_entry_confluence_filter(config=config.get('entry_confluence', {}))
result = confluence_filter.analyze_entry(
    signal_direction='long',
    current_price=current_price,
    symbol=symbol,
    market_data=df,
    atr=atr,
    signal_entry_price=signal.price
)

# Quality levels: EXCELLENT, GOOD, FAIR, POOR
# Actions:
# - EXCELLENT/GOOD: Execute immediately (position_mult = 1.0)
# - FAIR: Execute with reduced size (position_mult = 0.5-0.8)
# - POOR: Reject or queue for better entry

if not result.should_enter:
    if result.wait_for_better and result.optimal_entry:
        # Queue signal, wait for price to reach optimal_entry
        confluence_filter.register_pending_entry(
            signal_id=signal.id,
            signal_direction=signal_direction,
            optimal_entry=result.optimal_entry,
            symbol=symbol
        )
    return  # Don't execute now
```

### Negative Balance Protection

```python
# From RiskEvaluator.check_balance_protection()

if balance < 0:
    logger.critical(f"NEGATIVE BALANCE: ${balance:.2f} - ALL TRADING HALTED")
    if negative_balance_action == "close_all":
        _emergency_close_all_positions()
    return False, "CRITICAL: Negative balance - trading halted"

if balance < min_balance_threshold:
    return False, f"Balance ${balance:.2f} below minimum ${min_balance_threshold}"

if equity < 0:
    logger.critical(f"NEGATIVE EQUITY: ${equity:.2f} - emergency close")
    _emergency_close_all_positions()
    return False, "CRITICAL: Negative equity"
```

### Drawdown Halt

```python
# From AdaptiveDrawdownManager

drawdown_pct = ((peak_balance - current_balance) / peak_balance * 100)

if drawdown_pct >= survival_threshold (e.g., 40%):
    logger.critical(f"SURVIVAL MODE: Drawdown {drawdown_pct:.1f}%")
    # Actions:
    # - Close all positions
    # - Halt new entries
    # - Reduce position sizes dramatically
    # - Move to higher timeframes
```

---

## 8. Module Dependencies

```
cthulu/
├── __main__.py                    # Entry point, main() function
├── config_schema.py              # Configuration validation
├── constants.py                  # System constants
│
├── core/                         # Core system modules
│   ├── bootstrap.py              # Component initialization
│   ├── trading_loop.py           # Main execution loop
│   ├── shutdown.py               # Graceful shutdown handler
│   └── exceptions.py             # Custom exceptions
│
├── connector/                    # Market connectivity
│   └── mt5_connector.py          # MT5 connection & data
│
├── data/                         # Data handling
│   └── layer.py                  # Rate normalization, caching
│
├── strategy/                     # Trading strategies
│   ├── base.py                   # Strategy interface
│   ├── sma_crossover.py          # SMA strategy
│   ├── ema_crossover.py          # EMA strategy
│   ├── scalping.py               # Scalping strategy
│   ├── momentum_breakout.py      # Breakout strategy
│   ├── strategy_selector.py      # Dynamic strategy selection
│   └── selector_adapter.py       # Adapter for compatibility
│
├── risk/                         # Risk management
│   ├── evaluator.py              # Unified risk evaluation
│   ├── manager.py                # Legacy risk manager
│   ├── unified_manager.py        # Consolidated risk logic
│   ├── dynamic_sltp_manager.py   # ATR-based trailing stops
│   ├── adaptive_drawdown_manager.py  # Drawdown protection
│   └── adaptive_account_manager.py   # Phase-based scaling
│
├── execution/                    # Order execution
│   └── engine.py                 # ExecutionEngine, OrderRequest
│
├── position/                     # Position management
│   ├── tracker.py                # Low-level state tracking
│   ├── manager.py                # High-level monitoring
│   ├── lifecycle.py              # Position operations
│   ├── adoption.py               # External trade adoption
│   ├── profit_scaler.py          # Partial profit taking
│   └── trade_manager.py          # Trade coordination
│
├── exit/                         # Exit strategies
│   ├── base.py                   # ExitStrategy interface
│   ├── stop_loss.py              # Hard stop loss
│   ├── take_profit.py            # Take profit target
│   ├── trailing_stop.py          # Trailing stop
│   ├── time_based.py             # Max duration, weekend close
│   ├── multi_rrr.py              # Multi-level R:R exits
│   └── profit_scaling.py         # Profit scaling strategy
│
├── indicators/                   # Technical indicators
│   ├── rsi.py                    # Relative Strength Index
│   ├── atr.py                    # Average True Range
│   ├── adx.py                    # Average Directional Index
│   ├── macd.py                   # MACD
│   ├── bollinger.py              # Bollinger Bands
│   ├── stochastic.py             # Stochastic Oscillator
│   ├── supertrend.py             # Supertrend
│   └── vwap.py                   # Volume Weighted Average Price
│
├── cognition/                    # AI/ML enhancement
│   ├── engine.py                 # Cognition Engine interface
│   ├── entry_confluence.py       # Entry quality analysis
│   ├── exit_oracle.py            # AI-enhanced exit decisions
│   ├── regime_classifier.py      # Market regime detection
│   ├── sentiment_analyzer.py     # Market sentiment
│   └── structure_detector.py     # Market structure analysis
│
├── persistence/                  # Data persistence
│   └── database.py               # SQLite database
│
├── observability/                # Monitoring & metrics
│   ├── metrics.py                # MetricsCollector
│   ├── prometheus.py             # Prometheus exporter
│   ├── logger.py                 # Logging setup
│   └── comprehensive_collector.py # Full system metrics
│
├── monitoring/                   # Real-time monitoring
│   ├── indicator_collector.py    # Indicator snapshots
│   ├── system_health_collector.py # CPU, memory, disk
│   └── service.py                # Monitoring service
│
├── integrations/                 # External integrations
│   └── hektor/                   # Vector Studio semantic memory
│       ├── adapter.py            # Hektor adapter
│       └── retriever.py          # Similarity search
│
├── utils/                        # Utilities
│   ├── retry.py                  # Retry decorator
│   ├── rate_limiter.py           # Rate limiting
│   ├── health_monitor.py         # Health checks
│   └── indicator_calculator.py   # Indicator helpers
│
└── config/                       # Configuration
    ├── wizard.py                 # Interactive setup
    └── mindsets.py               # Risk profiles
```

---

## 9. Configuration Structure

```json
{
  "trading": {
    "symbol": "EURUSD",
    "timeframe": "TIMEFRAME_H1",
    "poll_interval": 60,
    "lookback_bars": 100,
    "min_trade_interval": 60
  },
  "mt5": {
    "login": 12345678,
    "password": "password",
    "server": "BrokerServer-Demo",
    "timeout": 60000,
    "path": "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
  },
  "strategy": {
    "type": "sma_crossover",
    "params": {
      "short_window": 20,
      "long_window": 50
    }
  },
  "risk": {
    "max_position_size_percent": 2.0,
    "max_total_exposure_percent": 10.0,
    "max_daily_loss": 500.0,
    "min_risk_reward_ratio": 1.5,
    "max_spread_points": 5000.0,
    "min_balance_threshold": 10.0,
    "drawdown_halt_percent": 50.0
  },
  "indicators": [
    {"type": "rsi", "params": {"period": 14}},
    {"type": "atr", "params": {"period": 14}},
    {"type": "adx", "params": {"period": 14}}
  ],
  "exit_strategies": [
    {"type": "stop_loss", "priority": 1, "enabled": true},
    {"type": "take_profit", "priority": 2, "enabled": true},
    {"type": "trailing_stop", "priority": 3, "enabled": true, 
     "params": {"atr_multiplier": 2.0}},
    {"type": "time_based", "priority": 4, "enabled": true,
     "params": {"max_duration_hours": 24, "weekend_protection": true}}
  ],
  "dynamic_sltp": {
    "enabled": true,
    "atr_multiplier_sl": 2.0,
    "atr_multiplier_tp": 4.0,
    "min_sl_distance_pct": 0.001
  },
  "profit_scaling": {
    "enabled": true,
    "levels": [
      {"profit_pct": 50, "close_pct": 30},
      {"profit_pct": 100, "close_pct": 50}
    ]
  },
  "entry_confluence": {
    "enabled": true,
    "min_score": 50,
    "queue_for_better": true,
    "max_wait_bars": 5
  },
  "observability": {
    "prometheus": {
      "enabled": true,
      "http_port": 8181,
      "textfile_path": "metrics/Cthulu_metrics.prom",
      "prefix": "Cthulu"
    }
  }
}
```

---

## 10. Key Interfaces & Contracts

### Signal Interface

```python
@dataclass
class Signal:
    id: str                          # Unique signal ID
    timestamp: datetime              # Signal generation time
    symbol: str                      # Trading symbol
    timeframe: str                   # Timeframe
    side: SignalType                 # LONG or SHORT
    action: str                      # 'BUY' or 'SELL'
    price: float                     # Entry price
    stop_loss: float                 # Stop loss price
    take_profit: float               # Take profit price
    confidence: float                # 0.0 to 1.0
    reason: str                      # Signal reason
    metadata: Dict[str, Any]         # Additional context
```

### Strategy Interface

```python
class Strategy(ABC):
    @abstractmethod
    def on_bar(self, bar: pd.Series) -> Optional[Signal]:
        """Generate signal from current bar"""
        pass
    
    def generate_signal(self, df: pd.DataFrame, bar: pd.Series) -> Optional[Signal]:
        """Generate signal with full dataframe context"""
        return self.on_bar(bar)
```

### RiskEvaluator Interface

```python
def approve(
    self,
    signal: Signal,
    account_info: Dict[str, Any],
    current_positions: int
) -> Tuple[bool, str, float]:
    """
    Evaluate signal and approve/reject.
    
    Returns:
        (approved, reason, position_size)
    """
    pass
```

### ExecutionEngine Interface

```python
@dataclass
class OrderRequest:
    signal_id: str
    symbol: str
    side: str                  # 'BUY' or 'SELL'
    volume: float
    order_type: OrderType      # MARKET, LIMIT, STOP
    sl: Optional[float] = None
    tp: Optional[float] = None

def place_order(self, order_req: OrderRequest) -> OrderResult:
    """Execute order and return result"""
    pass
```

### ExitStrategy Interface

```python
class ExitStrategy(ABC):
    @abstractmethod
    def should_exit(
        self,
        position: PositionInfo,
        market_data: Dict[str, Any]
    ) -> Optional[ExitSignal]:
        """Check if position should be closed"""
        pass
```

---

## 11. Weekend Trading Detection

**Location:** `exit/time_based.py` - `_check_weekend_protection()`

```python
def _check_weekend_protection(position, current_time) -> Optional[ExitSignal]:
    """
    Close forex positions before Friday market close.
    Skip for crypto symbols (24/7 trading).
    """
    symbol = position.symbol
    
    # Define crypto prefixes (trade 24/7)
    crypto_prefixes = (
        'BTC', 'ETH', 'XRP', 'LTC', 'BCH', 'ADA', 'DOT', 'DOGE',
        'SOL', 'AVAX', 'MATIC', 'LINK', 'UNI', 'ATOM', 'XLM'
    )
    
    # Check if crypto
    is_crypto = any(
        symbol.upper().startswith(prefix) 
        for prefix in crypto_prefixes
    )
    
    if is_crypto:
        return None  # No weekend protection needed
    
    # Friday is weekday 4
    if current_time.weekday() == 4:
        # Check if past Friday close time (e.g., 21:00 GMT)
        if current_time.time() >= friday_close_time:
            return ExitSignal(
                ticket=position.ticket,
                reason="Weekend protection (Friday close)",
                strategy_name="time_based"
            )
    
    return None
```

**Detection Logic:**
- **Crypto markets** (BTCUSD#, ETHUSD#, etc.): Open 24/7, no weekend close
- **Forex/Gold** (EURUSD, GOLD#, XAUUSD): Close Friday, reopen Sunday
- **Detection method**: Symbol name prefix matching

**Current Implementation:**
✅ Correctly detects crypto symbols
✅ Skips weekend protection for crypto
✅ Closes forex/gold positions before weekend

---

## Summary

The Cthulu trading system is a comprehensive, production-grade automated trading platform with:

- **Modular architecture**: Clean separation of concerns (data, strategy, risk, execution)
- **Robust error handling**: Connection recovery, position reconciliation, graceful shutdown
- **Advanced risk management**: Multi-layered protection (balance, drawdown, daily limits)
- **Quality gates**: Entry confluence filter, trade cooldown, opposite direction prevention
- **Adaptive features**: Dynamic SL/TP, profit scaling, phase-based risk adjustment
- **Comprehensive observability**: Real-time metrics, Prometheus export, health monitoring
- **AI/ML enhancement**: Optional Cognition Engine for signal and exit optimization
- **Semantic memory**: Hektor integration for pattern learning from past trades

The main loop orchestrates a continuous cycle of market data ingestion, indicator calculation, signal generation, risk evaluation, order execution, and position monitoring, with multiple safety mechanisms ensuring capital preservation and systematic risk control.
