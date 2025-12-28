"""
Prometheus Metrics Exporter

Exports trading metrics in Prometheus format for monitoring and alerting.
Can be served via HTTP or written to a file for node_exporter textfile collector.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class PrometheusMetric:
    """A single Prometheus metric"""
    name: str
    value: float
    metric_type: str  # gauge, counter, histogram
    help_text: str
    labels: Dict[str, str] = None
    
    def to_prometheus_format(self) -> str:
        """Format as Prometheus text format."""
        lines = []
        
        # HELP line
        lines.append(f"# HELP {self.name} {self.help_text}")
        # TYPE line
        lines.append(f"# TYPE {self.name} {self.metric_type}")
        
        # Value line with optional labels
        if self.labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in self.labels.items())
            lines.append(f"{self.name}{{{label_str}}} {self.value}")
        else:
            lines.append(f"{self.name} {self.value}")
        
        return "\n".join(lines)


class PrometheusExporter:
    """
    Prometheus metrics exporter for Cthulhu trading system.
    
    Exports metrics such as:
    - Trade count (total, wins, losses)
    - PnL (net profit, daily, per symbol)
    - Performance (win rate, profit factor, Sharpe)
    - System health (MT5 connected, uptime)
    """
    
    def __init__(self, prefix: str = "cthulhu"):
        """
        Initialize Prometheus exporter.
        
        Args:
            prefix: Metric name prefix
        """
        self.logger = logging.getLogger("cthulhu.prometheus")
        self.prefix = prefix
        self._start_time = time.time()
        self._metrics_cache: Dict[str, PrometheusMetric] = {}
        
        # Initialize counters
        self._trade_count = 0
        self._win_count = 0
        self._loss_count = 0
        self._total_profit = 0.0
        self._total_loss = 0.0
        
    def record_trade(self, profit: float, symbol: str = "unknown"):
        """Record a trade result."""
        self._trade_count += 1
        if profit > 0:
            self._win_count += 1
            self._total_profit += profit
        elif profit < 0:
            self._loss_count += 1
            self._total_loss += abs(profit)
            
    def set_connection_status(self, connected: bool):
        """Set MT5 connection status."""
        self._update_metric(
            f"{self.prefix}_mt5_connected",
            1 if connected else 0,
            "gauge",
            "MT5 terminal connection status (1=connected, 0=disconnected)"
        )
        
    def set_account_balance(self, balance: float, equity: float):
        """Set account balance metrics."""
        self._update_metric(
            f"{self.prefix}_account_balance",
            balance,
            "gauge",
            "Current account balance"
        )
        self._update_metric(
            f"{self.prefix}_account_equity",
            equity,
            "gauge",
            "Current account equity"
        )
        
    def set_open_positions(self, count: int, total_volume: float = 0.0):
        """Set open positions metrics."""
        self._update_metric(
            f"{self.prefix}_open_positions",
            count,
            "gauge",
            "Number of open positions"
        )
        self._update_metric(
            f"{self.prefix}_open_volume",
            total_volume,
            "gauge",
            "Total volume of open positions"
        )

    def record_sl_tp_success(self, ticket: int, symbol: str = "unknown"):
        """Record a successful SL/TP application for observability."""
        self._update_metric(
            f"{self.prefix}_sl_tp_success_total",
            1.0,
            "counter",
            "Count of successful SL/TP modifications applied to broker",
            labels={"symbol": symbol, "ticket": str(ticket)}
        )

    def record_sl_tp_failure(self, ticket: int, symbol: str = "unknown"):
        """Record a failed SL/TP modification for observability."""
        self._update_metric(
            f"{self.prefix}_sl_tp_failure_total",
            1.0,
            "counter",
            "Count of failed SL/TP modifications applied to broker",
            labels={"symbol": symbol, "ticket": str(ticket)}
        )
        
    def set_drawdown(self, drawdown_pct: float):
        """Set current drawdown percentage."""
        self._update_metric(
            f"{self.prefix}_drawdown_percent",
            drawdown_pct * 100,
            "gauge",
            "Current drawdown percentage"
        )
        
    def _update_metric(self, name: str, value: float, metric_type: str, help_text: str, labels: Dict[str, str] = None):
        """Update or create a metric."""
        self._metrics_cache[name] = PrometheusMetric(
            name=name,
            value=value,
            metric_type=metric_type,
            help_text=help_text,
            labels=labels
        )
        
    def get_all_metrics(self) -> List[PrometheusMetric]:
        """Get all current metrics."""
        # Update computed metrics
        self._update_computed_metrics()
        return list(self._metrics_cache.values())
    
    def _update_computed_metrics(self):
        """Update computed/derived metrics."""
        # Uptime
        uptime = time.time() - self._start_time
        self._update_metric(
            f"{self.prefix}_uptime_seconds",
            uptime,
            "counter",
            "Cthulhu uptime in seconds"
        )
        
        # Trade counters
        self._update_metric(
            f"{self.prefix}_trades_total",
            self._trade_count,
            "counter",
            "Total number of trades"
        )
        self._update_metric(
            f"{self.prefix}_trades_won",
            self._win_count,
            "counter",
            "Number of winning trades"
        )
        self._update_metric(
            f"{self.prefix}_trades_lost",
            self._loss_count,
            "counter",
            "Number of losing trades"
        )
        
        # PnL
        net_profit = self._total_profit - self._total_loss
        self._update_metric(
            f"{self.prefix}_pnl_total",
            net_profit,
            "gauge",
            "Total net profit/loss"
        )
        self._update_metric(
            f"{self.prefix}_profit_total",
            self._total_profit,
            "counter",
            "Total gross profit"
        )
        self._update_metric(
            f"{self.prefix}_loss_total",
            self._total_loss,
            "counter",
            "Total gross loss"
        )
        
        # Win rate
        win_rate = self._win_count / self._trade_count if self._trade_count > 0 else 0
        self._update_metric(
            f"{self.prefix}_win_rate",
            win_rate,
            "gauge",
            "Win rate (0-1)"
        )
        
        # Profit factor
        profit_factor = self._total_profit / self._total_loss if self._total_loss > 0 else 0
        self._update_metric(
            f"{self.prefix}_profit_factor",
            profit_factor,
            "gauge",
            "Profit factor (gross profit / gross loss)"
        )

    def update_from_metrics_dict(self, metrics: Dict[str, Any]):
        """Update exporter metrics from a PerformanceMetrics.to_dict() output.

        This method maps commonly used performance keys to Prometheus gauges/counters
        and labels per-symbol metrics where available.
        """
        try:
            # Basic counts and PnL
            self._update_metric(f"{self.prefix}_trades_total", metrics.get('total_trades', 0), 'counter', 'Total number of trades')
            self._update_metric(f"{self.prefix}_trades_won", metrics.get('winning_trades', 0), 'counter', 'Winning trades')
            self._update_metric(f"{self.prefix}_trades_lost", metrics.get('losing_trades', 0), 'counter', 'Losing trades')
            self._update_metric(f"{self.prefix}_pnl_total", metrics.get('net_profit', 0.0), 'gauge', 'Net profit/loss')
            self._update_metric(f"{self.prefix}_profit_total", metrics.get('gross_profit', 0.0), 'counter', 'Gross profit')
            self._update_metric(f"{self.prefix}_loss_total", metrics.get('gross_loss', 0.0), 'counter', 'Gross loss')
            self._update_metric(f"{self.prefix}_win_rate", metrics.get('win_rate', 0.0), 'gauge', 'Win rate (0-1)')
            self._update_metric(f"{self.prefix}_profit_factor", metrics.get('profit_factor', 0.0) or 0.0, 'gauge', 'Profit factor')

            # Drawdown magnitudes
            self._update_metric(f"{self.prefix}_drawdown_percent", metrics.get('max_drawdown_pct', 0.0) * 100.0, 'gauge', 'Max drawdown percent')
            self._update_metric(f"{self.prefix}_drawdown_abs", metrics.get('max_drawdown_abs', 0.0), 'gauge', 'Max drawdown absolute')

            # Drawdown durations
            self._update_metric(f"{self.prefix}_drawdown_duration_seconds", metrics.get('max_drawdown_duration_seconds', 0.0), 'gauge', 'Max drawdown duration in seconds')
            self._update_metric(f"{self.prefix}_current_drawdown_duration_seconds", metrics.get('current_drawdown_duration_seconds', 0.0), 'gauge', 'Current drawdown duration in seconds')

            # Risk/Reward and expectancy
            self._update_metric(f"{self.prefix}_avg_rr", metrics.get('avg_risk_reward', 0.0) or 0.0, 'gauge', 'Average risk:reward')
            self._update_metric(f"{self.prefix}_median_rr", metrics.get('median_risk_reward', 0.0) or 0.0, 'gauge', 'Median risk:reward')
            self._update_metric(f"{self.prefix}_rr_count", metrics.get('rr_count', 0), 'counter', 'Risk:Reward count')
            self._update_metric(f"{self.prefix}_expectancy", metrics.get('expectancy', 0.0) or 0.0, 'gauge', 'Expectancy per trade')

            # Sharpe metrics
            self._update_metric(f"{self.prefix}_sharpe", metrics.get('sharpe_ratio', 0.0) or 0.0, 'gauge', 'Sharpe ratio')
            self._update_metric(f"{self.prefix}_rolling_sharpe", metrics.get('rolling_sharpe', 0.0) or 0.0, 'gauge', 'Rolling Sharpe ratio')

            # Per-symbol metrics
            sym_map = metrics.get('symbol_aggregates', {}) or {}
            for s, v in sym_map.items():
                labels = {'symbol': s}
                self._update_metric(f"{self.prefix}_symbol_realized_pnl", v.get('realized_pnl', 0.0), 'gauge', 'Realized PnL per symbol', labels=labels)
                self._update_metric(f"{self.prefix}_symbol_unrealized_pnl", v.get('unrealized_pnl', 0.0), 'gauge', 'Unrealized PnL per symbol', labels=labels)
                self._update_metric(f"{self.prefix}_symbol_open_positions", v.get('open_positions', 0), 'gauge', 'Open positions per symbol', labels=labels)
                self._update_metric(f"{self.prefix}_symbol_exposure", v.get('exposure', 0.0), 'gauge', 'Exposure per symbol', labels=labels)

        except Exception as e:
            self.logger.exception(f"Failed to update metrics from performance snapshot: {e}")
    
    def export_text(self) -> str:
        """
        Export all metrics as Prometheus text format.
        
        Returns:
            String in Prometheus exposition format
        """
        metrics = self.get_all_metrics()
        lines = []
        
        for metric in metrics:
            lines.append(metric.to_prometheus_format())
            lines.append("")  # Empty line between metrics
        
        return "\n".join(lines)
    
    def write_to_file(self, path: str = "/tmp/cthulhu_metrics.prom"):
        """
        Write metrics to a file for node_exporter textfile collector.
        
        Args:
            path: Output file path
        """
        try:
            content = self.export_text()
            # Write atomically
            temp_path = Path(path).with_suffix(".tmp")
            temp_path.write_text(content)
            temp_path.rename(path)
            self.logger.debug(f"Metrics written to {path}")
        except Exception as e:
            self.logger.error(f"Failed to write metrics: {e}")
    
    def get_metrics_dict(self) -> Dict[str, Any]:
        """
        Get metrics as dictionary (for JSON export).
        
        Returns:
            Dict of metric names to values
        """
        metrics = self.get_all_metrics()
        return {m.name: m.value for m in metrics}
