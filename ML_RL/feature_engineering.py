"""
ML/RL Feature Engineering Module

Extracts features from raw JSONL event streams for model training.
Fully decoupled from main trading loop - processes data asynchronously.
"""

import gzip
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from collections import deque, defaultdict
import glob
import os


@dataclass
class TradeFeatures:
    """Features extracted for a single trade."""
    # Market context
    symbol: str
    timestamp: datetime
    hour_of_day: int
    day_of_week: int
    
    # Technical indicators (if available)
    volatility: float = 0.0
    trend_strength: float = 0.0
    volume_profile: float = 0.0
    
    # Strategy context
    strategy_name: str = "unknown"
    signal_confidence: float = 0.0
    
    # Risk metrics
    position_size: float = 0.0
    stop_loss_pct: float = 0.0
    take_profit_pct: float = 0.0
    
    # Execution quality
    slippage: float = 0.0
    execution_time_ms: float = 0.0
    
    # Outcome (target variable)
    pnl: float = 0.0
    was_win: bool = False
    hold_time_minutes: float = 0.0
    
    # Regime
    market_regime: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'hour_of_day': self.hour_of_day,
            'day_of_week': self.day_of_week,
            'volatility': self.volatility,
            'trend_strength': self.trend_strength,
            'volume_profile': self.volume_profile,
            'strategy_name': self.strategy_name,
            'signal_confidence': self.signal_confidence,
            'position_size': self.position_size,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'slippage': self.slippage,
            'execution_time_ms': self.execution_time_ms,
            'pnl': self.pnl,
            'was_win': self.was_win,
            'hold_time_minutes': self.hold_time_minutes,
            'market_regime': self.market_regime
        }


