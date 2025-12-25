"""
Metrics Module

Performance metrics collection and reporting.
Tracks PnL, trades, win rate, Sharpe ratio, max drawdown.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import statistics


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: datetime
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    net_profit: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    positions_opened: int = 0
    returns: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'net_profit': self.net_profit,
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'positions_opened': self.positions_opened,
        }


class MetricsCollector:
    """
    Metrics collection and calculation engine.
    
    Tracks trading performance metrics:
    - PnL tracking (total, daily, per-symbol)
    - Win rate and profit factor
    - Sharpe ratio
    - Maximum drawdown
    - Trade statistics
    """
    
    def __init__(self, database=None):
        """Initialize metrics collector."""
        self.logger = logging.getLogger("herald.metrics")
        self.database = database
        self.trade_results: List[float] = []
        self.equity_curve: List[float] = [0.0]
        self.peak_equity: float = 0.0
        self.max_drawdown: float = 0.0
        
        # Counters
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        # Open positions counter
        self.positions_opened = 0
        
        # Load historical trades if database is available
        if self.database:
            self._load_historical_trades()
        
    def _load_historical_trades(self):
        """Load historical closed trades from database and replay them."""
        try:
            # Get all closed trades with profit
            cursor = self.database.conn.cursor()
            cursor.execute("""
                SELECT profit, symbol FROM trades
                WHERE status = 'CLOSED' AND profit IS NOT NULL
                ORDER BY exit_time ASC
            """)
            
            for row in cursor.fetchall():
                profit = row['profit']
                symbol = row['symbol']
                # Replay the trade without incrementing positions_opened
                self._record_trade_internal(profit, symbol, update_positions=False)
                
            self.logger.info(f"Loaded {self.total_trades} historical trades from database")
            
        except Exception as e:
            self.logger.warning(f"Failed to load historical trades: {e}")
        
    def record_trade(self, profit: float, symbol: str):
        """
        Record trade result.
        
        Args:
            profit: Trade profit/loss
            symbol: Trading symbol
        """
        self._record_trade_internal(profit, symbol, update_positions=True)
        
    def _record_trade_internal(self, profit: float, symbol: str, update_positions: bool = True):
        self.total_trades += 1
        self.trade_results.append(profit)
        
        if profit > 0:
            self.winning_trades += 1
            self.total_profit += profit
        elif profit < 0:
            self.losing_trades += 1
            self.total_loss += abs(profit)
            
        # Update equity curve
        current_equity = self.equity_curve[-1] + profit
        self.equity_curve.append(current_equity)
        
        # Update drawdown
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        
        if self.peak_equity > 0:
            drawdown = (self.peak_equity - current_equity) / self.peak_equity
            if drawdown > self.max_drawdown:
                self.max_drawdown = drawdown
                
        self.logger.debug(
            f"Trade recorded: {profit:+.2f} on {symbol} | "
            f"Total trades: {self.total_trades} | "
            f"Net P&L: {current_equity:+.2f}"
        )

    def record_position_opened(self):
        """
        Record that a new position was opened/tracked by the system.
        This does not imply a closed trade; it is useful for observability.
        """
        try:
            self.positions_opened += 1
            self.logger.debug(f"Position opened recorded: total_opened={self.positions_opened}")
        except Exception:
            pass
        
    def get_metrics(self) -> PerformanceMetrics:
        """
        Calculate current performance metrics.
        
        Returns:
            PerformanceMetrics snapshot
        """
        metrics = PerformanceMetrics(timestamp=datetime.now())
        
        metrics.total_trades = self.total_trades
        metrics.winning_trades = self.winning_trades
        metrics.losing_trades = self.losing_trades
        metrics.total_profit = self.total_profit
        metrics.total_loss = self.total_loss
        
        # Net profit
        metrics.net_profit = self.total_profit - self.total_loss
        
        # Win rate
        if self.total_trades > 0:
            metrics.win_rate = self.winning_trades / self.total_trades
            
        # Average win/loss
        if self.winning_trades > 0:
            metrics.avg_win = self.total_profit / self.winning_trades
        if self.losing_trades > 0:
            metrics.avg_loss = self.total_loss / self.losing_trades
            
        # Profit factor
        if self.total_loss > 0:
            metrics.profit_factor = self.total_profit / self.total_loss
            
        # Max drawdown
        metrics.max_drawdown = self.max_drawdown
        # Open positions
        try:
            metrics.positions_opened = self.positions_opened
        except Exception:
            metrics.positions_opened = 0
        
        # Sharpe ratio (simplified)
        if len(self.trade_results) > 1:
            avg_return = statistics.mean(self.trade_results)
            std_return = statistics.stdev(self.trade_results)
            if std_return > 0:
                metrics.sharpe_ratio = (avg_return / std_return) * (252 ** 0.5)  # Annualized
                
        metrics.returns = self.trade_results.copy()
        
        return metrics
        
    def print_summary(self):
        """Print metrics summary to log."""
        metrics = self.get_metrics()
        
        self.logger.info("=" * 60)
        self.logger.info("PERFORMANCE SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Trades:    {metrics.total_trades}")
        self.logger.info(f"Winning Trades:  {metrics.winning_trades}")
        self.logger.info(f"Losing Trades:   {metrics.losing_trades}")
        self.logger.info(f"Win Rate:        {metrics.win_rate:.1%}")
        self.logger.info(f"Net Profit:      {metrics.net_profit:+.2f}")
        self.logger.info(f"Avg Win:         {metrics.avg_win:.2f}")
        self.logger.info(f"Avg Loss:        {metrics.avg_loss:.2f}")
        self.logger.info(f"Profit Factor:   {metrics.profit_factor:.2f}")
        self.logger.info(f"Max Drawdown:    {metrics.max_drawdown:.1%}")
        self.logger.info(f"Positions Opened: {getattr(metrics, 'positions_opened', 0)}")
        self.logger.info(f"Sharpe Ratio:    {metrics.sharpe_ratio:.2f}")
        self.logger.info("=" * 60)
        
    def reset(self):
        """Reset all metrics."""
        self.trade_results.clear()
        self.equity_curve = [0.0]
        self.peak_equity = 0.0
        self.max_drawdown = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        self.logger.info("Metrics reset")
