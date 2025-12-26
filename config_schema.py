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
    # Allow a legacy absolute dollar daily loss value to be stored by the wizard
    max_daily_loss: float = 0.0
    max_positions_per_symbol: int = 1
    max_total_positions: int = 3
    min_risk_reward_ratio: float = 1.0
    max_spread_pips: float = 50.0
    volatility_scaling: bool = True
    # SL/TP adaptive knobs
    emergency_stop_loss_pct: float = 8.0  # default emergency stop when adopting external trades (percent)
    sl_balance_thresholds: Dict[str, float] = Field(default_factory=lambda: {
        "tiny": 0.01,   # <= $1k
        "small": 0.02,  # <= $5k
        "medium": 0.05, # <= $20k
        "large": 0.25   # > $20k
    })
    sl_balance_breakpoints: list = Field(default_factory=lambda: [1000.0, 5000.0, 20000.0])


class TradingConfig(BaseModel):
    symbol: str = "EURUSD"
    timeframe: str = "TIMEFRAME_H1"
    poll_interval: int = 60
    lookback_bars: int = 500


class StrategyConfig(BaseModel):
    type: str = "sma_crossover"
    params: Dict[str, Any] = Field(default_factory=dict)
    # Dynamic selection config (if type=='dynamic')
    dynamic_selection: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # Child strategies for dynamic selection
    strategies: Optional[list] = Field(default_factory=list)


class OrphanConfig(BaseModel):
    """Configuration for orphan trade adoption."""
    enabled: bool = False
    adopt_symbols: list = Field(default_factory=list)  # Empty = all symbols
    ignore_symbols: list = Field(default_factory=list)
    apply_exit_strategies: bool = True
    max_adoption_age_hours: float = 0.0  # 0 = no limit
    log_only: bool = False  # If True, only log orphans without adopting


class AdvisoryConfig(BaseModel):
    """Configuration for advisory and ghost modes."""
    enabled: bool = False
    mode: str = 'advisory'  # 'advisory' | 'ghost' | 'production'
    ghost_lot_size: float = 0.01
    ghost_max_trades: int = 5
    ghost_max_duration: int = 3600  # seconds
    log_only: bool = False  # If True, do not actually place ghost trades; only log/record


class Config(BaseModel):
    mt5: MT5Config
    risk: RiskConfig
    trading: TradingConfig
    strategy: StrategyConfig
    providers: Dict[str, Any] = Field(default_factory=lambda: {
        'alpha_vantage_key': None,
        'binance_api_key': None,
        'binance_api_secret': None
    })
    runtime: Dict[str, Any] = Field(default_factory=lambda: {
        'dry_run': True,
        'live_run': False,
        'live_run_confirm_env': 'LIVE_RUN_CONFIRM'
    })
    indicators: Optional[list] = Field(default_factory=list)
    exit_strategies: Optional[list] = Field(default_factory=list)
    orphan_trades: OrphanConfig = Field(default_factory=OrphanConfig)
    advisory: AdvisoryConfig = Field(default_factory=AdvisoryConfig)
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
        # Wizard historically used 'position_size_pct' as a percentage (e.g. 2.0 for 2%).
        # Normalize to the canonical 'max_position_size_pct' as a decimal (0.02).
        if 'position_size_pct' in risk and 'max_position_size_pct' not in risk:
            try:
                val = float(risk.pop('position_size_pct'))
                # If user provided percent-style value (>1), convert to decimal
                if val > 1:
                    val = val / 100.0
                risk['max_position_size_pct'] = val
            except Exception:
                # Fallback: silently ignore conversion errors and leave value as-is
                risk['max_position_size_pct'] = risk.get('position_size_pct')
        # Map risk keys that could exist in older configs
        if 'max_daily_loss' in risk and 'max_daily_loss_pct' not in risk:
            # The wizard historically stored a dollar-denominated 'max_daily_loss'.
            # Preserve the original value and do not assume it's a percent; also
            # keep a pct field if present elsewhere. Store the raw dollar value
            # under 'max_daily_loss' (new in schema) while leaving pct untouched.
            try:
                # If the value seems fractional (<1), treat it as a pct and copy
                v = float(risk.get('max_daily_loss'))
                if v <= 1.0:
                    risk['max_daily_loss_pct'] = v
                else:
                    # store raw dollar value for backwards compatibility
                    risk['max_daily_loss'] = v
            except Exception:
                risk['max_daily_loss'] = risk.get('max_daily_loss')
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

        # Process environment variable overrides before validation
        if 'mt5' in raw:
            mt5_cfg = raw['mt5']
            # No FROM_ENV placeholders needed - env overrides below

        try:
            # Pydantic v2 uses model_validate, v1 uses parse_obj
            if hasattr(cls, 'model_validate'):
                cfg = cls.model_validate(raw)
            else:
                cfg = cls.parse_obj(raw)
        except Exception as e:
            # Try a simple validation fallback if pydantic isn't available
            # This approach will still yield a reasonable config for the app
            raise

        # Allow environment variable overrides for sensitive fields (takes priority over config values)
        mt5_login = os.getenv('MT5_LOGIN')
        mt5_password = os.getenv('MT5_PASSWORD')
        mt5_server = os.getenv('MT5_SERVER')
        if mt5_login:
            cfg.mt5.login = int(mt5_login)
        if mt5_password:
            cfg.mt5.password = mt5_password
        if mt5_server:
            cfg.mt5.server = mt5_server

        # If live_run requested in config, require explicit environment confirmation variable
        runtime = getattr(cfg, 'runtime', {}) or {}
        live_run = runtime.get('live_run', False)
        confirm_env = runtime.get('live_run_confirm_env', 'LIVE_RUN_CONFIRM')
        if live_run:
            if os.getenv(confirm_env) != '1':
                raise PermissionError(
                    "Live run requested in config but confirmation env var not set. "
                    f"Set environment variable {confirm_env}=1 to allow live trading."
                )

        return cfg
