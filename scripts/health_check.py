#!/usr/bin/env python3
"""
Health Check Script - Run before deployment
Verifies all critical components are present and functional.
"""
import sys
import os
import json
from pathlib import Path


def check_critical_files():
    """Check critical files exist."""
    critical_files = [
        'cognition/entry_confluence.py',  # THE SECRET SAUCE
        'risk/dynamic_sltp.py',
        'position/trade_manager.py',
        'strategy/sma_crossover.py',
        'strategy/ema_crossover.py',
        'strategy/strategy_selector.py',
        'core/bootstrap.py',
        'core/trading_loop.py',
        'config.json'
    ]
    
    missing = []
    for file in critical_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print(f"❌ CRITICAL FILES MISSING: {missing}")
        return False
    
    print("✅ All critical files present")
    return True


def check_config():
    """Check config has required sections."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        required_sections = [
            'entry_confluence',
            'orphan_trades',
            'strategy',
            'risk',
            'trading'
        ]
        
        missing = []
        for section in required_sections:
            if section not in config:
                missing.append(section)
        
        if missing:
            print(f"❌ CONFIG SECTIONS MISSING: {missing}")
            return False
        
        # Check entry confluence enabled
        if not config['entry_confluence'].get('enabled', False):
            print("⚠️  WARNING: Entry Confluence Filter is DISABLED")
        
        # Check adoption enabled
        if not config['orphan_trades'].get('enabled', False):
            print("⚠️  WARNING: Trade Adoption is DISABLED")
        
        # Check all 7 strategies
        strategies = config.get('strategy', {}).get('strategies', [])
        if len(strategies) < 7:
            print(f"⚠️  WARNING: Only {len(strategies)} strategies configured (expected 7)")
        
        print("✅ Config validated")
        return True
        
    except Exception as e:
        print(f"❌ Config validation failed: {e}")
        return False


def check_imports():
    """Check critical imports work."""
    try:
        import sys
        import os
        # Add parent directory to path for imports
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Core imports
        from core.bootstrap import CthuluBootstrap, SystemComponents
        from core.trading_loop import TradingLoop, TradingLoopContext
        
        # Critical components
        from cognition.entry_confluence import EntryConfluenceFilter, EntryQuality
        from risk.dynamic_sltp import DynamicSLTPManager
        from position.trade_manager import TradeManager
        
        # Strategies
        from strategy.sma_crossover import SmaCrossover
        from strategy.ema_crossover import EmaCrossover
        from strategy.strategy_selector import StrategySelector
        
        print("✅ All critical imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_git_status():
    """Check for uncommitted changes to critical files."""
    try:
        import subprocess
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        
        critical_patterns = ['entry_confluence', 'dynamic_sltp', 'trade_manager', 'adoption']
        
        modified = []
        for line in result.stdout.split('\n'):
            if any(pattern in line for pattern in critical_patterns):
                modified.append(line.strip())
        
        if modified:
            print(f"⚠️  Uncommitted changes to critical files:")
            for m in modified:
                print(f"   {m}")
        else:
            print("✅ No uncommitted critical changes")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Could not check git status: {e}")
        return True  # Don't fail on this


def main():
    """Run all health checks."""
    print("=" * 60)
    print("CTHULU HEALTH CHECK")
    print("=" * 60)
    print()
    
    checks = [
        ("Critical Files", check_critical_files),
        ("Configuration", check_config),
        ("Imports", check_imports),
        ("Git Status", check_git_status)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"Checking {name}...")
        result = check_func()
        results.append(result)
        print()
    
    print("=" * 60)
    if all(results):
        print("✅ ALL CHECKS PASSED - SYSTEM HEALTHY")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME CHECKS FAILED - DO NOT DEPLOY")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
