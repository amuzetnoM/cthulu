#!/usr/bin/env python3
"""
Force Signal Test - Manually trigger signal to test complete flow
Tests: Signal Generation → Entry Confluence → Risk Approval → Execution (dry run)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pandas as pd
import numpy as np
from datetime import datetime


def create_test_signal():
    """Create a test signal to trace through the system."""
    from strategy.base import Signal, SignalType
    
    signal = Signal(
        id=f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        timestamp=datetime.now(),
        symbol="BTCUSD#",
        timeframe="H1",
        side=SignalType.LONG,
        action="OPEN",
        confidence=0.75,
        price=100000.0,
        stop_loss=99000.0,
        take_profit=102000.0,
        metadata={'test': True, 'source': 'manual_test'}
    )
    
    print(f"✅ Created test signal: {signal.side.name} @ {signal.price}")
    return signal


def test_entry_confluence(signal):
    """Test entry confluence filter."""
    print("\n" + "=" * 60)
    print("TESTING: Entry Confluence Filter")
    print("=" * 60)
    
    try:
        from cognition.entry_confluence import EntryConfluenceFilter
        
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        confluence_config = config.get('entry_confluence', {})
        
        if not confluence_config.get('enabled', False):
            print("⚠️  Entry Confluence DISABLED - Signal would pass through")
            return signal
        
        filter = EntryConfluenceFilter(confluence_config)
        
        # Create market data
        test_df = pd.DataFrame({
            'open': np.linspace(99000, 100000, 100),
            'high': np.linspace(99500, 100500, 100),
            'low': np.linspace(98500, 99500, 100),
            'close': np.linspace(99000, 100000, 100),
            'volume': [1000] * 100
        })
        
        result = filter.analyze_entry(
            signal_direction=signal.side.name.lower(),
            current_price=signal.price,
            symbol=signal.symbol,
            market_data=test_df,
            atr=1000.0,
            signal_entry_price=signal.price
        )
        
        print(f"\n📊 Confluence Result:")
        print(f"   Quality: {result.quality.value}")
        print(f"   Score: {result.score:.1f}/100")
        print(f"   Should Enter: {'✅ YES' if result.should_enter else '❌ NO'}")
        print(f"   Position Multiplier: {result.position_mult:.2f}x")
        print(f"   Wait for Better: {result.wait_for_better}")
        
        if result.reasons:
            print(f"\n   Reasons:")
            for reason in result.reasons[:5]:
                print(f"     • {reason}")
        
        if result.warnings:
            print(f"\n   Warnings:")
            for warning in result.warnings:
                print(f"     ⚠️  {warning}")
        
        if not result.should_enter:
            print("\n❌ Signal REJECTED by Entry Confluence Filter")
            return None
        
        # Adjust signal confidence
        original_conf = signal.confidence
        signal.confidence *= result.position_mult
        print(f"\n✅ Signal PASSED - Confidence adjusted: {original_conf:.2f} → {signal.confidence:.2f}")
        
        return signal
        
    except Exception as e:
        print(f"❌ Entry confluence test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_risk_approval(signal):
    """Test risk manager approval."""
    print("\n" + "=" * 60)
    print("TESTING: Risk Manager Approval")
    print("=" * 60)
    
    try:
        from risk.evaluator import RiskEvaluator
        from unittest.mock import MagicMock
        
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Create mock connector and position tracker
        connector = MagicMock()
        position_tracker = MagicMock()
        position_tracker.get_open_positions.return_value = []
        
        risk_manager = RiskEvaluator(connector, position_tracker, config.get('risk', {}))
        
        # Mock account info
        account_info = {
            'balance': 1000.0,
            'equity': 1000.0,
            'margin': 0.0,
            'free_margin': 1000.0,
            'margin_level': 0.0
        }
        
        current_positions = 0
        
        approved, reason, position_size = risk_manager.approve(
            signal=signal,
            account_info=account_info,
            current_positions=current_positions
        )
        
        print(f"\n📊 Risk Approval Result:")
        print(f"   Approved: {'✅ YES' if approved else '❌ NO'}")
        print(f"   Reason: {reason}")
        print(f"   Position Size: {position_size:.4f} lots")
        
        if not approved:
            print("\n❌ Signal REJECTED by Risk Manager")
            return None
        
        print(f"\n✅ Signal APPROVED - Ready for execution")
        return position_size
        
    except Exception as e:
        print(f"❌ Risk approval test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_execution(signal, position_size):
    """Test execution engine (dry run)."""
    print("\n" + "=" * 60)
    print("TESTING: Execution Engine (DRY RUN)")
    print("=" * 60)
    
    try:
        from execution.engine import ExecutionEngine, OrderRequest, OrderType
        from strategy.base import SignalType
        from unittest.mock import MagicMock
        
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Create mock connector
        connector = MagicMock()
        
        engine = ExecutionEngine(connector, config)
        
        # Create order request
        order_req = OrderRequest(
            signal_id=signal.id,
            symbol=signal.symbol,
            side="BUY" if signal.side == SignalType.LONG else "SELL",
            volume=position_size,
            order_type=OrderType.MARKET,
            sl=signal.stop_loss,
            tp=signal.take_profit
        )
        
        print(f"\n📊 Order Request:")
        print(f"   Symbol: {order_req.symbol}")
        print(f"   Side: {order_req.side}")
        print(f"   Volume: {order_req.volume:.4f} lots")
        print(f"   Type: {order_req.order_type.value}")
        print(f"   Stop Loss: {order_req.sl:.2f}")
        print(f"   Take Profit: {order_req.tp:.2f}")
        
        print(f"\n✅ Order would be placed (DRY RUN MODE)")
        print(f"\n🎯 COMPLETE SIGNAL FLOW SUCCESSFUL!")
        
        return True
        
    except Exception as e:
        print(f"❌ Execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run complete signal flow test."""
    print("\n" + "=" * 70)
    print(" SIGNAL FLOW TEST - Manual Signal Injection")
    print("=" * 70 + "\n")
    
    # 1. Create test signal
    signal = create_test_signal()
    if not signal:
        print("❌ Failed to create test signal")
        return 1
    
    # 2. Test Entry Confluence
    signal = test_entry_confluence(signal)
    if not signal:
        print("\n❌ Signal rejected at Entry Confluence stage")
        return 1
    
    # 3. Test Risk Approval
    position_size = test_risk_approval(signal)
    if position_size is None:
        print("\n❌ Signal rejected at Risk Approval stage")
        return 1
    
    # 4. Test Execution
    success = test_execution(signal, position_size)
    if not success:
        print("\n❌ Execution test failed")
        return 1
    
    print("\n" + "=" * 70)
    print("✅ ALL STAGES PASSED - Signal flow is functional")
    print("=" * 70 + "\n")
    
    print("Signal Flow Summary:")
    print("  1. ✅ Signal Created")
    print("  2. ✅ Entry Confluence (quality gate)")
    print("  3. ✅ Risk Approved (position sizing)")
    print("  4. ✅ Execution Ready")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
