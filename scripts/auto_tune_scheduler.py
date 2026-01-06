"""
Auto-tune scheduler CLI

Features:
- Interactive CLI to configure schedules for auto-tune runs
- Save schedules under `cthulu/config/auto_tune_schedules/`
- Optionally run immediately (blocking) or schedule in-process with APScheduler
- Provides a compact config that can be used by cron or Windows Task Scheduler
- Hook point to call AI summarizer after runs

Usage examples:
    python scripts/auto_tune_scheduler.py --symbols GOLDm#,BTCUSD# --timeframes M15,H1 --days 30 --mode smoke --run-now
    python scripts/auto_tune_scheduler.py --create-schedule my-weekly --cron "0 3 * * 1" --symbols GOLDm# --timeframes M15 --days 30

Note: Scheduling to system scheduler (cron/Task Scheduler) is out of scope — this script writes the schedule config and can run it immediately.
"""
from __future__ import annotations
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import os

from cthulu.backtesting import BACKTEST_REPORTS_DIR
from scripts.auto_tune_pipeline import run_full_sweep, run_smoke_sweep

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("cthulu.auto_tune.scheduler")

SCHEDULE_DIR = Path('config/auto_tune_schedules')
SCHEDULE_DIR.mkdir(parents=True, exist_ok=True)


def save_schedule(name: str, cfg: Dict[str, Any]) -> Path:
    path = SCHEDULE_DIR / f"{name}.json"
    path.write_text(json.dumps(cfg, indent=2, default=str))
    return path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Auto-tune scheduler & helper")
    p.add_argument("--symbols", type=str, default="GOLDm#,BTCUSD#", help="Comma-separated symbols")
    p.add_argument("--timeframes", type=str, default="M15,H1", help="Comma-separated timeframes")
    p.add_argument("--days", type=int, default=30, help="Lookback window in days")
    p.add_argument("--mode", choices=["smoke", "full"], default="smoke", help="Run mode: smoke or full sweep")
    p.add_argument("--create-schedule", type=str, help="Create schedule with given name and exit")
    p.add_argument("--cron", type=str, help="Cron expression for schedule (optional, informational)")
    p.add_argument("--run-now", action="store_true", help="If set, run the sweep immediately")
    p.add_argument("--ai-summary", action="store_true", help="If set, run AI summarizer after sweep")
    return p.parse_args()


def build_cfg(args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "name": getattr(args, 'create_schedule', f"run_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}"),
        "symbols": [s.strip() for s in args.symbols.split(',') if s.strip()],
        "timeframes": [t.strip() for t in args.timeframes.split(',') if t.strip()],
        "days": args.days,
        "mode": args.mode,
        "created_at": datetime.utcnow().isoformat(),
        "cron": args.cron or None
    }


def run_cfg(cfg: Dict[str, Any], ai_summary: bool = False) -> Path:
    # Simple runner: uses the pipeline's run_smoke_sweep or run_full_sweep
    symbols = cfg.get('symbols', [])
    timeframes = cfg.get('timeframes', [])
    days = cfg.get('days', 30)
    mode = cfg.get('mode', 'smoke')

    if mode == 'smoke':
        out = run_smoke_sweep(symbols, timeframes=timeframes, days=days)
    else:
        out = run_full_sweep(symbols, timeframes=timeframes, days_list=[days])

    log.info(f"Sweep completed: {out}")

    if ai_summary:
        try:
            from scripts.auto_tune_ai_summary import summarize_reports
            summary_path = summarize_reports([out], output_dir=Path(BACKTEST_REPORTS_DIR) / 'auto_tune_summaries')
            log.info(f"AI-assisted summary written to: {summary_path}")
        except Exception as e:
            log.warning(f"AI summarizer failed: {e}")

    return out


def main():
    args = parse_args()
    cfg = build_cfg(args)

    if args.create_schedule:
        path = save_schedule(args.create_schedule, cfg)
        print(f"Schedule saved to: {path}")
        if args.cron:
            print(f"Cron suggestion: {args.cron} will trigger the schedule '{args.create_schedule}'")
        return

    # If run-now or no create-schedule, run immediately
    if args.run_now:
        run_cfg(cfg, ai_summary=args.ai_summary)
    else:
        # Save a local run config for later
        fallback_name = cfg['name']
        path = save_schedule(fallback_name, cfg)
        print(f"Saved run config to: {path}. Use --run-now to execute immediately or schedule via OS scheduler to call this script.")


if __name__ == '__main__':
    main()
