#!/usr/bin/env python3
"""Signal injection / stress tool for Cthulu RPC.

ENHANCED VERSION - Realistic Market Simulation

Usage examples:
  python monitoring/inject_signals.py --mode burst --count 100 --rate 5 --symbol BTCUSD#
  python monitoring/inject_signals.py --mode pattern --pattern "BUY,SELL,BUY" --repeat 50
  python monitoring/inject_signals.py --mode realistic --duration 120 --intensity medium
  python monitoring/inject_signals.py --mode indicator --indicator rsi_divergence --count 20

This script uses the Cthulu RPC POST /trade endpoint (default http://127.0.0.1:8278/trade).
"""
from __future__ import annotations
import argparse
import json
import random
import time
import urllib.request
import urllib.error
import os
import sqlite3
import math
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional

def get_utc_now():
    return datetime.now(timezone.utc)

def post_trade(url, payload, token=None, timeout=5.0):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8'), resp.status
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8'), e.code
    except Exception as e:
        return str(e), None


# Fallback: when RPC is unreachable, simulate trade by writing to DB and appending logs
def simulate_local_trade(cthulu_dir: str, payload: dict):
    """Simulate a trade by inserting records into the local SQLite DB and appending log lines.
    This allows stress-testing when the RPC server is not available.
    """
    import sqlite3
    import random
    from datetime import datetime
    db_path = os.path.join(cthulu_dir, 'Cthulu.db')
    log_path = os.path.join(cthulu_dir, 'logs', 'cthulu.log')

    # Create synthetic identifiers and prices
    ts = get_utc_now().isoformat()
    signal_id = f"inject_{int(time.time())}_{random.randint(1000,9999)}"
    fill_price = round(100.0 + random.random() * 1000.0, 5)
    ticket = random.randint(500000000, 999999999)

    # Append log lines to simulate the flow
    lines = [
        f"{ts} [INFO] Signal generated: {'LONG' if payload.get('side')=='BUY' else 'SHORT'} {payload.get('symbol')} (confidence: 0.85)",
        f"{ts} [INFO] Risk approved: {payload.get('volume')} lots - Trade approved",
        f"{ts} [INFO] Placing {payload.get('side')} order for {payload.get('volume')} lots",
        f"{ts} [INFO] Placing MARKET order: {payload.get('side')} {payload.get('volume')} {payload.get('symbol')}",
        f"{ts} [INFO] Order executed: Ticket #{ticket} | Price: {fill_price:.5f} | Volume: {payload.get('volume')}",
        f"{ts} [INFO] Order filled: ticket={ticket}, price={fill_price:.5f}"
    ]
    try:
        with open(log_path, 'a', encoding='utf-8') as fh:
            for l in lines:
                fh.write(l + '\n')
    except Exception:
        pass

    # Insert into the DB tables if possible
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cur = conn.cursor()
        now = get_utc_now().isoformat()
        # Insert a minimal signal row
        try:
            cur.execute("INSERT OR IGNORE INTO signals (signal_id, timestamp, symbol, timeframe, side, action, confidence, price, stop_loss, take_profit, reason, executed, execution_timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (signal_id, now, payload.get('symbol','UNKNOWN'), payload.get('timeframe','TIMEFRAME_M1'), 'BUY' if payload.get('side')=='BUY' else 'SELL', 'market', 0.85, fill_price, None, None, 'injected', True, now, json.dumps(payload)))
        except Exception:
            # table schema may be different; ignore
            pass
        # Insert a trade record
        try:
            cur.execute("INSERT INTO trades (signal_id, order_id, symbol, side, volume, entry_price, entry_time, status, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (signal_id, ticket, payload.get('symbol','UNKNOWN'), 'BUY' if payload.get('side')=='BUY' else 'SELL', payload.get('volume', 0.01), fill_price, now, 'OPEN', json.dumps({'injected': True})))
        except Exception:
            pass
        conn.commit()
        conn.close()
    except Exception:
        pass

    return {'simulated': True, 'signal_id': signal_id, 'ticket': ticket, 'price': fill_price}


INJECT_LOG = os.path.join(os.path.dirname(__file__), '..', 'logs', 'inject.log')

def log_inject(msg):
    ts = get_utc_now().isoformat()
    line = f"{ts} [INJECT] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(INJECT_LOG), exist_ok=True)
        with open(INJECT_LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass

def burst_mode(url, count=100, rate=5, symbol='BTCUSD#', token=None, simulate_dir='.'):
    delay = 1.0 / rate if rate > 0 else 0
    results = {'ok': 0, 'rejected': 0, 'errors': 0, 'simulated': 0}
    log_inject(f"Burst start: count={count} rate={rate} symbol={symbol}")
    for i in range(count):
        side = random.choice(['BUY', 'SELL'])
        volume = round(random.uniform(0.01, 0.2), 4)
        payload = {'symbol': symbol, 'side': side, 'volume': volume}
        body, status = post_trade(url, payload, token)
        if status == 200:
            results['ok'] += 1
            log_inject(f"#{i+1} {side} {volume} -> OK")
        elif status == 403:
            results['rejected'] += 1
            log_inject(f"#{i+1} {side} {volume} -> REJECTED (risk)")
        elif status is None:
            # RPC unreachable -> fallback to local simulation
            sim = simulate_local_trade(simulate_dir, payload)
            results['simulated'] += 1
            log_inject(f"#{i+1} {side} {volume} -> SIMULATED (RPC down)")
        else:
            results['errors'] += 1
            log_inject(f"#{i+1} {side} {volume} -> ERROR status={status}")
        if delay:
            time.sleep(delay)
    log_inject(f"Burst complete: {results}")
    return results


def pattern_mode(url, pattern: str, repeat: int, symbol='BTCUSD#', token=None, simulate_dir='.'):
    seq = [p.strip().upper() for p in pattern.split(',') if p.strip()]
    results = {'ok': 0, 'rejected': 0, 'errors': 0, 'simulated': 0}
    log_inject(f"Pattern start: pattern={pattern} repeat={repeat} symbol={symbol}")
    for r in range(repeat):
        for idx, p in enumerate(seq):
            if p not in ('BUY', 'SELL'):
                continue
            payload = {'symbol': symbol, 'side': p, 'volume': 0.01}
            body, status = post_trade(url, payload, token)
            if status == 200:
                results['ok'] += 1
                log_inject(f"R{r+1}/{idx+1} {p} 0.01 -> OK")
            elif status == 403:
                results['rejected'] += 1
                log_inject(f"R{r+1}/{idx+1} {p} 0.01 -> REJECTED")
            elif status is None:
                sim = simulate_local_trade(simulate_dir, payload)
                results['simulated'] += 1
                log_inject(f"R{r+1}/{idx+1} {p} 0.01 -> SIMULATED")
            else:
                results['errors'] += 1
                log_inject(f"R{r+1}/{idx+1} {p} 0.01 -> ERROR {status}")
            time.sleep(0.2)
    log_inject(f"Pattern complete: {results}")
    return results


def manual_order(url, side, volume, symbol='BTCUSD#', token=None):
    payload = {'symbol': symbol, 'side': side, 'volume': volume}
    log_inject(f"Manual order: {side} {volume} {symbol}")
    return post_trade(url, payload, token)


# =============================================================================
# REALISTIC MARKET SIMULATION MODE
# =============================================================================

class MarketCondition(Enum):
    """Simulated market conditions for realistic testing."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    LIQUIDITY_TRAP = "liquidity_trap"
    NEWS_EVENT = "news_event"


def get_market_phase(elapsed_minutes: float, total_minutes: float) -> MarketCondition:
    """
    Simulate changing market conditions over time.
    Creates a realistic progression through different market phases.
    """
    phase_pct = elapsed_minutes / total_minutes
    
    # Simulate a realistic trading session with phases
    if phase_pct < 0.1:
        return MarketCondition.RANGING  # Session start - quiet
    elif phase_pct < 0.2:
        return MarketCondition.TRENDING_UP  # Early momentum
    elif phase_pct < 0.3:
        return MarketCondition.HIGH_VOLATILITY  # Volatility spike
    elif phase_pct < 0.4:
        return MarketCondition.LIQUIDITY_TRAP  # Stop hunt
    elif phase_pct < 0.5:
        return MarketCondition.TRENDING_DOWN  # Reversal
    elif phase_pct < 0.6:
        return MarketCondition.RANGING  # Consolidation
    elif phase_pct < 0.7:
        return MarketCondition.NEWS_EVENT  # Simulated news
    elif phase_pct < 0.8:
        return MarketCondition.HIGH_VOLATILITY  # Post-news volatility
    elif phase_pct < 0.9:
        return MarketCondition.TRENDING_UP  # Trend continuation
    else:
        return MarketCondition.LOW_VOLATILITY  # Session wind-down


def get_signal_params_for_condition(condition: MarketCondition, symbol: str) -> Dict[str, Any]:
    """
    Generate realistic signal parameters based on market condition.
    
    Returns parameters that mimic what a real strategy would generate.
    """
    base_params = {
        'symbol': symbol,
        'volume': 0.01,
        'confidence': 0.5,
    }
    
    if condition == MarketCondition.TRENDING_UP:
        return {
            **base_params,
            'side': 'BUY',
            'volume': round(random.uniform(0.02, 0.05), 2),
            'confidence': round(random.uniform(0.65, 0.85), 2),
        }
    elif condition == MarketCondition.TRENDING_DOWN:
        return {
            **base_params,
            'side': 'SELL',
            'volume': round(random.uniform(0.02, 0.05), 2),
            'confidence': round(random.uniform(0.65, 0.85), 2),
        }
    elif condition == MarketCondition.RANGING:
        # Mean reversion signals in ranging markets
        side = random.choice(['BUY', 'SELL'])
        return {
            **base_params,
            'side': side,
            'volume': round(random.uniform(0.01, 0.02), 2),
            'confidence': round(random.uniform(0.40, 0.55), 2),
        }
    elif condition == MarketCondition.HIGH_VOLATILITY:
        # Smaller positions in volatility
        side = random.choice(['BUY', 'SELL'])
        return {
            **base_params,
            'side': side,
            'volume': round(random.uniform(0.01, 0.02), 2),
            'confidence': round(random.uniform(0.35, 0.50), 2),
        }
    elif condition == MarketCondition.LOW_VOLATILITY:
        # Skip most signals in low vol
        if random.random() > 0.3:
            return None  # No signal
        return {
            **base_params,
            'side': random.choice(['BUY', 'SELL']),
            'volume': 0.01,
            'confidence': round(random.uniform(0.30, 0.45), 2),
        }
    elif condition == MarketCondition.LIQUIDITY_TRAP:
        # Generate trap signals (these should be rejected by good risk management)
        # Spike in one direction then reverse
        return {
            **base_params,
            'side': random.choice(['BUY', 'SELL']),
            'volume': round(random.uniform(0.03, 0.08), 2),  # Larger volume trap
            'confidence': round(random.uniform(0.55, 0.70), 2),  # Looks confident
            'trap_signal': True,  # Internal marker
        }
    elif condition == MarketCondition.NEWS_EVENT:
        # High confidence directional move
        return {
            **base_params,
            'side': random.choice(['BUY', 'SELL']),
            'volume': round(random.uniform(0.02, 0.04), 2),
            'confidence': round(random.uniform(0.70, 0.90), 2),
        }
    
    return base_params


def realistic_mode(url: str, duration_minutes: int = 120, intensity: str = 'medium',
                   symbol: str = 'BTCUSD#', token: Optional[str] = None,
                   simulate_dir: str = '.') -> Dict[str, Any]:
    """
    Run realistic market simulation for specified duration.
    
    Args:
        url: RPC endpoint
        duration_minutes: How long to run (default 120 = 2 hours)
        intensity: 'low', 'medium', 'high' - affects signal frequency
        symbol: Trading symbol
        token: Auth token
        simulate_dir: Directory for local simulation fallback
        
    Returns:
        Results summary
    """
    # Signal intervals based on intensity
    intervals = {
        'low': (60, 180),      # 1-3 minutes between signals
        'medium': (30, 90),    # 30-90 seconds between signals
        'high': (10, 30),      # 10-30 seconds between signals
    }
    min_interval, max_interval = intervals.get(intensity, intervals['medium'])
    
    results = {
        'ok': 0, 'rejected': 0, 'errors': 0, 'simulated': 0, 'skipped': 0,
        'by_condition': {},
        'start_time': get_utc_now().isoformat(),
        'duration_minutes': duration_minutes,
    }
    
    log_inject(f"=== REALISTIC MODE START ===")
    log_inject(f"Duration: {duration_minutes} min, Intensity: {intensity}, Symbol: {symbol}")
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    signal_count = 0
    
    while time.time() < end_time:
        elapsed_minutes = (time.time() - start_time) / 60
        remaining_minutes = duration_minutes - elapsed_minutes
        
        # Get current market condition
        condition = get_market_phase(elapsed_minutes, duration_minutes)
        
        # Initialize condition counter
        if condition.value not in results['by_condition']:
            results['by_condition'][condition.value] = {'ok': 0, 'rejected': 0, 'skipped': 0}
        
        # Get signal parameters for this condition
        params = get_signal_params_for_condition(condition, symbol)
        
        if params is None:
            results['skipped'] += 1
            results['by_condition'][condition.value]['skipped'] += 1
            log_inject(f"[{condition.value}] Signal skipped (low vol filter)")
        else:
            signal_count += 1
            payload = {
                'symbol': params['symbol'],
                'side': params['side'],
                'volume': params['volume'],
            }
            
            body, status = post_trade(url, payload, token)
            
            if status == 200:
                results['ok'] += 1
                results['by_condition'][condition.value]['ok'] += 1
                log_inject(f"[{condition.value}] #{signal_count} {params['side']} {params['volume']} conf={params['confidence']:.2f} -> OK")
            elif status == 403:
                results['rejected'] += 1
                results['by_condition'][condition.value]['rejected'] += 1
                log_inject(f"[{condition.value}] #{signal_count} {params['side']} {params['volume']} conf={params['confidence']:.2f} -> REJECTED (risk)")
            elif status is None:
                sim = simulate_local_trade(simulate_dir, payload)
                results['simulated'] += 1
                log_inject(f"[{condition.value}] #{signal_count} {params['side']} {params['volume']} -> SIMULATED (RPC down)")
            else:
                results['errors'] += 1
                log_inject(f"[{condition.value}] #{signal_count} {params['side']} {params['volume']} -> ERROR {status}")
        
        # Progress report every 10 minutes
        if int(elapsed_minutes) % 10 == 0 and int(elapsed_minutes) > 0:
            log_inject(f"=== PROGRESS: {elapsed_minutes:.0f}/{duration_minutes} min, {signal_count} signals, {results['ok']} OK, {results['rejected']} rejected ===")
        
        # Wait for next signal (variable interval based on market condition)
        if condition in [MarketCondition.HIGH_VOLATILITY, MarketCondition.NEWS_EVENT]:
            # Faster signals in volatile conditions
            wait = random.uniform(min_interval * 0.5, max_interval * 0.5)
        elif condition == MarketCondition.LOW_VOLATILITY:
            # Slower signals in quiet markets
            wait = random.uniform(min_interval * 2, max_interval * 2)
        else:
            wait = random.uniform(min_interval, max_interval)
        
        time.sleep(wait)
    
    results['end_time'] = get_utc_now().isoformat()
    results['total_signals'] = signal_count
    
    log_inject(f"=== REALISTIC MODE COMPLETE ===")
    log_inject(f"Total signals: {signal_count}")
    log_inject(f"Results: OK={results['ok']}, Rejected={results['rejected']}, Errors={results['errors']}, Skipped={results['skipped']}")
    log_inject(f"By condition: {json.dumps(results['by_condition'], indent=2)}")
    
    return results


# =============================================================================
# INDICATOR SIGNAL INJECTION MODE
# =============================================================================

INDICATOR_SIGNALS = {
    'rsi_oversold': {
        'description': 'RSI below 30 - oversold bounce signal',
        'side': 'BUY',
        'confidence_range': (0.60, 0.75),
        'volume_range': (0.01, 0.03),
    },
    'rsi_overbought': {
        'description': 'RSI above 70 - overbought reversal signal',
        'side': 'SELL',
        'confidence_range': (0.60, 0.75),
        'volume_range': (0.01, 0.03),
    },
    'rsi_divergence': {
        'description': 'RSI divergence - trend reversal signal',
        'side': lambda: random.choice(['BUY', 'SELL']),
        'confidence_range': (0.70, 0.85),
        'volume_range': (0.02, 0.04),
    },
    'macd_crossover_bull': {
        'description': 'MACD bullish crossover',
        'side': 'BUY',
        'confidence_range': (0.55, 0.70),
        'volume_range': (0.01, 0.03),
    },
    'macd_crossover_bear': {
        'description': 'MACD bearish crossover',
        'side': 'SELL',
        'confidence_range': (0.55, 0.70),
        'volume_range': (0.01, 0.03),
    },
    'bollinger_squeeze': {
        'description': 'Bollinger band squeeze breakout',
        'side': lambda: random.choice(['BUY', 'SELL']),
        'confidence_range': (0.65, 0.80),
        'volume_range': (0.02, 0.04),
    },
    'ema_crossover': {
        'description': 'EMA crossover signal',
        'side': lambda: random.choice(['BUY', 'SELL']),
        'confidence_range': (0.50, 0.65),
        'volume_range': (0.01, 0.02),
    },
    'adx_strong_trend': {
        'description': 'ADX above 25 - strong trend continuation',
        'side': lambda: random.choice(['BUY', 'SELL']),
        'confidence_range': (0.60, 0.75),
        'volume_range': (0.02, 0.04),
    },
    'supertrend_flip': {
        'description': 'Supertrend indicator flip',
        'side': lambda: random.choice(['BUY', 'SELL']),
        'confidence_range': (0.55, 0.70),
        'volume_range': (0.01, 0.03),
    },
    'vwap_bounce': {
        'description': 'VWAP support/resistance bounce',
        'side': lambda: random.choice(['BUY', 'SELL']),
        'confidence_range': (0.50, 0.65),
        'volume_range': (0.01, 0.02),
    },
    'momentum_breakout': {
        'description': 'Momentum breakout with volume',
        'side': lambda: random.choice(['BUY', 'SELL']),
        'confidence_range': (0.70, 0.85),
        'volume_range': (0.03, 0.06),
    },
    'scalp_quick': {
        'description': 'Quick scalping signal',
        'side': lambda: random.choice(['BUY', 'SELL']),
        'confidence_range': (0.45, 0.55),
        'volume_range': (0.01, 0.01),
    },
}


def indicator_mode(url: str, indicator: str, count: int = 20, symbol: str = 'BTCUSD#',
                   token: Optional[str] = None, simulate_dir: str = '.') -> Dict[str, Any]:
    """
    Inject signals mimicking a specific indicator type.
    
    Args:
        url: RPC endpoint
        indicator: Indicator type from INDICATOR_SIGNALS
        count: Number of signals to inject
        symbol: Trading symbol
        token: Auth token
        simulate_dir: Fallback directory
        
    Returns:
        Results summary
    """
    if indicator not in INDICATOR_SIGNALS:
        available = ', '.join(INDICATOR_SIGNALS.keys())
        log_inject(f"Unknown indicator '{indicator}'. Available: {available}")
        return {'error': f'Unknown indicator. Available: {available}'}
    
    spec = INDICATOR_SIGNALS[indicator]
    results = {'ok': 0, 'rejected': 0, 'errors': 0, 'simulated': 0}
    
    log_inject(f"=== INDICATOR MODE: {indicator} ===")
    log_inject(f"Description: {spec['description']}")
    log_inject(f"Count: {count}, Symbol: {symbol}")
    
    for i in range(count):
        # Determine side
        side = spec['side']
        if callable(side):
            side = side()
        
        # Generate parameters
        conf_min, conf_max = spec['confidence_range']
        vol_min, vol_max = spec['volume_range']
        
        confidence = round(random.uniform(conf_min, conf_max), 2)
        volume = round(random.uniform(vol_min, vol_max), 2)
        
        payload = {
            'symbol': symbol,
            'side': side,
            'volume': volume,
        }
        
        body, status = post_trade(url, payload, token)
        
        if status == 200:
            results['ok'] += 1
            log_inject(f"[{indicator}] #{i+1} {side} {volume} conf={confidence} -> OK")
        elif status == 403:
            results['rejected'] += 1
            log_inject(f"[{indicator}] #{i+1} {side} {volume} conf={confidence} -> REJECTED")
        elif status is None:
            sim = simulate_local_trade(simulate_dir, payload)
            results['simulated'] += 1
            log_inject(f"[{indicator}] #{i+1} {side} {volume} -> SIMULATED")
        else:
            results['errors'] += 1
            log_inject(f"[{indicator}] #{i+1} {side} {volume} -> ERROR {status}")
        
        # Variable delay based on indicator type
        if 'scalp' in indicator:
            time.sleep(random.uniform(2, 5))
        else:
            time.sleep(random.uniform(5, 15))
    
    log_inject(f"=== INDICATOR MODE COMPLETE: {results} ===")
    return results


def main():
    parser = argparse.ArgumentParser(description='Cthulu Signal Injection Tool')
    parser.add_argument('--rpc-url', default='http://127.0.0.1:8278/trade')
    parser.add_argument('--token', default=None)
    parser.add_argument('--mode', choices=['burst', 'pattern', 'manual', 'realistic', 'indicator'], default='burst')
    parser.add_argument('--count', type=int, default=100)
    parser.add_argument('--rate', type=float, default=5.0)
    parser.add_argument('--symbol', default='BTCUSD#')
    parser.add_argument('--pattern', default='BUY,SELL')
    parser.add_argument('--repeat', type=int, default=10)
    parser.add_argument('--side', choices=['BUY', 'SELL'])
    parser.add_argument('--volume', type=float, default=0.01)
    # New arguments for enhanced modes
    parser.add_argument('--duration', type=int, default=120, help='Duration in minutes for realistic mode')
    parser.add_argument('--intensity', choices=['low', 'medium', 'high'], default='medium', help='Signal frequency for realistic mode')
    parser.add_argument('--indicator', default='rsi_divergence', help='Indicator type for indicator mode')
    args = parser.parse_args()

    if args.mode == 'burst':
        print(f"Starting burst: count={args.count}, rate={args.rate}, symbol={args.symbol}")
        r = burst_mode(args.rpc_url, args.count, args.rate, args.symbol, args.token, simulate_dir='.')
        print('Done:', r)
    elif args.mode == 'pattern':
        print(f"Starting pattern: pattern={args.pattern}, repeat={args.repeat}")
        r = pattern_mode(args.rpc_url, args.pattern, args.repeat, args.symbol, args.token, simulate_dir='.')
        print('Done:', r)
    elif args.mode == 'realistic':
        print(f"Starting realistic simulation: duration={args.duration}min, intensity={args.intensity}")
        r = realistic_mode(args.rpc_url, args.duration, args.intensity, args.symbol, args.token, simulate_dir='.')
        print('Done:', r)
    elif args.mode == 'indicator':
        print(f"Starting indicator injection: indicator={args.indicator}, count={args.count}")
        r = indicator_mode(args.rpc_url, args.indicator, args.count, args.symbol, args.token, simulate_dir='.')
        print('Done:', r)
    else:
        body, status = manual_order(args.rpc_url, args.side, args.volume, args.symbol, args.token)
        print('Response:', status, body)


if __name__ == '__main__':
    main()
