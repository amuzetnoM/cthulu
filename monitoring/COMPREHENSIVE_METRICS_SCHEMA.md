# Cthulu Comprehensive Metrics Schema
# 
# This document defines ALL metrics that should be collected in real-time
# for exhaustive trading system monitoring and benchmarking.
#
# Based on TRADING_REPORT.md with additions for completeness.

## Core Account Metrics (10)
- timestamp: ISO8601 datetime with timezone
- account_balance: Current account balance ($)
- account_equity: Current account equity ($)
- account_margin: Used margin ($)
- account_free_margin: Available margin ($)
- account_margin_level: Margin level (%)
- starting_balance: Session starting balance ($)
- realized_pnl: Total realized P&L ($)
- unrealized_pnl: Total unrealized P&L ($)
- total_pnl: Total P&L (realized + unrealized) ($)

## Trade Statistics (25)
- total_trades: Cumulative trades executed
- winning_trades: Number of winning trades
- losing_trades: Number of losing trades
- breakeven_trades: Number of breakeven trades
- active_positions: Currently open positions
- positions_opened_total: Cumulative positions ever opened
- gross_profit: Sum of all winning trades ($)
- gross_loss: Sum of all losing trades ($)
- net_profit: Gross profit - gross loss ($)
- avg_win: Average profit per winning trade ($)
- avg_loss: Average loss per losing trade ($)
- largest_win: Best single trade ($)
- largest_loss: Worst single trade ($)
- win_rate: Winning trades / total trades (%)
- profit_factor: Gross profit / gross loss
- expectancy: Expected $ per trade
- avg_trade_duration: Average time in trade (seconds)
- median_trade_duration: Median time in trade (seconds)
- shortest_trade: Shortest trade duration (seconds)
- longest_trade: Longest trade duration (seconds)
- trades_per_hour: Average trading frequency
- trades_today: Trades executed today
- daily_pnl: Today's P&L ($)
- weekly_pnl: This week's P&L ($)
- monthly_pnl: This month's P&L ($)

## Risk & Drawdown Metrics (15)
- max_drawdown_pct: Maximum drawdown (%)
- max_drawdown_abs: Maximum drawdown ($)
- current_drawdown_pct: Current drawdown (%)
- current_drawdown_abs: Current drawdown ($)
- max_drawdown_duration_seconds: Longest drawdown period
- current_drawdown_duration_seconds: Current drawdown duration
- drawdown_recovery_time_seconds: Time to recover from drawdown
- drawdown_frequency_per_hour: Drawdown events per hour
- avg_drawdown_pct: Average drawdown size (%)
- peak_equity: All-time high equity ($)
- trough_equity: All-time low equity ($)
- equity_curve_slope: Trend of equity curve
- risk_reward_ratio: Average risk:reward achieved
- median_risk_reward: Median risk:reward
- rr_count: Number of trades with valid R:R

## Advanced Statistical Metrics (10)
- sharpe_ratio: Risk-adjusted return (annualized)
- sortino_ratio: Downside risk-adjusted return
- calmar_ratio: Return / max drawdown
- omega_ratio: Probability-weighted gains vs losses
- k_ratio: Equity curve linearity
- recovery_factor: Net profit / max drawdown
- ulcer_index: Drawdown duration weighted severity
- rolling_sharpe_50: Rolling 50-trade Sharpe ratio
- rolling_sharpe_100: Rolling 100-trade Sharpe ratio
- var_95: Value at Risk (95% confidence)

## Execution Quality Metrics (12)
- avg_slippage_pips: Average slippage in pips
- median_slippage_pips: Median slippage in pips
- max_slippage_pips: Maximum slippage experienced
- avg_execution_time_ms: Average order execution time (ms)
- median_execution_time_ms: Median execution time (ms)
- max_execution_time_ms: Maximum execution time (ms)
- fill_rate_pct: Percentage of orders filled
- order_rejection_rate_pct: Percentage of orders rejected
- partial_fills: Number of partial fills
- requotes: Number of requotes
- orders_total: Total orders placed
- orders_filled: Total orders filled

## Signal & Strategy Metrics (20)
- signals_generated_total: Total signals generated
- signals_approved_total: Signals passed risk filters
- signals_rejected_total: Signals rejected by risk
- signal_approval_rate_pct: Approval rate (%)
- sma_crossover_signals: SMA crossover signals
- rsi_signals: RSI signals
- macd_signals: MACD signals
- combined_signals: Combined indicator signals
- spread_rejections: Rejected due to spread
- position_limit_rejections: Rejected due to position limits
- drawdown_limit_rejections: Rejected due to drawdown
- exposure_limit_rejections: Rejected due to exposure
- daily_loss_limit_rejections: Rejected due to daily loss
- strategy_sma_trades: Trades from SMA strategy
- strategy_momentum_trades: Trades from momentum strategy
- strategy_mean_reversion_trades: Trades from mean reversion
- exit_tp_count: Take profit exits
- exit_sl_count: Stop loss exits
- exit_trailing_count: Trailing stop exits
- exit_manual_count: Manual exits

