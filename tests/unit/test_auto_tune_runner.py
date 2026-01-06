import json
from pathlib import Path

import pytest

from cthulu.backtesting.scripts import auto_tune_runner as runner


def fake_run_grid_sweep_for_df(df, symbol, timeframe, cfg, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    # write a fake grid_sweep file
    (out_dir / 'grid_sweep_1.json').write_text(json.dumps([
        {
            'metrics': {'symbol': symbol, 'total_profit_estimate': 123.45},
            'min_time_in_trade_bars': 3,
            'trail_pct': 0.5,
            'concurrency': 1
        }
    ]))
    return [{
        'metrics': {'symbol': symbol, 'total_profit_estimate': 123.45},
        'min_time_in_trade_bars': 3,
        'trail_pct': 0.5,
        'concurrency': 1
    }]


def test_smoke_sweep_and_summarize(tmp_path, monkeypatch):
    # Patch grid sweep function
    monkeypatch.setattr(runner, 'run_grid_sweep_for_df', fake_run_grid_sweep_for_df)

    out = runner.run_smoke_sweep(['GOLDm#'], timeframes=['M15'], days=1, out_root=tmp_path / 'reports')
    assert out.exists()

    summary = runner.summarize_reports([out], output_dir=tmp_path / 'summaries', call_ai_if_available=False)
    assert summary.exists()

    rec = runner.apply_recommendations_from_dirs([out], output_dir=tmp_path / 'recommend', auto_apply=False)
    assert rec.exists()

    # Read recommendations content
    data = json.loads(rec.read_text())
    assert 'recommended_min_time_in_trade_bars' in data
    assert 'recommended_trail_pct' in data
    assert data['source_count'] >= 1
