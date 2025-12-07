"""Force a test trade using Herald's execution engine."""

from herald.connector.mt5_connector import MT5Connector, ConnectionConfig
from herald.execution.engine import ExecutionEngine, OrderRequest, OrderType
import json
import MetaTrader5 as mt5

# Load config
with open('config.json') as f:
    config = json.load(f)

# Connect to MT5
print("Connecting to MT5...")
connector = MT5Connector(ConnectionConfig(**config['mt5']))
connector.connect()

# Get account info
account = connector.get_account_info()
print(f"Account: {account['login']}")
print(f"Balance: ${account['balance']:.2f}")
print(f"Equity: ${account['equity']:.2f}")

# Get current price for BTCUSD#
symbol = config['trading']['symbol']
tick = mt5.symbol_info_tick(symbol)
print(f"\n{symbol} Ask: {tick.ask}, Bid: {tick.bid}")

# Create execution engine and place a small BUY order
engine = ExecutionEngine(connector)
order = OrderRequest(
    symbol=symbol,
    order_type=OrderType.MARKET,
    volume=0.01,  # Minimum lot size
    side='BUY',
    comment='Herald forced test trade'
)

print(f"\nPlacing BUY order for 0.01 lot {symbol}...")
result = engine.execute(order)
print(f"Order result: {result}")

if hasattr(result, 'ticket') and result.ticket:
    print(f"\n✅ Trade placed successfully! Ticket: {result.ticket}")
else:
    print(f"\n❌ Trade failed: {result}")

connector.disconnect()
print("\nDisconnected from MT5")
