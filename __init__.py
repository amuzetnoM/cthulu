"""
Cthulu Rule-Based Trading System v5.2.0
A clean, modular, rule-based autonomous trading engine.

Architecture:
- core/: Bootstrap, main loop, shutdown
- strategy/: Trading strategies (SMA, EMA, Momentum, Scalping, MeanReversion, TrendFollowing, RSI)
- indicators/: Technical indicators (RSI, ADX, ATR, MACD, Bollinger, Stochastic, VWAP)
- risk/: Risk management (evaluator, dynamic_sltp, adaptive_drawdown)
- position/: Position management (trade_manager, lifecycle, adoption)
- exit/: Exit strategies (trailing_stop, time_based, profit_target, adverse_movement)
- execution/: Order execution engine
- connector/: MT5 connector
- cognition/: Entry confluence, market regime, pattern analysis
- filters/: Liquidity filter
- persistence/: Database layer
- monitoring/: Metrics collection
"""

__version__ = "5.2.0"
__codename__ = "Rule-Based"
