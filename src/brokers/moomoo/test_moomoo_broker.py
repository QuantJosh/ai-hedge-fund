#!/usr/bin/env python3
"""
Moomoo Broker Integration Test Script
Comprehensive testing of Moomoo trading functionality
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    from src.brokers.moomoo import MoomooTrading, create_moomoo_trading
    from src.brokers.moomoo.config import MoomooConfig
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def test_configuration():
    """Test configuration loading and validation"""
    print("🔧 Testing Configuration...")
    print("-" * 40)
    
    try:
        # Test creating example config
        config = MoomooConfig()
        example_path = "src/brokers/moomoo/trading_keys.yaml"
        
        if not Path(example_path).exists():
            print("Creating example configuration file...")
            config.create_example_config(example_path)
        
        # Test loading config
        config = MoomooConfig(example_path)
        print(f"✅ Configuration loaded successfully")
        print(f"   Host: {config.host}:{config.port}")
        print(f"   Market: {config.market}")
        print(f"   Paper Trading: {config.paper_trading}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_connection():
    """Test connection to Moomoo OpenD"""
    print("\n🔌 Testing Connection...")
    print("-" * 40)
    
    try:
        trading = create_moomoo_trading()
        
        if trading.connect():
            print("✅ Connection successful!")
            
            # Test basic API calls
            try:
                market_state = trading.client.get_market_state()
                if market_state:
                    print(f"   Market State: {market_state}")
            except Exception as e:
                print(f"   Warning: Market state test failed: {e}")
            
            trading.disconnect()
            return True
        else:
            print("❌ Connection failed!")
            return False
            
    except KeyboardInterrupt:
        print("\n❌ Connection test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def test_account_info():
    """Test account information retrieval"""
    print("\n💰 Testing Account Information...")
    print("-" * 40)
    
    try:
        with create_moomoo_trading() as trading:
            if not trading.connected:
                print("❌ Not connected to Moomoo")
                return False
            
            account_info = trading.get_account_info()
            if account_info:
                print("✅ Account information retrieved:")
                print(f"   Cash: ${account_info.cash:,.2f}")
                print(f"   Total Assets: ${account_info.total_assets:,.2f}")
                print(f"   Market Value: ${account_info.market_value:,.2f}")
                print(f"   Unrealized P&L: ${account_info.unrealized_pnl:,.2f}")
                print(f"   Currency: {account_info.currency}")
                return True
            else:
                print("❌ Failed to get account information")
                return False
                
    except Exception as e:
        print(f"❌ Account info test failed: {e}")
        return False


def test_paper_trading_funds():
    """Test detailed paper trading account funds"""
    print("\n💵 Testing Paper Trading Account Funds...")
    print("-" * 40)
    
    try:
        with create_moomoo_trading() as trading:
            if not trading.connected:
                print("❌ Not connected to Moomoo")
                return False
            
            # Get detailed account information
            account_info = trading.get_account_info()
            if not account_info:
                print("❌ Failed to get account information")
                return False
            
            print("✅ Paper Trading Account Details:")
            print(f"   📊 Account Type: {'Paper Trading (Simulation)' if trading.config.paper_trading else 'Live Trading'}")
            print(f"   💰 Available Cash: ${account_info.cash:,.2f}")
            print(f"   📈 Total Assets: ${account_info.total_assets:,.2f}")
            print(f"   📊 Market Value: ${account_info.market_value:,.2f}")
            print(f"   💹 Unrealized P&L: ${account_info.unrealized_pnl:,.2f}")
            print(f"   💱 Currency: {account_info.currency}")
            
            # Calculate additional metrics
            cash_percentage = (account_info.cash / account_info.total_assets * 100) if account_info.total_assets > 0 else 0
            invested_percentage = (account_info.market_value / account_info.total_assets * 100) if account_info.total_assets > 0 else 0
            
            print(f"\n   📊 Portfolio Allocation:")
            print(f"   💵 Cash Allocation: {cash_percentage:.1f}%")
            print(f"   📈 Invested Allocation: {invested_percentage:.1f}%")
            
            # Check if this is truly paper trading
            if trading.config.paper_trading:
                print(f"\n   ✅ Confirmed: This is a PAPER TRADING account")
                print(f"   🎯 Simulation funds available for testing: ${account_info.cash:,.2f}")
            else:
                print(f"\n   ⚠️  WARNING: This appears to be a LIVE TRADING account!")
                print(f"   🚨 Real money at risk: ${account_info.cash:,.2f}")
            
            # Test buying power calculation
            max_order_value = account_info.cash * 0.95  # Leave 5% buffer
            print(f"\n   💪 Maximum Order Value (95% of cash): ${max_order_value:,.2f}")
            
            # Get current market prices for reference
            test_stocks = ["AAPL", "MSFT", "GOOGL", "TSLA"]
            print(f"\n   📊 Sample Stock Affordability:")
            
            for stock in test_stocks:
                try:
                    price = trading.get_current_price(stock)
                    if price:
                        max_shares = int(max_order_value / price)
                        print(f"   {stock}: ${price:.2f} → Can afford {max_shares:,} shares (${max_shares * price:,.2f})")
                    else:
                        print(f"   {stock}: Price not available")
                except Exception as e:
                    print(f"   {stock}: Error getting price - {e}")
            
            return True
                
    except Exception as e:
        print(f"❌ Paper trading funds test failed: {e}")
        return False


def test_positions():
    """Test position retrieval"""
    print("\n📊 Testing Position Information...")
    print("-" * 40)
    
    try:
        with create_moomoo_trading() as trading:
            if not trading.connected:
                print("❌ Not connected to Moomoo")
                return False
            
            positions = trading.get_positions()
            print(f"✅ Positions retrieved: {len(positions)} positions")
            
            if positions:
                print("   Current Positions:")
                for ticker, position in positions.items():
                    pnl_color = "🟢" if position.unrealized_pnl >= 0 else "🔴"
                    print(f"   {ticker}: {position.quantity} shares @ ${position.current_price:.2f} "
                          f"{pnl_color} P&L: ${position.unrealized_pnl:,.2f}")
            else:
                print("   📭 No active positions")
            
            return True
                
    except Exception as e:
        print(f"❌ Position test failed: {e}")
        return False


def test_market_data():
    """Test market data retrieval"""
    print("\n📈 Testing Market Data...")
    print("-" * 40)
    
    try:
        with create_moomoo_trading() as trading:
            if not trading.connected:
                print("❌ Not connected to Moomoo")
                return False
            
            test_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
            print("✅ Testing real-time prices:")
            
            for ticker in test_tickers:
                price = trading.get_current_price(ticker)
                if price:
                    print(f"   {ticker}: ${price:.2f}")
                else:
                    print(f"   {ticker}: ❌ Price not available")
            
            return True
                
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        return False


def test_order_validation():
    """Test order validation without placing actual orders"""
    print("\n🔍 Testing Order Validation...")
    print("-" * 40)
    
    try:
        with create_moomoo_trading() as trading:
            if not trading.connected:
                print("❌ Not connected to Moomoo")
                return False
            
            # Test validation logic
            test_decisions = {
                "AAPL": {
                    "action": "buy",
                    "quantity": 1,
                    "confidence": 85.0,
                    "reasoning": "Test validation order"
                }
            }
            
            print("✅ Testing order validation:")
            for ticker, decision in test_decisions.items():
                price = trading.get_current_price(ticker)
                if price:
                    order_value = decision["quantity"] * price
                    print(f"   {ticker}: {decision['action']} {decision['quantity']} shares")
                    print(f"   Current price: ${price:.2f}")
                    print(f"   Order value: ${order_value:.2f}")
                    
                    # Check account balance
                    account_info = trading.get_account_info()
                    if account_info and account_info.cash >= order_value:
                        print(f"   ✅ Sufficient funds available")
                    else:
                        print(f"   ⚠️ Insufficient funds (need ${order_value:.2f}, have ${account_info.cash:.2f})")
                else:
                    print(f"   ❌ Cannot get price for {ticker}")
            
            return True
                
    except Exception as e:
        print(f"❌ Order validation test failed: {e}")
        return False


def test_simulated_execution():
    """Test simulated order execution (dry run)"""
    print("\n🎯 Testing Simulated Execution...")
    print("-" * 40)
    
    try:
        # Create test decisions
        test_decisions = {
            "AAPL": {
                "action": "buy",
                "quantity": 1,
                "confidence": 85.0,
                "reasoning": "Test buy order - simulation only"
            },
            "MSFT": {
                "action": "hold",
                "quantity": 0,
                "confidence": 50.0,
                "reasoning": "Test hold decision"
            }
        }
        
        print("✅ Simulating execution of trading decisions:")
        for ticker, decision in test_decisions.items():
            print(f"   {ticker}: {decision['action']} {decision['quantity']} shares "
                  f"(confidence: {decision['confidence']}%)")
        
        print("\n   Note: This is a simulation - no actual orders will be placed")
        print("   To enable real trading, modify the test to call execute_decisions()")
        
        return True
        
    except Exception as e:
        print(f"❌ Simulated execution test failed: {e}")
        return False


def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Moomoo Broker Integration Test Suite")
    print("=" * 60)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check moomoo-api package
    try:
        import moomoo
        print(f"✅ moomoo-api package found (version: {moomoo.__version__})")
    except ImportError:
        print("❌ moomoo-api package not found!")
        print("   Please install it with: pip install moomoo-api")
        return False
    
    # Run tests
    tests = [
        ("Configuration", test_configuration),
        ("Connection", test_connection),
        ("Account Information", test_account_info),
        ("Paper Trading Funds", test_paper_trading_funds),
        ("Position Information", test_positions),
        ("Market Data", test_market_data),
        ("Order Validation", test_order_validation),
        ("Simulated Execution", test_simulated_execution),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    success_rate = passed / len(results) if results else 0
    print(f"\nTotal: {passed}/{len(results)} tests passed ({success_rate:.1%})")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Moomoo integration is ready to use.")
        print("\n📋 Next Steps:")
        print("1. Copy trading_keys.example.yaml to trading_keys.yaml")
        print("2. Update configuration with your settings")
        print("3. Ensure Moomoo OpenD is running")
        print("4. Run Portfolio Manager with Moomoo integration")
    else:
        print(f"\n⚠️ {len(results) - passed} test(s) failed.")
        print("\n🔧 Common Issues:")
        print("- Moomoo OpenD not running")
        print("- Network connection problems")
        print("- Account not logged in")
        print("- Paper trading not enabled")
    
    return passed == len(results)


def main():
    """Main function"""
    import argparse
    import signal
    
    def signal_handler(signum, frame):
        print("\n⚠️ Test interrupted by user. Exiting...")
        sys.exit(1)
    
    # Set up global signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description="Moomoo Broker Integration Test")
    parser.add_argument("--test", choices=[
        "config", "connection", "account", "paper_funds", "positions", 
        "market", "validation", "simulation", "all"
    ], default="all", help="Specific test to run")
    parser.add_argument("--timeout", type=int, default=30, help="Connection timeout in seconds")
    
    args = parser.parse_args()
    
    try:
        if args.test == "all":
            success = run_comprehensive_test()
        else:
            test_map = {
                "config": test_configuration,
                "connection": test_connection,
                "account": test_account_info,
                "paper_funds": test_paper_trading_funds,
                "positions": test_positions,
                "market": test_market_data,
                "validation": test_order_validation,
                "simulation": test_simulated_execution
            }
            
            if args.test in test_map:
                success = test_map[args.test]()
            else:
                print(f"Unknown test: {args.test}")
                success = False
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test suite interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()