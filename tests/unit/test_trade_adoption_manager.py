import time
from datetime import datetime
from cthulu.position.adoption import TradeAdoptionManager, TradeAdoptionPolicy
from cthulu.position.tracker import PositionTracker
from cthulu.position.lifecycle import PositionLifecycle
from cthulu.position.manager import PositionManager


class DummyConnector:
    def __init__(self, positions):
        self._positions = positions

    def get_open_positions(self):
        return self._positions

    def get_point(self, symbol):
        return 0.01


class DummyExecEngine:
    pass


class DummyDB:
    def save_position(self, *args, **kwargs):
        return None


def test_adopted_trades_added_to_position_manager():
    # Arrange
    ticket = 12345
    now_ts = time.time()
    ext_trade = {
        'ticket': ticket,
        'symbol': 'GOLDm#',
        'type': 0,
        'volume': 0.1,
        'price_open': 1900.0,
        'price_current': 1901.0,
        'sl': None,
        'tp': None,
        'profit': 0.0,
        'time': now_ts,
        'magic': 0,
        'comment': 'manual'
    }

    connector = DummyConnector([ext_trade])
    tracker = PositionTracker()
    lifecycle = PositionLifecycle(connector, DummyExecEngine(), tracker, DummyDB())
    position_manager = PositionManager()
    policy = TradeAdoptionPolicy(enabled=True, min_age_seconds=0)

    adop = TradeAdoptionManager(connector, tracker, lifecycle, policy=policy, position_manager=position_manager)

    # Act
    adopted = adop.scan_and_adopt()

    # Assert
    assert adopted == 1
    positions = position_manager.get_positions()
    assert any(p.ticket == ticket for p in positions)
