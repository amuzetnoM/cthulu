"""
Database Persistence - Clean Implementation
SQLite-based persistence for trades, signals, and metrics.
"""
import logging
import sqlite3
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class Database:
    """
    SQLite database for Cthulu persistence.
    
    Tables:
    - trades: Trade history
    - signals: Signal history
    - metrics: Performance metrics
    """
    
    def __init__(self, db_name: str = "cthulu.db"):
        """
        Initialize database.
        
        Args:
            db_name: Database filename
        """
        self.db_path = Path(db_name)
        self._local = threading.local()
        self._init_database()
        
        logger.info(f"Database initialized: {db_name}")
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn
    
    def _init_database(self):
        """Create tables if they don't exist."""
        conn = self.connection
        cursor = conn.cursor()
        
        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket INTEGER UNIQUE,
                symbol TEXT,
                direction TEXT,
                volume REAL,
                entry_price REAL,
                exit_price REAL,
                sl REAL,
                tp REAL,
                profit REAL,
                strategy TEXT,
                signal_id TEXT,
                open_time TEXT,
                close_time TEXT,
                status TEXT DEFAULT 'open',
                metadata TEXT
            )
        """)
        
        # Signals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT UNIQUE,
                symbol TEXT,
                direction TEXT,
                strategy TEXT,
                confidence REAL,
                confluence_score INTEGER,
                regime TEXT,
                timestamp TEXT,
                executed INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)
        
        # Metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                balance REAL,
                equity REAL,
                open_positions INTEGER,
                unrealized_pnl REAL,
                daily_pnl REAL,
                win_rate REAL,
                metadata TEXT
            )
        """)
        
        conn.commit()
    
    def record_trade(
        self,
        ticket: int,
        symbol: str,
        direction: str,
        volume: float,
        entry_price: float,
        sl: float = 0,
        tp: float = 0,
        strategy: str = "",
        signal_id: str = ""
    ):
        """Record a new trade."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO trades 
                (ticket, symbol, direction, volume, entry_price, sl, tp, strategy, signal_id, open_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
            """, (ticket, symbol, direction, volume, entry_price, sl, tp, strategy, signal_id, datetime.now().isoformat()))
            self.connection.commit()
        except Exception as e:
            logger.error(f"Failed to record trade: {e}")
    
    def close_trade(
        self,
        ticket: int,
        exit_price: float,
        profit: float
    ):
        """Close a trade record."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE trades 
                SET exit_price = ?, profit = ?, close_time = ?, status = 'closed'
                WHERE ticket = ?
            """, (exit_price, profit, datetime.now().isoformat(), ticket))
            self.connection.commit()
        except Exception as e:
            logger.error(f"Failed to close trade record: {e}")
    
    def record_signal(
        self,
        signal_id: str,
        symbol: str,
        direction: str,
        strategy: str,
        confidence: float,
        confluence_score: int = 0,
        regime: str = ""
    ):
        """Record a signal."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO signals
                (signal_id, symbol, direction, strategy, confidence, confluence_score, regime, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (signal_id, symbol, direction, strategy, confidence, confluence_score, regime, datetime.now().isoformat()))
            self.connection.commit()
        except Exception as e:
            logger.error(f"Failed to record signal: {e}")
    
    def mark_signal_executed(self, signal_id: str):
        """Mark a signal as executed."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE signals SET executed = 1 WHERE signal_id = ?", (signal_id,))
            self.connection.commit()
        except Exception as e:
            logger.error(f"Failed to mark signal executed: {e}")
    
    def record_metrics(
        self,
        balance: float,
        equity: float,
        open_positions: int,
        unrealized_pnl: float,
        daily_pnl: float = 0,
        win_rate: float = 0
    ):
        """Record performance metrics snapshot."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO metrics
                (timestamp, balance, equity, open_positions, unrealized_pnl, daily_pnl, win_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (datetime.now().isoformat(), balance, equity, open_positions, unrealized_pnl, daily_pnl, win_rate))
            self.connection.commit()
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")
    
    def get_trade_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trade history."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM trades 
                ORDER BY id DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get trade history: {e}")
            return []
    
    def get_win_rate(self, period_days: int = 30) -> float:
        """Calculate win rate for period."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN profit > 0 THEN 1 END) as wins,
                    COUNT(*) as total
                FROM trades 
                WHERE status = 'closed' 
                AND close_time > datetime('now', ?)
            """, (f'-{period_days} days',))
            row = cursor.fetchone()
            if row and row['total'] > 0:
                return row['wins'] / row['total']
            return 0.5
        except Exception as e:
            logger.error(f"Failed to calculate win rate: {e}")
            return 0.5
    
    def close(self):
        """Close database connection."""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
