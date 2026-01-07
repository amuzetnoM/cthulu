import pandas as pd
from types import SimpleNamespace
from cthulu.core.trading_loop import TradingLoopContext, TradingLoop
from cthulu.strategy.base import Signal, SignalType


def test_signal_symbol_fallback_sets_system_symbol(tmp_path):
    # Arrange: minimal context
    import logging
    ctx = SimpleNamespace()
    ctx.logger = logging.getLogger('test')
    ctx.logger.addHandler(logging.NullHandler())
    ctx.symbol = 'GOLDm#'
    ctx.timeframe = 'TIMEFRAME_M1'
    ctx.poll_interval = 0
    ctx.lookback_bars = 10
    ctx.args = SimpleNamespace(max_loops=1)
    # Create a dummy strategy that returns a signal with UNKNOWN symbol
    class DummyStrategy:
        def on_bar(self, bar):
            return Signal(
                id='test',
                timestamp=bar.name,
                symbol='UNKNOWN',
                timeframe='M1',
                side=SignalType.SHORT,
                action='SELL',
                price=100.0,
                stop_loss=101.0,
                take_profit=99.0,
                confidence=0.9
            )
    ctx.strategy = DummyStrategy()
    # Dummy connector and data layer
    class DummyConnector:
        def get_rates(self, symbol, timeframe, count):
            import pandas as pd
            idx = pd.date_range(end=pd.Timestamp.now(), periods=10, freq='T')
            df = pd.DataFrame({'close': [100+i*0.1 for i in range(10)]}, index=idx)
            return df
        def get_account_info(self):
            return {'balance': 100}
    ctx.connector = DummyConnector()
    class DummyDataLayer:
        def normalize_rates(self, rates, symbol):
            df = pd.DataFrame(rates)
            df.index = pd.date_range(end=pd.Timestamp.now(), periods=len(rates), freq='T')
            df['rsi'] = 50
            df['atr'] = 1.0
            df['close'] = df['close'] if 'close' in df.columns else df.iloc[:,0]
            return df
    ctx.data_layer = DummyDataLayer()
    ctx.risk_manager = SimpleNamespace(approve=lambda **kwargs: (True, 'ok', 0.01))
    ctx.position_manager = SimpleNamespace(get_positions=lambda symbol=None: [])
    ctx.position_lifecycle = SimpleNamespace(modify_position=lambda *a, **k: True)
    ctx.metrics = SimpleNamespace()
    ctx.database = SimpleNamespace()
    ctx.args = SimpleNamespace(max_loops=1)
    # Minimal indicators and config required by TradingLoop
    ctx.indicators = []
    ctx.config = {}
    ctx.lookback_bars = 10
    ctx.poll_interval = 0

    tl = TradingLoop(ctx)

    # Act: create a minimal DataFrame and call _generate_signal directly
    import pandas as pd
    df = pd.DataFrame({'close': [100.0]}, index=pd.date_range(end=pd.Timestamp.now(), periods=1, freq='min'))
    signal = tl._generate_signal(df)

    # Assert: signal symbol should be system symbol (GOLDm#)
    assert signal is not None
    assert signal.symbol == 'GOLDm#'