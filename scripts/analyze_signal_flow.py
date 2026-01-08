#!/usr/bin/env python3
"""
Signal Flow Analyzer - Debug signal generation pipeline
Traces: Strategy Selection -> Signal Generation -> Entry Confluence -> Risk Approval -> Execution
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pandas as pd
import numpy as np
from datetime import datetime


def analyze_market_data():
    """Check if market data is sufficient for signal generation."""
    print("=" * 60)
    print("1. MARKET DATA ANALYSIS")
    print("=" * 60)
    
    try:
        from connector.mt5_connector import MT5Connector
        
        # Load config
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        connector = MT5Connector(config['connector'])
        
        # Try to connect
        if not connector.connect():
            print("❌ Cannot connect to MT5")
            return False
        
        print(f"✅ Connected to MT5")
        
        # Get market data
        symbol = config['trading']['symbol']
        timeframe = config['trading']['timeframe']
        
        # Parse timeframe
        import MetaTrader5 as mt5
        tf_map = {
            'TIMEFRAME_M1': mt5.TIMEFRAME_M1,
            'TIMEFRAME_M5': mt5.TIMEFRAME_M5,
            'TIMEFRAME_M15': mt5.TIMEFRAME_M15,
            'TIMEFRAME_H1': mt5.TIMEFRAME_H1,
            'TIMEFRAME_H4': mt5.TIMEFRAME_H4,
            'TIMEFRAME_D1': mt5.TIMEFRAME_D1
        }
        tf = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
        
        bars = mt5.copy_rates_from_pos(symbol, tf, 0, 500)
        
        if bars is None or len(bars) < 50:
            print(f"❌ Insufficient data: {len(bars) if bars is not None else 0} bars")
            return False
        
        print(f"✅ Market data: {len(bars)} bars available")
        
        df = pd.DataFrame(bars)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Check data quality
        print(f"   Latest bar: {df['time'].iloc[-1]}")
        print(f"   Close: {df['close'].iloc[-1]:.2f}")
        print(f"   Volume: {df['tick_volume'].iloc[-1]}")
        
        # Calculate indicators
        df['sma_10'] = df['close'].rolling(window=10, min_periods=1).mean()
        df['sma_30'] = df['close'].rolling(window=30, min_periods=1).mean()
        df['ema_12'] = df['close'].ewm(span=12, adjust=False, min_periods=1).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False, min_periods=1).mean()
        
        # Check for crossovers
        sma_cross = df['sma_10'].iloc[-1] - df['sma_30'].iloc[-1]
        ema_cross = df['ema_12'].iloc[-1] - df['ema_26'].iloc[-1]
        
        print(f"   SMA(10): {df['sma_10'].iloc[-1]:.2f}, SMA(30): {df['sma_30'].iloc[-1]:.2f}, Diff: {sma_cross:.2f}")
        print(f"   EMA(12): {df['ema_12'].iloc[-1]:.2f}, EMA(26): {df['ema_26'].iloc[-1]:.2f}, Diff: {ema_cross:.2f}")
        
        if abs(sma_cross) < 5:
            print("   ⚠️  SMA near crossover - signal potential")
        if abs(ema_cross) < 5:
            print("   ⚠️  EMA near crossover - signal potential")
        
        return True
        
    except Exception as e:
        print(f"❌ Market data analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def analyze_strategy_selection():
    """Check strategy selector logic."""
    print("\n" + "=" * 60)
    print("2. STRATEGY SELECTION ANALYSIS")
    print("=" * 60)
    
    try:
        from strategy.strategy_selector import StrategySelector, MarketRegime
        
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        strategy_config = config.get('strategy', {})
        selector = StrategySelector(strategy_config)
        
        print(f"✅ StrategySelector loaded with {len(selector.strategies)} strategies:")
        for name, strat in selector.strategies.items():
            print(f"   - {name}: {strat.__class__.__name__}")
        
        # Check what regime would be selected
        print("\n   Simulating regime detection...")
        print("   Trend (ADX > 30) -> EMA/SMA/Trend strategies preferred")
        print("   Range (ADX < 20) -> Mean Reversion/Scalping preferred")
        print("   Volatile -> Breakout/Momentum preferred")
        
        return True
        
    except Exception as e:
        print(f"❌ Strategy selection analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def analyze_entry_confluence():
    """Check entry confluence filter configuration."""
    print("\n" + "=" * 60)
    print("3. ENTRY CONFLUENCE FILTER ANALYSIS")
    print("=" * 60)
    
    try:
        from cognition.entry_confluence import EntryConfluenceFilter, EntryQuality
        
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        confluence_config = config.get('entry_confluence', {})
        
        if not confluence_config.get('enabled', False):
            print("⚠️  Entry Confluence Filter is DISABLED")
            return False
        
        print("✅ Entry Confluence Filter ENABLED")
        print(f"   Min score to enter: {confluence_config.get('min_score_to_enter', 50)}")
        print(f"   Min score for full size: {confluence_config.get('min_score_for_full_size', 75)}")
        print(f"   Wait mode: {confluence_config.get('enable_wait_mode', True)}")
        
        # Test filter
        filter = EntryConfluenceFilter(confluence_config)
        
        # Create test data
        test_df = pd.DataFrame({
            'open': [100] * 50,
            'high': [101] * 50,
            'low': [99] * 50,
            'close': np.linspace(100, 105, 50),
            'volume': [1000] * 50
        })
        
        # Simulate entry analysis
        print("\n   Testing confluence scoring...")
        result = filter.analyze_entry(
            signal_direction='long',
            current_price=105.0,
            symbol='BTCUSD#',
            market_data=test_df,
            atr=2.0
        )
        
        print(f"   Test Result: {result.quality.value}")
        print(f"   Score: {result.score:.1f}/100")
        print(f"   Should enter: {result.should_enter}")
        print(f"   Position multiplier: {result.position_mult:.2f}")
        print(f"   Reasons: {', '.join(result.reasons[:3])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Entry confluence analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def analyze_risk_approval():
    """Check risk manager configuration."""
    print("\n" + "=" * 60)
    print("4. RISK APPROVAL ANALYSIS")
    print("=" * 60)
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        risk_config = config.get('risk', {})
        
        print("✅ Risk Configuration:")
        print(f"   Max risk per trade: {risk_config.get('max_risk_per_trade_pct', 2.0)}%")
        print(f"   Max total risk: {risk_config.get('max_total_risk_pct', 10.0)}%")
        print(f"   Max concurrent trades: {risk_config.get('max_concurrent_trades', 3)}")
        print(f"   Min balance threshold: ${risk_config.get('min_balance_threshold', 10.0)}")
        
        # Check for overly restrictive settings
        if risk_config.get('max_risk_per_trade_pct', 2.0) < 0.5:
            print("   ⚠️  Max risk per trade is very low - may prevent trading")
        
        if risk_config.get('max_concurrent_trades', 3) == 0:
            print("   ❌ Max concurrent trades is 0 - NO TRADING ALLOWED")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Risk approval analysis failed: {e}")
        return False


def analyze_execution_path():
    """Check execution engine configuration."""
    print("\n" + "=" * 60)
    print("5. EXECUTION PATH ANALYSIS")
    print("=" * 60)
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        trading_config = config.get('trading', {})
        
        print("✅ Trading Configuration:")
        print(f"   Symbol: {trading_config.get('symbol', 'N/A')}")
        print(f"   Timeframe: {trading_config.get('timeframe', 'N/A')}")
        print(f"   Concurrency: {trading_config.get('concurrency', 1)}")
        print(f"   Min trade interval: {trading_config.get('min_trade_interval', 120)}s")
        
        # Check advisory mode
        advisory_config = config.get('advisory', {})
        if advisory_config.get('enabled', False):
            print("\n   ⚠️  Advisory Mode ENABLED:")
            print(f"      Mode: {advisory_config.get('mode', 'advisory')}")
            if advisory_config.get('mode') == 'advisory':
                print("      → Trades will be logged but NOT executed")
            elif advisory_config.get('mode') == 'ghost':
                print("      → Trades will be simulated only")
        else:
            print("\n   ✅ Advisory Mode DISABLED - Real execution")
        
        return True
        
    except Exception as e:
        print(f"❌ Execution path analysis failed: {e}")
        return False


def main():
    """Run complete signal flow analysis."""
    print("\n" + "=" * 70)
    print(" SIGNAL FLOW ANALYZER - Cthulu Trading System")
    print("=" * 70 + "\n")
    
    results = []
    
    # 1. Market Data
    results.append(analyze_market_data())
    
    # 2. Strategy Selection
    results.append(analyze_strategy_selection())
    
    # 3. Entry Confluence
    results.append(analyze_entry_confluence())
    
    # 4. Risk Approval
    results.append(analyze_risk_approval())
    
    # 5. Execution
    results.append(analyze_execution_path())
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if all(results):
        print("✅ ALL COMPONENTS FUNCTIONAL")
        print("\nSignal Flow: Strategy → Confluence → Risk → Execution")
        print("\nIf no signals generating:")
        print("  → Market conditions don't meet strategy criteria (legitimate)")
        print("  → Wait for SMA/EMA crossover or other strategy conditions")
    else:
        print("❌ ISSUES DETECTED - Review output above")
        failed = ["Market Data", "Strategy Selection", "Entry Confluence", "Risk Approval", "Execution"]
        for i, passed in enumerate(results):
            if not passed:
                print(f"   ✗ {failed[i]} FAILED")
    
    print("=" * 70 + "\n")
    
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
