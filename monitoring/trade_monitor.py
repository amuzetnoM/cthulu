"""
Background trade monitor responsible for:
- Polling tracked positions
- Verifying SL/TP readbacks and scheduling/reporting retries
- Recording ML events for position state changes and market snapshots
- Exposing a simple API to start/stop the monitor
"""
from __future__ import annotations
import threading
import time
import logging
from typing import Optional
from herald.position.manager import PositionManager
from herald.position.trade_manager import TradeManager

logger = logging.getLogger('herald.monitor')

class TradeMonitor:
    def __init__(self, position_manager: PositionManager, trade_manager: Optional[TradeManager] = None, poll_interval: float = 5.0, ml_collector: Optional[object] = None, news_manager: Optional[object] = None, news_alert_window: int = 600):
        self.position_manager = position_manager
        self.trade_manager = trade_manager
        self.poll_interval = poll_interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True, name='trade-monitor')
        self.ml_collector = ml_collector
        self.news_manager = news_manager
        self.news_alert_window = news_alert_window  # seconds to pause trading after a high-impact event

    def start(self):
        logger.info('Starting TradeMonitor')
        self._stop.clear()
        if not self._thread.is_alive():
            self._thread = threading.Thread(target=self._loop, daemon=True, name='trade-monitor')
            self._thread.start()

    def stop(self):
        logger.info('Stopping TradeMonitor')
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _loop(self):
        while not self._stop.is_set():
            try:
                self._scan_and_record()
            except Exception:
                logger.exception('Error in TradeMonitor cycle')
            self._stop.wait(self.poll_interval)

    def _scan_and_record(self):
        # Iterate positions and check SL/TP verification and state
        for ticket, pos in list(self.position_manager._positions.items()):
            try:
                # Read back values from MT5 where possible (PositionManager keeps cached values)
                sl = pos.stop_loss
                tp = pos.take_profit
                unrealized = pos.unrealized_pnl
                # Record an ML event for position snapshot
                try:
                    if self.ml_collector:
                        payload = {
                            'ticket': ticket,
                            'symbol': pos.symbol,
                            'volume': pos.volume,
                            'sl': sl,
                            'tp': tp,
                            'unrealized_pnl': unrealized,
                            'timestamp': time.time()
                        }
                        self.ml_collector.record_market_snapshot(payload)
                except Exception:
                    logger.exception('ML collector failed to record market snapshot')

                # If SL/TP are unset (0 or None) then log/warn
                if (not sl or sl == 0.0) or (not tp or tp == 0.0):
                    logger.warning(f'Position #{ticket} missing SL/TP: sl={sl}, tp={tp}')

            except Exception:
                logger.exception(f'Error scanning position {ticket}')

        # Report pending SL/TP retries from TradeManager if available
        try:
            if self.trade_manager and getattr(self.trade_manager, '_pending_sl_tp', None):
                pending = self.trade_manager._pending_sl_tp.copy()
                if pending:
                    logger.info(f"Pending SL/TP retries: {len(pending)} ticket(s)")
                    try:
                        if self.ml_collector:
                            for tkt, info in pending.items():
                                payload = {
                                    'ticket': tkt,
                                    'sl': info.get('sl'),
                                    'tp': info.get('tp'),
                                    'attempts': info.get('attempts'),
                                    'next_retry_ts': info.get('next_retry_ts')
                                }
                                self.ml_collector.record_event('monitor.pending_sl_tp', payload)
                    except Exception:
                        logger.exception('ML collector failed to record pending SL/TP')

        except Exception:
            logger.exception('Failed to inspect pending SL/TP')

        # Also emit a heartbeat ML event
        try:
            if self.ml_collector:
                self.ml_collector.record_event('monitor.heartbeat', {'ts': time.time()})
        except Exception:
            logger.exception('Failed to emit monitor heartbeat')

        # Check for recent news / calendar events and emit alerts or pause trading
        try:
            if self.news_manager:
                events = self.news_manager.fetch_recent() or []
                for e in events:
                    try:
                        importance = None
                        if isinstance(e.meta, dict):
                            importance = e.meta.get('importance') or e.meta.get('impact')
                        # Normalize string
                        if isinstance(importance, str):
                            importance = importance.strip().lower()
                        if importance == 'high' or (e.provider and 'tradingeconomics' in e.provider.lower() and importance is None):
                            logger.info(f'High-impact event detected: {e.headline}')
                            # Record ML alert
                            if self.ml_collector:
                                self.ml_collector.record_event('monitor.news_alert', {'provider': e.provider, 'headline': e.headline, 'symbol': e.symbol, 'ts': e.ts, 'importance': importance})
                            # Pause trading if trade_manager available
                            if self.trade_manager:
                                self.trade_manager.pause_trading(self.news_alert_window)
                    except Exception:
                        logger.exception('Failed to process news event in TradeMonitor')
        except Exception:
            logger.exception('Failed to fetch news events')

        return
