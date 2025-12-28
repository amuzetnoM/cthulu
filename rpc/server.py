"""Lightweight RPC server for controlling Cthulu at runtime.

Provides a minimal POST /trade endpoint protected by a bearer token.
Designed to be local-only (binds to 127.0.0.1 by default) and dependency-free (uses http.server).
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
from urllib.parse import urlparse
from threading import Thread
from typing import Optional

logger = logging.getLogger('Cthulu.rpc')


class RPCRequestHandler(BaseHTTPRequestHandler):
    # These class members will be set when the server is created by run_rpc_server
    token: Optional[str] = None
    execution_engine = None
    risk_manager = None
    position_manager = None
    database = None

    def _send_json(self, status_code: int, payload: dict):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _unauthorized(self, msg='Unauthorized'):
        self._send_json(401, {'error': msg})

    def _bad_request(self, msg='Bad Request'):
        self._send_json(400, {'error': msg})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != '/trade':
            self._bad_request('Unknown endpoint')
            return

        # Authenticate with Bearer token or X-Api-Key header
        auth = self.headers.get('Authorization')
        api_key = self.headers.get('X-Api-Key')
        if self.token:
            if auth and auth.startswith('Bearer '):
                token = auth.split(' ', 1)[1].strip()
            else:
                token = api_key
            if not token or token != self.token:
                self._unauthorized('Invalid or missing API token')
                return

        # Read body
        length = int(self.headers.get('Content-Length', 0))
        try:
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode('utf-8') if isinstance(raw, (bytes, bytearray)) else raw)
        except Exception as e:
            logger.exception('Failed to parse JSON body')
            self._bad_request('Invalid JSON')
            return

        # Validate minimal fields
        symbol = payload.get('symbol')
        side = payload.get('side')
        volume = payload.get('volume')
        price = payload.get('price', None)
        sl = payload.get('sl', None)
        tp = payload.get('tp', None)

        if not symbol or side not in ('BUY', 'SELL') or (volume is None):
            self._bad_request('Missing or invalid fields: require symbol, side(BUY/SELL), volume')
            return

        try:
            volume = float(volume)
        except Exception:
            self._bad_request('volume must be numeric')
            return

        # Build OrderRequest lazily to avoid importing heavy modules at module import time
        try:
            from cthulu.execution.engine import OrderRequest, OrderType, OrderStatus, ExecutionResult
        except Exception:
            self._send_json(500, {'error': 'Server misconfiguration: cannot import Execution engine'})
            return

        order_type = OrderType.MARKET if not price else OrderType.LIMIT
        order_req = OrderRequest(
            signal_id='rpc_manual',
            symbol=symbol,
            side=side,
            volume=volume,
            order_type=order_type,
            price=price,
            sl=sl,
            tp=tp,
        )
        # Mark source for provenance
        try:
            order_req.metadata['source'] = 'rpc'
            order_req.metadata['client_ip'] = self.client_address[0]
            # Include any auth token hint (do not store full token)
            auth = self.headers.get('Authorization')
            if auth and auth.startswith('Bearer '):
                order_req.metadata['auth_hint'] = f"bearer:{auth.split(' ',1)[1][:6]}"
        except Exception:
            pass

        # Risk approval (fetch account state if available)
        try:
            account_info = None
            try:
                connector = getattr(self.position_manager, 'connector', None)
                if connector and hasattr(connector, 'get_account_info'):
                    account_info = connector.get_account_info()
            except Exception:
                account_info = None

            # The RiskManager was designed for `Signal` objects with attributes like
            # stop_loss, take_profit, price, confidence etc. Build a small signal-like
            # object from the order request so the approve() call can inspect necessary fields.
            class _SignalLike:
                pass

            signal_like = _SignalLike()
            # Provide fields expected by RiskEvaluator.approve()
            signal_like.symbol = order_req.symbol
            signal_like.price = order_req.price
            signal_like.stop_loss = order_req.sl
            signal_like.take_profit = order_req.tp
            # Normalized attributes
            signal_like.side = order_req.side
            signal_like.confidence = getattr(order_req, 'confidence', 1.0)
            signal_like.action = getattr(order_req, 'order_type', 'manual')
            signal_like.size_hint = getattr(order_req, 'volume', None)
            signal_like.metadata = {}

            approved, reason, position_size = self.risk_manager.approve(
                signal_like,
                account_info,
                len(self.position_manager.get_positions(symbol=symbol))
            )
        except Exception as e:
            logger.exception('Risk manager check failed')
            self._send_json(500, {'error': 'Risk manager error'})
            return

        if not approved:
            logger.info('RPC trade rejected by risk manager: %s', reason)
            self._send_json(403, {'error': 'Risk rejected', 'reason': reason})
            return

        # Overwrite volume with calculated position size if available
        if position_size:
            order_req.volume = position_size

        # Place the order
        try:
            result = self.execution_engine.place_order(order_req)
        except Exception:
            logger.exception('Execution engine error while placing manual order')
            self._send_json(500, {'error': 'Execution failed'})
            return

        if result is None:
            self._send_json(500, {'error': 'Execution returned no result'})
            return

        # If filled, track position and record
        try:
            if result.status == OrderStatus.FILLED:
                tracked = self.position_manager.track_position(result, signal_metadata={})
                # record in DB via TradeRecord
                try:
                    from cthulu.persistence.database import TradeRecord
                    from datetime import datetime as _dt
                    tr = TradeRecord(
                        signal_id='rpc_manual',
                        order_id=result.order_id,
                        symbol=order_req.symbol,
                        side=order_req.side,
                        entry_price=result.fill_price,
                        volume=result.filled_volume,
                        entry_time=_dt.now(),
                    )
                    self.database.record_trade(tr)
                except Exception:
                    logger.exception('Failed to record RPC-placed trade')

        except Exception:
            logger.exception('Failed to track or record RPC trade')

        # Return structured result
        resp = {
            'status': result.status.name,
            'order_id': getattr(result, 'order_id', None),
            'fill_price': getattr(result, 'fill_price', None),
            'filled_volume': getattr(result, 'filled_volume', None),
            'message': getattr(result, 'message', None)
        }

        self._send_json(200, resp)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != '/provenance':
            self.send_response(404)
            self.end_headers()
            return

        # Authenticate with same token as POST
        auth = self.headers.get('Authorization')
        api_key = self.headers.get('X-Api-Key')
        if self.token:
            if auth and auth.startswith('Bearer '):
                token = auth.split(' ', 1)[1].strip()
            else:
                token = api_key
            if not token or token != self.token:
                self._unauthorized('Invalid or missing API token')
                return

        # Parse query params for limit
        try:
            q = dict([p.split('=') for p in parsed.query.split('&') if p])
            limit = int(q.get('limit', 50))
        except Exception:
            limit = 50

        try:
            results = []
            if self.database:
                results = self.database.get_recent_provenance(limit=limit)
            body = json.dumps({'limit': limit, 'results': results}, default=str).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            logger.exception('Failed to serve provenance')
            self._send_json(500, {'error': 'Internal server error'})

    def log_message(self, format, *args):
        # Redirect logging through our logger rather than default stderr
        logger.info("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format % args))


def run_rpc_server(host: str, port: int, token: Optional[str], execution_engine, risk_manager, position_manager, database, daemon=True):
    """Start RPC server in background thread. Returns the Thread and HTTPServer instances."""
    RPCRequestHandler.token = token
    RPCRequestHandler.execution_engine = execution_engine
    RPCRequestHandler.risk_manager = risk_manager
    RPCRequestHandler.position_manager = position_manager
    RPCRequestHandler.database = database

    server = HTTPServer((host, port), RPCRequestHandler)

    t = Thread(target=server.serve_forever, daemon=daemon, name='rpc-server')
    t.start()
    logger.info(f"RPC server listening on http://{host}:{port} (local only).")
    return t, server




