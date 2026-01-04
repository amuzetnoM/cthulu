"""
MT5 Android File-Based Interface

This module provides real MT5 integration on Android by:
1. Reading MT5 data files directly from the app's data directory
2. Parsing .hst (history), .sym (symbol), and account files
3. Using Android Accessibility or Intent-based trading

MT5 Android stores data in specific locations that we can read.
"""

import os
import sys
import struct
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger('MT5Android.FileInterface')


@dataclass
class MT5SymbolInfo:
    """Symbol information from MT5."""
    name: str = ''
    bid: float = 0.0
    ask: float = 0.0
    spread: int = 0
    digits: int = 5
    point: float = 0.00001
    trade_mode: int = 0
    volume_min: float = 0.01
    volume_max: float = 100.0
    volume_step: float = 0.01
    contract_size: float = 100000.0
    currency_base: str = ''
    currency_profit: str = ''
    currency_margin: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'bid': self.bid,
            'ask': self.ask,
            'spread': self.spread,
            'digits': self.digits,
            'point': self.point,
            'trade_mode': self.trade_mode,
            'volume_min': self.volume_min,
            'volume_max': self.volume_max,
            'volume_step': self.volume_step,
            'contract_size': self.contract_size,
            'currency_base': self.currency_base,
            'currency_profit': self.currency_profit,
            'currency_margin': self.currency_margin,
        }


@dataclass
class MT5AccountInfo:
    """Account information."""
    login: int = 0
    server: str = ''
    balance: float = 0.0
    equity: float = 0.0
    margin: float = 0.0
    margin_free: float = 0.0
    margin_level: float = 0.0
    profit: float = 0.0
    currency: str = 'USD'
    leverage: int = 100
    trade_allowed: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'login': self.login,
            'server': self.server,
            'balance': self.balance,
            'equity': self.equity,
            'margin': self.margin,
            'margin_free': self.margin_free,
            'margin_level': self.margin_level,
            'profit': self.profit,
            'currency': self.currency,
            'leverage': self.leverage,
            'trade_allowed': self.trade_allowed,
        }


@dataclass
class MT5Position:
    """Open position."""
    ticket: int = 0
    symbol: str = ''
    type: int = 0  # 0=BUY, 1=SELL
    volume: float = 0.0
    price_open: float = 0.0
    price_current: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    profit: float = 0.0
    swap: float = 0.0
    magic: int = 0
    time: int = 0
    comment: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'ticket': self.ticket,
            'symbol': self.symbol,
            'type': self.type,
            'volume': self.volume,
            'price_open': self.price_open,
            'price_current': self.price_current,
            'sl': self.sl,
            'tp': self.tp,
            'profit': self.profit,
            'swap': self.swap,
            'magic': self.magic,
            'time': self.time,
            'comment': self.comment,
        }


@dataclass 
class MT5Tick:
    """Price tick."""
    time: int = 0
    bid: float = 0.0
    ask: float = 0.0
    last: float = 0.0
    volume: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'time': self.time,
            'bid': self.bid,
            'ask': self.ask,
            'last': self.last,
            'volume': self.volume,
        }


