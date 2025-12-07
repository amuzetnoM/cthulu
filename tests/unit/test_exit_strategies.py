"""
Unit tests for Phase 2 exit strategy system.
Tests all 4 exit strategies: StopLoss, TakeProfit, TrailingStop, TimeBased.
"""

import unittest
from datetime import datetime, timedelta
from decimal import Decimal


class TestExitDecision(unittest.TestCase):
    """Test ExitDecision dataclass."""
    
    def test_exit_decision_import(self):
        """Test that ExitDecision can be imported."""
        try:
            from herald.exit.exit_manager import ExitDecision
            self.assertTrue(True)
        except ImportError:
            self.fail("Could not import ExitDecision from exit.exit_manager")
    
    def test_exit_decision_creation(self):
        """Test creating an ExitDecision instance."""
        from herald.exit.exit_manager import ExitDecision
        
        decision = ExitDecision(
            should_exit=True,
            strategy_name="StopLossExit",
            reason="Stop loss triggered at 1.0950",
            priority=1,
            exit_price=1.0950
        )
        
        self.assertTrue(decision.should_exit)
        self.assertEqual(decision.strategy_name, "StopLossExit")
        self.assertEqual(decision.priority, 1)


class TestStopLossExit(unittest.TestCase):
    """Test StopLossExit strategy."""
    
    def test_stop_loss_import(self):
        """Test that StopLossExit can be imported."""
        try:
            from herald.exit.stop_loss import StopLossExit
            self.assertTrue(True)
        except ImportError:
            self.fail("Could not import StopLossExit from exit.stop_loss")
    
    def test_stop_loss_initialization(self):
        """Test StopLossExit initialization."""
        from herald.exit.stop_loss import StopLossExit
        
        strategy = StopLossExit(stop_loss_pct=0.02)
        
        self.assertEqual(strategy.priority, 1)
        self.assertEqual(strategy.stop_loss_pct, 0.02)
    
    def test_stop_loss_triggered(self):
        """Test stop loss triggering on losing position."""
        from herald.exit.stop_loss import StopLossExit
        from herald.position.manager import PositionInfo
        
        strategy = StopLossExit(stop_loss_pct=0.02)
        
        # Buy position that has lost more than 2%
        position = PositionInfo(
            ticket=12345,
            symbol="EURUSD",
            volume=1.0,
            open_price=1.1000,
            current_price=1.0750,  # 2.27% loss
            open_time=datetime.now(),
            side="BUY",
            stop_loss=1.0780
        )
        
        decision = strategy.should_exit(position)
        
        self.assertTrue(decision.should_exit)
        self.assertEqual(decision.priority, 1)
        self.assertIn("stop loss", decision.reason.lower())
    
    def test_stop_loss_not_triggered(self):
        """Test stop loss not triggering on profitable position."""
        from herald.exit.stop_loss import StopLossExit
        from herald.position.manager import PositionInfo
        
        strategy = StopLossExit(stop_loss_pct=0.02)
        
        # Buy position with profit
        position = PositionInfo(
            ticket=12345,
            symbol="EURUSD",
            volume=1.0,
            open_price=1.1000,
            current_price=1.1050,  # Profit
            open_time=datetime.now(),
            side="BUY",
            stop_loss=1.0780
        )
        
        decision = strategy.should_exit(position)
        
        self.assertFalse(decision.should_exit)


class TestTakeProfitExit(unittest.TestCase):
    """Test TakeProfitExit strategy."""
    
    def test_take_profit_import(self):
        """Test that TakeProfitExit can be imported."""
        try:
            from herald.exit.take_profit import TakeProfitExit
            self.assertTrue(True)
        except ImportError:
            self.fail("Could not import TakeProfitExit from exit.take_profit")
    
    def test_take_profit_initialization(self):
        """Test TakeProfitExit initialization."""
        from herald.exit.take_profit import TakeProfitExit
        
        strategy = TakeProfitExit(take_profit_pct=0.03)
        
        self.assertEqual(strategy.priority, 2)
        self.assertEqual(strategy.take_profit_pct, 0.03)
    
    def test_take_profit_triggered(self):
        """Test take profit triggering on winning position."""
        from herald.exit.take_profit import TakeProfitExit
        from herald.position.manager import PositionInfo
        
        strategy = TakeProfitExit(take_profit_pct=0.03)
        
        # Buy position with >3% profit
        position = PositionInfo(
            ticket=12345,
            symbol="EURUSD",
            volume=1.0,
            open_price=1.1000,
            current_price=1.1350,  # 3.18% profit
            open_time=datetime.now(),
            side="BUY",
            take_profit=1.1330
        )
        
        decision = strategy.should_exit(position)
        
        self.assertTrue(decision.should_exit)
        self.assertEqual(decision.priority, 2)
        self.assertIn("take profit", decision.reason.lower())
    
    def test_take_profit_not_triggered(self):
        """Test take profit not triggering when target not reached."""
        from herald.exit.take_profit import TakeProfitExit
        from herald.position.manager import PositionInfo
        
        strategy = TakeProfitExit(take_profit_pct=0.03)
        
        # Buy position with small profit
        position = PositionInfo(
            ticket=12345,
            symbol="EURUSD",
            volume=1.0,
            open_price=1.1000,
            current_price=1.1020,  # Only 0.18% profit
            open_time=datetime.now(),
            side="BUY",
            take_profit=1.1330
        )
        
        decision = strategy.should_exit(position)
        
        self.assertFalse(decision.should_exit)


