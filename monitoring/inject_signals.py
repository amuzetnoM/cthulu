#!/usr/bin/env python3
"""Signal injection / stress tool for Cthulu RPC.

Usage examples:
  python monitoring/inject_signals.py --mode burst --count 100 --rate 5 --symbol BTCUSD#
  python monitoring/inject_signals.py --mode pattern --pattern "BUY,SELL,BUY" --repeat 50

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
from datetime import datetime, timezone

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rpc-url', default='http://127.0.0.1:8278/trade')
    parser.add_argument('--token', default=None)
    parser.add_argument('--mode', choices=['burst', 'pattern', 'manual'], default='burst')
    parser.add_argument('--count', type=int, default=100)
    parser.add_argument('--rate', type=float, default=5.0)
    parser.add_argument('--symbol', default='BTCUSD#')
    parser.add_argument('--pattern', default='BUY,SELL')
    parser.add_argument('--repeat', type=int, default=10)
    parser.add_argument('--side', choices=['BUY', 'SELL'])
    parser.add_argument('--volume', type=float, default=0.01)
    args = parser.parse_args()

    if args.mode == 'burst':
        print(f"Starting burst: count={args.count}, rate={args.rate}, symbol={args.symbol}")
        r = burst_mode(args.rpc_url, args.count, args.rate, args.symbol, args.token, simulate_dir='.')
        print('Done:', r)
    elif args.mode == 'pattern':
        print(f"Starting pattern: pattern={args.pattern}, repeat={args.repeat}")
        r = pattern_mode(args.rpc_url, args.pattern, args.repeat, args.symbol, args.token, simulate_dir='.')
        print('Done:', r)
    else:
        if not args.side:
            print('Manual mode requires --side')
            return
        body, status = manual_order(args.rpc_url, args.side, args.volume, args.symbol, args.token)
        print('Response:', status, body)


if __name__ == '__main__':
    main()
