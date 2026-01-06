"""
AI-assisted summarizer for auto-tune sweep reports.

Features:
- Aggregates grid-sweep JSONs and summary.json files
- Computes aggregated metrics and top configuration recommendations
- Optionally calls an LLM endpoint if env var LLM_ENDPOINT is set to produce an enriched human-friendly summary
- Emits both JSON and human-readable text summaries under the reports directory
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import os
import statistics
import textwrap
import requests

from cthulu.backtesting import BACKTEST_REPORTS_DIR

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("cthulu.auto_tune.summary")


def _collect_grid_files(root: Path) -> List[Path]:
    files = list(root.rglob('grid_sweep_*.json'))
    return files


def _load_ranked(path: Path) -> List[Dict[str, Any]]:
    try:
        return json.loads(path.read_text())
    except Exception as e:
        log.warning(f"Failed to load {path}: {e}")
        return []


def aggregate_rankings(dirs: List[Path]) -> Dict[str, Any]:
    """Aggregate ranked results across multiple sweep directories."""
    entries = []
    for d in dirs:
        for p in _collect_grid_files(d):
            ranked = _load_ranked(p)
            if not ranked:
                continue
            # top item only for now
            top = ranked[0]
            entries.append({
                'file': str(p),
                'symbol': top.get('metrics', {}).get('symbol') if isinstance(top.get('metrics', {}), dict) else None,
                'min_time_in_trade_bars': top.get('min_time_in_trade_bars'),
                'trail_pct': top.get('trail_pct'),
                'concurrency': top.get('concurrency'),
                'total_profit_estimate': top.get('metrics', {}).get('total_profit_estimate', 0.0) if isinstance(top.get('metrics', {}), dict) else 0.0,
            })

    # Produce aggregated stats
    out = {'count': len(entries), 'entries': entries}
    if entries:
        out['stats'] = {
            'avg_profit_est': statistics.mean([e['total_profit_estimate'] for e in entries]),
            'median_profit_est': statistics.median([e['total_profit_estimate'] for e in entries]),
            'min_time_mode': statistics.mode([e['min_time_in_trade_bars'] for e in entries]) if len(entries) > 0 else None,
        }
    else:
        out['stats'] = {}

    return out


def compose_human_summary(agg: Dict[str, Any]) -> str:
    lines = []
    lines.append("Auto-Tune Aggregate Summary")
    lines.append("--------------------------")
    lines.append(f"Windows processed: {agg.get('count', 0)}")

    stats = agg.get('stats', {})
    if stats:
        lines.append(f"Average profit estimate: {stats.get('avg_profit_est', 0):.2f}")
        lines.append(f"Median profit estimate: {stats.get('median_profit_est', 0):.2f}")
        lines.append(f"Mode min_time_in_trade_bars: {stats.get('min_time_mode')}")

    # Top 5 entries
    lines.append("\nTop entries (top 5):")
    for e in sorted(agg.get('entries', []), key=lambda x: x['total_profit_estimate'], reverse=True)[:5]:
        lines.append(f"- file={Path(e['file']).name} profit_est={e['total_profit_estimate']:.2f} min_time={e['min_time_in_trade_bars']} trail={e['trail_pct']} concurrency={e['concurrency']}")

    return "\n".join(lines)


def call_llm_for_enhanced_summary(prompt: str) -> str:
    """Call external LLM endpoint if configured via env var LLM_ENDPOINT. The endpoint should accept JSON {"prompt":...}."""
    endpoint = os.environ.get('LLM_ENDPOINT')
    api_key = os.environ.get('LLM_API_KEY')
    if not endpoint:
        raise RuntimeError("No LLM_ENDPOINT configured")

    payload = {"prompt": prompt}
    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['Authorization'] = f"Bearer {api_key}"

    resp = requests.post(endpoint, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # Accept 'text' or 'response' in response
    return data.get('text') or data.get('response') or json.dumps(data)


def summarize_reports(report_dirs: List[Path], output_dir: Path | None = None, call_ai_if_available: bool = True) -> Path:
    output_dir = Path(output_dir or (Path(BACKTEST_REPORTS_DIR) / 'auto_tune_summaries'))
    output_dir.mkdir(parents=True, exist_ok=True)

    agg = aggregate_rankings(report_dirs)
    human = compose_human_summary(agg)

    # Optionally call LLM
    ai_text = None
    if call_ai_if_available:
        try:
            ai_text = call_llm_for_enhanced_summary(human)
        except Exception as e:
            log.warning(f"LLM call failed: {e}")

    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    out_json = output_dir / f'auto_tune_summary_{ts}.json'
    out_txt = output_dir / f'auto_tune_summary_{ts}.txt'

    out_json.write_text(json.dumps({'aggregated': agg, 'ai_summary': ai_text}, indent=2, default=str))
    out_txt.write_text(human + ("\n\nAI_SUMMARY:\n" + ai_text if ai_text else ""))

    log.info(f"Wrote summaries to {out_json} and {out_txt}")
    return out_json


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('dirs', nargs='+', help='Sweep report dirs to summarize')
    p.add_argument('--no-ai', action='store_true', help='Do not call LLM even if configured')
    args = p.parse_args()

    paths = [Path(d) for d in args.dirs]
    summarize_reports(paths, call_ai_if_available=not args.no_ai)
