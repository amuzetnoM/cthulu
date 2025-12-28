import pytest
from datetime import datetime

from cthulhu.execution.engine import ExecutionEngine, ExecutionResult, OrderStatus, OrderRequest, OrderType
from cthulhu.position.lifecycle import PositionLifecycle


class DummyConnector:
    def is_connected(self):
        return True


class DummyDB:
    def __init__(self):
        self.updated = []

    def update_position_status(self, ticket, status, reason):
        self.updated.append((ticket, status, reason))


class DummyTracker:
    def __init__(self):
        self.positions = {}
        self.removed = []

    def get_position(self, ticket):
        return self.positions.get(ticket)

    def remove_position(self, ticket):
        self.removed.append(ticket)

    def track_position(self, pos):
        self.positions[pos.ticket] = pos


class FakeExecutionEngine:
    def __init__(self, result=None):
        self._result = result

    def place_order(self, order_req: OrderRequest):
        return self._result

    def close_position(self, ticket):
        return self._result


def test_execute_order_wrapper_returns_ticket(monkeypatch):
    # Arrange
    connector = DummyConnector()
    exec_engine = ExecutionEngine(connector)

    # Create a fake ExecutionResult to be returned by place_order
    res = ExecutionResult(order_id=111, position_ticket=222, status=OrderStatus.FILLED, executed_price=1.2, executed_volume=0.01, timestamp=datetime.now())

    # Monkeypatch place_order
    monkeypatch.setattr(exec_engine, 'place_order', lambda req: res)

    # Act
    ticket = exec_engine.execute_order(symbol='EURUSD', order_type='buy', volume=0.01)

    # Assert
    assert ticket == 222 or ticket == 111


def test_lifecycle_close_position_handles_execution_result(monkeypatch):
    # Arrange
    # Prepare execution result indicating filled
    res = ExecutionResult(order_id=11, position_ticket=22, status=OrderStatus.FILLED, executed_price=1.1, executed_volume=0.01, timestamp=datetime.now())

    engine = FakeExecutionEngine(result=res)
    connector = DummyConnector()
    db = DummyDB()
    tracker = DummyTracker()

    # Track a fake position
    class P:
        def __init__(self, ticket=22):
            self.ticket = ticket
            self.symbol = 'EURUSD'
            self.type = 'buy'
    tracker.track_position(P())

    lifecycle = PositionLifecycle(connector=connector, execution_engine=engine, position_tracker=tracker, db_handler=db)

    # Act
    closed = lifecycle.close_position(ticket=22, reason='Test close')

    # Assert
    assert closed is True
    assert 22 in tracker.removed
    assert db.updated == [(22, 'closed', 'Test close')]
