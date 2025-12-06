"""Quick MT5 connection test using .env credentials"""
import MetaTrader5 as mt5
from dotenv import load_dotenv
import os

load_dotenv()

login = int(os.getenv('MT5_LOGIN'))
password = os.getenv('MT5_PASSWORD')
server = os.getenv('MT5_SERVER')

print(f"Connecting to {server} with account {login}...")

# Try initialize with path to MT5 terminal
result = mt5.initialize(
    path="C:\\Program Files\\MetaTrader 5\\terminal64.exe",
    login=login,
    password=password,
    server=server,
    timeout=10000
)

if result:
    print(f"Initialize: {result}")
    info = mt5.account_info()
    if info:
        print(f"Account Name: {info.name}")
        print(f"Account ID: {info.login}")
        print(f"Balance: ${info.balance:,.2f}")
        print(f"Equity: ${info.equity:,.2f}")
        print(f"Server: {info.server}")
        print("\n✅ Connection successful!")
    else:
        print("Failed to get account info")
else:
    error = mt5.last_error()
    print(f"❌ Connection failed: {error}")

mt5.shutdown()
