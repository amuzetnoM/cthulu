#!/usr/bin/env python3
import json
import urllib.request
import urllib.error

# Read token from herald/.env (simple parser)
with open('herald/.env', 'r', encoding='utf-8') as f:
    token = None
    for line in f:
        if line.startswith('HERALD_API_TOKEN='):
            token = line.split('=', 1)[1].strip()
            break

if not token:
    print('No HERALD_API_TOKEN found in herald/.env')
    raise SystemExit(1)

url = 'http://127.0.0.1:8181/trade'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
body = {'symbol': 'BTCUSD#m', 'side': 'BUY', 'volume': 0.01}
req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers=headers)

try:
    r = urllib.request.urlopen(req, timeout=10)
    print('STATUS', r.status)
    print(r.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print('HTTP ERROR', e.code, e.read().decode('utf-8'))
except Exception as e:
    print('ERROR', e)
