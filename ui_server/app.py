import sqlite3
import time
import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for Angular UI

# Configuration
DB_PATH = r"C:\workspace\cthulu\cthulu.db"
LOG_FILE = r"C:\workspace\cthulu\out.log"

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return None

def normalize_trade(row):
    return {
        "id": str(row['order_id']) if row['order_id'] else str(row['id']), # Fallback to DB ID if no order ID
        "type": row['side'].upper() if row['side'] else 'UNKNOWN',
        "price": row['entry_price'],
        "size": row['volume'],
        "timestamp": int(time.mktime(time.strptime(row['entry_time'], '%Y-%m-%d %H:%M:%S')) * 1000) if row['entry_time'] else 0, # Parse TS
        "status": row['status'],
        "pnl": row['profit'],
        "origin": "AUTO", # Default to AUTO
        "reason": row['exit_reason'] or row['metadata'] or ""
    }

@app.route('/api/trades', methods=['GET'])
def get_trades():
    conn = get_db_connection()
    if not conn:
        return jsonify([]), 500
    
    try:
        # Get open trades (or all recent)
        trades = conn.execute("SELECT * FROM trades ORDER BY entry_time DESC LIMIT 50").fetchall()
        return jsonify([normalize_trade(t) for t in trades])
    except Exception as e:
        print(f"Error querying trades: {e}")
        return jsonify([]), 500
    finally:
        conn.close()

@app.route('/api/logs', methods=['GET'])
def get_logs():
    if not os.path.exists(LOG_FILE):
        return jsonify([])
    
    try:
        lines = []
        # Read last 100 lines
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            # Simple tail implementation
            f.seek(0, os.SEEK_END)
            position = f.tell()
            line_count = 0
            block_size = 1024
            
            while position > 0 and line_count < 100:
                read_len = min(block_size, position)
                position -= read_len
                f.seek(position, os.SEEK_SET)
                block = f.read(read_len)
                
                # Count newlines
                line_count += block.count('\n')
                
            f.seek(position, os.SEEK_SET)
            # Find the start of the first full line
            if position > 0:
                f.readline()
                
            lines = f.readlines()[-100:]
            
        parsed_logs = []
        for line in lines:
            # Parse standard log format: 2026-01-10 13:00:00 [INFO] Message
            try:
                parts = line.strip().split(' ', 3) # date time [level] msg
                if len(parts) >= 4:
                    ts_str = f"{parts[0]} {parts[1]}"
                    level = parts[2].strip('[]')
                    msg = parts[3]
                    
                    parsed_logs.append({
                        "timestamp": int(time.time() * 1000), # Approx/Current time as parsing log time is strict
                        "real_time_str": ts_str,
                        "level": level if level in ['INFO', 'WARN', 'ERROR'] else 'INFO',
                        "message": msg,
                        "source": "SYSTEM"
                    })
                else:
                     parsed_logs.append({
                        "timestamp": int(time.time() * 1000), 
                        "level": 'INFO',
                        "message": line.strip(),
                        "source": "SYSTEM"
                    })
            except:
                pass
                
        return jsonify(parsed_logs[::-1]) # Newest first
    except Exception as e:
        print(f"Error reading logs: {e}")
        return jsonify([])



@app.route('/api/signals', methods=['GET'])
def get_signals():
    conn = get_db_connection()
    if not conn:
        return jsonify([]), 500
    try:
        # Get recent signals
        signals = conn.execute("SELECT * FROM signals ORDER BY timestamp DESC LIMIT 20").fetchall()
        return jsonify([dict(s) for s in signals])
    except Exception as e:
        print(f"Error querying signals: {e}")
        return jsonify([]), 500
    finally:
        conn.close()

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    conn = get_db_connection()
    if not conn:
        return jsonify([]), 500
    try:
        # Get recent metrics
        metrics = conn.execute("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 50").fetchall()
        return jsonify([dict(m) for m in metrics])
    except Exception as e:
        print(f"Error querying metrics: {e}")
        return jsonify([]), 500
    finally:
        conn.close()

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "online", "db": os.path.exists(DB_PATH)})

import yfinance as yf
import requests

# ... (existing imports)

# Configuration
RPC_URL = "http://127.0.0.1:8278/trade"

# ... (existing code)

@app.route('/api/ticker', methods=['GET'])
def get_ticker():
    symbol = request.args.get('symbol', 'BTC-USD')
    try:
        ticker = yf.Ticker(symbol)
        # Fast fetch
        data = ticker.fast_info
        price = data.last_price
        return jsonify({
            "symbol": symbol,
            "price": price,
            "timestamp": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"Error fetching ticker for {symbol}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    symbol = request.args.get('symbol', 'BTC-USD')
    period = request.args.get('period', '1d')
    interval = request.args.get('interval', '1m')
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        # Convert to list of dicts
        candles = []
        for index, row in hist.iterrows():
            candles.append({
                "time": int(index.timestamp() * 1000),
                "open": row['Open'],
                "high": row['High'],
                "low": row['Low'],
                "close": row['Close'],
                "volume": row['Volume']
            })
        return jsonify(candles)
    except Exception as e:
        print(f"Error fetching history for {symbol}: {e}")
        return jsonify([]), 500

@app.route('/api/trade', methods=['POST'])
def proxy_trade():
    try:
        payload = request.json
        # Forward to RPC server
        # RPC expects: {"symbol": str, "side": str, "volume": float, ...}
        resp = requests.post(RPC_URL, json=payload, timeout=5)
        return (resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        print(f"Error proxying trade to RPC: {e}")
        return jsonify({"error": "RPC Server Unreachable"}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