class TestTrailingStopExit(unittest.TestCase):
    """Test TrailingStopExit strategy."""
    
    def test_trailing_stop_import(self):
        """Test that TrailingStopExit can be imported."""
        try:
            from herald.exit.trailing_stop import TrailingStopExit
            self.assertTrue(True)
        except ImportError:
            self.fail("Could not import TrailingStopExit from exit.trailing_stop")
    
    def test_trailing_stop_initialization(self):
        """Test TrailingStopExit initialization."""
        from herald.exit.trailing_stop import TrailingStopExit
        
        strategy = TrailingStopExit(trail_distance=0.015)
        
        self.assertEqual(strategy.priority, 3)
        self.assertEqual(strategy.trail_distance, 0.015)
    
    def test_trailing_stop_adjustment(self):
        """Test trailing stop adjusts as price moves favorably."""
        from herald.exit.trailing_stop import TrailingStopExit
        from herald.position.manager import PositionInfo
        
        strategy = TrailingStopExit(trail_distance=0.015)
        
        # Buy position that has moved in profit
        position = PositionInfo(
            ticket=12345,
            symbol="EURUSD",
            volume=1.0,
            open_price=1.1000,
            current_price=1.1200,
            open_time=datetime.now(),
            side="BUY",
            stop_loss=1.0850
        )
        
        # Trailing stop should update
        new_stop = strategy.calculate_trailing_stop(position)
        
        # New stop should be higher than original stop
        self.assertGreater(new_stop, position.stop_loss)


class TestTimeBasedExit(unittest.TestCase):
    """Test TimeBasedExit strategy."""
    
    def test_time_based_import(self):
        """Test that TimeBasedExit can be imported."""
        try:
            from herald.exit.time_based import TimeBasedExit
            self.assertTrue(True)
        except ImportError:
            self.fail("Could not import TimeBasedExit from exit.time_based")
    
    def test_time_based_initialization(self):
        """Test TimeBasedExit initialization."""
        from herald.exit.time_based import TimeBasedExit
        
        strategy = TimeBasedExit(max_hold_hours=24)
        
        self.assertEqual(strategy.priority, 4)
        self.assertEqual(strategy.max_hold_hours, 24)
    
    def test_time_based_triggered(self):
        """Test time-based exit triggering after hold period."""
        from herald.exit.time_based import TimeBasedExit
        from herald.position.manager import PositionInfo
        
        strategy = TimeBasedExit(max_hold_hours=24)
        
        # Position opened 25 hours ago
        position = PositionInfo(
            ticket=12345,
            symbol="EURUSD",
            volume=1.0,
            open_price=1.1000,
            current_price=1.1050,
            open_time=datetime.now() - timedelta(hours=25),
            side="BUY"
        )
        
        decision = strategy.should_exit(position)
        
        self.assertTrue(decision.should_exit)
        self.assertEqual(decision.priority, 4)
        self.assertIn("time", decision.reason.lower())
    
    def test_time_based_not_triggered(self):
        """Test time-based exit not triggering before hold period."""
        from herald.exit.time_based import TimeBasedExit
        from herald.position.manager import PositionInfo
        
        strategy = TimeBasedExit(max_hold_hours=24)
        
        # Position opened 1 hour ago
        position = PositionInfo(
            ticket=12345,
            symbol="EURUSD",
            volume=1.0,
            open_price=1.1000,
            current_price=1.1050,
            open_time=datetime.now() - timedelta(hours=1),
            side="BUY"
        )
        
        decision = strategy.should_exit(position)
        
        self.assertFalse(decision.should_exit)


class TestExitStrategyManager(unittest.TestCase):
    """Test ExitStrategyManager coordinating multiple strategies."""
    
    def test_exit_manager_import(self):
        """Test that ExitStrategyManager can be imported."""
        try:
            from herald.exit.exit_manager import ExitStrategyManager
            self.assertTrue(True)
        except ImportError:
            self.fail("Could not import ExitStrategyManager from exit.exit_manager")
    
    def test_exit_manager_initialization(self):
        """Test ExitStrategyManager initialization."""
        from herald.exit.exit_manager import ExitStrategyManager
        
        manager = ExitStrategyManager()
        
        self.assertIsNotNone(manager)
    
    def test_exit_manager_register_strategy(self):
        """Test registering exit strategies."""
        from herald.exit.exit_manager import ExitStrategyManager
        from herald.exit.stop_loss import StopLossExit
        from herald.exit.take_profit import TakeProfitExit
        
        manager = ExitStrategyManager()
        
        manager.register(StopLossExit(stop_loss_pct=0.02))
        manager.register(TakeProfitExit(take_profit_pct=0.03))
        
        self.assertEqual(len(manager.strategies), 2)
    
    def test_exit_manager_priority_order(self):
        """Test that exit decisions are evaluated in priority order."""
        from herald.exit.exit_manager import ExitStrategyManager
        from herald.exit.stop_loss import StopLossExit
        from herald.exit.take_profit import TakeProfitExit
        from herald.position.manager import PositionInfo
        
        manager = ExitStrategyManager()
        manager.register(TakeProfitExit(take_profit_pct=0.03))  # Priority 2
        manager.register(StopLossExit(stop_loss_pct=0.02))      # Priority 1
        
        # Position that triggers stop loss
        position = PositionInfo(
            ticket=12345,
            symbol="EURUSD",
            volume=1.0,
            open_price=1.1000,
            current_price=1.0750,  # Loss
            open_time=datetime.now(),
            side="BUY",
            stop_loss=1.0780
        )
        
        decision = manager.evaluate_exit(position)
        
        # Should return stop loss decision (priority 1)
        self.assertTrue(decision.should_exit)
        self.assertEqual(decision.priority, 1)


if __name__ == '__main__':
    unittest.main()
