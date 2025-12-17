"""
ML instrumentation and lightweight collector.
Writes JSONL entries to `ML_RL/data/raw/` and provides simple rotate-by-size logic.
"""
from __future__ import annotations
import os
import json
import gzip
import time
from datetime import datetime
from threading import Lock
from typing import Dict, Any, Optional

BASE = os.path.join(os.path.dirname(__file__), 'data', 'raw')
os.makedirs(BASE, exist_ok=True)

class MLDataCollector:
    """Simple, fast JSONL event collector.

    Usage:
        collector = MLDataCollector()
        collector.record_event('order', {...})
        collector.record_event('execution', {...})
    """
    def __init__(self, prefix: str = 'events', rotate_size_bytes: int = 10_000_000):
        self.prefix = prefix
        self.rotate_size_bytes = rotate_size_bytes
        self._lock = Lock()
        self._open_file = None
        self._open_path = None
        self._open_handle = None
        self._ensure_rotated()

    def _path(self):
        ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        return os.path.join(BASE, f"{self.prefix}.{ts}.jsonl.gz")

    def _ensure_rotated(self):
        with self._lock:
            if self._open_handle:
                try:
                    size = os.path.getsize(self._open_path)
                except Exception:
                    size = 0
                if size >= self.rotate_size_bytes:
                    try:
                        self._open_handle.close()
                    except Exception:
                        pass
                    self._open_handle = None
                    self._open_path = None
            if not self._open_handle:
                self._open_path = self._path()
                self._open_handle = gzip.open(self._open_path, 'at', encoding='utf-8')

    def record_event(self, event_type: str, payload: Dict[str, Any]):
        entry = {
            'ts': datetime.utcnow().isoformat() + 'Z',
            'event_type': event_type,
            'payload': payload
        }
        line = json.dumps(entry, default=str)
        with self._lock:
            self._ensure_rotated()
            try:
                self._open_handle.write(line + "\n")
                self._open_handle.flush()
            except Exception:
                # best-effort: fallback to append to a timestamped file uncompressed
                fallback = os.path.join(BASE, f"{self.prefix}.fallback.{int(time.time())}.jsonl")
                with open(fallback, 'a', encoding='utf-8') as f:
                    f.write(line + "\n")

    def record_order(self, order_req: Dict[str, Any]):
        self.record_event('order_request', order_req)

    def record_execution(self, exec_result: Dict[str, Any]):
        self.record_event('execution', exec_result)

    def record_market_snapshot(self, snapshot: Dict[str, Any]):
        self.record_event('market_snapshot', snapshot)
