"""
Main Trading Loop - Clean Implementation
Handles the core signal-to-execution pipeline with clear flow.
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class LoopMetrics:
    """Metrics for a single loop iteration."""
    loop_number: int = 0
    start_time: float = 0.0
    duration_ms: float = 0.0
    signal_generated: bool = False
    trade_executed: bool = False
    positions_managed: int = 0
    adoptions: int = 0
    errors: List[str] = field(default_factory=list)


class TradingLoop:
    """
    Clean trading loop implementation.
    
    Each loop iteration:
    1. Fetch market data
    2. Calculate indicators
    3. Classify market regime
    4. Generate signals (strategy + confluence)
    5. Execute approved signals
    6. Scan for external trades (adoption)
    7. Manage existing positions (dynamic SLTP)
    8. Evaluate exit conditions
    """
    
    def __init__(self, components):
        """
        Initialize trading loop with system components.
        
        Args:
            components: SystemComponents from bootstrap
        """
        self.components = components
        self.config = components.config
        self.symbol = self.config.get('symbol', 'GOLDm#')
        self.timeframe = self.config.get('timeframe', 'M5')
        self.loop_interval = self.config.get('loop_interval', 15)
        
        self._running = False
        self._loop_count = 0
        self._last_regime_update = 0
        self._current_regime = None
        self._market_data = None
        self._indicators = {}
        
        # Initialize Session ORB and Order Block detectors
        self._init_advanced_detectors()
        
    def _init_advanced_detectors(self):
        """Initialize Session ORB and Order Block detection systems."""
        try:
            from cognition import SessionORBDetector, OrderBlockDetector, SessionType
            
            # Session ORB - detect opening range breakouts
            orb_config = self.config.get('session_orb', {})
            if orb_config.get('enabled', True):
                self._session_orb = SessionORBDetector(
                    sessions=[SessionType.LONDON, SessionType.NEW_YORK],
                    range_duration_minutes=orb_config.get('range_duration', 30),
                    confirm_bars=orb_config.get('confirm_bars', 1),
                )
                logger.info("Session ORB Detector initialized")
            else:
                self._session_orb = None
                
            # Order Block detection
            ob_config = self.config.get('order_blocks', {})
            if ob_config.get('enabled', True):
                self._order_block_detector = OrderBlockDetector(
                    swing_lookback=ob_config.get('swing_lookback', 5),
                    min_move_atr=ob_config.get('min_move_atr', 1.5),
                    max_age_bars=ob_config.get('max_age_bars', 100),
                )
                logger.info("Order Block Detector initialized")
            else:
                self._order_block_detector = None
                
        except Exception as e:
            logger.warning(f"Advanced detectors init error (non-fatal): {e}")
            self._session_orb = None
            self._order_block_detector = None
        
    async def run(self):
        """Main trading loop - runs until stopped."""
        self._running = True
        logger.info("Starting autonomous trading loop...")
        logger.info(f"Symbol: {self.symbol}, Timeframe: {self.timeframe}")
        logger.info(f"Loop interval: {self.loop_interval}s")
        logger.info("Press Ctrl+C to shutdown gracefully")
        
        while self._running:
            try:
                metrics = await self._execute_loop()
                self._log_metrics(metrics)
                
                # Sleep until next iteration
                sleep_time = max(0, self.loop_interval - (metrics.duration_ms / 1000))
                await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                logger.info("Trading loop cancelled")
                break
            except Exception as e:
                logger.error(f"Loop error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Brief pause on error
                
        logger.info("Trading loop stopped")
        
    def stop(self):
        """Signal the loop to stop."""
        self._running = False
        
    async def _execute_loop(self) -> LoopMetrics:
        """Execute a single loop iteration."""
        self._loop_count += 1
        metrics = LoopMetrics(
            loop_number=self._loop_count,
            start_time=time.time()
        )
        
        try:
            # Step 1: Fetch market data
            logger.info(f"Loop #{self._loop_count}: Fetching market data...")
            self._market_data = await self._fetch_market_data()
            
            if self._market_data is None or len(self._market_data) < 50:
                logger.warning("Insufficient market data")
                return metrics
            
            # Step 2: Calculate indicators
            logger.info(f"Loop #{self._loop_count}: Calculating indicators...")
            self._indicators = await self._calculate_indicators()
            
            # Step 3: Classify market regime (every 5 min)
            await self._update_regime()
            
            # Step 4: Generate signals
            logger.info(f"Loop #{self._loop_count}: Generating signals...")
            signal = await self._generate_signal()
            
            if signal:
                metrics.signal_generated = True
                
                # Step 5: Execute signal
                executed = await self._execute_signal(signal)
                metrics.trade_executed = executed
            
            # Step 6: Scan for external trades (adoption)
            adoptions = await self._scan_for_adoptions()
            metrics.adoptions = adoptions
            
            # Step 7: Manage existing positions
            positions_managed = await self._manage_positions()
            metrics.positions_managed = positions_managed
            
            # Step 8: Evaluate exit conditions
            await self._evaluate_exits()
            
        except Exception as e:
            metrics.errors.append(str(e))
            logger.error(f"Loop execution error: {e}", exc_info=True)
        
        metrics.duration_ms = (time.time() - metrics.start_time) * 1000
        return metrics
    
    async def _fetch_market_data(self):
        """Fetch OHLCV data from MT5."""
        try:
            data = self.components.data_layer.get_ohlcv(
                symbol=self.symbol,
                timeframe=self.timeframe,
                count=200
            )
            return data
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            return None
    
    async def _calculate_indicators(self) -> Dict[str, Any]:
        """Calculate all required indicators."""
        indicators = {}
        
        if self._market_data is None:
            return indicators
        
        try:
            # Core indicators
            from indicators.rsi import calculate_rsi
            from indicators.adx import calculate_adx
            from indicators.atr import calculate_atr
            from indicators.macd import calculate_macd
            from indicators.bollinger import calculate_bollinger
            
            close = self._market_data['close'].values
            high = self._market_data['high'].values
            low = self._market_data['low'].values
            
            indicators['RSI'] = calculate_rsi(close, period=14)
            indicators['ADX'] = calculate_adx(high, low, close, period=14)
            indicators['ATR'] = calculate_atr(high, low, close, period=14)
            indicators['MACD'] = calculate_macd(close)
            indicators['BB'] = calculate_bollinger(close, period=20, std_dev=2.0)
            
            # Moving averages for strategies
            indicators['SMA_10'] = close[-10:].mean() if len(close) >= 10 else close[-1]
            indicators['SMA_30'] = close[-30:].mean() if len(close) >= 30 else close[-1]
            indicators['EMA_12'] = self._calculate_ema(close, 12)
            indicators['EMA_26'] = self._calculate_ema(close, 26)
            
            logger.info(f"Indicator collector updated: RSI={indicators['RSI']:.1f}, ADX={indicators['ADX']:.1f}")
            
        except Exception as e:
            logger.error(f"Indicator calculation error: {e}")
        
        return indicators
    
    def _calculate_ema(self, data, period: int) -> float:
        """Calculate EMA for given period."""
        if len(data) < period:
            return data[-1]
        
        multiplier = 2 / (period + 1)
        ema = data[:period].mean()  # SMA for initial
        
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    async def _update_regime(self):
        """Update market regime classification (every 5 minutes)."""
        now = time.time()
        if now - self._last_regime_update < 300:  # 5 minutes
            return
        
        self._last_regime_update = now
        
        try:
            self._current_regime = self.components.regime_classifier.classify(
                indicators=self._indicators,
                market_data=self._market_data
            )
            logger.info(f"Market regime: {self._current_regime}")
        except Exception as e:
            logger.error(f"Regime classification error: {e}")
            self._current_regime = "unknown"
    
    async def _generate_signal(self):
        """Generate trading signal using strategy selector + advanced detectors."""
        try:
            # Get current price and ATR for advanced detectors
            current_price = self._market_data['close'].iloc[-1] if self._market_data is not None else 0
            atr = self._indicators.get('ATR', 10.0)
            
            # Check Session ORB first (high priority signals)
            orb_signal = await self._check_session_orb(current_price, atr)
            if orb_signal:
                logger.info(f"Session ORB signal detected!")
                return self._format_orb_signal(orb_signal)
            
            # Check Order Blocks (high priority zones)
            ob_signal = await self._check_order_blocks(current_price, atr)
            if ob_signal:
                logger.info(f"Order Block signal detected!")
                return self._format_ob_signal(ob_signal)
            
            # Fall back to strategy selector
            signal = self.components.strategy_selector.generate_signal(
                data=self._market_data,
                indicators=self._indicators,
                regime=self._current_regime
            )
            
            if signal is None:
                logger.info("Strategy returned NO SIGNAL for this bar")
                return None
            
            # Ensure symbol is set
            if signal.get('symbol') in (None, 'UNKNOWN', ''):
                signal['symbol'] = self.symbol
            
            # Apply entry confluence filter
            if self.components.entry_confluence:
                confluence_result = self.components.entry_confluence.analyze(
                    signal=signal,
                    data=self._market_data,
                    indicators=self._indicators
                )
                
                logger.info(f"Entry Confluence: {confluence_result['quality']} (score={confluence_result['score']})")
                
                if confluence_result['should_reject']:
                    logger.warning(f"Entry REJECTED: {confluence_result['reason']}")
                    return None
                
                # Adjust confidence based on confluence
                signal['confidence'] *= confluence_result['confidence_multiplier']
                signal['confluence_score'] = confluence_result['score']
            
            direction = "🟢 LONG" if signal['direction'] == 'buy' else "🔴 SHORT"
            logger.info(f"Signal generated: {direction} {signal['symbol']} (confidence: {signal['confidence']:.2f})")
            
            return signal
            
        except Exception as e:
            logger.error(f"Signal generation error: {e}")
            return None
    
    async def _check_session_orb(self, current_price: float, atr: float):
        """Check for Session ORB breakout signals."""
        if self._session_orb is None or self._market_data is None:
            return None
        
        try:
            timestamp = datetime.now()
            signal = self._session_orb.update(
                df=self._market_data,
                current_price=current_price,
                atr=atr,
                timestamp=timestamp
            )
            return signal
        except Exception as e:
            logger.debug(f"Session ORB check error: {e}")
            return None
    
    async def _check_order_blocks(self, current_price: float, atr: float):
        """Check for Order Block entry signals."""
        if self._order_block_detector is None or self._market_data is None:
            return None
        
        try:
            timestamp = datetime.now()
            signal = self._order_block_detector.update(
                df=self._market_data,
                current_price=current_price,
                atr=atr,
                timestamp=timestamp
            )
            return signal
        except Exception as e:
            logger.debug(f"Order Block check error: {e}")
            return None
    
    def _format_orb_signal(self, orb_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Format ORB signal for execution."""
        direction = 'buy' if orb_signal['direction'] == 'long' else 'sell'
        return {
            'direction': direction,
            'symbol': self.symbol,
            'entry_price': orb_signal['entry_price'],
            'stop_loss': orb_signal['stop_loss'],
            'take_profit': orb_signal['take_profit'],
            'confidence': orb_signal['confidence'],
            'strategy': 'session_orb',
            'reason': orb_signal['reason'],
            'session': orb_signal.get('session', 'unknown'),
        }
    
    def _format_ob_signal(self, ob_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Format Order Block signal for execution."""
        direction = 'buy' if ob_signal['direction'] == 'long' else 'sell'
        return {
            'direction': direction,
            'symbol': self.symbol,
            'entry_price': ob_signal['entry_price'],
            'stop_loss': ob_signal['stop_loss'],
            'take_profit': ob_signal['take_profit'],
            'confidence': ob_signal['confidence'],
            'strategy': 'order_block',
            'reason': ob_signal['reason'],
            'ob_type': ob_signal.get('ob_type', 'unknown'),
        }
    
    async def _execute_signal(self, signal: Dict[str, Any]) -> bool:
        """Execute an approved signal."""
        try:
            # Risk approval
            risk_result = self.components.risk_evaluator.evaluate(signal)
            
            if not risk_result['approved']:
                logger.info(f"Risk rejected: {risk_result['reason']}")
                return False
            
            logger.info(f"Risk approved: {risk_result['lot_size']:.2f} lots - {risk_result['reason']}")
            
            # Execute the trade
            result = self.components.execution_engine.execute(
                signal=signal,
                lot_size=risk_result['lot_size']
            )
            
            if result['success']:
                logger.info(f"Order executed: Ticket #{result['ticket']} | Price: {result['price']} | Volume: {result['volume']}")
                
                # Register with trade manager
                self.components.trade_manager.register_trade(
                    ticket=result['ticket'],
                    signal=signal,
                    result=result
                )
                
                # Apply initial SL/TP
                await self._apply_initial_sltp(result['ticket'], signal)
                
                return True
            else:
                logger.error(f"Order failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return False
    
    async def _apply_initial_sltp(self, ticket: int, signal: Dict[str, Any]):
        """Apply initial SL/TP to a new position."""
        try:
            atr = self._indicators.get('ATR', 10.0)
            
            result = self.components.dynamic_sltp_manager.calculate_initial_sltp(
                ticket=ticket,
                direction=signal['direction'],
                entry_price=signal.get('entry_price', 0),
                atr=atr
            )
            
            if result['sl'] and result['tp']:
                success = self.components.mt5_connector.modify_position(
                    ticket=ticket,
                    sl=result['sl'],
                    tp=result['tp']
                )
                
                if success:
                    logger.info(f"Initial SL/TP applied to {ticket}: SL={result['sl']:.2f}, TP={result['tp']:.2f}")
                    # Update trade manager so position tracking is current
                    self.components.trade_manager.update_position_sltp(
                        ticket=ticket,
                        sl=result['sl'],
                        tp=result['tp']
                    )
                else:
                    logger.warning(f"Failed to apply initial SL/TP to {ticket}")
                    
        except Exception as e:
            logger.error(f"Initial SLTP error: {e}")
    
    async def _scan_for_adoptions(self) -> int:
        """Scan for and adopt external trades."""
        try:
            logger.info("ADOPTION: Running scan...")
            
            adoptions = self.components.lifecycle_manager.scan_and_adopt()
            
            if adoptions > 0:
                logger.info(f"ADOPTION: Adopted {adoptions} external trade(s)")
                
                # Apply SL/TP to adopted trades
                for position in self.components.trade_manager.get_adopted_positions():
                    if position.sl is None or position.tp is None:
                        await self._apply_initial_sltp(
                            ticket=position.ticket,
                            signal={
                                'direction': 'buy' if position.type == 0 else 'sell',
                                'entry_price': position.price_open
                            }
                        )
            else:
                logger.info("ADOPTION: Found 0 external trades")
            
            return adoptions
            
        except Exception as e:
            logger.error(f"Adoption scan error: {e}")
            return 0
    
    async def _manage_positions(self) -> int:
        """Manage existing positions (dynamic SL/TP)."""
        positions = self.components.trade_manager.get_all_positions()
        managed = 0
        
        for position in positions:
            try:
                atr = self._indicators.get('ATR', 10.0)
                current_price = self._market_data['close'].iloc[-1] if self._market_data is not None else 0
                
                result = self.components.dynamic_sltp_manager.update_position_sltp(
                    position=position,
                    current_price=current_price,
                    atr=atr
                )
                
                logger.info(f"SLTP check {position.ticket}: action={result['action']}, "
                           f"update_sl={result['update_sl']}, update_tp={result['update_tp']}, "
                           f"sl={result['new_sl']:.2f}, tp={result['new_tp']:.2f}")
                
                if result['update_sl'] or result['update_tp']:
                    success = self.components.mt5_connector.modify_position(
                        ticket=position.ticket,
                        sl=result['new_sl'] if result['update_sl'] else position.sl,
                        tp=result['new_tp'] if result['update_tp'] else position.tp
                    )
                    
                    if success:
                        managed += 1
                        # Update position tracking
                        self.components.trade_manager.update_position_sltp(
                            ticket=position.ticket,
                            sl=result['new_sl'] if result['update_sl'] else position.sl,
                            tp=result['new_tp'] if result['update_tp'] else position.tp
                        )
                    else:
                        logger.warning(f"Failed to modify position {position.ticket}")
                        
            except Exception as e:
                logger.error(f"Position management error for {position.ticket}: {e}")
        
        return managed
    
    async def _evaluate_exits(self):
        """Evaluate exit conditions for all positions."""
        try:
            positions = self.components.trade_manager.get_all_positions()
            
            for position in positions:
                exit_signal = self.components.exit_coordinator.evaluate(
                    position=position,
                    current_price=self._market_data['close'].iloc[-1] if self._market_data is not None else 0,
                    indicators=self._indicators
                )
                
                # ExitSignal is a dataclass, access attributes directly
                if exit_signal.should_exit:
                    logger.info(f"Exit signal for {position.ticket}: {exit_signal.reason}")
                    
                    # Execute exit
                    self.components.execution_engine.close_position(
                        ticket=position.ticket,
                        reason=exit_signal.reason
                    )
                    
        except Exception as e:
            logger.error(f"Exit evaluation error: {e}")
    
    def _log_metrics(self, metrics: LoopMetrics):
        """Log loop metrics periodically."""
        if metrics.loop_number % 10 == 0:
            positions = self.components.trade_manager.get_all_positions()
            total_pnl = sum(p.profit for p in positions)
            
            logger.info(f"Performance metrics after {metrics.loop_number} loops:")
            logger.info(f"Position stats: {{'open_positions': {len(positions)}, 'total_unrealized_pnl': {total_pnl:.2f}}}")
