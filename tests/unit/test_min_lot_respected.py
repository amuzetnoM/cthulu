from types import SimpleNamespace
from cthulu.risk.evaluator import RiskEvaluator


class DummyConnector:
    def __init__(self, min_lot_map=None):
        self._min_lot_map = min_lot_map or {}

    def get_min_lot(self, symbol: str) -> float:
        return self._min_lot_map.get(symbol, 0.01)

    def get_point_value(self, symbol: str):
        return 1.0


class DummyTracker:
    def get_all_positions(self):
        return []


def test_min_lot_respected_for_gold():
    conn = DummyConnector({
        'GOLDm#': 0.1,
        'BTCUSD': 0.01
    })
    evaluator = RiskEvaluator(conn, DummyTracker())

    # When SL points not provided and method is percent, we should fall back to min lot
    volume = evaluator.calculate_position_size('GOLDm#', balance=1000.0, method='percent')
    assert volume >= 0.1

    # Other symbols should still default to small lots
    vol2 = evaluator.calculate_position_size('BTCUSD', balance=1000.0, method='percent')
    assert vol2 >= 0.01
