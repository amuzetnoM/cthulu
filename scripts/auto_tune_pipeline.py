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

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("cthulu.auto_tune")

SYMBOLS_CFG = Path('cthulu/config/symbols.json')
REPORT_ROOT = Path('backtesting/reports/auto_tune')

# Default timeframes to sweep
DEFAULT_TIMEFRAMES = ['M1', 'M5', 'M15', 'H1', 'H4', 'D1']


def load_symbols():
    with open(SYMBOLS_CFG, 'r', encoding='utf-8') as f:
        return json.load(f)


def rolling_windows(end_date: datetime, days: int = 30):
    # Return (start, end) covering last `days` trading days; use end_date - days
    end = end_date
    start = end - timedelta(days=days)
    return [(start, end)]


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

                # Load mindset config if available for timeframe (fallback to None)
                mindset_cfg = None
                # try to find a mindset file matching timeframe
                mf = Path(f'cthulu/configs/mindsets/ultra_aggressive/config_ultra_aggressive_{timeframe.lower()}.json')
                if mf.exists():
                    try:
                        mindset_cfg = json.loads(mf.read_text())
                    except Exception:
                        mindset_cfg = None

                out_dir = out_root / f"{symbol}_{timeframe}_{start.date()}_{end.date()}"
                ranked = run_grid_sweep_for_df(df, symbol, timeframe, mindset_cfg, out_dir)
                # Save a small summary
                summary = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'window_start': start.isoformat(),
                    'window_end': end.isoformat(),
                    'top_config': ranked[0] if ranked else None
                }
                (out_dir / 'summary.json').write_text(json.dumps(summary, indent=2, default=str))
                log.info(f"Completed sweep for {symbol} {timeframe} ({start.date()} -> {end.date()}); results at {out_dir}")

    return out_root


if __name__ == '__main__':
    # Example smoke run for GOLD and BTC last 7 days
    run_smoke_sweep(['GOLDm#', 'BTCUSD#'], timeframes=['M15', 'H1'], days=7)