## Position & Exposure Metrics (10)
- open_positions_count: Currently open positions
- open_positions_volume: Total volume in lots
- long_positions_count: Long positions open
- short_positions_count: Short positions open
- long_exposure_usd: Long exposure ($)
- short_exposure_usd: Short exposure ($)
- net_exposure_usd: Net exposure ($)
- max_concurrent_positions: Peak concurrent positions
- avg_position_size_lots: Average position size
- position_sizing_factor: Current position sizing multiplier

## Per-Symbol Metrics (8 per symbol, track top 5)
- symbol_trades_total: Total trades for symbol
- symbol_winning_trades: Winning trades for symbol
- symbol_win_rate_pct: Win rate for symbol (%)
- symbol_realized_pnl: Realized P&L for symbol ($)
- symbol_unrealized_pnl: Unrealized P&L for symbol ($)
- symbol_open_positions: Open positions for symbol
- symbol_exposure_usd: Exposure for symbol ($)
- symbol_avg_trade_pnl: Average trade P&L for symbol ($)

## Session & Time-Based Metrics (10)
- session_asian_trades: Trades during Asian session
- session_european_trades: Trades during European session
- session_us_trades: Trades during US session
- session_overlap_trades: Trades during session overlaps
- hour_00_04_trades: Trades 00:00-04:00 UTC
- hour_04_08_trades: Trades 04:00-08:00 UTC
- hour_08_12_trades: Trades 08:00-12:00 UTC
- hour_12_16_trades: Trades 12:00-16:00 UTC
- hour_16_20_trades: Trades 16:00-20:00 UTC
- hour_20_24_trades: Trades 20:00-24:00 UTC

## System Health Metrics (15)
- system_uptime_seconds: System uptime
- mt5_connected: MT5 connection status (1/0)
- mt5_connection_uptime_seconds: MT5 connection uptime
- mt5_reconnections: Number of reconnections
- cpu_usage_pct: CPU usage (%)
- memory_usage_mb: Memory usage (MB)
- memory_usage_pct: Memory usage (%)
- disk_usage_gb: Disk usage (GB)
- network_latency_ms: Network latency to broker (ms)
- api_calls_per_minute: API calls to MT5 per minute
- errors_total: Total errors encountered
- warnings_total: Total warnings
- critical_errors_total: Critical errors
- last_error_timestamp: Last error occurrence
- system_restarts: Number of system restarts

## Adaptive & Dynamic Metrics (8)
- drawdown_state: Current drawdown management state
- position_sizing_adjustment: Position sizing adjustment factor
- adaptive_sl_distance_pips: Current adaptive SL distance
- adaptive_tp_distance_pips: Current adaptive TP distance
- trailing_stop_active: Trailing stop active (1/0)
- breakeven_stop_active: Breakeven stop active (1/0)
- survival_mode_active: Survival mode active (1/0)
- recovery_mode_active: Recovery mode active (1/0)

## Performance Grade Metrics (5)
- overall_grade: Overall system grade (A+ to F)
- win_rate_grade: Win rate grade
- profit_factor_grade: Profit factor grade
- drawdown_grade: Drawdown grade
- sharpe_grade: Sharpe ratio grade

## TOTAL COMPREHENSIVE METRICS: 173 fields

## Missing Metrics Identified (Not in TRADING_REPORT.md)
1. Account margin metrics (margin, free margin, margin level)
2. Trade duration statistics (avg, median, min, max)
3. Slippage statistics (median, max)
4. Execution time statistics (median, max)
5. Partial fills and requotes
6. Per-session trading statistics (Asian, European, US, Overlap)
7. Hourly trading distribution (6 time blocks)
8. System resource usage (CPU, memory, disk)
9. Network latency and API call rate
10. Error classification (errors, warnings, critical)
11. Adaptive system state (drawdown state, position sizing adjustments)
12. Dynamic SL/TP distances
13. Trailing and breakeven stop status
14. Survival/recovery mode indicators
15. Performance grading by category
16. Equity curve analysis (slope, peak, trough)
17. VaR (Value at Risk)
18. Rolling Sharpe ratios (50, 100 trades)
19. Weekly and monthly P&L tracking
20. Max concurrent positions
