from cthulu.scripts.auto_tune_pipeline import run_full_sweep

symbols=['GOLDm#','BTCUSD#','ETHUSD#','XRPUSD#','USDTUSD#','EURUSD']
# Start with a 30-day sweep; we'll follow with longer windows after this completes
run_full_sweep(symbols, days_list=[30])
print('Full 30-day sweep invocation complete')
