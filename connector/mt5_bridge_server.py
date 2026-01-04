"""
MT5 Android Bridge Server

This is a simple REST API bridge server that runs on Android (Termux)
and provides an interface between Cthulu and the MT5 Android app.

The bridge uses AndroidHelperAPI or similar mechanisms to communicate
with the MT5 Android app and exposes a REST API for Cthulu to use.

Requirements:
- Flask (pip install flask)
- MT5 Android app installed
- Run in Termux on Android

Usage:
    python mt5_bridge_server.py --port 18812 --host 127.0.0.1
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("WARNING: Flask not available. Install with: pip install flask")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MT5AndroidBridge:
    """
    Bridge between Cthulu and MT5 Android app.
    
    This bridge provides a REST API that Cthulu can use to interact
    with the MT5 Android app. It handles:
    - Connection management
    - Market data retrieval
    - Account information
    - Position management
    """
    
    def __init__(self):
        self.connected = False
        self.mt5_initialized = False
        self.logger = logging.getLogger("MT5Bridge")
        
        # Try to detect and use available MT5 interface methods
        self._init_mt5_interface()
    
    def _init_mt5_interface(self):
        """
        Initialize MT5 interface.
        
        Priority:
        1. MetaTrader5 Python package (Windows/Linux)
        2. Android file-based interface (Termux)
        """
        # Try standard MT5 package first
        try:
            import MetaTrader5 as mt5
            self.mt5 = mt5
            self.interface_type = "mt5_package"
            self.logger.info("Using MetaTrader5 Python package")
            return
        except ImportError:
            pass
        
        # Try Android file-based interface
        try:
            from connector.mt5_android_interface import MT5AndroidInterface
            self.android_interface = MT5AndroidInterface()
            if self.android_interface.available:
                self.interface_type = "android_file"
                self.logger.info("Using Android file-based MT5 interface")
                self.logger.info(f"MT5 data directory: {self.android_interface.data_dir}")
                return
        except ImportError as e:
            self.logger.debug(f"Android interface import failed: {e}")
        except Exception as e:
            self.logger.warning(f"Android interface init failed: {e}")
        
        # Fall back to simulation mode
        self.logger.warning("No MT5 interface available - running in SIMULATION mode")
        self.interface_type = "simulation"
        self.android_interface = None
    
    def _detect_mt5_data_dir(self) -> Optional[Path]:
        """Detect MT5 Android app data directory."""
        possible_paths = [
            Path("/storage/emulated/0/Android/data/net.metaquotes.metatrader5/files"),
            Path("/sdcard/Android/data/net.metaquotes.metatrader5/files"),
            Path("/data/data/net.metaquotes.metatrader5/files"),
            Path.home() / "MT5",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize MT5 connection."""
        try:
            if self.interface_type == "mt5_package":
                # Use MT5 package
                login = params.get('login')
                password = params.get('password')
                server = params.get('server')
                
                if login and password and server:
                    result = self.mt5.initialize(
                        login=int(login),
                        password=password,
                        server=server
                    )
                else:
                    result = self.mt5.initialize()
                
                if result:
                    self.mt5_initialized = True
                    self.connected = True
                    return {'success': True, 'message': 'Connected to MT5'}
                else:
                    error = self.mt5.last_error()
                    return {'success': False, 'error': f'MT5 initialization failed: {error}'}
            
            elif self.interface_type == "android_file" and self.android_interface:
                # Android file-based interface
                self.logger.info("Android file-based interface: checking MT5 data access")
                self.connected = self.android_interface.available
                if self.connected:
                    return {
                        'success': True,
                        'message': 'Connected via Android file-based interface',
                        'data_dir': str(self.android_interface.data_dir)
                    }
                else:
                    return {
                        'success': False,
                        'error': 'MT5 data directory not accessible'
                    }
            
            else:
                # Simulation mode
                self.logger.info("Simulation mode: no real MT5 connection")
                self.connected = True
                return {
                    'success': True,
                    'message': 'Connected in SIMULATION mode',
                    'warning': 'No real MT5 connection - data is simulated'
                }
        
        except Exception as e:
            self.logger.error(f"Initialize error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def connect(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Alias for initialize - used by connector."""
        return self.initialize(params)
    
    def rates(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Alias for copy_rates_from_pos - used by connector."""
        return self.copy_rates_from_pos(params)
    
    def shutdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Shutdown MT5 connection."""
        try:
            if self.interface_type == "mt5_package" and self.mt5_initialized:
                self.mt5.shutdown()
            
            self.connected = False
            self.mt5_initialized = False
            return {'success': True}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def terminal_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get terminal information."""
        try:
            if self.interface_type == "mt5_package" and self.mt5_initialized:
                info = self.mt5.terminal_info()
                if info:
                    return {
                        'success': True,
                        'data': {
                            'connected': info.connected,
                            'trade_allowed': info.trade_allowed,
                            'company': info.company,
                            'name': info.name,
                        }
                    }
            
            # Fallback/simulated data
            return {
                'success': True,
                'data': {
                    'connected': self.connected,
                    'trade_allowed': True,
                    'company': 'Unknown',
                    'name': 'MT5 Android',
                }
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def account_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get account information."""
        try:
            if self.interface_type == "mt5_package" and self.mt5_initialized:
                account = self.mt5.account_info()
                if account:
                    return {
                        'success': True,
                        'data': {
                            'login': account.login,
                            'server': account.server,
                            'balance': account.balance,
                            'equity': account.equity,
                            'margin': account.margin,
                            'margin_free': account.margin_free,
                            'margin_level': account.margin_level,
                            'profit': account.profit,
                            'currency': account.currency,
                            'leverage': account.leverage,
                            'trade_allowed': account.trade_allowed,
                        }
                    }
            
            elif self.interface_type == "android_file" and self.android_interface:
                # Use Android file interface
                return self.android_interface.get_account_info()
            
            # Fallback/simulated data
            return {
                'success': True,
                'data': {
                    'login': 0,
                    'server': 'SimulatedServer',
                    'balance': 10000.0,
                    'equity': 10000.0,
                    'margin': 0.0,
                    'margin_free': 10000.0,
                    'margin_level': 0.0,
                    'profit': 0.0,
                    'currency': 'USD',
                    'leverage': 100,
                    'trade_allowed': True,
                }
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def symbol_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get symbol information."""
        symbol = params.get('symbol', '')
        
        try:
            if self.interface_type == "mt5_package" and self.mt5_initialized:
                info = self.mt5.symbol_info(symbol)
                if info:
                    return {
                        'success': True,
                        'data': {
                            'name': info.name,
                            'bid': info.bid,
                            'ask': info.ask,
                            'spread': info.spread,
                            'digits': info.digits,
                            'point': info.point,
                            'trade_mode': info.trade_mode,
                            'volume_min': info.volume_min,
                            'volume_max': info.volume_max,
                            'volume_step': info.volume_step,
                            'contract_size': info.trade_contract_size,
                            'currency_base': info.currency_base,
                            'currency_profit': info.currency_profit,
                            'currency_margin': info.currency_margin,
                        }
                    }
            
            elif self.interface_type == "android_file" and self.android_interface:
                # Use Android file interface
                return self.android_interface.get_symbol_info(symbol)
            
            # Fallback/simulated data
            return {
                'success': True,
                'data': {
                    'name': symbol,
                    'bid': 1.10000,
                    'ask': 1.10010,
                    'spread': 10,
                    'digits': 5,
                    'point': 0.00001,
                    'trade_mode': 0,
                    'volume_min': 0.01,
                    'volume_max': 100.0,
                    'volume_step': 0.01,
                    'contract_size': 100000.0,
                    'currency_base': 'EUR',
                    'currency_profit': 'USD',
                    'currency_margin': 'USD',
                }
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def copy_rates_from_pos(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get historical rate data."""
        symbol = params.get('symbol', '')
        timeframe = params.get('timeframe', 0)
        start_pos = params.get('start_pos', 0)
        count = params.get('count', 100)
        
        try:
            if self.interface_type == "mt5_package" and self.mt5_initialized:
                rates = self.mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
                if rates is not None:
                    rates_list = [
                        {
                            'time': datetime.fromtimestamp(rate[0]).isoformat(),
                            'open': float(rate[1]),
                            'high': float(rate[2]),
                            'low': float(rate[3]),
                            'close': float(rate[4]),
                            'tick_volume': int(rate[5]),
                            'spread': int(rate[6]),
                            'real_volume': int(rate[7])
                        }
                        for rate in rates
                    ]
                    return {'success': True, 'data': rates_list}
            
            elif self.interface_type == "android_file" and self.android_interface:
                # Use Android file interface
                return self.android_interface.get_rates(symbol, timeframe, count)
            
            # Fallback: return empty data with message
            return {
                'success': False,
                'error': 'Historical data not available in simulation mode',
                'data': []
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def positions_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get open positions."""
        try:
            if self.interface_type == "mt5_package" and self.mt5_initialized:
                positions = self.mt5.positions_get()
                if positions:
                    positions_list = [
                        {
                            'ticket': p.ticket,
                            'symbol': p.symbol,
                            'price_open': p.price_open,
                            'price_current': p.price_current,
                            'profit': p.profit,
                            'volume': p.volume,
                            'type': p.type,
                            'magic': p.magic,
                            'time': p.time,
                            'sl': p.sl,
                            'tp': p.tp,
                        }
                        for p in positions
                    ]
                    return {'success': True, 'data': positions_list}
            
            # No positions in simulation
            return {'success': True, 'data': []}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def position_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific position by ticket."""
        ticket = params.get('ticket')
        
        try:
            if self.interface_type == "mt5_package" and self.mt5_initialized:
                positions = self.mt5.positions_get(ticket=ticket)
                if positions and len(positions) > 0:
                    p = positions[0]
                    return {
                        'success': True,
                        'data': {
                            'ticket': p.ticket,
                            'symbol': p.symbol,
                            'price_open': p.price_open,
                            'price_current': p.price_current,
                            'profit': p.profit,
                            'volume': p.volume,
                            'type': p.type,
                            'magic': p.magic,
                            'time': p.time,
                            'sl': p.sl,
                            'tp': p.tp,
                            'swap': getattr(p, 'swap', 0),
                            'comment': getattr(p, 'comment', ''),
                        }
                    }
            
            return {'success': False, 'error': f'Position #{ticket} not found'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def symbol_info_tick(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current tick for a symbol."""
        symbol = params.get('symbol', '')
        
        try:
            if self.interface_type == "mt5_package" and self.mt5_initialized:
                tick = self.mt5.symbol_info_tick(symbol)
                if tick:
                    return {
                        'success': True,
                        'data': {
                            'time': tick.time,
                            'bid': tick.bid,
                            'ask': tick.ask,
                            'last': tick.last,
                            'volume': tick.volume,
                            'time_msc': getattr(tick, 'time_msc', 0),
                            'flags': getattr(tick, 'flags', 0),
                            'volume_real': getattr(tick, 'volume_real', 0),
                        }
                    }
            
            elif self.interface_type == "android_file" and self.android_interface:
                # Use Android file interface for tick data
                return self.android_interface.get_tick(symbol)
            
            # Fallback: return simulated tick based on symbol_info
            info_result = self.symbol_info({'symbol': symbol})
            if info_result.get('success'):
                data = info_result.get('data', {})
                return {
                    'success': True,
                    'data': {
                        'time': int(datetime.now().timestamp()),
                        'bid': data.get('bid', 1.10000),
                        'ask': data.get('ask', 1.10010),
                        'last': data.get('last', 0),
                        'volume': 0,
                        'time_msc': 0,
                        'flags': 0,
                        'volume_real': 0,
                    }
                }
            
            return {'success': False, 'error': f'Symbol {symbol} tick not available'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def symbol_select(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Select/enable a symbol in Market Watch."""
        symbol = params.get('symbol', '')
        enable = params.get('enable', True)
        
        try:
            if self.interface_type == "mt5_package" and self.mt5_initialized:
                result = self.mt5.symbol_select(symbol, enable)
                return {'success': result, 'data': {'symbol': symbol, 'enabled': enable}}
            
            # Simulation: always succeed
            return {'success': True, 'data': {'symbol': symbol, 'enabled': enable}}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def order_send(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a trading order to MT5.
        
        This is the critical trading method that handles:
        - Market orders (buy/sell)
        - Pending orders (limit/stop)
        - Position modifications (SL/TP changes)
        - Position closes
        """
        try:
            if self.interface_type == "mt5_package" and self.mt5_initialized:
                # Build MT5 request from params
                request = {
                    "action": params.get('action'),
                    "symbol": params.get('symbol'),
                    "volume": float(params.get('volume', 0)),
                    "type": params.get('type'),
                    "price": float(params.get('price', 0)),
                    "deviation": int(params.get('deviation', 20)),
                    "magic": int(params.get('magic', 0)),
                    "comment": params.get('comment', 'Cthulu'),
                    "type_time": params.get('type_time', 0),  # ORDER_TIME_GTC
                    "type_filling": params.get('type_filling', 1),  # ORDER_FILLING_IOC
                }
                
                # Optional fields
                if params.get('sl') is not None:
                    request['sl'] = float(params.get('sl'))
                if params.get('tp') is not None:
                    request['tp'] = float(params.get('tp'))
                if params.get('position') is not None:
                    request['position'] = int(params.get('position'))
                if params.get('stoplimit') is not None:
                    request['stoplimit'] = float(params.get('stoplimit'))
                if params.get('expiration') is not None:
                    request['expiration'] = params.get('expiration')
                
                # Send order
                result = self.mt5.order_send(request)
                
                if result is None:
                    error = self.mt5.last_error()
                    return {
                        'success': False,
                        'error': str(error),
                        'retcode': error[0] if error else 0
                    }
                
                # Build response
                response_data = {
                    'retcode': result.retcode,
                    'deal': result.deal,
                    'order': result.order,
                    'volume': result.volume,
                    'price': result.price,
                    'bid': result.bid,
                    'ask': result.ask,
                    'comment': result.comment,
                    'request_id': result.request_id,
                    'retcode_external': getattr(result, 'retcode_external', 0),
                }
                
                # Add profit if available (for close operations)
                if hasattr(result, 'profit'):
                    response_data['profit'] = result.profit
                
                # Check if order was successful
                TRADE_RETCODE_DONE = 10009
                if result.retcode == TRADE_RETCODE_DONE:
                    return {'success': True, 'data': response_data}
                else:
                    return {
                        'success': False,
                        'error': result.comment,
                        'retcode': result.retcode,
                        'data': response_data
                    }
            
            elif self.interface_type == "android_file" and self.android_interface:
                # Android interface - queue order for execution
                self.logger.info("Order requested via Android interface - queuing for execution")
                return self.android_interface.send_order(params)
            
            else:
                # Simulation mode - cannot execute real trades
                self.logger.warning("Order requested in simulation mode - no real trade executed")
                return {
                    'success': False,
                    'error': 'Trading not available in simulation mode. MT5 package required.',
                    'retcode': 10013,  # TRADE_RETCODE_INVALID
                    'data': {
                        'retcode': 10013,
                        'deal': 0,
                        'order': 0,
                        'volume': 0,
                        'price': 0,
                        'comment': 'Simulation mode - no trading',
                    }
                }
        
        except Exception as e:
            self.logger.error(f"Order send error: {e}", exc_info=True)
            return {'success': False, 'error': str(e), 'retcode': 10013}
    
    def last_error(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get last MT5 error."""
        try:
            if self.interface_type == "mt5_package" and self.mt5_initialized:
                error = self.mt5.last_error()
                return {
                    'success': True,
                    'data': {
                        'code': error[0] if error else 0,
                        'message': error[1] if error and len(error) > 1 else 'No error'
                    }
                }
            
            return {'success': True, 'data': {'code': 0, 'message': 'No error'}}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}


def create_app(bridge: MT5AndroidBridge) -> Flask:
    """Create Flask application."""
    app = Flask(__name__)
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint."""
        return jsonify({
            'status': 'ok',
            'connected': bridge.connected,
            'interface': bridge.interface_type,
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/mt5/<method>', methods=['POST'])
    def mt5_api(method):
        """Generic MT5 API endpoint."""
        try:
            params = request.get_json() or {}
            
            # Route to appropriate bridge method
            if hasattr(bridge, method):
                handler = getattr(bridge, method)
                result = handler(params)
                return jsonify(result)
            else:
                return jsonify({
                    'success': False,
                    'error': f'Unknown method: {method}'
                }), 400
        
        except Exception as e:
            logger.error(f"API error: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return app


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='MT5 Android Bridge Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=18812, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    if not FLASK_AVAILABLE:
        logger.error("Flask is not installed. Install with: pip install flask")
        sys.exit(1)
    
    # Create bridge
    logger.info("Initializing MT5 Android Bridge...")
    bridge = MT5AndroidBridge()
    
    # Create Flask app
    app = create_app(bridge)
    
    # Start server
    logger.info(f"Starting bridge server on {args.host}:{args.port}")
    logger.info("Press Ctrl+C to stop")
    
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Shutting down bridge server...")


if __name__ == '__main__':
    main()
