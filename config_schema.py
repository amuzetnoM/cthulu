"""
Configuration loader and validation.

This module centralizes config loading and schema validation. It maps common legacy keys
to canonical names, applies defaults, and returns typed config objects for the application.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import json
import os

try:
    from pydantic import BaseModel, Field, ValidationError
except Exception:
    # If pydantic is not available, provide a very small fallback validator
    BaseModel = object
    Field = lambda *a, **k: None
    ValidationError = Exception


class MT5Config(BaseModel):
    login: int
    password: str
    server: str
    timeout: int = 60000
    path: Optional[str] = None


class RiskConfig(BaseModel):
    max_position_size_pct: float = 0.02
    max_total_exposure_pct: float = 0.10
    max_daily_loss_pct: float = 0.05
    max_positions_per_symbol: int = 1
    max_total_positions: int = 3
    min_risk_reward_ratio: float = 1.0
    max_spread_pips: float = 50.0
    volatility_scaling: bool = True


class TradingConfig(BaseModel):
    symbol: str = "EURUSD"
    timeframe: str = "TIMEFRAME_H1"
    poll_interval: int = 60
    lookback_bars: int = 500


class StrategyConfig(BaseModel):
    type: str = "sma_crossover"
    params: Dict[str, Any] = Field(default_factory=dict)


class OrphanConfig(BaseModel):
    """Configuration for orphan trade adoption."""
    enabled: bool = False
    adopt_symbols: list = Field(default_factory=list)  # Empty = all symbols
    ignore_symbols: list = Field(default_factory=list)
    apply_exit_strategies: bool = True
    max_adoption_age_hours: float = 0.0  # 0 = no limit
    log_only: bool = False  # If True, only log orphans without adopting


class Config(BaseModel):
    mt5: MT5Config
    risk: RiskConfig
    trading: TradingConfig
    strategy: StrategyConfig
    indicators: Optional[list] = Field(default_factory=list)
    exit_strategies: Optional[list] = Field(default_factory=list)
    orphan_trades: OrphanConfig = Field(default_factory=OrphanConfig)
    database: Dict[str, Any] = Field(default_factory=lambda: {"path": "herald.db"})
    cache_enabled: bool = True
    logging: Dict[str, Any] = Field(default_factory=dict)

    @staticmethod
    def _map_legacy_keys(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Map legacy or alternate key names to canonical keys used by this app.

        This helps support configs that use alternate names (e.g., 'fast_period' vs 'short_window').
        """
        # Map top-level risk keys
        r = raw.copy()
        risk = r.get('risk', {})
        if 'max_position_size' in risk:
            risk['max_position_size_pct'] = risk.pop('max_position_size')
        # Map risk keys that could exist in older configs
        if 'max_daily_loss' in risk and 'max_daily_loss_pct' not in risk:
            risk['max_daily_loss_pct'] = risk.get('max_daily_loss')
        r['risk'] = risk

        # Map strategy param keys
        strategy = r.get('strategy', {})
        params = strategy.get('params', {}) if isinstance(strategy, dict) else {}
        # common naming alternatives
        if 'fast_period' in params and 'short_window' not in params:
            params['short_window'] = params.pop('fast_period')
        if 'slow_period' in params and 'long_window' not in params:
            params['long_window'] = params.pop('slow_period')
        strategy['params'] = params
        r['strategy'] = strategy

        # Indicators: sometimes passed as dict; ensure list of dicts
        inds = r.get('indicators', [])
        if isinstance(inds, dict):
            # convert to list
            r['indicators'] = [ { 'type': k, 'params': v or {} } for k,v in inds.items() ]

        # Exit strategies: ensure list-of-dicts
        if isinstance(r.get('exit_strategies', []), dict):
            r['exit_strategies'] = [ { 'type': k, **v } for k, v in r['exit_strategies'].items() ]

        return r

    @classmethod
    def load(cls, path: str) -> 'Config':
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        text = p.read_text()
        raw = json.loads(text)
        raw = cls._map_legacy_keys(raw)

        try:
            cfg = cls.parse_obj(raw)
        except Exception as e:
            # Try a simple validation fallback if pydantic isn't available
            # This approach will still yield a reasonable config for the app
            raise

        # Allow environment variable overrides for sensitive fields
        mt5_login = os.getenv('MT5_LOGIN')
        mt5_password = os.getenv('MT5_PASSWORD')
        mt5_server = os.getenv('MT5_SERVER')
        if mt5_login and mt5_password and mt5_server:
            cfg.mt5.login = int(mt5_login)
            cfg.mt5.password = mt5_password
            cfg.mt5.server = mt5_server

        return cfg
