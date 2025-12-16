import unittest
from herald.config.wizard import parse_natural_language_intent


class TestNLPWizardParser(unittest.TestCase):
    def test_parse_basic_aggressive(self):
        txt = "Aggressive GOLD#m M15 H1, 2% risk, $100 max loss"
        intent = parse_natural_language_intent(txt)
        self.assertEqual(intent.get('mindset'), 'aggressive')
        self.assertIn('GOLD#m', intent.get('symbol', ''))
        self.assertEqual(intent.get('position_size_pct'), 2.0)
        self.assertEqual(intent.get('max_daily_loss'), 100.0)
        self.assertIn('TIMEFRAME_M15', intent.get('timeframes'))

    def test_parse_conservative_minfields(self):
        txt = "Conservative EURUSD 1m, 0.5% risk"
        intent = parse_natural_language_intent(txt)
        self.assertEqual(intent.get('mindset'), 'conservative')
        self.assertIn('EURUSD', intent.get('symbol', ''))
        self.assertEqual(intent.get('position_size_pct'), 0.5)
        self.assertIn('TIMEFRAME_M1', intent.get('timeframes'))

    def test_parse_defaults(self):
        txt = "Trade XAUUSD on H1"
        intent = parse_natural_language_intent(txt)
        self.assertIn('XAU', intent.get('symbol', ''))
        self.assertIn('TIMEFRAME_H1', intent.get('timeframes'))


if __name__ == '__main__':
    unittest.main()