class FeatureExtractor:
    """
    Extract features from ML_RL event streams.
    
    Processes JSONL files to create training datasets for ML models.
    Fully decoupled - reads from disk, doesn't interact with live system.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize feature extractor.
        
        Args:
            data_dir: Directory containing JSONL event files
        """
        self.logger = logging.getLogger("Cthulu.ml_features")
        
        if data_dir is None:
            # Default to ML_RL/data/raw
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, 'data', 'raw')
        
        self.data_dir = data_dir
        self.logger.info(f"FeatureExtractor initialized with data_dir: {data_dir}")
        
        # Track open positions for calculating outcomes
        self.open_positions = {}  # ticket -> event data
        self.completed_trades = []
        
    def load_events(self, file_pattern: str = "*.jsonl.gz") -> List[Dict[str, Any]]:
        """
        Load events from JSONL files.
        
        Args:
            file_pattern: Glob pattern for files to load
            
        Returns:
            List of event dictionaries
        """
        events = []
        pattern = os.path.join(self.data_dir, file_pattern)
        files = sorted(glob.glob(pattern))
        
        self.logger.info(f"Loading events from {len(files)} files")
        
        for filepath in files:
            try:
                if filepath.endswith('.gz'):
                    with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                        for line in f:
                            try:
                                event = json.loads(line.strip())
                                events.append(event)
                            except json.JSONDecodeError:
                                continue
                else:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                event = json.loads(line.strip())
                                events.append(event)
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                self.logger.warning(f"Failed to load {filepath}: {e}")
                continue
        
        self.logger.info(f"Loaded {len(events)} events")
        return events
    
    def extract_trade_features(self, events: List[Dict[str, Any]]) -> List[TradeFeatures]:
        """
        Extract trade features from events.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            List of TradeFeatures objects
        """
        # Sort events by timestamp
        events = sorted(events, key=lambda e: e.get('ts', ''))
        
        features_list = []
        position_map = {}  # Track positions
        
        for event in events:
            event_type = event.get('event_type')
            payload = event.get('payload', {})
            ts_str = event.get('ts')
            
            if not ts_str:
                continue
            
            try:
                timestamp = datetime.fromisoformat(ts_str.rstrip('Z'))
            except Exception:
                continue
            
            # Handle order requests
            if event_type == 'order_request':
                signal_id = payload.get('signal_id')
                if signal_id:
                    position_map[signal_id] = {
                        'timestamp': timestamp,
                        'symbol': payload.get('symbol'),
                        'side': payload.get('side'),
                        'volume': payload.get('volume'),
                        'strategy': payload.get('strategy', 'unknown'),
                        'confidence': payload.get('confidence', 0.5),
                        'regime': payload.get('regime', 'unknown')
                    }
            
            # Handle executions (trade outcomes)
            elif event_type == 'execution':
                signal_id = payload.get('signal_id')
                position_ticket = payload.get('position_ticket')
                
                if signal_id and signal_id in position_map:
                    # Opening trade
                    if payload.get('action') in ['OPEN', 'open']:
                        position_map[signal_id]['ticket'] = position_ticket
                        position_map[signal_id]['open_price'] = payload.get('price', 0)
                        position_map[signal_id]['open_time'] = timestamp
                        position_map[signal_id]['sl'] = payload.get('sl', 0)
                        position_map[signal_id]['tp'] = payload.get('tp', 0)
                
                # Closing trade - extract features
                elif position_ticket and payload.get('action') in ['CLOSE', 'close']:
                    # Find matching open position
                    for sig_id, pos_data in position_map.items():
                        if pos_data.get('ticket') == position_ticket:
                            # Calculate outcomes
                            open_price = pos_data.get('open_price', 0)
                            close_price = payload.get('price', 0)
                            pnl = payload.get('profit', 0)
                            
                            # Calculate hold time
                            open_time = pos_data.get('open_time', timestamp)
                            hold_time = (timestamp - open_time).total_seconds() / 60.0
                            
                            # Calculate slippage (if available)
                            slippage = payload.get('slippage', 0)
                            
                            # Build features
                            features = TradeFeatures(
                                symbol=pos_data.get('symbol', 'UNKNOWN'),
                                timestamp=open_time,
                                hour_of_day=open_time.hour,
                                day_of_week=open_time.weekday(),
                                strategy_name=pos_data.get('strategy', 'unknown'),
                                signal_confidence=pos_data.get('confidence', 0.5),
                                position_size=pos_data.get('volume', 0),
                                pnl=pnl,
                                was_win=pnl > 0,
                                hold_time_minutes=hold_time,
                                market_regime=pos_data.get('regime', 'unknown'),
                                slippage=slippage
                            )
                            
                            features_list.append(features)
                            
                            # Remove from map
                            del position_map[sig_id]
                            break
        
        self.logger.info(f"Extracted {len(features_list)} trade features")
        return features_list
    
    def extract_market_features(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract market snapshot features.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            List of market feature dictionaries
        """
        market_features = []
        
        for event in events:
            if event.get('event_type') == 'market_snapshot':
                payload = event.get('payload', {})
                ts_str = event.get('ts')
                
                if ts_str:
                    try:
                        timestamp = datetime.fromisoformat(ts_str.rstrip('Z'))
                        
                        features = {
                            'timestamp': timestamp.isoformat(),
                            'symbol': payload.get('symbol'),
                            'bid': payload.get('bid', 0),
                            'ask': payload.get('ask', 0),
                            'spread': payload.get('spread', 0),
                            'volume': payload.get('volume', 0)
                        }
                        
                        market_features.append(features)
                    except Exception:
                        continue
        
        self.logger.info(f"Extracted {len(market_features)} market snapshots")
        return market_features
    
    def create_training_dataset(
        self,
        file_pattern: str = "*.jsonl.gz",
        output_path: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Create complete training dataset.
        
        Args:
            file_pattern: Pattern for input files
            output_path: Path to save dataset (optional)
            
        Returns:
            Tuple of (dataset, output_path)
        """
        # Load events
        events = self.load_events(file_pattern)
        
        if not events:
            self.logger.warning("No events loaded")
            return [], ""
        
        # Extract features
        trade_features = self.extract_trade_features(events)
        
        # Convert to dictionaries
        dataset = [f.to_dict() for f in trade_features]
        
        # Save if output path provided
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    for row in dataset:
                        f.write(json.dumps(row) + '\n')
                self.logger.info(f"Saved dataset to {output_path}")
            except Exception as e:
                self.logger.error(f"Failed to save dataset: {e}")
        
        return dataset, output_path or ""


class RealtimeFeatureStream:
    """
    Stream features in real-time as events arrive.
    
    Monitors the data directory and processes new events incrementally.
    Fully async and decoupled from main loop.
    """
    
    def __init__(self, data_dir: str = None, window_size: int = 100):
        """
        Initialize realtime feature stream.
        
        Args:
            data_dir: Directory to monitor
            window_size: Number of recent events to keep in memory
        """
        self.logger = logging.getLogger("Cthulu.ml_stream")
        
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, 'data', 'raw')
        
        self.data_dir = data_dir
        self.window_size = window_size
        
        # Sliding window of recent events
        self.event_window = deque(maxlen=window_size)
        
        # Track file positions
        self.file_positions = {}
        
        self.logger.info(f"RealtimeFeatureStream initialized")
    
    def poll_new_events(self) -> List[Dict[str, Any]]:
        """
        Poll for new events from files.
        
        Returns:
            List of new events
        """
        new_events = []
        
        pattern = os.path.join(self.data_dir, "*.jsonl.gz")
        files = glob.glob(pattern)
        
        for filepath in files:
            try:
                # Get current file size
                current_size = os.path.getsize(filepath)
                last_size = self.file_positions.get(filepath, 0)
                
                if current_size > last_size:
                    # File has grown, read new content
                    # For gzipped files, we need to read from start and skip
                    # This is simplified - in production, use a smarter approach
                    with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                        lines = f.readlines()
                        # Process lines after last position
                        # (simplified line-based tracking)
                        for line in lines[last_size:]:
                            try:
                                event = json.loads(line.strip())
                                new_events.append(event)
                            except json.JSONDecodeError:
                                continue
                    
                    self.file_positions[filepath] = len(lines)
            
            except Exception as e:
                self.logger.warning(f"Error polling {filepath}: {e}")
                continue
        
        # Add to window
        for event in new_events:
            self.event_window.append(event)
        
        return new_events
    
    def get_recent_window(self) -> List[Dict[str, Any]]:
        """Get recent event window."""
        return list(self.event_window)
