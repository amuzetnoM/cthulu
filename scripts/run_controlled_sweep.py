"""
Run a controlled auto-tune sweep for quick validation.
"""
from pathlib import Path
from cthulu.scripts.auto_tune_pipeline import run_smoke_sweep
from scripts.auto_tune_ai_summary import summarize_reports

if __name__ == '__main__':
    out = run_smoke_sweep(['GOLDm#','BTCUSD#'], timeframes=['M15','H1'], days=30)
    print('Smoke sweep out dir:', out)
    # Summarize results (AI optional via env var)
    summary = summarize_reports([out])
    print('Summary written to:', summary)