class MT5FileReader:
    """
    Reads MT5 data files from Android storage.
    
    MT5 Android stores various files:
    - config/accounts/*.dat - Account configurations
    - bases/<server>/symbols.raw - Symbol information
    - bases/<server>/history/<symbol>*.hst - Historical data
    - bases/<server>/ticks/<symbol>.tkc - Tick cache
    """
    
    # MT5 file magic numbers
    HST_VERSION = 401
    SYMBOL_RECORD_SIZE = 1936  # Size of symbol record in symbols.raw
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.logger = logging.getLogger('MT5FileReader')
        
        # Cache for parsed data
        self._symbols_cache: Dict[str, MT5SymbolInfo] = {}
        self._account_cache: Optional[MT5AccountInfo] = None
        self._last_cache_time = 0
        self._cache_ttl = 5  # seconds
    
    def find_server_dir(self) -> Optional[Path]:
        """Find the active server directory."""
        bases_dir = self.data_dir / 'bases'
        if not bases_dir.exists():
            return None
        
        # Look for server directories
        for item in bases_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                return item
        
        return None
    
    def read_symbols(self, server_dir: Optional[Path] = None) -> Dict[str, MT5SymbolInfo]:
        """
        Read symbol information from symbols.raw or symbol cache files.
        
        The symbols.raw file contains binary records for each symbol.
        Format varies by MT5 version but typically includes:
        - Symbol name (64 bytes)
        - Description (128 bytes)
        - Various trading parameters
        """
        if server_dir is None:
            server_dir = self.find_server_dir()
        
        if not server_dir:
            return {}
        
        symbols = {}
        
        # Try symbols.raw first
        symbols_file = server_dir / 'symbols.raw'
        if symbols_file.exists():
            try:
                symbols = self._parse_symbols_raw(symbols_file)
            except Exception as e:
                self.logger.error(f"Failed to parse symbols.raw: {e}")
        
        # Fallback: try to find individual symbol files
        if not symbols:
            syminfo_dir = server_dir / 'syminfo'
            if syminfo_dir.exists():
                for sym_file in syminfo_dir.glob('*.sym'):
                    try:
                        info = self._parse_symbol_file(sym_file)
                        if info:
                            symbols[info.name] = info
                    except Exception as e:
                        self.logger.debug(f"Failed to parse {sym_file}: {e}")
        
        self._symbols_cache = symbols
        return symbols
    
    def _parse_symbols_raw(self, filepath: Path) -> Dict[str, MT5SymbolInfo]:
        """Parse the binary symbols.raw file."""
        symbols = {}
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # Symbols.raw structure varies, but generally:
        # Header (variable) + N symbol records
        # Each record is typically 1936 bytes in MT5
        
        record_size = self.SYMBOL_RECORD_SIZE
        offset = 0
        
        # Skip header if present (look for recognizable patterns)
        # Try to find first valid symbol name
        while offset < len(data) - record_size:
            # Read potential symbol name (first 64 bytes, null-terminated string)
            name_bytes = data[offset:offset+64]
            try:
                name = name_bytes.split(b'\x00')[0].decode('utf-8').strip()
                if name and name.isalnum() or '.' in name or '_' in name:
                    break
            except:
                pass
            offset += 1
        
        # Parse records
        while offset + record_size <= len(data):
            try:
                record = data[offset:offset + record_size]
                info = self._parse_symbol_record(record)
                if info and info.name:
                    symbols[info.name] = info
            except Exception as e:
                self.logger.debug(f"Failed to parse symbol record at {offset}: {e}")
            offset += record_size
        
        return symbols
    
    def _parse_symbol_record(self, record: bytes) -> Optional[MT5SymbolInfo]:
        """Parse a single symbol record from symbols.raw."""
        if len(record) < 200:
            return None
        
        try:
            # Extract symbol name (first 64 bytes)
            name = record[0:64].split(b'\x00')[0].decode('utf-8').strip()
            if not name:
                return None
            
            # These offsets are approximate - MT5 format varies
            # You may need to adjust based on actual file inspection
            info = MT5SymbolInfo(name=name)
            
            # Try to extract numeric fields
            # Digits typically at offset ~200
            if len(record) >= 208:
                info.digits = struct.unpack('<I', record[200:204])[0]
                if info.digits > 10:  # Sanity check
                    info.digits = 5
            
            # Point value
            info.point = 10 ** (-info.digits)
            
            # Contract size typically around offset 400
            if len(record) >= 408:
                try:
                    info.contract_size = struct.unpack('<d', record[400:408])[0]
                    if info.contract_size <= 0 or info.contract_size > 1000000000:
                        info.contract_size = 100000.0
                except:
                    info.contract_size = 100000.0
            
            # Volume constraints
            if len(record) >= 500:
                try:
                    info.volume_min = struct.unpack('<d', record[480:488])[0]
                    info.volume_max = struct.unpack('<d', record[488:496])[0]
                    info.volume_step = struct.unpack('<d', record[496:504])[0]
                    
                    # Sanity checks
                    if info.volume_min <= 0 or info.volume_min > 100:
                        info.volume_min = 0.01
                    if info.volume_max <= 0 or info.volume_max > 10000:
                        info.volume_max = 100.0
                    if info.volume_step <= 0 or info.volume_step > 1:
                        info.volume_step = 0.01
                except:
                    pass
            
            return info
            
        except Exception as e:
            self.logger.debug(f"Symbol record parse error: {e}")
            return None
    
    def _parse_symbol_file(self, filepath: Path) -> Optional[MT5SymbolInfo]:
        """Parse an individual .sym file."""
        name = filepath.stem
        return MT5SymbolInfo(name=name)
    
    def read_history(self, symbol: str, timeframe: int, count: int = 100) -> List[Dict[str, Any]]:
        """
        Read historical OHLCV data from .hst files.
        
        Timeframe mapping:
        1 = M1, 5 = M5, 15 = M15, 30 = M30, 60 = H1, 240 = H4, 1440 = D1, etc.
        """
        server_dir = self.find_server_dir()
        if not server_dir:
            return []
        
        # Try different history file patterns
        history_dir = server_dir / 'history'
        patterns = [
            f'{symbol}{timeframe}.hst',
            f'{symbol.upper()}{timeframe}.hst',
            f'{symbol.lower()}{timeframe}.hst',
        ]
        
        hst_file = None
        for pattern in patterns:
            candidate = history_dir / pattern
            if candidate.exists():
                hst_file = candidate
                break
        
        if not hst_file:
            self.logger.warning(f"History file not found for {symbol} TF{timeframe}")
            return []
        
        return self._parse_hst_file(hst_file, count)
    
    def _parse_hst_file(self, filepath: Path, count: int = 100) -> List[Dict[str, Any]]:
        """
        Parse MT5 .hst (history) file.
        
        HST file format (version 401):
        Header: 148 bytes
        - version (4 bytes)
        - copyright (64 bytes)
        - symbol (12 bytes)
        - period (4 bytes)
        - digits (4 bytes)
        - timesign (4 bytes)
        - last_sync (4 bytes)
        - unused (52 bytes)
        
        Records: 60 bytes each
        - time (8 bytes, int64)
        - open (8 bytes, double)
        - high (8 bytes, double)
        - low (8 bytes, double)
        - close (8 bytes, double)
        - tick_volume (8 bytes, int64)
        - spread (4 bytes, int32)
        - real_volume (8 bytes, int64)
        """
        rates = []
        
        try:
            with open(filepath, 'rb') as f:
                # Read header
                header = f.read(148)
                if len(header) < 148:
                    return []
                
                version = struct.unpack('<I', header[0:4])[0]
                if version != self.HST_VERSION:
                    self.logger.warning(f"Unknown HST version: {version}")
                
                # Read records from end (most recent first)
                f.seek(0, 2)  # End of file
                file_size = f.tell()
                record_size = 60
                num_records = (file_size - 148) // record_size
                
                # Read last 'count' records
                start_record = max(0, num_records - count)
                f.seek(148 + start_record * record_size)
                
                for _ in range(min(count, num_records)):
                    record = f.read(record_size)
                    if len(record) < record_size:
                        break
                    
                    try:
                        time_val = struct.unpack('<q', record[0:8])[0]
                        open_val = struct.unpack('<d', record[8:16])[0]
                        high_val = struct.unpack('<d', record[16:24])[0]
                        low_val = struct.unpack('<d', record[24:32])[0]
                        close_val = struct.unpack('<d', record[32:40])[0]
                        tick_vol = struct.unpack('<q', record[40:48])[0]
                        spread = struct.unpack('<i', record[48:52])[0]
                        real_vol = struct.unpack('<q', record[52:60])[0]
                        
                        rates.append({
                            'time': datetime.fromtimestamp(time_val, tz=timezone.utc).isoformat(),
                            'open': open_val,
                            'high': high_val,
                            'low': low_val,
                            'close': close_val,
                            'tick_volume': tick_vol,
                            'spread': spread,
                            'real_volume': real_vol,
                        })
                    except Exception as e:
                        self.logger.debug(f"Failed to parse rate record: {e}")
                
        except Exception as e:
            self.logger.error(f"Failed to read HST file: {e}")
        
        return rates
    
    def read_tick_cache(self, symbol: str) -> Optional[MT5Tick]:
        """
        Read latest tick from tick cache file.
        
        MT5 stores tick data in .tkc files in bases/<server>/ticks/
        """
        server_dir = self.find_server_dir()
        if not server_dir:
            return None
        
        ticks_dir = server_dir / 'ticks'
        if not ticks_dir.exists():
            return None
        
        # Look for tick file
        tick_file = ticks_dir / f'{symbol}.tkc'
        if not tick_file.exists():
            tick_file = ticks_dir / f'{symbol.upper()}.tkc'
        if not tick_file.exists():
            return None
        
        try:
            return self._parse_tick_file(tick_file)
        except Exception as e:
            self.logger.error(f"Failed to read tick file: {e}")
            return None
    
    def _parse_tick_file(self, filepath: Path) -> Optional[MT5Tick]:
        """Parse tick cache file to get latest tick."""
        with open(filepath, 'rb') as f:
            # Seek to end to get latest tick
            f.seek(0, 2)
            file_size = f.tell()
            
            # Tick record size is typically 48 bytes
            tick_size = 48
            if file_size < tick_size:
                return None
            
            # Read last tick
            f.seek(file_size - tick_size)
            record = f.read(tick_size)
            
            if len(record) < tick_size:
                return None
            
            # Parse tick
            # Format: time(8), bid(8), ask(8), last(8), volume(8), flags(8)
            time_val = struct.unpack('<q', record[0:8])[0]
            bid = struct.unpack('<d', record[8:16])[0]
            ask = struct.unpack('<d', record[16:24])[0]
            last = struct.unpack('<d', record[24:32])[0]
            volume = struct.unpack('<q', record[32:40])[0]
            
            return MT5Tick(
                time=time_val,
                bid=bid,
                ask=ask,
                last=last,
                volume=volume
            )
    
    def read_account_info(self) -> Optional[MT5AccountInfo]:
        """
        Read account information from config files.
        
        Account info is typically stored in:
        - config/accounts/<account_id>/account.dat
        - Or in the main config files
        """
        config_dir = self.data_dir / 'config'
        if not config_dir.exists():
            return None
        
        # Look for account directories
        accounts_dir = config_dir / 'accounts'
        if accounts_dir.exists():
            for account_dir in accounts_dir.iterdir():
                if account_dir.is_dir():
                    account_file = account_dir / 'account.dat'
                    if account_file.exists():
                        try:
                            return self._parse_account_file(account_file)
                        except Exception as e:
                            self.logger.debug(f"Failed to parse account file: {e}")
        
        return None
    
    def _parse_account_file(self, filepath: Path) -> Optional[MT5AccountInfo]:
        """Parse account.dat file."""
        # Account files are binary with varying formats
        # This is a best-effort parser
        with open(filepath, 'rb') as f:
            data = f.read()
        
        info = MT5AccountInfo()
        
        # Try to extract login (usually first int in file)
        if len(data) >= 8:
            try:
                info.login = struct.unpack('<Q', data[0:8])[0]
            except:
                pass
        
        # Balance/equity are typically stored as doubles
        # Locations vary by MT5 version
        
        return info


