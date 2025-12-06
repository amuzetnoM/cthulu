"""
MT5 Connection Test Script

Tests connection to MetaTrader 5 using credentials from .env file.
Verifies broker server connectivity and retrieves account information.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from connector.mt5_connector import MT5Connector, ConnectionConfig


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_environment_variables():
    """Test that required environment variables are set."""
    print_section("Environment Variables Check")
    
    required_vars = ['MT5_LOGIN', 'MT5_PASSWORD', 'MT5_SERVER']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive data
            if 'PASSWORD' in var:
                display_value = '*' * len(value)
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    
    print("\n✅ All required environment variables are set")
    return True


def test_mt5_connection():
    """Test MT5 connection."""
    print_section("MT5 Connection Test")
    
    try:
        # Create connection config from environment
        config = ConnectionConfig(
            login=int(os.getenv('MT5_LOGIN')),
            password=os.getenv('MT5_PASSWORD'),
            server=os.getenv('MT5_SERVER'),
            timeout=60000,
            path=os.getenv('MT5_PATH', '')
        )
        
        print(f"Account: {config.login}")
        print(f"Server: {config.server}")
        print(f"Timeout: {config.timeout}ms")
        
        # Create connector
        connector = MT5Connector(config)
        
        # Attempt connection
        print("\nConnecting to MT5...")
        if connector.connect():
            print("✅ Connection successful!")
            return connector
        else:
            print("❌ Connection failed")
            return None
            
    except Exception as e:
        print(f"❌ Error during connection: {e}")
        return None


def test_account_info(connector: MT5Connector):
    """Test account information retrieval."""
    print_section("Account Information")
    
    try:
        account_info = connector.get_account_info()
        
        if account_info:
            print(f"✅ Account Info Retrieved Successfully\n")
            print(f"Login: {account_info.get('login', 'N/A')}")
            print(f"Name: {account_info.get('name', 'N/A')}")
            print(f"Server: {account_info.get('server', 'N/A')}")
            print(f"Company: {account_info.get('company', 'N/A')}")
            print(f"Currency: {account_info.get('currency', 'N/A')}")
            print(f"Balance: {account_info.get('balance', 0):.2f}")
            print(f"Equity: {account_info.get('equity', 0):.2f}")
            print(f"Margin: {account_info.get('margin', 0):.2f}")
            print(f"Free Margin: {account_info.get('margin_free', 0):.2f}")
            print(f"Margin Level: {account_info.get('margin_level', 0):.2f}%")
            print(f"Leverage: 1:{account_info.get('leverage', 0)}")
            print(f"Profit: {account_info.get('profit', 0):.2f}")
            
            return True
        else:
            print("❌ Failed to retrieve account information")
            return False
            
    except Exception as e:
        print(f"❌ Error retrieving account info: {e}")
        return False


def test_market_data(connector: MT5Connector):
    """Test market data retrieval."""
    print_section("Market Data Test")
    
    # Test with EURUSD (most liquid pair)
    symbol = os.getenv('TEST_SYMBOL', 'EURUSD')
    
    try:
        import MetaTrader5 as mt5
        
        print(f"Testing symbol: {symbol}")
        
        # Get current rates
        rates = connector.get_rates(
            symbol=symbol,
            timeframe=mt5.TIMEFRAME_H1,
            count=10
        )
        
        if rates is not None and len(rates) > 0:
            print(f"✅ Market Data Retrieved Successfully\n")
            print(f"Bars retrieved: {len(rates)}")
            print(f"Latest bar:")
            latest = rates[-1]
            print(f"  Time: {datetime.fromtimestamp(latest[0])}")
            print(f"  Open: {latest[1]:.5f}")
            print(f"  High: {latest[2]:.5f}")
            print(f"  Low: {latest[3]:.5f}")
            print(f"  Close: {latest[4]:.5f}")
            print(f"  Volume: {latest[5]}")
            
            return True
        else:
            print(f"❌ Failed to retrieve market data for {symbol}")
            print("This symbol may not be available on your account")
            return False
            
    except Exception as e:
        print(f"❌ Error retrieving market data: {e}")
        return False


def test_connection_health(connector: MT5Connector):
    """Test connection health check."""
    print_section("Connection Health Check")
    
    try:
        is_connected = connector.is_connected()
        
        if is_connected:
            print("✅ Connection is healthy")
            return True
        else:
            print("❌ Connection check failed")
            return False
            
    except Exception as e:
        print(f"❌ Error checking connection: {e}")
        return False


def run_all_tests():
    """Run all connection tests."""
    print("\n" + "=" * 70)
    print("  HERALD MT5 CONNECTION TEST SUITE")
    print("  Testing connection to broker and data retrieval")
    print("=" * 70)
    
    # Load environment variables
    load_dotenv()
    
    results = {
        'environment': False,
        'connection': False,
        'account_info': False,
        'market_data': False,
        'health_check': False
    }
    
    # Test 1: Environment variables
    results['environment'] = test_environment_variables()
    if not results['environment']:
        print("\n❌ TESTS ABORTED: Missing environment variables")
        return False
    
    # Test 2: MT5 connection
    connector = test_mt5_connection()
    results['connection'] = connector is not None
    
    if not connector:
        print("\n❌ TESTS ABORTED: Could not connect to MT5")
        print("\nTroubleshooting:")
        print("1. Verify MT5 terminal is installed and running")
        print("2. Check credentials in .env file")
        print("3. Confirm broker server name is correct")
        print("4. Ensure account allows automated trading")
        print("5. Try connecting manually in MT5 first")
        return False
    
    # Test 3: Account information
    results['account_info'] = test_account_info(connector)
    
    # Test 4: Market data
    results['market_data'] = test_market_data(connector)
    
    # Test 5: Connection health
    results['health_check'] = test_connection_health(connector)
    
    # Disconnect
    print_section("Cleanup")
    connector.disconnect()
    print("✅ Disconnected from MT5")
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n{'='*70}")
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Herald is ready to connect to your broker.")
        return True
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Please review the errors above and fix any issues.")
        return False


def main():
    """Main entry point."""
    success = run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
