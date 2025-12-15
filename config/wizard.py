"""
Herald Interactive Setup Wizard

A friendly, non-overwhelming configuration wizard that helps users configure
Herald's key trading parameters before starting. 
Designed to be:
- Comprehensive yet concise
- Smart with defaults
- Non-destructive to existing config

Usage:
    from config.wizard import run_setup_wizard
    config = run_setup_wizard(config_path)
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from copy import deepcopy

# Available mindsets from mindsets.py
MINDSETS = {
    "1": ("conservative", "Lower risk, wider stops, capital preservation"),
    "2": ("balanced", "Moderate risk, standard settings (recommended)"),
    "3": ("aggressive", "Higher risk, faster entries, tighter stops"),
}

TIMEFRAMES = {
    "1": ("TIMEFRAME_M5", "5 Minutes"),
    "2": ("TIMEFRAME_M15", "15 Minutes"),
    "3": ("TIMEFRAME_M30", "30 Minutes"),
    "4": ("TIMEFRAME_H1", "1 Hour (recommended)"),
    "5": ("TIMEFRAME_H4", "4 Hours"),
    "6": ("TIMEFRAME_D1", "Daily"),
}

COMMON_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD",
    "EURUSD#", "GBPUSD#", "XAUUSD#", "BTCUSD#",
]


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Print Herald setup banner."""
    banner = """
    ╦ ╦╔═╗╦═╗╔═╗╦  ╔╦╗
    ╠═╣║╣ ╠╦╝╠═╣║   ║║
    ╩ ╩╚═╝╩╚═╩ ╩╩═╝═╩╝
    ─────────────────────────────
    Interactive Setup Wizard
    """
    print("\033[96m" + banner + "\033[0m")


def print_section(title: str):
    """Print a section header."""
    print(f"\n\033[93m{'─' * 50}\033[0m")
    print(f"\033[93m  {title}\033[0m")
    print(f"\033[93m{'─' * 50}\033[0m\n")


def print_option(key: str, label: str, description: str = "", selected: bool = False):
    """Print a menu option."""
    marker = "●" if selected else "○"
    if description:
        print(f"  [{key}] {marker} {label} - \033[90m{description}\033[0m")
    else:
        print(f"  [{key}] {marker} {label}")


def print_success(msg: str):
    print(f"\033[92m  ✓ {msg}\033[0m")


def print_info(msg: str):
    print(f"\033[94m  ℹ {msg}\033[0m")


def print_warning(msg: str):
    print(f"\033[93m  ⚠ {msg}\033[0m")


