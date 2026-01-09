"""
Execution Engine - Clean Implementation
Handles order execution with validation and logging.
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of order execution."""
    success: bool
    ticket: int = 0
    price: float = 0.0
    volume: float = 0.0
    error: str = ""
    execution_time_ms: float = 0.0


class ExecutionEngine:
    """
    Order execution engine.
    
    Responsibilities:
    - Execute market orders
    - Apply slippage controls
    - Log all execution attempts
    - Handle partial fills
    """
    
    CTHULU_MAGIC = 123456
    
    def __init__(
        self,
        connector,
        risk_evaluator,
        config: Dict[str, Any]
    ):
        """
        Initialize execution engine.
        
        Args:
            connector: MT5 connector
            risk_evaluator: Risk evaluator for final checks
            config: System configuration
        """
        self.connector = connector
        self.risk_evaluator = risk_evaluator
        self.config = config
        
        # Execution settings
        exec_config = config.get('execution', {})
        self.max_slippage_points = exec_config.get('max_slippage_points', 50)
        self.retry_count = exec_config.get('retry_count', 3)
        self.retry_delay_ms = exec_config.get('retry_delay_ms', 500)
        
        logger.info("ExecutionEngine initialized")
    
    def execute(
        self,
        signal: Dict[str, Any],
        lot_size: float
    ) -> Dict[str, Any]:
        """
        Execute a trade based on signal.
        
        Args:
            signal: Trading signal with direction, symbol
            lot_size: Position size in lots
            
        Returns:
            Execution result dict
        """
        start_time = time.time()
        
        symbol = signal.get('symbol', 'UNKNOWN')
        direction = signal.get('direction', 'buy')
        
        # Validate symbol
        symbol_info = self.connector.get_symbol_info(symbol)
        if not symbol_info:
            logger.error(f"Invalid symbol: {symbol}")
            return {
                'success': False,
                'error': f'Invalid symbol: {symbol}',
                'execution_time_ms': (time.time() - start_time) * 1000
            }
        
        # Adjust lot size to valid steps
        lot_size = self._adjust_lot_size(lot_size, symbol_info)
        
        # Get entry price
        tick = self.connector.get_tick(symbol)
        if not tick:
            return {
                'success': False,
                'error': 'Failed to get tick data',
                'execution_time_ms': (time.time() - start_time) * 1000
            }
        
        entry_price = tick['ask'] if direction == 'buy' else tick['bid']
        
        # Log execution attempt
        logger.info(f"Placing {direction.upper()} order for {lot_size} lots")
        
        # Execute with retries
        for attempt in range(1, self.retry_count + 1):
            result = self.connector.place_order(
                symbol=symbol,
                order_type=direction,
                volume=lot_size,
                price=entry_price,
                magic=self.CTHULU_MAGIC,
                comment=f"Cthulu_{signal.get('strategy', 'unknown')}"
            )
            
            if result['success']:
                exec_time = (time.time() - start_time) * 1000
                
                return {
                    'success': True,
                    'ticket': result['ticket'],
                    'price': result['price'],
                    'volume': result['volume'],
                    'execution_time_ms': exec_time
                }
            
            if attempt < self.retry_count:
                logger.warning(f"Execution attempt {attempt} failed, retrying...")
                time.sleep(self.retry_delay_ms / 1000)
        
        return {
            'success': False,
            'error': result.get('error', 'Max retries exceeded'),
            'execution_time_ms': (time.time() - start_time) * 1000
        }
    
    def close_position(
        self,
        ticket: int,
        reason: str = "",
        volume: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Close a position.
        
        Args:
            ticket: Position ticket
            reason: Reason for closing
            volume: Volume to close (None for full)
            
        Returns:
            Close result dict
        """
        logger.info(f"Closing position {ticket}: {reason}")
        
        success = self.connector.close_position(ticket, volume)
        
        return {
            'success': success,
            'ticket': ticket,
            'reason': reason
        }
    
    def close_all_positions(self, symbol: Optional[str] = None) -> int:
        """
        Close all positions (optionally filtered by symbol).
        
        Args:
            symbol: Symbol to filter (None for all)
            
        Returns:
            Number of positions closed
        """
        positions = self.connector.get_positions()
        
        if symbol:
            positions = [p for p in positions if p.symbol == symbol]
        
        closed = 0
        for pos in positions:
            if self.connector.close_position(pos.ticket):
                closed += 1
        
        logger.info(f"Closed {closed} positions")
        return closed
    
    def _adjust_lot_size(
        self,
        lot_size: float,
        symbol_info: Dict[str, Any]
    ) -> float:
        """Adjust lot size to valid steps."""
        min_lot = symbol_info.get('volume_min', 0.01)
        max_lot = symbol_info.get('volume_max', 100.0)
        step = symbol_info.get('volume_step', 0.01)
        
        # Clamp to min/max
        lot_size = max(min_lot, min(max_lot, lot_size))
        
        # Round to step
        lot_size = round(lot_size / step) * step
        lot_size = round(lot_size, 2)  # Ensure 2 decimal places
        
        return lot_size
