from types import SimpleNamespace
from cthulu.execution.engine import ExecutionEngine, OrderRequest, OrderType


class DummyConnector:
    def __init__(self):
        pass

    def ensure_symbol_selected(self, symbol):
        return symbol

    def get_symbol_info(self, symbol):
        return {'name': symbol, 'bid': 100.0, 'ask': 100.2, 'volume_min': 0.1, 'volume_max': 100, 'volume_step': 0.01}

    def _mt5_symbol_info_tick(self, symbol):
        return None


class DummyEngine(ExecutionEngine):
    def __init__(self):
        # don’t call parent init heavy stuff; set attributes used by _build_mt5_request
        self.connector = DummyConnector()
        self.slippage = 10
        self.magic_number = 0
        self.logger = SimpleNamespace(warning=lambda *a, **k: None, error=lambda *a, **k: None)


def test_engine_bumps_volume_to_min():
    eng = DummyEngine()
    order_req = OrderRequest(signal_id='s1', symbol='GOLDm#', side='BUY', volume=0.01, order_type=OrderType.MARKET)
    req = eng._build_mt5_request(order_req)
    assert req['volume'] >= 0.1
    assert abs(req['volume'] - 0.1) < 1e-6
