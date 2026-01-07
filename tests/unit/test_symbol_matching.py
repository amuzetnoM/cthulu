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


def test_find_matching_symbol_prefix_short_suffix():
    symbols = [_FakeSymbol('GOLDm#'), _FakeSymbol('GOLDX'), _FakeSymbol('GOLDMANSACHS')]
    import pytest

    m5.mt5.symbols_get = lambda: symbols
    conn = m5.MT5Connector.__new__(m5.MT5Connector)

    matches = conn._find_matching_symbol('GOLD')
    assert 'GOLDm#' in matches or 'GOLDM' in matches
    assert 'GOLDMANSACHS' not in matches
