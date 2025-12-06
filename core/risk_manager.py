"""
Risk management for trading operations
"""

import MetaTrader5 as mt5
from typing import Optional, Dict, Any
from datetime import datetime, date
import logging


class RiskManager:
    """Manages trading risk and position sizing"""
    
    def __init__(
        self,
        connection,
        risk_per_trade: float = 0.01,
        max_positions: int = 3,
        max_daily_loss: float = 0.05
    ):
        """
        Initialize risk manager
        
        Args:
            connection: MT5Connection instance
            risk_per_trade: Risk per trade as decimal (0.01 = 1%)
            max_positions: Maximum concurrent positions
            max_daily_loss: Maximum daily loss as decimal (0.05 = 5%)
        """
        self.connection = connection
        self.risk_per_trade = risk_per_trade
        self.max_positions = max_positions
        self.max_daily_loss = max_daily_loss
        self.logger = logging.getLogger("Herald.RiskManager")
        
        # Daily tracking
        self.daily_pnl = 0.0
        self.current_date = date.today()
        
    def update(self):
        """Update daily tracking (call this regularly)"""
        today = date.today()
        
        # Reset daily stats if new day
        if today != self.current_date:
            self.logger.info(f"New trading day. Previous P&L: ${self.daily_pnl:.2f}")
            self.daily_pnl = 0.0
            self.current_date = today
            
    def can_open_trade(self) -> tuple[bool, str]:
        """
        Check if new trade can be opened
        
        Returns:
            (can_trade, reason) tuple
        """
        # Check connection
        if not self.connection.is_connected():
            return False, "Not connected to MT5"
            
        # Check daily loss limit
        account = self.connection.get_account_info()
        daily_loss_limit = account['balance'] * self.max_daily_loss
        
        if self.daily_pnl < -daily_loss_limit:
            return False, f"Daily loss limit exceeded: ${self.daily_pnl:.2f}"
            
        # Check max positions
        positions = mt5.positions_total()
        if positions >= self.max_positions:
            return False, f"Maximum positions ({self.max_positions}) reached"
            
        # Check if trading allowed
        terminal = mt5.terminal_info()
        if not terminal.trade_allowed:
            return False, "Trading not allowed by terminal"
            
        account_info = mt5.account_info()
        if not account_info.trade_allowed:
            return False, "Trading not allowed for account"
            
        return True, "OK"
        
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        account_balance: Optional[float] = None
    ) -> float:
        """
        Calculate position size based on risk per trade
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            account_balance: Account balance (fetched if not provided)
            
        Returns:
            Position size in lots
        """
        if account_balance is None:
            account = self.connection.get_account_info()
            account_balance = account['balance']
            
        # Get symbol info
        symbol_info = self.connection.get_symbol_info(symbol)
        if not symbol_info:
            raise ValueError(f"Cannot get info for symbol {symbol}")
            
        # Calculate risk amount
        risk_amount = account_balance * self.risk_per_trade
        
        # Calculate pip/point value
        pip_value = symbol_info['trade_contract_size'] * symbol_info['point']
        
        # Calculate stop loss distance in pips
        sl_distance = abs(entry_price - stop_loss) / symbol_info['point']
        
        if sl_distance == 0:
            raise ValueError("Stop loss distance cannot be zero")
            
        # Calculate position size
        position_size = risk_amount / (sl_distance * pip_value)
        
        # Round to volume step
        volume_step = symbol_info['volume_step']
        position_size = round(position_size / volume_step) * volume_step
        
        # Apply limits
        position_size = max(symbol_info['volume_min'], position_size)
        position_size = min(symbol_info['volume_max'], position_size)
        
        self.logger.info(
            f"Position size calculated: {position_size} lots "
            f"(risk: ${risk_amount:.2f}, SL distance: {sl_distance:.1f} pips)"
        )
        
        return position_size
        
    def calculate_stop_loss(
        self,
        symbol: str,
        entry_price: float,
        order_type: str,
        atr: Optional[float] = None,
        atr_multiple: float = 2.0,
        fixed_pips: Optional[float] = None
    ) -> float:
        """
        Calculate stop loss price
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            order_type: 'BUY' or 'SELL'
            atr: Average True Range value (optional)
            atr_multiple: ATR multiplier for dynamic SL
            fixed_pips: Fixed pip distance (optional)
            
        Returns:
            Stop loss price
        """
        symbol_info = self.connection.get_symbol_info(symbol)
        if not symbol_info:
            raise ValueError(f"Cannot get info for symbol {symbol}")
            
        point = symbol_info['point']
        
        # Calculate SL distance
        if fixed_pips:
            sl_distance = fixed_pips * point
        elif atr:
            sl_distance = atr * atr_multiple
        else:
            # Default: 100 pips
            sl_distance = 100 * point
            
        # Apply SL based on order type
        if order_type.upper() == 'BUY':
            stop_loss = entry_price - sl_distance
        else:  # SELL
            stop_loss = entry_price + sl_distance
            
        return round(stop_loss, symbol_info['digits'])
        
    def calculate_take_profit(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        order_type: str,
        risk_reward_ratio: float = 2.0
    ) -> float:
        """
        Calculate take profit price
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            order_type: 'BUY' or 'SELL'
            risk_reward_ratio: Risk:Reward ratio (e.g., 2.0 = 1:2)
            
        Returns:
            Take profit price
        """
        symbol_info = self.connection.get_symbol_info(symbol)
        if not symbol_info:
            raise ValueError(f"Cannot get info for symbol {symbol}")
            
        # Calculate SL distance
        sl_distance = abs(entry_price - stop_loss)
        
        # Calculate TP distance
        tp_distance = sl_distance * risk_reward_ratio
        
        # Apply TP based on order type
        if order_type.upper() == 'BUY':
            take_profit = entry_price + tp_distance
        else:  # SELL
            take_profit = entry_price - tp_distance
            
        return round(take_profit, symbol_info['digits'])
        
    def check_margin(self, symbol: str, volume: float, order_type: str) -> tuple[bool, str]:
        """
        Check if sufficient margin available
        
        Args:
            symbol: Trading symbol
            volume: Position size in lots
            order_type: 'BUY' or 'SELL'
            
        Returns:
            (sufficient_margin, reason) tuple
        """
        account = self.connection.get_account_info()
        
        # Get required margin
        action = mt5.ORDER_TYPE_BUY if order_type.upper() == 'BUY' else mt5.ORDER_TYPE_SELL
        margin_required = mt5.order_calc_margin(action, symbol, volume, account['balance'])
        
        if margin_required is None:
            return False, "Cannot calculate margin requirement"
            
        if margin_required > account['margin_free']:
            return False, f"Insufficient margin: required ${margin_required:.2f}, available ${account['margin_free']:.2f}"
            
        # Check margin level after trade
        margin_level_after = (account['equity'] / (account['margin'] + margin_required)) * 100
        
        if margin_level_after < 150:  # Safety threshold
            return False, f"Margin level too low: {margin_level_after:.1f}%"
            
        return True, "OK"
        
    def update_daily_pnl(self, profit: float):
        """
        Update daily P&L tracking
        
        Args:
            profit: Profit/loss from closed trade
        """
        self.daily_pnl += profit
        self.logger.info(f"Daily P&L updated: ${self.daily_pnl:.2f}")
