"""
Database Module

Implements SQLite-based persistence for trades, signals, and metrics.
Provides historical retention and export capabilities.
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class TradeRecord:
    """Trade record structure"""
    id: Optional[int] = None
    signal_id: str = ""
    order_id: Optional[int] = None
    symbol: str = ""
    side: str = ""
    volume: float = 0.0
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    profit: Optional[float] = None
    status: str = "OPEN"
    exit_reason: str = ""
    metadata: str = ""  # JSON string


@dataclass
class SignalRecord:
    """Signal record structure"""
    id: Optional[int] = None
    signal_id: str = ""
    timestamp: Optional[datetime] = None
    symbol: str = ""
    timeframe: str = ""
    side: str = ""
    action: str = ""
    confidence: float = 0.0
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: str = ""
    executed: bool = False
    metadata: str = ""  # JSON string


class Database:
    """
    SQLite database manager for trade and signal persistence.
    
    Responsibilities:
    - Store all trades, signals, and execution results
    - Provide query interface for analytics
    - Historical data retention
    - Export capabilities
    """
    
    def __init__(self, db_path: str = "herald.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.logger = logging.getLogger("herald.persistence")
        self.conn: Optional[sqlite3.Connection] = None
        
        # Create database directory if needed
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_db()
        
    def _initialize_db(self):
        """Create database tables if they don't exist."""
        try:
            self.conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self.conn.row_factory = sqlite3.Row
            
            cursor = self.conn.cursor()
            
            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT NOT NULL,
                    order_id INTEGER,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    volume REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    entry_time TIMESTAMP NOT NULL,
                    exit_time TIMESTAMP,
                    profit REAL,
                    status TEXT DEFAULT 'OPEN',
                    exit_reason TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Signals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT UNIQUE NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    side TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    reason TEXT,
                    executed BOOLEAN DEFAULT FALSE,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)")
            
            self.conn.commit()
            self.logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}", exc_info=True)
            raise
            
    def record_signal(self, signal_record: SignalRecord) -> int:
        """
        Record a trading signal.
        
        Args:
            signal_record: Signal record to store
            
        Returns:
            Database row ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO signals (
                    signal_id, timestamp, symbol, timeframe, side, action,
                    confidence, price, stop_loss, take_profit, reason, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_record.signal_id,
                signal_record.timestamp,
                signal_record.symbol,
                signal_record.timeframe,
                signal_record.side,
                signal_record.action,
                signal_record.confidence,
                signal_record.price,
                signal_record.stop_loss,
                signal_record.take_profit,
                signal_record.reason,
                signal_record.metadata
            ))
            self.conn.commit()
            
            row_id = cursor.lastrowid
            self.logger.debug(f"Signal recorded: {signal_record.signal_id} (ID: {row_id})")
            return row_id
            
        except Exception as e:
            self.logger.error(f"Failed to record signal: {e}", exc_info=True)
            return -1
            
    def record_trade(self, trade_record: TradeRecord) -> int:
        """
        Record a trade entry.
        
        Args:
            trade_record: Trade record to store
            
        Returns:
            Database row ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO trades (
                    signal_id, order_id, symbol, side, volume, entry_price,
                    stop_loss, take_profit, entry_time, status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_record.signal_id,
                trade_record.order_id,
                trade_record.symbol,
                trade_record.side,
                trade_record.volume,
                trade_record.entry_price,
                trade_record.stop_loss,
                trade_record.take_profit,
                trade_record.entry_time,
                trade_record.status,
                trade_record.metadata
            ))
            self.conn.commit()
            
            row_id = cursor.lastrowid
            self.logger.info(f"Trade recorded: {trade_record.symbol} {trade_record.side} (ID: {row_id})")
            return row_id
            
        except Exception as e:
            self.logger.error(f"Failed to record trade: {e}", exc_info=True)
            return -1
            
    def update_trade_exit(
        self,
        order_id: int,
        exit_price: float,
        exit_time: datetime,
        profit: float,
        exit_reason: str
    ) -> bool:
        """
        Update trade with exit information.
        
        Args:
            order_id: MT5 order ticket
            exit_price: Exit price
            exit_time: Exit timestamp
            profit: Realized profit/loss
            exit_reason: Reason for exit
            
        Returns:
            True if updated successfully
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE trades
                SET exit_price = ?,
                    exit_time = ?,
                    profit = ?,
                    status = 'CLOSED',
                    exit_reason = ?
                WHERE order_id = ?
            """, (exit_price, exit_time, profit, exit_reason, order_id))
            self.conn.commit()
            
            if cursor.rowcount > 0:
                self.logger.info(f"Trade exit recorded: Order #{order_id} | Profit: {profit:.2f}")
                return True
            else:
                self.logger.warning(f"Trade not found for update: Order #{order_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update trade exit: {e}", exc_info=True)
            return False
            
    def get_open_trades(self) -> List[TradeRecord]:
        """
        Get all open trades.
        
        Returns:
            List of open trade records
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM trades
                WHERE status = 'OPEN'
                ORDER BY entry_time DESC
            """)
            
            trades = []
            for row in cursor.fetchall():
                trades.append(TradeRecord(
                    id=row['id'],
                    signal_id=row['signal_id'],
                    order_id=row['order_id'],
                    symbol=row['symbol'],
                    side=row['side'],
                    volume=row['volume'],
                    entry_price=row['entry_price'],
                    exit_price=row['exit_price'],
                    stop_loss=row['stop_loss'],
                    take_profit=row['take_profit'],
                    entry_time=row['entry_time'],
                    exit_time=row['exit_time'],
                    profit=row['profit'],
                    status=row['status'],
                    exit_reason=row['exit_reason'],
                    metadata=row['metadata']
                ))
            
            return trades
            
        except Exception as e:
            self.logger.error(f"Failed to get open trades: {e}", exc_info=True)
            return []
            
    def record_metric(self, name: str, value: float, metadata: str = "") -> bool:
        """
        Record a performance metric.
        
        Args:
            name: Metric name
            value: Metric value
            metadata: Additional metadata (JSON)
            
        Returns:
            True if recorded successfully
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO metrics (timestamp, metric_name, metric_value, metadata)
                VALUES (?, ?, ?, ?)
            """, (datetime.now(), name, value, metadata))
            self.conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to record metric: {e}", exc_info=True)
            return False
            
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed")
