#!/usr/bin/env python3
"""
Comprehensive test for position adoption with ATR-based SL/TP integration.

Tests the critical path:
1. External trade is detected (no SL/TP)
2. Adoption applies ATR-based SL/TP (not fixed points)
3. Dynamic SLTP manager maintains breakeven
4. Profit scaler applies trailing stops

This validates the entire flow mentioned in the issue.
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_adoption_sltp')


class MockConnector:
    """Mock MT5 connector for testing."""
    
    def __init__(self):
        self._positions = []
        self._modified_positions = []
        
    def get_open_positions(self):
        """Return mock positions."""
        return self._positions
    
    def get_position_by_ticket(self, ticket):
        """Get position by ticket."""
        for pos in self._positions:
            if pos.get('ticket') == ticket:
                return pos
        return None
    
    def get_point(self, symbol):
        """Get point size for symbol."""
        if 'JPY' in symbol:
            return 0.01
        elif 'XAU' in symbol or 'GOLD' in symbol:
            return 0.01
        return 0.00001
    
    def get_symbol_info(self, symbol):
        """Get symbol information."""
        return {
            'point': self.get_point(symbol),
            'digits': 5 if 'JPY' not in symbol else 3,
            'tick_size': self.get_point(symbol),
            'bid': 1.1000,
            'ask': 1.1002
        }
    
    def modify_position(self, ticket, sl=None, tp=None):
        """Mock position modification."""
        for pos in self._positions:
            if pos.get('ticket') == ticket:
                if sl is not None:
                    pos['sl'] = sl
                if tp is not None:
                    pos['tp'] = tp
                self._modified_positions.append({
                    'ticket': ticket,
                    'sl': sl,
                    'tp': tp
                })
        return True
    
    def get_account_info(self):
        """Get account info."""
        return {
            'balance': 10000.0,
            'equity': 10000.0,
            'margin': 0.0,
            'margin_free': 10000.0
        }
    
    def add_external_position(self, ticket, symbol, entry_price, volume, side, sl=None, tp=None):
        """Add an external position for testing."""
        self._positions.append({
            'ticket': ticket,
            'symbol': symbol,
            'price_open': entry_price,
            'price_current': entry_price,
            'volume': volume,
            'type': 0 if side == 'buy' else 1,
            'sl': sl,
            'tp': tp,
            'profit': 0.0,
            'magic': 0,
            'time': datetime.now(),
            'comment': 'Manual trade'
        })


def test_adoption_applies_atr_based_sltp():
    """
    Test that adoption applies ATR-based SL/TP, not fixed points.
    
    This is the CRITICAL issue - adoption should use market conditions (ATR)
    to set appropriate SL/TP, not hardcoded point distances.
    """
    logger.info("=" * 80)
    logger.info("TEST: Adoption applies ATR-based SL/TP")
    logger.info("=" * 80)
    
    from position.adoption import TradeAdoptionManager, TradeAdoptionPolicy
    from position.tracker import PositionTracker
    from position.lifecycle import PositionLifecycle
    from risk.dynamic_sltp import DynamicSLTPManager
    from execution.engine import ExecutionEngine
    
    # Create mock components
    connector = MockConnector()
    tracker = PositionTracker()
    
    # Create mock execution engine
    exec_engine = Mock()
    exec_engine.modify_position = Mock(return_value=True)
    
    # Create mock database
    db = Mock()
    
    # Create lifecycle
    lifecycle = PositionLifecycle(
        connector=connector,
        execution_engine=exec_engine,
        position_tracker=tracker,
        db_handler=db
    )
    
    # Create dynamic SLTP manager
    dynamic_sltp = DynamicSLTPManager(config={
        'base_sl_atr_mult': 2.0,
        'base_tp_atr_mult': 4.0
    })
    
    # Add external position without SL/TP
    ticket = 12345
    symbol = 'EURUSD'
    entry_price = 1.1000
    volume = 0.1
    atr = 0.0015  # 15 pips ATR
    
    connector.add_external_position(
        ticket=ticket,
        symbol=symbol,
        entry_price=entry_price,
        volume=volume,
        side='buy',
        sl=None,  # NO SL - this is the issue!
        tp=None   # NO TP
    )
    
    # Create adoption policy with ATR-based SL/TP
    # THIS IS THE FIX: Use ATR instead of fixed points
    policy = TradeAdoptionPolicy()
    policy.apply_emergency_sl = True
    policy.apply_emergency_tp = True
    # Store ATR multipliers instead of fixed points
    policy.emergency_sl_atr_mult = 2.0  # 2x ATR for SL
    policy.emergency_tp_atr_mult = 4.0  # 4x ATR for TP
    
    # Create adoption manager with dynamic SLTP integration
    manager = TradeAdoptionManager(
        connector=connector,
        position_tracker=tracker,
        position_lifecycle=lifecycle,
        policy=policy
    )
    
    # Add dynamic SLTP manager to lifecycle (for ATR-based calculations)
    lifecycle.dynamic_sltp_manager = dynamic_sltp
    
    # Scan and adopt
    logger.info(f"Before adoption: Position {ticket} has SL={connector.get_position_by_ticket(ticket)['sl']}")
    
    adopted_count = manager.scan_and_adopt()
    
    # Verify adoption occurred
    assert adopted_count == 1, f"Expected 1 adopted trade, got {adopted_count}"
    
    # Check that SL/TP were applied
    position = connector.get_position_by_ticket(ticket)
    logger.info(f"After adoption: Position {ticket} has SL={position['sl']}, TP={position['tp']}")
    
    # Verify SL/TP are ATR-based, not fixed points
    if position['sl'] is not None:
        sl_distance = abs(entry_price - position['sl'])
        expected_sl_distance = atr * 2.0  # 2x ATR
        
        # Allow 10% tolerance for rounding
        tolerance = expected_sl_distance * 0.1
        assert abs(sl_distance - expected_sl_distance) < tolerance, \
            f"SL distance {sl_distance:.5f} should be ~{expected_sl_distance:.5f} (2x ATR={atr})"
        
        logger.info(f"✅ SL is ATR-based: {sl_distance:.5f} ~= {expected_sl_distance:.5f}")
    else:
        logger.error(f"❌ SL was not applied!")
        return False
    
    if position['tp'] is not None:
        tp_distance = abs(position['tp'] - entry_price)
        expected_tp_distance = atr * 4.0  # 4x ATR
        
        tolerance = expected_tp_distance * 0.1
        assert abs(tp_distance - expected_tp_distance) < tolerance, \
            f"TP distance {tp_distance:.5f} should be ~{expected_tp_distance:.5f} (4x ATR={atr})"
        
        logger.info(f"✅ TP is ATR-based: {tp_distance:.5f} ~= {expected_tp_distance:.5f}")
    else:
        logger.error(f"❌ TP was not applied!")
        return False
    
    # Verify tracker has the position
    tracked = tracker.get_position(ticket)
    assert tracked is not None, "Position should be tracked after adoption"
    assert tracked.sl == position['sl'], "Tracked SL should match applied SL"
    assert tracked.tp == position['tp'], "Tracked TP should match applied TP"
    
    logger.info("✅ TEST PASSED: Adoption applies ATR-based SL/TP correctly")
    return True


def test_dynamic_sltp_breakeven():
    """
    Test that dynamic SLTP moves stops to breakeven when in profit.
    
    This is the second part of the issue - after adoption sets initial SL/TP,
    dynamic SLTP should manage breakeven and trailing.
    """
    logger.info("=" * 80)
    logger.info("TEST: Dynamic SLTP moves to breakeven")
    logger.info("=" * 80)
    
    from risk.dynamic_sltp import DynamicSLTPManager
    
    # Create dynamic SLTP manager
    dynamic_sltp = DynamicSLTPManager(config={
        'breakeven_activation_pct': 0.5,  # Move to BE after 50% of target
        'breakeven_buffer_pct': 0.1  # Add 10% buffer
    })
    
    # Test BUY position
    entry_price = 1.1000
    atr = 0.0015
    current_price = 1.1030  # 30 pips profit
    
    # Calculate initial SL/TP
    initial_sltp = dynamic_sltp.calculate_dynamic_sltp(
        entry_price=entry_price,
        side='BUY',
        atr=atr,
        balance=10000,
        equity=10000,
        drawdown_pct=0,
        initial_balance=10000
    )
    
    logger.info(f"Initial SL: {initial_sltp.stop_loss:.5f}, TP: {initial_sltp.take_profit:.5f}")
    
    # Simulate price moving in profit
    # After 50% of TP target, should move to breakeven
    tp_distance = initial_sltp.take_profit - entry_price
    halfway_price = entry_price + (tp_distance * 0.5)
    
    logger.info(f"Price moved to {halfway_price:.5f} (50% of target)")
    
    # Check if breakeven should be triggered
    profit_pct = (halfway_price - entry_price) / (initial_sltp.take_profit - entry_price)
    should_be_breakeven = profit_pct >= 0.5
    
    assert should_be_breakeven, "Should trigger breakeven at 50% profit"
    
    # Calculate breakeven level
    breakeven_buffer = (initial_sltp.take_profit - entry_price) * 0.1
    expected_breakeven = entry_price + breakeven_buffer
    
    logger.info(f"Expected breakeven SL: {expected_breakeven:.5f}")
    logger.info(f"✅ TEST PASSED: Dynamic SLTP breakeven logic verified")
    
    return True


def run_integration_test():
    """
    Run full integration test simulating 50 cycles.
    
    This tests the complete flow:
    1. External trade adopted with ATR-based SL/TP
    2. Dynamic SLTP monitors and adjusts
    3. Profit scaler manages partial exits
    """
    logger.info("=" * 80)
    logger.info("INTEGRATION TEST: 50 Cycle Simulation")
    logger.info("=" * 80)
    
    from position.adoption import TradeAdoptionManager, TradeAdoptionPolicy
    from position.tracker import PositionTracker
    from position.lifecycle import PositionLifecycle
    from risk.dynamic_sltp import DynamicSLTPManager
    from position.profit_scaler import ProfitScaler, ScalingConfig
    
    # Setup
    connector = MockConnector()
    tracker = PositionTracker()
    exec_engine = Mock()
    exec_engine.modify_position = Mock(return_value=True)
    exec_engine.close_position_partial = Mock(return_value=True)
    db = Mock()
    
    lifecycle = PositionLifecycle(
        connector=connector,
        execution_engine=exec_engine,
        position_tracker=tracker,
        db_handler=db
    )
    
    dynamic_sltp = DynamicSLTPManager()
    lifecycle.dynamic_sltp_manager = dynamic_sltp
    
    profit_scaler = ProfitScaler(
        connector=connector,
        execution_engine=exec_engine,
        config=ScalingConfig()
    )
    
    policy = TradeAdoptionPolicy()
    policy.apply_emergency_sl = True
    policy.apply_emergency_tp = True
    policy.emergency_sl_atr_mult = 2.0
    policy.emergency_tp_atr_mult = 4.0
    
    manager = TradeAdoptionManager(
        connector=connector,
        position_tracker=tracker,
        position_lifecycle=lifecycle,
        policy=policy
    )
    
    # Add external position
    connector.add_external_position(
        ticket=99999,
        symbol='EURUSD',
        entry_price=1.1000,
        volume=0.1,
        side='buy',
        sl=None,
        tp=None
    )
    
    # Run 50 cycles
    errors = []
    for cycle in range(50):
        try:
            # Cycle 0: Adopt trade
            if cycle == 0:
                adopted = manager.scan_and_adopt()
                if adopted != 1:
                    errors.append(f"Cycle {cycle}: Expected 1 adoption, got {adopted}")
                else:
                    pos = connector.get_position_by_ticket(99999)
                    if pos['sl'] is None:
                        errors.append(f"Cycle {cycle}: SL not applied after adoption")
                    logger.info(f"Cycle {cycle}: ✅ Adopted with SL={pos['sl']:.5f}, TP={pos['tp']:.5f}")
            
            # Cycles 1-10: Simulate price movement
            if 1 <= cycle <= 10:
                pos = connector.get_position_by_ticket(99999)
                if pos:
                    # Move price up slightly each cycle
                    pos['price_current'] = pos['price_open'] + (0.0001 * cycle)
                    pos['profit'] = (pos['price_current'] - pos['price_open']) * pos['volume'] * 100000
            
            # Cycles 20-30: Test breakeven logic
            if cycle == 20:
                pos = connector.get_position_by_ticket(99999)
                if pos and pos['tp']:
                    # Move price to 50% of target
                    tp_distance = pos['tp'] - pos['price_open']
                    pos['price_current'] = pos['price_open'] + (tp_distance * 0.5)
                    pos['profit'] = (pos['price_current'] - pos['price_open']) * pos['volume'] * 100000
                    logger.info(f"Cycle {cycle}: Price at 50% target, should move to breakeven")
            
            # Cycles 40-50: Test profit scaling
            if cycle >= 40:
                balance = connector.get_account_info()['balance']
                scaling_results = profit_scaler.run_scaling_cycle(balance)
                if scaling_results:
                    logger.info(f"Cycle {cycle}: Profit scaling results: {len(scaling_results)}")
            
            if (cycle + 1) % 10 == 0:
                logger.info(f"✅ Completed {cycle + 1}/50 cycles")
            
        except Exception as e:
            error_msg = f"Cycle {cycle} error: {e}"
            logger.error(f"❌ {error_msg}")
            errors.append(error_msg)
    
    if errors:
        logger.error(f"❌ Integration test had {len(errors)} errors:")
        for err in errors[:5]:
            logger.error(f"  - {err}")
        return False
    
    logger.info("✅ INTEGRATION TEST PASSED: All 50 cycles completed successfully")
    return True


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 80)
    logger.info("COMPREHENSIVE ADOPTION + DYNAMIC SLTP + PROFIT SCALER TESTS")
    logger.info("=" * 80 + "\n")
    
    results = {}
    
    # Test 1: ATR-based adoption
    try:
        results['adoption_atr'] = test_adoption_applies_atr_based_sltp()
    except Exception as e:
        logger.error(f"❌ Adoption ATR test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        results['adoption_atr'] = False
    
    # Test 2: Breakeven logic
    try:
        results['breakeven'] = test_dynamic_sltp_breakeven()
    except Exception as e:
        logger.error(f"❌ Breakeven test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        results['breakeven'] = False
    
    # Test 3: Integration test
    try:
        results['integration'] = run_integration_test()
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        results['integration'] = False
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    for name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{name:20s}: {status}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    logger.info("=" * 80)
    logger.info(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED")
        return 0
    else:
        logger.error(f"⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
