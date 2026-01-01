"""Generate sample reports into backtesting/reports for UI testing"""
from backtesting import ReportGenerator, ReportFormat
from types import SimpleNamespace
import json

# Create dummy results and metrics
results = {
    'config': {'initial_capital': 10000, 'commission': 0.0001, 'slippage_pct': 0.0002, 'speed_mode': 'fast'},
    'bars_processed': 1000,
    'duration_seconds': 0.05,
    'bars_per_second': 20000,
    'trades': []
}
metrics = SimpleNamespace(**{
    'total_return': -23.75,
    'sharpe_ratio': -1.51,
    'sortino_ratio': -1.18,
    'calmar_ratio': -3.70,
    'omega_ratio': 0.54,
    'max_drawdown_pct': 24.6,
    'win_rate': 0.0,
    'total_trades': 5,
    'avg_win': 0.0,
    'avg_loss': 22.31,
    'largest_win': -18.43,
    'largest_loss': -28.39,
})

rg = ReportGenerator()
print('Generating HTML report...')
html_path = rg.generate(results, metrics, output_path=None, format=ReportFormat.HTML)
print('HTML path:', html_path)

print('Generating JSON report...')
json_path = rg.generate(results, metrics, output_path='summary.json', format=ReportFormat.JSON)
print('JSON path:', json_path)

# Print manifest
with open('backtesting/reports/index.json') as f:
    print('Manifest:', json.dumps(json.load(f), indent=2))
