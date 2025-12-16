import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from herald.execution.engine import ExecutionEngine, OrderRequest, OrderType, OrderStatus
from herald.position.manager import PositionInfo
from herald import constants


class TestExecutionEngine(unittest.TestCase):
    @patch('herald.execution.engine.mt5')
    def test_place_order_resolves_position_ticket(self, mock_mt5):
        # Mock MT5 result for order_send
        mock_result = MagicMock()
        mock_result.retcode = getattr(mock_mt5, 'TRADE_RETCODE_DONE', 10009)
        mock_result.price = 1.2345
        mock_result.volume = 0.1
        mock_result.order = 777
        mock_result.comment = 'done'

        mock_mt5.order_send.return_value = mock_result

        # Mock positions_get to return a matching position
        mock_pos = MagicMock()
        mock_pos.ticket = 888
        mock_pos.symbol = 'EURUSD'
        mock_pos.volume = 0.1
        mock_pos.magic = constants.DEFAULT_MAGIC
        mock_pos.time = datetime.now().timestamp()

        mock_mt5.positions_get.return_value = [mock_pos]

        # Setup a connector stub with required methods
        connector = MagicMock()
        connector.is_connected.return_value = True
        connector.get_symbol_info.return_value = {'ask': 1.2346, 'bid': 1.2344}
        connector.get_account_info.return_value = {'trade_allowed': True}

        engine = ExecutionEngine(connector=connector)

        order_req = OrderRequest(
            signal_id='s1',
            symbol='EURUSD',
            side='BUY',
            volume=0.1,
            order_type=OrderType.MARKET
        )

        result = engine.place_order(order_req)

        self.assertEqual(result.status, OrderStatus.FILLED)
        self.assertEqual(result.order_id, 777)
        self.assertEqual(result.position_ticket, 888)


if __name__ == '__main__':
    unittest.main()
