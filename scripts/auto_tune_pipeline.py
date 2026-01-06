"""
Auto-tune pipeline runner.
Orchestrates data fetch, grid sweeps, aggregation and report generation.
"""
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd

from backtesting.data_manager import HistoricalDataManager, DataSource
from scripts.grid_sweep_scaler import run_grid_sweep_for_df
from cthulu.backtesting import BACKTEST_REPORTS_DIR, BACKTEST_CACHE_DIR

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("cthulu.auto_tune")

SYMBOLS_CFG = Path('config/symbols.json')
REPORT_ROOT = BACKTEST_REPORTS_DIR / 'auto_tune'

# Default timeframes to sweep
DEFAULT_TIMEFRAMES = ['M1', 'M5', 'M15', 'H1', 'H4', 'D1']


def load_symbols():
    with open(SYMBOLS_CFG, 'r', encoding='utf-8') as f:
        return json.load(f)


def rolling_windows(end_date: datetime, days: int = 30):
    # Return (start, end) covering last `days` calendar days; for now we return a single window
    end = end_date
    start = end - timedelta(days=days)
    return [(start, end)]


def _is_weekend_only_range(start: datetime, end: datetime) -> bool:
    """Return True if every day in [start, end] is Sat/Sun."""
    cur = start.date()
    while cur <= end.date():
        if cur.weekday() < 5:  # 0-4 are Mon-Fri
            return False
        cur = cur + timedelta(days=1)
    return True


def run_full_sweep(symbols: list, timeframes: list = None, days_list: list | None = None, mindsets: list = None):
    """Run expanded sweep across multiple rolling windows (days_list).

    days_list: list of window lengths in days to run, e.g. [30, 60, 90]
    """
    days_list = days_list or [30]
    results_root = BACKTEST_REPORTS_DIR / 'auto_tune_full' / datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    results_root.mkdir(parents=True, exist_ok=True)

    for days in days_list:
        log.info(f"Starting sweeps for window={days} days")
        out_root = results_root / f"window_{days}d"
        out_root.mkdir(parents=True, exist_ok=True)

        # Reuse run_smoke_sweep semantics but iterate windows of the requested size
        dm = HistoricalDataManager()
        sym_cfgs = load_symbols()
        timeframes = timeframes or DEFAULT_TIMEFRAMES

        now = datetime.utcnow()
        windows = rolling_windows(now, days=days)

        for symbol in symbols:
            cfg = sym_cfgs.get(symbol, {})
            for timeframe in timeframes:
                for (start, end) in windows:
                    # Skip weekend-only window for symbols that don't trade on weekends
                    if not cfg.get('weekend_trading', False) and _is_weekend_only_range(start, end):
                        log.info(f"Skipping weekend-only window for {symbol} {timeframe} {start} -> {end}")
                        continue

                    try:
                        df, meta = dm.fetch_data(symbol, start, end, timeframe=timeframe, source=DataSource.MT5, use_cache=True)
                    except Exception as e:
                        log.warning(f"Failed to fetch {symbol} {timeframe} {start}->{end}: {e}")
                        continue

                    # Discover all mindset configs that match timeframe
                    mindset_cfgs = []
                    mindsets_dir = Path('configs/mindsets')
                    if mindsets_dir.exists():
                        for ms_dir in mindsets_dir.iterdir():
                            if ms_dir.is_dir():
                                candidate = ms_dir / f'config_{ms_dir.name}_{timeframe.lower()}.json'
                                if candidate.exists():
                                    try:
                                        cfg_parsed = json.loads(candidate.read_text())
                                        mindset_cfgs.append({'name': ms_dir.name, 'cfg': cfg_parsed})
                                    except Exception:
                                        log.warning(f"Failed to parse mindset config {candidate}")

                    if not mindset_cfgs:
                        mindset_cfgs = [{'name': 'default_dynamic', 'cfg': None}]

                    for m in mindset_cfgs:
                        out_dir = out_root / f"{symbol}_{timeframe}_{m['name']}_{start.date()}_{end.date()}"
                        ranked = run_grid_sweep_for_df(df, symbol, timeframe, m['cfg'], out_dir)
                        # Save a small summary
                        summary = {
                            'symbol': symbol,
                            'timeframe': timeframe,
                            'mindset': m['name'],
                            'window_start': start.isoformat(),
                            'window_end': end.isoformat(),
                            'top_config': ranked[0] if ranked else None
                        }
                        (out_dir / 'summary.json').write_text(json.dumps(summary, indent=2, default=str))
                        log.info(f"Completed sweep for {symbol} {timeframe} mindset={m['name']} ({start.date()} -> {end.date()}); results at {out_dir}")

    return results_root


def run_smoke_sweep(symbols: list, timeframes: list = None, days: int = 30, mindsets: list = None):
    dm = HistoricalDataManager()
    sym_cfgs = load_symbols()
    timeframes = timeframes or DEFAULT_TIMEFRAMES

    now = datetime.utcnow()
    windows = rolling_windows(now, days=days)

    out_root = REPORT_ROOT / now.strftime('%Y%m%d_%H%M%S')
    out_root.mkdir(parents=True, exist_ok=True)

    for symbol in symbols:
        cfg = sym_cfgs.get(symbol, {})
        for timeframe in timeframes:
            for (start, end) in windows:
                try:
                    df, meta = dm.fetch_data(symbol, start, end, timeframe=timeframe, source=DataSource.MT5, use_cache=True)
                except Exception as e:
                    log.warning(f"Failed to fetch {symbol} {timeframe} {start}->{end}: {e}")
                    continue

                # Discover available mindset configs for timeframe
                mindset_cfgs = []
                mindsets_dir = Path('configs/mindsets')
                if mindsets_dir.exists():
                    for ms_dir in mindsets_dir.iterdir():
                        if ms_dir.is_dir():
                            candidate = ms_dir / f'config_{ms_dir.name}_{timeframe.lower()}.json'
                            if candidate.exists():
                                try:
                                    cfg_parsed = json.loads(candidate.read_text())
                                    mindset_cfgs.append({'name': ms_dir.name, 'cfg': cfg_parsed})
                                except Exception:
                                    log.warning(f"Failed to parse mindset config {candidate}")

                if not mindset_cfgs:
                    mindset_cfgs = [{'name': 'default_dynamic', 'cfg': None}]

                for m in mindset_cfgs:
                    out_dir = out_root / f"{symbol}_{timeframe}_{m['name']}_{start.date()}_{end.date()}"
                    ranked = run_grid_sweep_for_df(df, symbol, timeframe, m['cfg'], out_dir)
                    # Save a small summary
                    summary = {
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'mindset': m['name'],
                        'window_start': start.isoformat(),
                        'window_end': end.isoformat(),
                        'top_config': ranked[0] if ranked else None
                    }
                    (out_dir / 'summary.json').write_text(json.dumps(summary, indent=2, default=str))
                    log.info(f"Completed sweep for {symbol} {timeframe} mindset={m['name']} ({start.date()} -> {end.date()}); results at {out_dir}")

    return out_root


if __name__ == '__main__':
    # Example smoke run for GOLD and BTC last 7 days
    run_smoke_sweep(['GOLDm#', 'BTCUSD#'], timeframes=['M15', 'H1'], days=7)
