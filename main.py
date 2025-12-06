"""
Herald - MetaTrader 5 Trading Bot
Main entry point
"""

import sys
import signal
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
from utils.config import Config
from core.connection import MT5Connection
from core.trade_manager import TradeManager
from core.risk_manager import RiskManager
from strategies.simple_ma_cross import SimpleMovingAverageCross


class Herald:
    """Main trading bot orchestrator"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize Herald bot"""
        self.logger = setup_logger("Herald")
        self.config = Config(config_path)
        self.running = False
        
        # Core components
        self.connection = None
        self.trade_manager = None
        self.risk_manager = None
        self.strategy = None
        
    def initialize(self) -> bool:
        """Initialize all bot components"""
        try:
            self.logger.info("Initializing Herald Trading Bot...")
            
            # Connect to MT5
            self.connection = MT5Connection(
                login=self.config.get("mt5.login"),
                password=self.config.get("mt5.password"),
                server=self.config.get("mt5.server"),
                timeout=self.config.get("mt5.timeout", 60000)
            )
            
            if not self.connection.connect():
                self.logger.error("Failed to connect to MT5")
                return False
                
            self.logger.info(f"Connected to MT5: {self.connection.get_account_info()}")
            
            # Initialize risk manager
            self.risk_manager = RiskManager(
                connection=self.connection,
                risk_per_trade=self.config.get("trading.risk_per_trade"),
                max_positions=self.config.get("trading.max_positions"),
                max_daily_loss=self.config.get("trading.max_daily_loss")
            )
            
            # Initialize trade manager
            self.trade_manager = TradeManager(
                connection=self.connection,
                risk_manager=self.risk_manager,
                magic_number=self.config.get("trading.magic_number"),
                slippage=self.config.get("trading.slippage")
            )
            
            # Initialize strategy
            strategy_name = self.config.get("strategy.name")
            if strategy_name == "simple_ma_cross":
                self.strategy = SimpleMovingAverageCross(
                    connection=self.connection,
                    trade_manager=self.trade_manager,
                    config=self.config
                )
            else:
                self.logger.error(f"Unknown strategy: {strategy_name}")
                return False
                
            self.logger.info(f"Strategy loaded: {strategy_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization error: {e}", exc_info=True)
            return False
    
    def run(self):
        """Main trading loop"""
        if not self.initialize():
            self.logger.error("Initialization failed, exiting")
            return
            
        self.running = True
        self.logger.info("Herald is now running. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                # Check connection health
                if not self.connection.is_connected():
                    self.logger.warning("Lost connection, attempting to reconnect...")
                    if not self.connection.connect():
                        self.logger.error("Reconnection failed, waiting 30s...")
                        time.sleep(30)
                        continue
                
                # Run strategy logic
                try:
                    self.strategy.execute()
                except Exception as e:
                    self.logger.error(f"Strategy execution error: {e}", exc_info=True)
                
                # Update risk manager
                self.risk_manager.update()
                
                # Sleep before next iteration
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("Shutdown signal received")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Cleanup and disconnect"""
        self.logger.info("Shutting down Herald...")
        self.running = False
        
        if self.connection:
            self.connection.disconnect()
            
        self.logger.info("Herald stopped")


def signal_handler(signum, frame):
    """Handle termination signals"""
    print("\nShutdown signal received...")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the bot
    bot = Herald()
    bot.run()
