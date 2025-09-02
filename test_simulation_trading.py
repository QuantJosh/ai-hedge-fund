#!/usr/bin/env python3
"""
Test Simulation Trading Integration
Quick test to verify AI decisions can be executed on Moomoo paper trading
"""

import sys
import json
import signal
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from src.brokers.moomoo import create_moomoo_trading
    from src.integrations.moomoo_client import create_moomoo_integration
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def test_moomoo_connection():
    """Test basic Moomoo connection and account info"""
    print("🔌 Testing Moomoo Connection...")
    
    try:
        # Create Moomoo integration
        integration = create_moomoo_integration(paper_trading=True)
        
        if not integration:
            print("❌ Failed to connect to Moomoo")
            return False
        
        # Get account info
        account_info = integration.client.get_account_info()
        print(f"✅ Connected to Moomoo Paper Trading")
        print(f"   💰 Cash: ${account_info.get('cash', 0):,.2f}")
        print(f"   📊 Total Assets: ${account_info.get('total_assets', 0):,.2f}")
        
        # Get positions
        positions = integration.client.get_positions()
        print(f"   📈 Current Positions: {len(positions)}")
        
        for ticker, pos in positions.items():
            print(f"      {ticker}: {pos['quantity']} shares @ ${pos['current_price']:.2f}")
        
        integration.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def test_price_fetching():
    """Test real-time price fetching"""
    print("\n📊 Testing Price Fetching...")
    
    test_tickers = ["AAPL", "MSFT", "GOOGL"]
    
    try:
        integration = create_moomoo_integration(paper_trading=True)
        
        if not integration:
            return False
        
        prices = {}
        for ticker in test_tickers:
            price = integration.client.get_current_price(ticker)
            prices[ticker] = price
            
            if price:
                print(f"   📈 {ticker}: ${price:.2f}")
            else:
                print(f"   ❌ {ticker}: Price not available")
        
        integration.disconnect()
        return all(prices.values())
        
    except Exception as e:
        print(f"❌ Price fetching test failed: {e}")
        return False


def test_mock_trading_decisions():
    """Test executing mock trading decisions"""
    print("\n🎯 Testing Mock Trading Decisions...")
    
    # Create mock decisions (small quantities for safety)
    mock_decisions = {
        "AAPL": {
            "action": "buy",
            "quantity": 1,
            "confidence": 75.0,
            "reasoning": "Test buy order for simulation"
        },
        "MSFT": {
            "action": "hold",
            "quantity": 0,
            "confidence": 50.0,
            "reasoning": "Test hold decision"
        }
    }
    
    try:
        integration = create_moomoo_integration(paper_trading=True)
        
        if not integration:
            return False
        
        print("   📋 Mock Decisions:")
        for ticker, decision in mock_decisions.items():
            print(f"      {ticker}: {decision['action']} {decision['quantity']} shares")
        
        # Ask for confirmation
        response = input("\n   Execute these mock trades on paper account? (yes/no): ").lower()
        
        if response not in ['yes', 'y']:
            print("   ⏭️  Skipping execution test")
            integration.disconnect()
            return True
        
        # Get current prices
        current_prices = {}
        for ticker in mock_decisions.keys():
            price = integration.client.get_current_price(ticker)
            if price:
                current_prices[ticker] = price
        
        # Execute decisions
        results = integration.execute_decisions(mock_decisions, current_prices)
        
        # Print results
        print("   📊 Execution Results:")
        for ticker, result in results.items():
            status = "✅" if result.success else "❌"
            print(f"      {status} {ticker}: {result.message}")
        
        # Save execution log
        integration.save_execution_log("test_execution_log.json")
        
        integration.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Mock trading test failed: {e}")
        return False


def test_portfolio_sync():
    """Test portfolio synchronization"""
    print("\n🔄 Testing Portfolio Sync...")
    
    try:
        integration = create_moomoo_integration(paper_trading=True)
        
        if not integration:
            return False
        
        # Get synchronized portfolio
        portfolio = integration.get_portfolio_sync()
        
        print("   📊 Synchronized Portfolio:")
        print(f"      💰 Cash: ${portfolio.get('cash', 0):,.2f}")
        print(f"      📈 Total Assets: ${portfolio.get('total_assets', 0):,.2f}")
        
        positions = portfolio.get('positions', {})
        print(f"      📊 Positions: {len(positions)}")
        
        for ticker, pos in positions.items():
            long_qty = pos.get('long', 0)
            short_qty = pos.get('short', 0)
            if long_qty > 0:
                print(f"         {ticker}: LONG {long_qty} shares @ ${pos.get('long_cost_basis', 0):.2f}")
            if short_qty > 0:
                print(f"         {ticker}: SHORT {short_qty} shares @ ${pos.get('short_cost_basis', 0):.2f}")
        
        integration.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Portfolio sync test failed: {e}")
        return False


def run_all_tests():
    """Run all simulation trading tests"""
    print("🧪 AI Hedge Fund - Simulation Trading Tests")
    print("=" * 50)
    print("⚠️  All tests use PAPER TRADING only")
    print("=" * 50)
    
    tests = [
        ("Moomoo Connection", test_moomoo_connection),
        ("Price Fetching", test_price_fetching),
        ("Portfolio Sync", test_portfolio_sync),
        ("Mock Trading Decisions", test_mock_trading_decisions),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    success_rate = passed / len(results) if results else 0
    print(f"\nTotal: {passed}/{len(results)} tests passed ({success_rate:.1%})")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Simulation trading is ready.")
        print("\n📋 Next Steps:")
        print("1. Run: python run_simulation_trading.py")
        print("2. Review AI decisions before execution")
        print("3. Monitor paper trading results")
    else:
        print(f"\n⚠️ {len(results) - passed} test(s) failed.")
        print("Please check Moomoo OpenD connection and configuration.")
    
    return passed == len(results)


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n⚠️ Tests interrupted by user (Ctrl+C)")
    print("👋 Goodbye!")
    sys.exit(1)

def main():
    """Main function"""
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()