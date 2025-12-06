"""
Trade execution and management
"""

import MetaTrader5 as mt5
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging


class TradeManager:
    """Manages trade execution and position tracking"""
    
    def __init__(
        self,
        connection,
        risk_manager,
        magic_number: int = 20241206,
        slippage: int = 10
    ):
        """
        Initialize trade manager
        
        Args:
            connection: MT5Connection instance
            risk_manager: RiskManager instance
            magic_number: Unique identifier for bot's orders
            slippage: Maximum slippage in points
        """
        self.connection = connection
        self.risk_manager = risk_manager
        self.magic_number = magic_number
        self.slippage = slippage
        self.logger = logging.getLogger("Herald.TradeManager")
        
    def open_position(
        self,
        symbol: str,
        order_type: str,
        volume: Optional[float] = None,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        comment: str = "Herald Bot"
    ) -> Optional[int]:
        """
        Open a new position
        
        Args:
            symbol: Trading symbol
            order_type: 'BUY' or 'SELL'
            volume: Position size (calculated if None)
            price: Entry price (market price if None)
            stop_loss: Stop loss price
            take_profit: Take profit price
            comment: Order comment
            
        Returns:
            Order ticket number or None if failed
        """
        try:
            # Check if can trade
            can_trade, reason = self.risk_manager.can_open_trade()
            if not can_trade:
                self.logger.warning(f"Trade rejected: {reason}")
                return None
                
            # Get current price if not specified
            symbol_info = self.connection.get_symbol_info(symbol)
            if not symbol_info:
                self.logger.error(f"Cannot get symbol info for {symbol}")
                return None
                
            if price is None:
                if order_type.upper() == 'BUY':
                    price = symbol_info['ask']
                else:
                    price = symbol_info['bid']
                    
            # Calculate position size if not specified
            if volume is None and stop_loss is not None:
                volume = self.risk_manager.calculate_position_size(
                    symbol, price, stop_loss
                )
            elif volume is None:
                # Default to minimum volume
                volume = symbol_info['volume_min']
                
            # Check margin
            sufficient_margin, margin_reason = self.risk_manager.check_margin(
                symbol, volume, order_type
            )
            if not sufficient_margin:
                self.logger.warning(f"Margin check failed: {margin_reason}")
                return None
                
            # Prepare order request
            order_type_mt5 = mt5.ORDER_TYPE_BUY if order_type.upper() == 'BUY' else mt5.ORDER_TYPE_SELL
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type_mt5,
                "price": price,
                "deviation": self.slippage,
                "magic": self.magic_number,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Add SL/TP if specified
            if stop_loss:
                request["sl"] = stop_loss
            if take_profit:
                request["tp"] = take_profit
                
            # Send order
            self.logger.info(
                f"Opening {order_type} position: {volume} {symbol} @ {price:.5f}"
            )
            
            result = mt5.order_send(request)
            
            if result is None:
                self.logger.error(f"order_send failed: {mt5.last_error()}")
                return None
                
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(
                    f"Order failed: {result.retcode} - {result.comment}"
                )
                return None
                
            self.logger.info(
                f"Position opened successfully: Ticket #{result.order} | "
                f"Price: {result.price:.5f} | Volume: {result.volume}"
            )
            
            return result.order
            
        except Exception as e:
            self.logger.error(f"Error opening position: {e}", exc_info=True)
            return None
            
    def close_position(
        self,
        ticket: int,
        volume: Optional[float] = None,
        reason: str = "Manual"
    ) -> bool:
        """
        Close an existing position
        
        Args:
            ticket: Position ticket number
            volume: Volume to close (None = close all)
            reason: Reason for closing
            
        Returns:
            True if closed successfully
        """
        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if not position:
                self.logger.error(f"Position #{ticket} not found")
                return False
                
            position = position[0]
            
            # Determine close volume
            if volume is None:
                volume = position.volume
                
            # Determine order type (opposite of position)
            if position.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(position.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(position.symbol).ask
                
            # Prepare close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": self.slippage,
                "magic": self.magic_number,
                "comment": f"Close: {reason}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send close order
            self.logger.info(f"Closing position #{ticket} ({reason})")
            
            result = mt5.order_send(request)
            
            if result is None:
                self.logger.error(f"order_send failed: {mt5.last_error()}")
                return False
                
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(
                    f"Close failed: {result.retcode} - {result.comment}"
                )
                return False
                
            profit = result.profit if hasattr(result, 'profit') else 0.0
            self.risk_manager.update_daily_pnl(profit)
            
            self.logger.info(
                f"Position closed: #{ticket} | Profit: ${profit:.2f}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}", exc_info=True)
            return False
            
    def modify_position(
        self,
        ticket: int,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """
        Modify position SL/TP
        
        Args:
            ticket: Position ticket number
            stop_loss: New stop loss (None = no change)
            take_profit: New take profit (None = no change)
            
        Returns:
            True if modified successfully
        """
        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if not position:
                self.logger.error(f"Position #{ticket} not found")
                return False
                
            position = position[0]
            
            # Use existing values if not specified
            if stop_loss is None:
                stop_loss = position.sl
            if take_profit is None:
                take_profit = position.tp
                
            # Prepare modification request
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": ticket,
                "sl": stop_loss,
                "tp": take_profit,
                "magic": self.magic_number,
            }
            
            # Send modification
            self.logger.info(f"Modifying position #{ticket}")
            
            result = mt5.order_send(request)
            
            if result is None:
                self.logger.error(f"order_send failed: {mt5.last_error()}")
                return False
                
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(
                    f"Modification failed: {result.retcode} - {result.comment}"
                )
                return False
                
            self.logger.info(
                f"Position modified: #{ticket} | SL: {stop_loss:.5f} | TP: {take_profit:.5f}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error modifying position: {e}", exc_info=True)
            return False
            
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open positions
        
        Args:
            symbol: Filter by symbol (None = all symbols)
            
        Returns:
            List of position dictionaries
        """
        try:
            # Get positions
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
                
            if positions is None:
                return []
                
            # Filter by magic number
            bot_positions = [
                p for p in positions 
                if p.magic == self.magic_number
            ]
            
            # Convert to dictionaries
            return [
                {
                    'ticket': p.ticket,
                    'symbol': p.symbol,
                    'type': 'BUY' if p.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    'volume': p.volume,
                    'price_open': p.price_open,
                    'price_current': p.price_current,
                    'sl': p.sl,
                    'tp': p.tp,
                    'profit': p.profit,
                    'swap': p.swap,
                    'comment': p.comment,
                    'time': datetime.fromtimestamp(p.time)
                }
                for p in bot_positions
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}", exc_info=True)
            return []
            
    def close_all_positions(self, symbol: Optional[str] = None) -> int:
        """
        Close all open positions
        
        Args:
            symbol: Close only positions for this symbol (None = all)
            
        Returns:
            Number of positions closed
        """
        positions = self.get_positions(symbol)
        closed_count = 0
        
        for position in positions:
            if self.close_position(position['ticket'], reason="Close All"):
                closed_count += 1
                
        self.logger.info(f"Closed {closed_count} positions")
        return closed_count
