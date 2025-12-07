"""
Trading Mindsets / Risk Profiles

Provides preset configurations for different trading styles:
- AGGRESSIVE: Higher risk, faster entries, tighter stops
- BALANCED: Default moderate risk/reward settings  
- CONSERVATIVE: Lower risk, wider stops, stricter filters

Usage:
    from herald.config.mindsets import MINDSETS, apply_mindset
    
    # Apply a mindset to your config
    config = apply_mindset(base_config, "balanced")
    
    # Or use CLI: python -m herald --mindset balanced
"""

from typing import Dict, Any
from copy import deepcopy


# Aggressive profile: higher risk tolerance, faster signals
AGGRESSIVE = {
    "name": "aggressive",
    "description": "Higher risk, faster entries, tighter stops. For experienced traders.",
    
    "risk": {
        "max_position_size": 1.0,         # Up to 1 lot per position
        "default_position_size": 0.05,    # Default 0.05 lots
        "position_size_pct": 5.0,         # 5% of equity per trade
        "max_daily_loss": 100.0,          # $100 daily loss limit
        "max_positions_per_symbol": 2,    # Allow 2 positions per symbol
        "max_total_positions": 5,         # Allow up to 5 total positions
        "use_kelly_sizing": True,         # Use Kelly criterion
        "emergency_stop_loss_pct": 8.0,   # 8% emergency stop
        "circuit_breaker_enabled": True,
        "circuit_breaker_threshold_pct": 5.0,  # 5% circuit breaker
    },
    
    "strategy": {
        "sma_crossover": {
            "short_window": 5,            # Fast: 5-period SMA
            "long_window": 15,            # Slow: 15-period SMA
            "atr_period": 10,             # Faster ATR
            "atr_multiplier": 1.5,        # Tighter stops
            "risk_reward_ratio": 2.5,     # Higher R:R target
        }
    },
    
    "trading": {
        "poll_interval": 30,              # Check every 30 seconds
        "lookback_bars": 300,             # Less historical data
    },
    
    "confidence_threshold": 0.5,          # Lower confidence required
}


# Balanced profile: moderate risk/reward
BALANCED = {
    "name": "balanced",
    "description": "Moderate risk, balanced approach. Recommended for most users.",
    
    "risk": {
        "max_position_size": 0.5,         # Up to 0.5 lots per position
        "default_position_size": 0.02,    # Default 0.02 lots
        "position_size_pct": 2.0,         # 2% of equity per trade
        "max_daily_loss": 50.0,           # $50 daily loss limit
        "max_positions_per_symbol": 1,    # 1 position per symbol
        "max_total_positions": 3,         # Allow up to 3 total positions
        "use_kelly_sizing": False,        # Fixed sizing
        "emergency_stop_loss_pct": 5.0,   # 5% emergency stop
        "circuit_breaker_enabled": True,
        "circuit_breaker_threshold_pct": 3.0,  # 3% circuit breaker
    },
    
    "strategy": {
        "sma_crossover": {
            "short_window": 10,           # Fast: 10-period SMA
            "long_window": 30,            # Slow: 30-period SMA
            "atr_period": 14,             # Standard ATR
            "atr_multiplier": 2.0,        # Standard stops
            "risk_reward_ratio": 2.0,     # 2:1 R:R
        }
    },
    
    "trading": {
        "poll_interval": 60,              # Check every minute
        "lookback_bars": 500,             # Standard history
    },
    
    "confidence_threshold": 0.6,          # Moderate confidence required
}


# Conservative profile: lower risk, stricter filters
CONSERVATIVE = {
    "name": "conservative",
    "description": "Lower risk, wider stops, stricter entry filters. Capital preservation focus.",
    
    "risk": {
        "max_position_size": 0.2,         # Up to 0.2 lots per position
        "default_position_size": 0.01,    # Default 0.01 lots
        "position_size_pct": 1.0,         # 1% of equity per trade
        "max_daily_loss": 25.0,           # $25 daily loss limit
        "max_positions_per_symbol": 1,    # 1 position per symbol
        "max_total_positions": 2,         # Allow up to 2 total positions
        "use_kelly_sizing": False,        # Fixed sizing
        "emergency_stop_loss_pct": 3.0,   # 3% emergency stop
        "circuit_breaker_enabled": True,
        "circuit_breaker_threshold_pct": 2.0,  # 2% circuit breaker
    },
    
    "strategy": {
        "sma_crossover": {
            "short_window": 20,           # Fast: 20-period SMA (slower signals)
            "long_window": 50,            # Slow: 50-period SMA
            "atr_period": 20,             # Longer ATR period
            "atr_multiplier": 2.5,        # Wider stops
            "risk_reward_ratio": 1.5,     # Conservative R:R
        }
    },
    
    "trading": {
        "poll_interval": 120,             # Check every 2 minutes
        "lookback_bars": 750,             # More historical data
    },
    
    "confidence_threshold": 0.75,         # Higher confidence required
}


# All available mindsets
MINDSETS: Dict[str, Dict[str, Any]] = {
    "aggressive": AGGRESSIVE,
    "balanced": BALANCED, 
    "conservative": CONSERVATIVE,
}


def apply_mindset(config: Dict[str, Any], mindset_name: str) -> Dict[str, Any]:
    """
    Apply a mindset preset to a configuration.
    
    The mindset values override the base config values.
    MT5 credentials and other non-mindset settings are preserved.
    
    Args:
        config: Base configuration dictionary
        mindset_name: One of "aggressive", "balanced", "conservative"
        
    Returns:
        New configuration dict with mindset applied
        
    Raises:
        ValueError: If mindset_name is not recognized
    """
    mindset_name = mindset_name.lower()
    
    if mindset_name not in MINDSETS:
        available = ", ".join(MINDSETS.keys())
        raise ValueError(f"Unknown mindset '{mindset_name}'. Available: {available}")
    
    mindset = MINDSETS[mindset_name]
    result = deepcopy(config)
    
    # Apply risk settings
    if "risk" in mindset:
        if "risk" not in result:
            result["risk"] = {}
        result["risk"].update(mindset["risk"])
    
    # Apply strategy settings
    if "strategy" in mindset:
        strategy_type = result.get("strategy", {}).get("type", "sma_crossover")
        if strategy_type in mindset["strategy"]:
            if "strategy" not in result:
                result["strategy"] = {"type": strategy_type, "params": {}}
            if "params" not in result["strategy"]:
                result["strategy"]["params"] = {}
            result["strategy"]["params"].update(mindset["strategy"][strategy_type])
    
    # Apply trading settings
    if "trading" in mindset:
        if "trading" not in result:
            result["trading"] = {}
        result["trading"].update(mindset["trading"])
    
    # Store confidence threshold
    if "confidence_threshold" in mindset:
        result["confidence_threshold"] = mindset["confidence_threshold"]
    
    # Mark which mindset was applied
    result["_mindset"] = mindset_name
    
    return result


def get_mindset_info(mindset_name: str) -> Dict[str, Any]:
    """
    Get information about a specific mindset.
    
    Args:
        mindset_name: Mindset name
        
    Returns:
        Mindset configuration dict
    """
    mindset_name = mindset_name.lower()
    if mindset_name not in MINDSETS:
        raise ValueError(f"Unknown mindset: {mindset_name}")
    return MINDSETS[mindset_name]


def list_mindsets() -> Dict[str, str]:
    """
    List available mindsets with descriptions.
    
    Returns:
        Dict of mindset_name -> description
    """
    return {name: m["description"] for name, m in MINDSETS.items()}