class MT5AndroidTrader:
    """
    Executes trades on MT5 Android using various methods.
    
    Methods available:
    1. Android Intent/Activity launch (deeplinks)
    2. Accessibility service automation
    3. File-based order queue (if MT5 supports it)
    """
    
    MT5_PACKAGE = 'net.metaquotes.metatrader5'
    MT5_TRADE_ACTIVITY = 'net.metaquotes.metatrader5.QuoteActivity'
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.logger = logging.getLogger('MT5Trader')
        
        # Order queue for pending trades
        self._order_queue: List[Dict[str, Any]] = []
        
        # Check available trading methods
        self._check_trading_methods()
    
    def _check_trading_methods(self):
        """Detect available trading methods."""
        self.can_use_intents = self._check_android_intents()
        self.can_use_accessibility = self._check_accessibility()
        
        self.logger.info(f"Trading methods: intents={self.can_use_intents}, accessibility={self.can_use_accessibility}")
    
    def _check_android_intents(self) -> bool:
        """Check if we can use Android intents via termux-am."""
        try:
            result = subprocess.run(
                ['termux-am', '--help'],
                capture_output=True,
                timeout=5
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _check_accessibility(self) -> bool:
        """Check if accessibility service is available."""
        # Accessibility automation requires additional setup
        # Return False for now - this is an advanced feature
        return False
    
    def launch_mt5(self) -> bool:
        """Launch MT5 Android app."""
        if not self.can_use_intents:
            self.logger.warning("Cannot launch MT5: intents not available")
            return False
        
        try:
            subprocess.run([
                'termux-am', 'start',
                '-n', f'{self.MT5_PACKAGE}/{self.MT5_TRADE_ACTIVITY}'
            ], check=True, timeout=10)
            return True
        except Exception as e:
            self.logger.error(f"Failed to launch MT5: {e}")
            return False
    
    def open_trade_dialog(self, symbol: str) -> bool:
        """
        Open MT5 trade dialog for a symbol.
        
        Uses MT5's deep link support if available.
        """
        if not self.can_use_intents:
            return False
        
        try:
            # MT5 supports some deep links for navigation
            # This may vary by MT5 version
            subprocess.run([
                'termux-am', 'start',
                '-a', 'android.intent.action.VIEW',
                '-d', f'metatrader5://trade?symbol={symbol}'
            ], check=True, timeout=10)
            return True
        except Exception as e:
            self.logger.error(f"Failed to open trade dialog: {e}")
            return False
    
    def queue_order(self, order: Dict[str, Any]) -> str:
        """
        Queue an order for execution.
        
        Since direct trading API isn't available, we queue orders
        and the user can execute them manually or via automation.
        
        Returns: Order queue ID
        """
        order_id = f"ORD_{int(time.time() * 1000)}"
        order['queue_id'] = order_id
        order['queued_at'] = datetime.now(timezone.utc).isoformat()
        order['status'] = 'QUEUED'
        
        self._order_queue.append(order)
        
        # Save to file for persistence
        self._save_order_queue()
        
        # Try to open trade dialog
        if self.can_use_intents:
            self.open_trade_dialog(order.get('symbol', 'EURUSD'))
        
        self.logger.info(f"Order queued: {order_id}")
        return order_id
    
    def _save_order_queue(self):
        """Save order queue to file."""
        queue_file = self.data_dir / 'order_queue.json'
        try:
            with open(queue_file, 'w') as f:
                json.dump(self._order_queue, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save order queue: {e}")
    
    def load_order_queue(self):
        """Load order queue from file."""
        queue_file = self.data_dir / 'order_queue.json'
        if queue_file.exists():
            try:
                with open(queue_file, 'r') as f:
                    self._order_queue = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load order queue: {e}")
    
    def get_pending_orders(self) -> List[Dict[str, Any]]:
        """Get all pending orders."""
        return [o for o in self._order_queue if o.get('status') == 'QUEUED']
    
    def mark_order_executed(self, order_id: str, ticket: int):
        """Mark an order as executed with the MT5 ticket."""
        for order in self._order_queue:
            if order.get('queue_id') == order_id:
                order['status'] = 'EXECUTED'
                order['ticket'] = ticket
                order['executed_at'] = datetime.now(timezone.utc).isoformat()
                break
        self._save_order_queue()


class MT5AndroidInterface:
    """
    Main interface for MT5 Android integration.
    
    Combines file reading and trading capabilities.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.logger = logging.getLogger('MT5Android')
        
        # Find MT5 data directory
        if data_dir:
            self.data_dir = data_dir
        else:
            self.data_dir = self._detect_data_dir()
        
        if self.data_dir and self.data_dir.exists():
            self.logger.info(f"MT5 data directory: {self.data_dir}")
            self.file_reader = MT5FileReader(self.data_dir)
            self.trader = MT5AndroidTrader(self.data_dir)
            self.available = True
        else:
            self.logger.warning("MT5 data directory not found")
            self.file_reader = None
            self.trader = None
            self.available = False
    
    def _detect_data_dir(self) -> Optional[Path]:
        """Detect MT5 Android data directory."""
        paths = [
            Path('/storage/emulated/0/Android/data/net.metaquotes.metatrader5/files'),
            Path('/sdcard/Android/data/net.metaquotes.metatrader5/files'),
            Path('/data/data/net.metaquotes.metatrader5/files'),
            Path.home() / '.mt5',
            Path.home() / 'MT5',
        ]
        
        for path in paths:
            if path.exists():
                return path
        
        return None
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        if not self.available or not self.file_reader:
            return {'success': False, 'error': 'MT5 interface not available'}
        
        info = self.file_reader.read_account_info()
        if info:
            return {'success': True, 'data': info.to_dict()}
        
        # Return default if can't read
        return {
            'success': True,
            'data': MT5AccountInfo().to_dict(),
            'note': 'Using default values - account file not readable'
        }
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information."""
        if not self.available or not self.file_reader:
            return {'success': False, 'error': 'MT5 interface not available'}
        
        symbols = self.file_reader.read_symbols()
        if symbol in symbols:
            return {'success': True, 'data': symbols[symbol].to_dict()}
        
        # Return default for unknown symbol
        default = MT5SymbolInfo(name=symbol)
        return {
            'success': True,
            'data': default.to_dict(),
            'note': f'Symbol {symbol} not found in cache, using defaults'
        }
    
    def get_tick(self, symbol: str) -> Dict[str, Any]:
        """Get current tick for symbol."""
        if not self.available or not self.file_reader:
            return {'success': False, 'error': 'MT5 interface not available'}
        
        tick = self.file_reader.read_tick_cache(symbol)
        if tick:
            return {'success': True, 'data': tick.to_dict()}
        
        return {'success': False, 'error': f'No tick data for {symbol}'}
    
    def get_rates(self, symbol: str, timeframe: int, count: int = 100) -> Dict[str, Any]:
        """Get historical rates."""
        if not self.available or not self.file_reader:
            return {'success': False, 'error': 'MT5 interface not available'}
        
        rates = self.file_reader.read_history(symbol, timeframe, count)
        return {'success': True, 'data': rates}
    
    def send_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a trading order.
        
        Note: This queues the order since direct API isn't available.
        The order will be flagged for manual or automated execution.
        """
        if not self.available or not self.trader:
            return {'success': False, 'error': 'MT5 interface not available'}
        
        order_id = self.trader.queue_order(order)
        
        return {
            'success': True,
            'data': {
                'queue_id': order_id,
                'status': 'QUEUED',
                'note': 'Order queued - execute manually in MT5 app or enable automation'
            }
        }
    
    def get_pending_orders(self) -> Dict[str, Any]:
        """Get pending orders from queue."""
        if not self.available or not self.trader:
            return {'success': False, 'error': 'MT5 interface not available'}
        
        orders = self.trader.get_pending_orders()
        return {'success': True, 'data': orders}


# Export main interface
__all__ = ['MT5AndroidInterface', 'MT5FileReader', 'MT5AndroidTrader']
