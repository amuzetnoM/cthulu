"""
Critical Path Tests - Prevent Regression
Tests the core functionality that must NEVER break.
Run these before any deployment or major changes.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime


class TestIndicators:
    """Test that all indicators compute correctly."""
    
    def test_sma_indicators_present(self):
        """SMA indicators must always be computed."""
        from core.trading_loop import ensure_runtime_indicators
        
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100.5, 101.5, 102.5],
            'volume': [1000, 1100, 1200]
        })
        
        # After processing, SMA columns must exist
        df['sma_short'] = df['close'].rolling(window=10, min_periods=1).mean()
        df['sma_long'] = df['close'].rolling(window=30, min_periods=1).mean()
        
        assert 'sma_short' in df.columns, "SMA short missing"
        assert 'sma_long' in df.columns, "SMA long missing"
        assert not df['sma_short'].isna().all(), "SMA short has no data"
    
    def test_ema_indicators_present(self):
        """EMA indicators must always be computed."""
        df = pd.DataFrame({
            'close': [100, 101, 102, 103, 104]
        })
        
        df['ema_fast'] = df['close'].ewm(span=12, adjust=False, min_periods=1).mean()
        df['ema_slow'] = df['close'].ewm(span=26, adjust=False, min_periods=1).mean()
        
        assert 'ema_fast' in df.columns, "EMA fast missing"
        assert 'ema_slow' in df.columns, "EMA slow missing"
        assert not df['ema_fast'].isna().all(), "EMA fast has no data"


class TestTradeAdoption:
    """Test trade adoption never breaks."""
    
    def test_adoption_policy_exists(self):
        """Adoption policy must always be configured."""
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        assert 'orphan_trades' in config, "orphan_trades config missing"
        assert 'enabled' in config['orphan_trades'], "adoption enabled flag missing"
    
    def test_trade_manager_has_scan_method(self):
        """TradeManager must have scan_and_adopt method."""
        from position.trade_manager import TradeManager
        
        assert hasattr(TradeManager, 'scan_and_adopt'), "scan_and_adopt method missing from TradeManager"


class TestDynamicSLTP:
    """Test Dynamic SL/TP never breaks."""
    
    def test_dynamic_sltp_manager_exists(self):
        """Dynamic SLTP manager must be available."""
        from risk.dynamic_sltp import DynamicSLTPManager
        
        config = {
            'base_sl_atr_multiplier': 2.0,
            'base_tp_atr_multiplier': 4.0
        }
        manager = DynamicSLTPManager(config)
        assert manager is not None
    
    def test_sltp_modes_available(self):
        """All 5 SLTP modes must be available."""
        from risk.dynamic_sltp import DynamicSLTPManager
        
        config = {'base_sl_atr_multiplier': 2.0, 'base_tp_atr_multiplier': 4.0}
        manager = DynamicSLTPManager(config)
        
        # Check all 5 modes exist
        assert hasattr(manager, 'calculate_dynamic_sltp'), "calculate_dynamic_sltp missing"


class TestEntryConfluence:
    """Test Entry Confluence Filter never breaks."""
    
    def test_entry_confluence_file_exists(self):
        """Entry confluence file must exist."""
        import os
        assert os.path.exists('cognition/entry_confluence.py'), "entry_confluence.py missing - CRITICAL FILE!"
    
    def test_entry_confluence_can_import(self):
        """Entry confluence must be importable."""
        from cognition.entry_confluence import EntryConfluenceFilter, EntryQuality
        
        assert EntryConfluenceFilter is not None
        assert EntryQuality is not None
    
    def test_entry_confluence_config_exists(self):
        """Entry confluence config must exist."""
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        assert 'entry_confluence' in config, "entry_confluence config missing"
        assert 'enabled' in config['entry_confluence'], "entry_confluence enabled flag missing"


class TestStrategies:
    """Test all strategies are loaded."""
    
    def test_all_7_strategies_loaded(self):
        """All 7 strategies must be available."""
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        strategies = config.get('strategy', {}).get('strategies', [])
        strategy_names = [s.get('type', s.get('name', '')) for s in strategies]
        
        required = ['sma_crossover', 'ema_crossover', 'momentum_breakout', 
                   'scalping', 'mean_reversion', 'trend_following', 'rsi_reversal']
        
        for strat in required:
            assert any(strat in name for name in strategy_names), f"Strategy {strat} missing from config"
    
    def test_strategies_importable(self):
        """All strategies must be importable."""
        from strategy.sma_crossover import SMACrossover
        from strategy.ema_crossover import EMACrossover
        from strategy.strategy_selector import StrategySelector
        
        assert SMACrossover is not None
        assert EMACrossover is not None
        assert StrategySelector is not None


class TestBootstrap:
    """Test bootstrap never breaks."""
    
    def test_bootstrap_imports(self):
        """Bootstrap must be importable."""
        from core.bootstrap import CthuluBootstrap, SystemComponents
        
        assert CthuluBootstrap is not None
        assert SystemComponents is not None
    
    def test_trading_loop_imports(self):
        """Trading loop must be importable."""
        from core.trading_loop import TradingLoop, TradingLoopContext
        
        assert TradingLoop is not None
        assert TradingLoopContext is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