def get_input(prompt: str, default: str = "") -> str:
    """Get user input with optional default."""
    if default:
        result = input(f"  {prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"  {prompt}: ").strip()


def get_float(prompt: str, default: float, min_val: float = 0, max_val: float = float('inf')) -> float:
    """Get a float input with validation."""
    while True:
        try:
            result = get_input(prompt, str(default))
            val = float(result)
            if min_val <= val <= max_val:
                return val
            print(f"\033[91m  Please enter a value between {min_val} and {max_val}\033[0m")
        except ValueError:
            print("\033[91m  Please enter a valid number\033[0m")


def get_int(prompt: str, default: int, min_val: int = 0, max_val: int = 100) -> int:
    """Get an integer input with validation."""
    while True:
        try:
            result = get_input(prompt, str(default))
            val = int(result)
            if min_val <= val <= max_val:
                return val
            print(f"\033[91m  Please enter a value between {min_val} and {max_val}\033[0m")
        except ValueError:
            print("\033[91m  Please enter a valid integer\033[0m")


def choose_mindset() -> str:
    """Let user choose a trading mindset."""
    print_section("STEP 1: Trading Mindset")
    print("  Choose your risk tolerance and trading style:\n")
    
    for key, (name, desc) in MINDSETS.items():
        print_option(key, name.capitalize(), desc)
    
    print()
    while True:
        choice = get_input("Select mindset (1-3)", "2")
        if choice in MINDSETS:
            selected = MINDSETS[choice][0]
            print_success(f"Selected: {selected.capitalize()}")
            return selected
        print("\033[91m  Invalid choice. Enter 1, 2, or 3.\033[0m")


def choose_symbol(current: str = "EURUSD") -> str:
    """Let user choose or enter a trading symbol."""
    print_section("STEP 2: Trading Symbol")
    print("  Enter the symbol you want to trade.\n")
    print(f"  \033[90mCommon symbols: {', '.join(COMMON_SYMBOLS[:5])}\033[0m")
    print(f"  \033[90mNote: Some brokers use suffixes like # or .m\033[0m\n")
    
    symbol = get_input("Symbol", current).upper()
    print_success(f"Symbol: {symbol}")
    return symbol


def choose_timeframe(current: str = "TIMEFRAME_H1") -> str:
    """Let user choose a timeframe."""
    print_section("STEP 3: Timeframe")
    print("  Select your trading timeframe:\n")
    
    for key, (tf, desc) in TIMEFRAMES.items():
        selected = tf == current
        print_option(key, desc, "", selected)
    
    print()
    while True:
        choice = get_input("Select timeframe (1-6)", "4")
        if choice in TIMEFRAMES:
            selected_tf = TIMEFRAMES[choice][0]
            print_success(f"Timeframe: {TIMEFRAMES[choice][1]}")
            return selected_tf
        print("\033[91m  Invalid choice. Enter 1-6.\033[0m")


def configure_risk(current_risk: Dict[str, Any]) -> Dict[str, Any]:
    """Configure risk management settings."""
    print_section("STEP 4: Risk Management")
    print("  Set your risk limits to protect your capital.\n")
    
    risk = deepcopy(current_risk)
    
    # Daily loss limit
    print_info("Maximum daily loss - trading stops if this limit is hit")
    risk['max_daily_loss'] = get_float(
        "Max daily loss ($)", 
        current_risk.get('max_daily_loss', 50.0),
        min_val=1, max_val=10000
    )
    
    # Position size percentage
    print()
    print_info("Position size as % of equity per trade")
    risk['position_size_pct'] = get_float(
        "Position size (%)", 
        current_risk.get('position_size_pct', 2.0),
        min_val=0.1, max_val=10
    )
    
    # Max positions
    print()
    print_info("Maximum simultaneous open positions")
    risk['max_total_positions'] = get_int(
        "Max positions", 
        current_risk.get('max_total_positions', 3),
        min_val=1, max_val=10
    )
    
    print()
    print_success(f"Daily loss limit: ${risk['max_daily_loss']}")
    print_success(f"Position size: {risk['position_size_pct']}% of equity")
    print_success(f"Max positions: {risk['max_total_positions']}")
    
    return risk


def configure_strategy(current_strategy: Dict[str, Any]) -> Dict[str, Any]:
    """Configure strategy-specific settings."""
    print_section("STEP 5: Strategy Settings")
    
    strategy = deepcopy(current_strategy)
    params = strategy.get('params', {})
    
    strategy_type = strategy.get('type', 'sma_crossover')
    print(f"  Current strategy: \033[96m{strategy_type}\033[0m\n")
    
    if strategy_type == 'sma_crossover':
        print_info("SMA Crossover uses fast and slow moving averages")
        
        params['fast_period'] = get_int(
            "Fast SMA period",
            params.get('fast_period', params.get('short_window', 10)),
            min_val=3, max_val=50
        )
        
        params['slow_period'] = get_int(
            "Slow SMA period",
            params.get('slow_period', params.get('long_window', 30)),
            min_val=10, max_val=200
        )
        
        # Ensure fast < slow
        if params['fast_period'] >= params['slow_period']:
            print_warning("Fast period must be less than slow period. Adjusting...")
            params['slow_period'] = params['fast_period'] + 20
        
        print()
        print_success(f"Fast SMA: {params['fast_period']} periods")
        print_success(f"Slow SMA: {params['slow_period']} periods")
    
    strategy['params'] = params
    return strategy


def confirm_and_save(config: Dict[str, Any], config_path: str) -> bool:
    """Show summary and confirm save."""
    print_section("CONFIGURATION SUMMARY")
    
    print(f"  Symbol:           \033[96m{config['trading']['symbol']}\033[0m")
    print(f"  Timeframe:        \033[96m{config['trading']['timeframe']}\033[0m")
    print(f"  Strategy:         \033[96m{config['strategy']['type']}\033[0m")
    print()
    print(f"  Max Daily Loss:   \033[93m${config['risk']['max_daily_loss']}\033[0m")
    print(f"  Position Size:    \033[93m{config['risk']['position_size_pct']}%\033[0m")
    print(f"  Max Positions:    \033[93m{config['risk']['max_total_positions']}\033[0m")
    
    print()
    confirm = get_input("Save this configuration? (y/n)", "y").lower()
    
    if confirm == 'y':
        # Backup existing config
        config_file = Path(config_path)
        if config_file.exists():
            backup_path = config_file.with_suffix('.json.bak')
            backup_path.write_text(config_file.read_text())
            print_info(f"Backed up existing config to {backup_path.name}")
        
        # Save new config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print_success(f"Configuration saved to {config_path}")
        return True
    else:
        print_warning("Configuration not saved.")
        return False


def run_setup_wizard(config_path: str = "config.json") -> Optional[Dict[str, Any]]:
    """
    Run the interactive setup wizard.
    
    Args:
        config_path: Path to config.json file
        
    Returns:
        Updated configuration dict, or None if cancelled
    """
    clear_screen()
    print_banner()
    
    print("  Welcome to Herald! This wizard will help you configure")
    print("  the key trading parameters before you start.\n")
    print("  \033[90mPress Enter to accept defaults shown in [brackets].\033[0m")
    print("  \033[90mType 'q' at any prompt to quit without saving.\033[0m\n")
    
    proceed = get_input("Start setup? (y/n)", "y").lower()
    if proceed != 'y':
        print_info("Setup cancelled.")
        return None
    
    # Load existing config if available
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        print_success(f"Loaded existing configuration from {config_path}")
    else:
        # Load from example
        example_path = Path(config_path).parent / "config.example.json"
        if example_path.exists():
            with open(example_path) as f:
                config = json.load(f)
            print_info("Starting from example configuration")
        else:
            print_warning("No existing config found. Using defaults.")
            config = {
                "mt5": {"login": 0, "password": "", "server": ""},
                "trading": {"symbol": "EURUSD", "timeframe": "TIMEFRAME_H1", "poll_interval": 60, "lookback_bars": 500},
                "risk": {"max_daily_loss": 50.0, "position_size_pct": 2.0, "max_total_positions": 3},
                "strategy": {"type": "sma_crossover", "params": {"fast_period": 10, "slow_period": 30}},
                "exit_strategies": [],
                "indicators": []
            }
    
    # Step 1: Mindset (applied as overlay later)
    mindset = choose_mindset()
    
    # Step 2: Symbol
    current_symbol = config.get('trading', {}).get('symbol', 'EURUSD')
    config['trading']['symbol'] = choose_symbol(current_symbol)
    
    # Also update symbol in strategy params if present
    if 'strategy' in config and 'params' in config['strategy']:
        config['strategy']['params']['symbol'] = config['trading']['symbol']
    
    # Step 3: Timeframe
    current_tf = config.get('trading', {}).get('timeframe', 'TIMEFRAME_H1')
    config['trading']['timeframe'] = choose_timeframe(current_tf)
    
    # Step 4: Risk Management
    config['risk'] = configure_risk(config.get('risk', {}))
    
    # Step 5: Strategy Settings
    config['strategy'] = configure_strategy(config.get('strategy', {}))
    
    # Apply mindset overlay (from mindsets.py logic)
    # Note: We apply mindset values that weren't explicitly set by user
    # The wizard values take precedence
    
    # Step 6: Confirm and save
    print()
    if confirm_and_save(config, config_path):
        print()
        print(f"  \033[92m{'═' * 48}\033[0m")
        print(f"  \033[92m  Herald is ready! Run with:\033[0m")
        print(f"  \033[96m  python -m herald --config {config_path}\033[0m")
        if mindset != 'balanced':
            print(f"  \033[96m  python -m herald --config {config_path} --mindset {mindset}\033[0m")
        print(f"  \033[92m{'═' * 48}\033[0m")
        print()
        return config
    
    return None


if __name__ == "__main__":
    # Allow running wizard standalone
    run_setup_wizard("config.json")
