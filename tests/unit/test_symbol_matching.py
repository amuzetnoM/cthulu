from types import SimpleNamespace
import cthulu.connector.mt5_connector as m5


class _FakeSymbol:
    def __init__(self, name):
        self.name = name


def test_find_matching_symbol_prefers_goldm_over_goldman(monkeypatch):
    # Arrange: fake symbols returned by mt5.symbols_get()
    symbols = [_FakeSymbol('GOLDm#'), _FakeSymbol('Goldman Sachs'), _FakeSymbol('GOLDM')]

    monkeypatch.setattr(m5.mt5, 'symbols_get', lambda: symbols)

    conn = m5.MT5Connector.__new__(m5.MT5Connector)
    # call the private method
    matches = conn._find_matching_symbol('GOLD')

    # Assert: should match 'GOLDm#' or 'GOLDM' but not 'Goldman Sachs'
    assert any(s in ('GOLDm#', 'GOLDM') for s in matches)
    assert not any('Goldman' in s for s in matches)


def test_ensure_symbol_selected_prefers_tradable(monkeypatch):
    # Provide fake symbols list
    symbols = [_FakeSymbol('Goldman Sachs'), _FakeSymbol('GOLDm#')]
    monkeypatch.setattr(m5.mt5, 'symbols_get', lambda: symbols)

    # Stub symbol_select to return True only for the real tradable symbol
    def symbol_select_stub(s, v):
        return s == 'GOLDm#'
    monkeypatch.setattr(m5.mt5, 'symbol_select', symbol_select_stub)

    # Create connector and stub get_symbol_info to mark only GOLDm# as tradable
    conn = m5.MT5Connector.__new__(m5.MT5Connector)
    import logging
    conn.logger = logging.getLogger('test_mt5')
    def fake_get_symbol_info(s):
        if 'GOLDm#' in s:
            return {'point': 0.01, 'volume_min': 0.1}
        return None
    monkeypatch.setattr(conn, 'get_symbol_info', fake_get_symbol_info)

    selected = conn.ensure_symbol_selected('GOLD')
    assert selected in ('GOLDm#', 'GOLDM') or 'GOLD' in selected

def test_find_matching_symbol_prefix_short_suffix():
    symbols = [_FakeSymbol('GOLDm#'), _FakeSymbol('GOLDX'), _FakeSymbol('GOLDMANSACHS')]
    import pytest

    m5.mt5.symbols_get = lambda: symbols
    conn = m5.MT5Connector.__new__(m5.MT5Connector)

    matches = conn._find_matching_symbol('GOLD')
    assert 'GOLDm#' in matches or 'GOLDM' in matches
    assert 'GOLDMANSACHS' not in matches
