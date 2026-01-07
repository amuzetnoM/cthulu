from types import SimpleNamespace
from cthulu.risk.manager import RiskManager


class DummyConnector:
    def get_min_lot(self, symbol: str):
        if symbol == 'GOLDm#':
            return 0.1
        return 0.01


def test_risk_manager_enforces_symbol_min_lot():
    conn = DummyConnector()
    rm = RiskManager(config={}, connector=conn)
    signal = SimpleNamespace(symbol='GOLDm#', size_hint=0.01, price=4000.0)

    ok, reason, size = rm.approve(signal, account_info={'balance': 1000.0}, current_positions=0)
    assert ok
    assert size >= 0.1
