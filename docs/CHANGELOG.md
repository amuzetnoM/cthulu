# Changelog

## [1.0.0] - 2026-01-09

### Initial Release - Clean Rule-Based Implementation

#### Core Features
- **Signal Engine**: Multi-strategy signal generation with proper SMA/EMA calculations
- **Dynamic SLTP**: ATR-based with initial, breakeven, and trailing modes
- **Strategy Selector**: Regime-aware strategy selection (7 strategies)
- **Entry Confluence**: S/R, momentum, timing, and structure scoring
- **Risk Management**: Position sizing, exposure limits, drawdown protection

#### Strategies
- SMA Crossover (10/30) with continuation signals
- EMA Crossover (12/26) with continuation signals  
- Momentum Breakout with RSI confirmation
- Scalping with fast EMA and RSI extremes
- Mean Reversion with Bollinger Bands
- Trend Following with ADX filter
- RSI Reversal at extreme levels

#### Position Management
- Trade adoption for external positions
- Automatic SL/TP application on adoption
- Position lifecycle tracking
- Magic number management

#### Exit Strategies
- Dynamic trailing stop with protective mode
- Partial profit taking at levels
- Time-based exit (24h max hold, weekend close)

#### Infrastructure
- MT5 connector with retry logic
- SQLite persistence layer
- Data layer with caching
- Liquidity/spread filters
- Trade monitoring

### Technical Notes
- Built from windows-ml branch as foundation
- Removed all ML/AI components for pure rule-based operation
- Clean separation of concerns across modules
- Proper symbol propagation (no more "UNKNOWN")
- ATR-based calculations throughout
