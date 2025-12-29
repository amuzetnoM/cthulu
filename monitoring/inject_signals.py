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


def burst_mode(url, count=100, rate=5, symbol='BTCUSD#', token=None):
    delay = 1.0 / rate if rate > 0 else 0
    results = {'ok': 0, 'rejected': 0, 'errors': 0}
    for i in range(count):
        side = random.choice(['BUY', 'SELL'])
        volume = round(random.uniform(0.01, 0.2), 4)
        payload = {'symbol': symbol, 'side': side, 'volume': volume}
        body, status = post_trade(url, payload, token)
        if status == 200:
            results['ok'] += 1
        elif status == 403:
            results['rejected'] += 1
        else:
            results['errors'] += 1
        if delay:
            time.sleep(delay)
    return results


def pattern_mode(url, pattern: str, repeat: int, symbol='BTCUSD#', token=None):
    seq = [p.strip().upper() for p in pattern.split(',') if p.strip()]
    results = {'ok': 0, 'rejected': 0, 'errors': 0}
    for _ in range(repeat):
        for p in seq:
            if p not in ('BUY', 'SELL'):
                continue
            payload = {'symbol': symbol, 'side': p, 'volume': 0.01}
            body, status = post_trade(url, payload, token)
            if status == 200:
                results['ok'] += 1
            elif status == 403:
                results['rejected'] += 1
            else:
                results['errors'] += 1
            time.sleep(0.2)
    return results


def manual_order(url, side, volume, symbol='BTCUSD#', token=None):
    payload = {'symbol': symbol, 'side': side, 'volume': volume}
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
        r = burst_mode(args.rpc_url, args.count, args.rate, args.symbol, args.token)
        print('Done:', r)
    elif args.mode == 'pattern':
        print(f"Starting pattern: pattern={args.pattern}, repeat={args.repeat}")
        r = pattern_mode(args.rpc_url, args.pattern, args.repeat, args.symbol, args.token)
        print('Done:', r)
    else:
        if not args.side:
            print('Manual mode requires --side')
            return
        body, status = manual_order(args.rpc_url, args.side, args.volume, args.symbol, args.token)
        print('Response:', status, body)


if __name__ == '__main__':
    main()
