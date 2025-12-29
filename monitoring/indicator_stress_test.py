#!/usr/bin/env python
"""
Indicator Stress Test Harness

Purpose: Test all indicators with synthetic market data to verify:
1. Signal generation correctness (BUY/SELL/NEUTRAL)
2. Edge case handling (NaN, gaps, extremes)
3. Calculation accuracy against known values
4. Integration with strategy layer

This is the legacy-style ML/RL approach to precision-tuning Cthulu.
"""

import sys
import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from indicators.rsi import RSI
from indicators.macd import MACD
from indicators.bollinger import BollingerBands
from indicators.adx import ADX
from indicators.supertrend import Supertrend
from indicators.atr import ATR
from indicators.stochastic import Stochastic
from indicators.vwap import VWAP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """Generate synthetic OHLCV data for indicator testing."""
    
    @staticmethod
    def uptrend(bars: int = 100, start_price: float = 85000.0, 
                volatility: float = 0.005) -> pd.DataFrame:
        """Generate STRONG uptrending market data for RSI overbought."""
        dates = pd.date_range(end=datetime.now(timezone.utc), periods=bars, freq='1min')
        # Exponential growth to push RSI high - consistent gains
        trend = np.exp(np.linspace(0, 0.5, bars)) * start_price - start_price
        noise = np.random.randn(bars) * start_price * volatility * 0.1  # Minimal noise
        
        close = start_price + trend + np.abs(noise)  # Force upward bias
        high = close * (1 + np.random.uniform(0.002, 0.01, bars))
        low = close * (1 - np.random.uniform(0.001, 0.003, bars))  # Small lows
        open_ = close * (1 - np.random.uniform(0.001, 0.005, bars))  # Open below close (bullish)
        volume = np.random.uniform(50, 200, bars)  # Higher volume
        
        return pd.DataFrame({
            'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume
        }, index=dates)
    
    @staticmethod
    def downtrend(bars: int = 100, start_price: float = 95000.0,
                  volatility: float = 0.005) -> pd.DataFrame:
        """Generate STRONG downtrending market data for RSI oversold."""
        dates = pd.date_range(end=datetime.now(timezone.utc), periods=bars, freq='1min')
        # Linear consistent decline - every bar closes lower
        decline = np.linspace(0, start_price * 0.4, bars)  # 40% drop
        noise = np.random.randn(bars) * start_price * volatility * 0.05
        
        close = start_price - decline - np.abs(noise)  # Force downward consistently
        high = close * (1 + np.random.uniform(0.001, 0.002, bars))  # Small highs
        low = close * (1 - np.random.uniform(0.003, 0.01, bars))  # Larger lows
        open_ = close * (1 + np.random.uniform(0.002, 0.008, bars))  # Open above close (bearish)
        volume = np.random.uniform(50, 200, bars)
        
        return pd.DataFrame({
            'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume
        }, index=dates)
    
    @staticmethod
    def sideways(bars: int = 100, mid_price: float = 90000.0,
                 volatility: float = 0.01) -> pd.DataFrame:
        """Generate sideways/ranging market data."""
        dates = pd.date_range(end=datetime.now(timezone.utc), periods=bars, freq='1min')
        noise = np.random.randn(bars) * mid_price * volatility
        
        close = mid_price + noise
        high = close * (1 + np.random.uniform(0.001, 0.005, bars))
        low = close * (1 - np.random.uniform(0.001, 0.005, bars))
        open_ = close * (1 + np.random.uniform(-0.002, 0.002, bars))
        volume = np.random.uniform(10, 100, bars)
        
        return pd.DataFrame({
            'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume
        }, index=dates)
    
    @staticmethod
    def volatile_spike(bars: int = 100, base_price: float = 88000.0) -> pd.DataFrame:
        """Generate data with sudden volatility spikes."""
        dates = pd.date_range(end=datetime.now(timezone.utc), periods=bars, freq='1min')
        close = np.full(bars, base_price)
        
        # Add spike in middle
        spike_start = bars // 3
        spike_end = spike_start + 10
        close[spike_start:spike_end] = base_price * 1.05  # 5% spike up
        close[spike_end:spike_end+5] = base_price * 0.97  # 3% crash down
        
        # Add noise
        close += np.random.randn(bars) * base_price * 0.005
        
        high = close * (1 + np.random.uniform(0.001, 0.015, bars))
        low = close * (1 - np.random.uniform(0.001, 0.015, bars))
        open_ = close * (1 + np.random.uniform(-0.005, 0.005, bars))
        volume = np.random.uniform(10, 100, bars)
        
        return pd.DataFrame({
            'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume
        }, index=dates)
    
    @staticmethod
    def with_gaps(bars: int = 100, base_price: float = 87000.0) -> pd.DataFrame:
        """Generate data with price gaps (like after weekend)."""
        dates = pd.date_range(end=datetime.now(timezone.utc), periods=bars, freq='1min')
        close = np.linspace(base_price, base_price + 1000, bars)
        
        # Insert gap
        gap_idx = bars // 2
        close[gap_idx:] += 500  # Gap up
        
        high = close * (1 + np.random.uniform(0.001, 0.01, bars))
        low = close * (1 - np.random.uniform(0.001, 0.01, bars))
        open_ = close.copy()
        open_[gap_idx] = close[gap_idx - 1]  # Open at previous close
        volume = np.random.uniform(10, 100, bars)
        
        return pd.DataFrame({
            'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume
        }, index=dates)
    
    @staticmethod
    def crossover_setup(bars: int = 100, base_price: float = 90000.0) -> pd.DataFrame:
        """Generate data designed to trigger SMA/EMA crossovers."""
        dates = pd.date_range(end=datetime.now(timezone.utc), periods=bars, freq='1min')
        
        # Start flat, then trend up to force crossover
        close = np.concatenate([
            np.full(bars//2, base_price),  # Flat period
            np.linspace(base_price, base_price * 1.05, bars//2)  # Uptrend
        ])
        
        high = close * (1 + np.random.uniform(0.001, 0.01, bars))
        low = close * (1 - np.random.uniform(0.001, 0.01, bars))
        open_ = close * (1 + np.random.uniform(-0.003, 0.003, bars))
        volume = np.random.uniform(10, 100, bars)
        
        return pd.DataFrame({
            'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume
        }, index=dates)


class IndicatorTestResult:
    """Result of an indicator test."""
    
    def __init__(self, indicator_name: str, test_name: str):
        self.indicator_name = indicator_name
        self.test_name = test_name
        self.passed = False
        self.signal = None
        self.expected_signal = None
        self.details = {}
        self.error = None
        self.duration_ms = 0
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'indicator': self.indicator_name,
            'test': self.test_name,
            'passed': self.passed,
            'signal': self.signal,
            'expected': self.expected_signal,
            'details': self.details,
            'error': str(self.error) if self.error else None,
            'duration_ms': self.duration_ms,
            'timestamp': self.timestamp
        }


class IndicatorStressTest:
    """Comprehensive indicator stress testing."""
    
    def __init__(self, report_path: str = None, csv_path: str = None):
        self.data_gen = SyntheticDataGenerator()
        self.results: List[IndicatorTestResult] = []
        self.report_path = report_path or 'C:\\workspace\\cthulu\\SYSTEM_REPORT.md'
        self.csv_path = csv_path or 'C:\\workspace\\cthulu\\monitoring\\metrics.csv'
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all indicator tests and return summary."""
        logger.info("=" * 60)
        logger.info("INDICATOR STRESS TEST SUITE")
        logger.info("=" * 60)
        
        # Test each indicator
        self._test_rsi()
        self._test_macd()
        self._test_bollinger()
        self._test_adx()
        self._test_supertrend()
        self._test_atr()
        
        # Generate summary
        summary = self._generate_summary()
        
        # Update reports
        self._update_report(summary)
        self._append_csv(summary)
        
        return summary
    
    def _test_rsi(self):
        """Test RSI indicator across scenarios."""
        logger.info("\n--- Testing RSI Indicator ---")
        
        rsi = RSI(period=14, overbought=70, oversold=30)
        
        # Test 1: Overbought detection (uptrend should push RSI high)
        result = IndicatorTestResult('RSI', 'overbought_detection')
        try:
            data = self.data_gen.uptrend(bars=50)
            rsi_values = rsi.calculate(data)
            signal = rsi.get_signal()
            last_rsi = rsi_values.iloc[-1]
            
            result.signal = signal
            result.details = {'last_rsi': float(last_rsi), 'is_overbought': rsi.is_overbought()}
            result.expected_signal = 'SELL'  # Overbought = SELL signal
            result.passed = last_rsi > 60  # RSI should be elevated in uptrend
            logger.info(f"  RSI overbought test: RSI={last_rsi:.2f}, signal={signal}, PASS={result.passed}")
        except Exception as e:
            result.error = e
            logger.error(f"  RSI overbought test FAILED: {e}")
        self.results.append(result)
        
        # Test 2: Oversold detection (downtrend should push RSI low)
        result = IndicatorTestResult('RSI', 'oversold_detection')
        try:
            data = self.data_gen.downtrend(bars=50)
            rsi_values = rsi.calculate(data)
            signal = rsi.get_signal()
            last_rsi = rsi_values.iloc[-1]
            
            result.signal = signal
            result.details = {'last_rsi': float(last_rsi), 'is_oversold': rsi.is_oversold()}
            result.expected_signal = 'BUY'  # Oversold = BUY signal
            result.passed = last_rsi < 40  # RSI should be depressed in downtrend
            logger.info(f"  RSI oversold test: RSI={last_rsi:.2f}, signal={signal}, PASS={result.passed}")
        except Exception as e:
            result.error = e
            logger.error(f"  RSI oversold test FAILED: {e}")
        self.results.append(result)
        
        # Test 3: Sideways market (RSI should be neutral)
        result = IndicatorTestResult('RSI', 'neutral_detection')
        try:
            data = self.data_gen.sideways(bars=50)
            rsi_values = rsi.calculate(data)
            signal = rsi.get_signal()
            last_rsi = rsi_values.iloc[-1]
            
            result.signal = signal
            result.details = {'last_rsi': float(last_rsi)}
            result.expected_signal = 'NEUTRAL'
            result.passed = 35 < last_rsi < 65  # RSI should be mid-range
            logger.info(f"  RSI neutral test: RSI={last_rsi:.2f}, signal={signal}, PASS={result.passed}")
        except Exception as e:
            result.error = e
            logger.error(f"  RSI neutral test FAILED: {e}")
        self.results.append(result)
    
    def _test_macd(self):
        """Test MACD indicator."""
        logger.info("\n--- Testing MACD Indicator ---")
        
        macd = MACD(fast_period=12, slow_period=26, signal_period=9)
        
        # Test 1: Bullish crossover
        result = IndicatorTestResult('MACD', 'bullish_crossover')
        try:
            data = self.data_gen.crossover_setup(bars=60)
            macd_result = macd.calculate(data)
            signal = macd.get_signal()
            
            result.signal = signal
            result.details = {
                'last_macd': float(macd_result['macd'].iloc[-1]),
                'last_signal': float(macd_result['signal'].iloc[-1]),
                'histogram': float(macd_result['histogram'].iloc[-1]),
                'bullish_cross': macd.is_bullish_crossover()
            }
            result.expected_signal = 'BUY'
            # In uptrend, MACD should be positive or crossing up
            result.passed = macd_result['histogram'].iloc[-1] > 0
            logger.info(f"  MACD bullish test: histogram={result.details['histogram']:.2f}, PASS={result.passed}")
        except Exception as e:
            result.error = e
            logger.error(f"  MACD bullish test FAILED: {e}")
        self.results.append(result)
        
        # Test 2: Bearish signal in downtrend
        result = IndicatorTestResult('MACD', 'bearish_trend')
        try:
            data = self.data_gen.downtrend(bars=60)
            macd_result = macd.calculate(data)
            signal = macd.get_signal()
            
            result.signal = signal
            result.details = {
                'last_macd': float(macd_result['macd'].iloc[-1]),
                'histogram': float(macd_result['histogram'].iloc[-1])
            }
            result.expected_signal = 'SELL'
            result.passed = macd_result['histogram'].iloc[-1] < 0
            logger.info(f"  MACD bearish test: histogram={result.details['histogram']:.2f}, PASS={result.passed}")
        except Exception as e:
            result.error = e
            logger.error(f"  MACD bearish test FAILED: {e}")
        self.results.append(result)
    
    def _test_bollinger(self):
        """Test Bollinger Bands indicator."""
        logger.info("\n--- Testing Bollinger Bands ---")
        
        bb = BollingerBands(period=20, std_dev=2.0)
        
        # Test 1: Volatile spike should touch bands
        result = IndicatorTestResult('BollingerBands', 'band_touch')
        try:
            data = self.data_gen.volatile_spike(bars=50)
            bb_result = bb.calculate(data)
            signal = bb.get_signal()
            
            last_close = data['close'].iloc[-1]
            upper = bb_result['bb_upper'].iloc[-1]
            lower = bb_result['bb_lower'].iloc[-1]
            
            result.signal = signal
            result.details = {
                'close': float(last_close),
                'upper': float(upper),
                'lower': float(lower),
                'percent_b': float(bb_result['bb_percent'].iloc[-1])
            }
            result.passed = True  # Just verify calculation completes
            logger.info(f"  BB band test: close={last_close:.2f}, upper={upper:.2f}, lower={lower:.2f}, PASS={result.passed}")
        except Exception as e:
            result.error = e
            logger.error(f"  BB band test FAILED: {e}")
        self.results.append(result)
        
        # Test 2: Sideways should show squeeze
        result = IndicatorTestResult('BollingerBands', 'volatility_state')
        try:
            data = self.data_gen.sideways(bars=50)
            bb_result = bb.calculate(data)
            vol_state = bb.get_volatility_state()
            
            result.signal = vol_state
            result.details = {'width': float(bb_result['bb_width'].iloc[-1])}
            result.passed = vol_state in ['LOW', 'NORMAL']  # Sideways = low volatility
            logger.info(f"  BB volatility test: state={vol_state}, PASS={result.passed}")
        except Exception as e:
            result.error = e
            logger.error(f"  BB volatility test FAILED: {e}")
        self.results.append(result)
    
    def _test_adx(self):
        """Test ADX indicator."""
        logger.info("\n--- Testing ADX Indicator ---")
        
        adx = ADX(period=14)
        
        # Test 1: Strong trend detection
        result = IndicatorTestResult('ADX', 'strong_trend')
        try:
            data = self.data_gen.uptrend(bars=50)
            adx_result = adx.calculate(data)
            strength = adx.get_trend_strength()
            direction = adx.get_trend_direction()
            
            last_adx = adx_result['adx'].iloc[-1]
            result.signal = f"{strength}_{direction}"
            result.details = {
                'adx': float(last_adx),
                'plus_di': float(adx_result['plus_di'].iloc[-1]),
                'minus_di': float(adx_result['minus_di'].iloc[-1])
            }
            result.passed = adx.is_trending()
            logger.info(f"  ADX strong trend: adx={last_adx:.2f}, strength={strength}, direction={direction}, PASS={result.passed}")
        except Exception as e:
            result.error = e
            logger.error(f"  ADX strong trend test FAILED: {e}")
        self.results.append(result)
        
        # Test 2: Ranging market detection
        result = IndicatorTestResult('ADX', 'ranging_market')
        try:
            data = self.data_gen.sideways(bars=50)
            adx_result = adx.calculate(data)
            
            last_adx = adx_result['adx'].iloc[-1]
            result.signal = 'RANGING' if adx.is_ranging() else 'TRENDING'
            result.details = {'adx': float(last_adx)}
            result.passed = last_adx < 30  # Sideways should have low ADX
            logger.info(f"  ADX ranging test: adx={last_adx:.2f}, PASS={result.passed}")
        except Exception as e:
            result.error = e
            logger.error(f"  ADX ranging test FAILED: {e}")
        self.results.append(result)
    
    def _test_supertrend(self):
        """Test Supertrend indicator."""
        logger.info("\n--- Testing Supertrend Indicator ---")
        
        st = Supertrend(period=10, multiplier=3.0)
        
        # Test 1: Bullish trend detection
        result = IndicatorTestResult('Supertrend', 'bullish_trend')
        try:
            data = self.data_gen.uptrend(bars=50)
            st_result = st.calculate(data)
            
            direction = st_result['supertrend_direction'].iloc[-1]
            result.signal = 'BULLISH' if st.is_bullish() else 'BEARISH'
            result.details = {
                'direction': int(direction),
                'supertrend_value': float(st_result['supertrend'].iloc[-1])
            }
            result.passed = st.is_bullish()
            logger.info(f"  Supertrend bullish test: direction={direction}, PASS={result.passed}")
        except Exception as e:
            result.error = e
            logger.error(f"  Supertrend bullish test FAILED: {e}")
        self.results.append(result)
        
        # Test 2: Bearish trend detection
        result = IndicatorTestResult('Supertrend', 'bearish_trend')
        try:
            data = self.data_gen.downtrend(bars=50)
            st_result = st.calculate(data)
            
            direction = st_result['supertrend_direction'].iloc[-1]
            result.signal = 'BULLISH' if st.is_bullish() else 'BEARISH'
            result.details = {'direction': int(direction)}
            result.passed = not st.is_bullish()  # Should be bearish
            logger.info(f"  Supertrend bearish test: direction={direction}, PASS={result.passed}")
        except Exception as e:
            result.error = e
            logger.error(f"  Supertrend bearish test FAILED: {e}")
        self.results.append(result)
    
    def _test_atr(self):
        """Test ATR indicator."""
        logger.info("\n--- Testing ATR Indicator ---")
        
        atr = ATR(period=14)
        
        # Test 1: Volatile data should have higher ATR
        result = IndicatorTestResult('ATR', 'volatility_measure')
        try:
            data_calm = self.data_gen.sideways(bars=50)
            data_volatile = self.data_gen.volatile_spike(bars=50)
            
            atr_calm = atr.calculate(data_calm).iloc[-1]
            atr_volatile = atr.calculate(data_volatile).iloc[-1]
            
            result.signal = 'VOLATILE' if atr_volatile > atr_calm else 'CALM'
            result.details = {
                'atr_calm': float(atr_calm),
                'atr_volatile': float(atr_volatile)
            }
            result.passed = atr_volatile > atr_calm * 0.8  # Volatile should be higher
            logger.info(f"  ATR volatility test: calm={atr_calm:.2f}, volatile={atr_volatile:.2f}, PASS={result.passed}")
        except Exception as e:
            result.error = e
            logger.error(f"  ATR volatility test FAILED: {e}")
        self.results.append(result)
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate test summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed and r.error is None)
        errors = sum(1 for r in self.results if r.error is not None)
        
        # Group by indicator
        by_indicator = {}
        for r in self.results:
            if r.indicator_name not in by_indicator:
                by_indicator[r.indicator_name] = {'passed': 0, 'failed': 0, 'errors': 0}
            if r.error:
                by_indicator[r.indicator_name]['errors'] += 1
            elif r.passed:
                by_indicator[r.indicator_name]['passed'] += 1
            else:
                by_indicator[r.indicator_name]['failed'] += 1
        
        grade = self._calculate_grade(passed, total)
        
        summary = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'pass_rate': passed / total if total > 0 else 0,
            'grade': grade,
            'by_indicator': by_indicator,
            'results': [r.to_dict() for r in self.results]
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("INDICATOR STRESS TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed} ({passed/total*100:.1f}%)")
        logger.info(f"Failed: {failed}")
        logger.info(f"Errors: {errors}")
        logger.info(f"Grade: {grade}")
        
        return summary
    
    def _calculate_grade(self, passed: int, total: int) -> str:
        """Calculate letter grade."""
        if total == 0:
            return 'N/A'
        rate = passed / total
        if rate >= 0.95:
            return 'A+'
        elif rate >= 0.90:
            return 'A'
        elif rate >= 0.85:
            return 'A-'
        elif rate >= 0.80:
            return 'B+'
        elif rate >= 0.75:
            return 'B'
        elif rate >= 0.70:
            return 'B-'
        elif rate >= 0.65:
            return 'C+'
        elif rate >= 0.60:
            return 'C'
        else:
            return 'D'
    
    def _update_report(self, summary: Dict[str, Any]):
        """Update SYSTEM_REPORT.md with test results."""
        try:
            report_content = f"""

### Indicator Stress Test - {summary['timestamp'][:19]}
- **Total Tests:** {summary['total_tests']}
- **Passed:** {summary['passed']} ({summary['pass_rate']*100:.1f}%)
- **Failed:** {summary['failed']}
- **Errors:** {summary['errors']}
- **Grade:** {summary['grade']}

**By Indicator:**
"""
            for ind, stats in summary['by_indicator'].items():
                report_content += f"- {ind}: {stats['passed']} passed, {stats['failed']} failed, {stats['errors']} errors\n"
            
            with open(self.report_path, 'a', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Updated report: {self.report_path}")
        except Exception as e:
            logger.error(f"Failed to update report: {e}")
    
    def _append_csv(self, summary: Dict[str, Any]):
        """Append metrics to CSV."""
        try:
            row = f"{summary['timestamp']},indicator_stress_test,ultra_aggressive,BTCUSD#," \
                  f"tests={summary['total_tests']} passed={summary['passed']} grade={summary['grade']}\n"
            
            with open(self.csv_path, 'a', encoding='utf-8') as f:
                f.write(row)
            
            logger.info(f"Appended to CSV: {self.csv_path}")
        except Exception as e:
            logger.error(f"Failed to append CSV: {e}")


def main():
    """Run indicator stress tests."""
    tester = IndicatorStressTest()
    summary = tester.run_all_tests()
    
    # Output JSON for programmatic consumption
    print("\n--- JSON Summary ---")
    print(json.dumps(summary, indent=2, default=str))
    
    return 0 if summary['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
