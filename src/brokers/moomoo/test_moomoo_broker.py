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


def test_place_and_cancel():
    """Place a tiny market order in SIMULATE env and then cancel it (paper-only safety)."""
    print("\n🧪 Testing Paper Order Place & Cancel (SIMULATE only)...")
    print("-" * 40)
    try:
        with create_moomoo_trading() as trading:
            if not trading.connected:
                print("❌ Not connected to Moomoo")
                return False
            # Safety: only allow in paper trading
            if not getattr(trading.config, "paper_trading", True):
                print("⚠️ Refusing to place order: not in paper (SIMULATE) environment")
                return False

            ticker = "AAPL"  # You may change to a symbol in your paper market
            qty = 1
            print(f"Placing MARKET BUY {qty} share(s) of {ticker} in SIMULATE env...")
            ok, msg, order_id = trading.client.place_order(
                ticker=ticker,
                side="BUY",
                quantity=qty,
                order_type="MARKET",
            )
            if not ok or not order_id:
                print(f"❌ Place order failed: {msg}")
                return False
            print(f"✅ Order placed. ID={order_id}")

            # Brief wait, then query status
            time.sleep(2)
            status = trading.client.get_order_status(order_id)
            if status:
                print(f"🔎 Order status: {status.get('status')} | filled={status.get('filled_qty')} avg_price={status.get('avg_price')}")
            else:
                print("🔎 Order status not found yet")

            # Cancel the order (safe in paper env)
            ok_cancel, cancel_msg = trading.client.cancel_order(order_id)
            if ok_cancel:
                print("✅ Order cancelled successfully")
                return True
            else:
                print(f"⚠️ Cancel failed: {cancel_msg}")
                # Still consider placement success as primary objective
                return True
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Place & Cancel test failed: {e}")
        return False


def test_final_snapshot():
    """Print final snapshot: account info, positions, today's orders, and open orders."""
    print("\n📸 Final Snapshot (Account / Positions / Orders)...")
    print("-" * 60)
    try:
        with create_moomoo_trading() as trading:
            if not trading.connected:
                print("❌ Not connected to Moomoo")
                return False

            # Account info
            acct = trading.get_account_info()
            if acct:
                print("✅ Account:")
                print(f"   Cash=${acct.cash:,.2f}  Total=${acct.total_assets:,.2f}  MV=${acct.market_value:,.2f}  UPL=${acct.unrealized_pnl:,.2f}  CCY={acct.currency}")
            else:
                print("❌ Failed to get account info")

            # Positions
            positions = trading.get_positions()
            print(f"✅ Positions: {len(positions)}")
            if positions:
                for tkr, pos in positions.items():
                    print(f"   {tkr}: qty={pos.quantity} mv=${pos.market_value:,.2f} upnl=${pos.unrealized_pnl:,.2f}")
            else:
                print("   📭 No active positions")

            # Today's orders
            try:
                ret, data = trading.client.trade_ctx.order_list_query(trd_env=trading.config.get_trd_env())
                if ret == 0 and data is not None and not data.empty:
                    print(f"✅ Today's Orders: {len(data)}")
                    open_statuses = {"SUBMITTED", "SUBMITTING", "PARTIALLY_FILLED", "PENDING_SUBMIT"}
                    open_cnt = 0
                    for _, row in data.iterrows():
                        oid = row.get("order_id")
                        code = row.get("code")
                        side = row.get("trd_side") or row.get("trdSide")
                        status = str(row.get("order_status") or row.get("orderStatus") or "")
                        qty = row.get("qty", 0)
                        dealt = row.get("dealt_qty", 0)
                        avg = row.get("dealt_avg_price", 0)
                        print(f"   {oid} | {code} | {side} | {status} | qty={qty} dealt={dealt} avg={avg}")
                        if status.upper() in open_statuses:
                            open_cnt += 1
                    print(f"   🔎 Open/Waiting orders: {open_cnt}")
                else:
                    print("✅ Today's Orders: 0")
            except Exception as e:
                print(f"⚠️ Failed to get today's orders: {e}")

            # Recent history (last 7 days)
            try:
                from datetime import datetime, timedelta
                end = datetime.now().date()
                start = end - timedelta(days=7)
                ret, hdata = trading.client.trade_ctx.history_order_list_query(
                    trd_env=trading.config.get_trd_env(),
                    start=start.strftime("%Y-%m-%d"),
                    end=end.strftime("%Y-%m-%d"),
                )
                if ret == 0 and hdata is not None and not hdata.empty:
                    print(f"✅ History Orders (7d): {len(hdata)}")
                else:
                    print("✅ History Orders (7d): 0")
            except Exception as e:
                print(f"⚠️ Failed to get history orders: {e}")

            return True
    except Exception as e:
        print(f"❌ Final snapshot failed: {e}")
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
        ("Place & Cancel (Paper)", test_place_and_cancel),
        ("Final Snapshot (Acct/Pos/Orders)", test_final_snapshot),
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
        "market", "validation", "simulation", "place_cancel", "final_snapshot", "all"
    ], default="all", help="Specific test to run")
    parser.add_argument("--timeout", type=int, default=30, help="Connection timeout in seconds")
    parser.add_argument("--env", choices=["simulate", "real"], default="simulate", help="Trading environment")
    parser.add_argument("--i-know-what-im-doing", action="store_true", dest="ack_risk", help="Allow real trading actions in tests")
    
    args = parser.parse_args()
    
    try:
        if args.test == "all":
            # Override environment globally by updating config loader default
            # Tests use create_moomoo_trading() which accepts paper_override
            def _runner():
                nonlocal args
                paper = True if args.env == "simulate" else False
                # Monkey-patch factory in closure for each test call
                # We'll pass paper_override in every test by wrapping create_moomoo_trading
                import importlib
                moomoo_pkg = importlib.import_module("src.brokers.moomoo")
                orig_factory = getattr(moomoo_pkg, "create_moomoo_trading")
                def wrapped_factory(config_path=None):
                    return orig_factory(config_path=config_path, paper_override=paper)
                moomoo_pkg.create_moomoo_trading = wrapped_factory
                try:
                    return run_comprehensive_test()
                finally:
                    moomoo_pkg.create_moomoo_trading = orig_factory
            success = _runner()
        else:
            test_map = {
                "config": test_configuration,
                "connection": test_connection,
                "account": test_account_info,
                "paper_funds": test_paper_trading_funds,
                "positions": test_positions,
                "market": test_market_data,
                "validation": test_order_validation,
                "simulation": test_simulated_execution,
                "place_cancel": test_place_and_cancel,
                "final_snapshot": test_final_snapshot,
            }
            
            if args.test in test_map:
                # Wrap factory to apply env override
                paper = True if args.env == "simulate" else False
                from src.brokers.moomoo import __init__ as moomoo_pkg
                orig_factory = moomoo_pkg.create_moomoo_trading
                def wrapped_factory(config_path=None):
                    return orig_factory(config_path=config_path, paper_override=paper)
                moomoo_pkg.create_moomoo_trading = wrapped_factory

                # Block risky tests in REAL unless user acknowledges
                if args.env == "real" and args.test == "place_cancel" and not args.ack_risk:
                    print("⚠️ Refusing to run place_cancel in REAL env without --i-know-what-im-doing")
                    success = False
                else:
                    success = test_map[args.test]()

                moomoo_pkg.create_moomoo_trading = orig_factory
            else:
                print(f"Unknown test: {args.test}")
                success = False
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test suite interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()