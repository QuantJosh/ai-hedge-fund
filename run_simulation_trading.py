#!/usr/bin/env python3
"""
AI Hedge Fund - Moomoo Simulation Trading
Complete integration between AI decision system and Moomoo paper trading
"""

import sys
import json
import time
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from src.brokers.moomoo import create_moomoo_trading
    from src.integrations.moomoo_client import MoomooIntegration
    # from src.agents.portfolio_manager_moomoo import portfolio_management_agent_moomoo
    # from src.main import run_hedge_fund_workflow
    # from src.graph.state import AgentState
    from src.utils.logger import init_logger, get_logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Create moomoo integration function
def create_moomoo_integration(paper_trading=True, auto_execute=False):
    """Create Moomoo integration instance"""
    return MoomooIntegration(
        host="127.0.0.1",
        port=11111,
        paper_trading=paper_trading,
        auto_execute=auto_execute
    )


class SimulationTradingRunner:
    """Runs AI hedge fund with Moomoo paper trading integration"""
    
    def __init__(self, 
                 tickers: List[str] = None,
                 paper_trading_only: bool = True,
                 auto_execute: bool = False,
                 sync_positions: bool = True):
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        self._shutdown_requested = False
        """
        Initialize simulation trading runner
        
        Args:
            tickers: List of tickers to analyze and trade
            paper_trading_only: SAFETY: Only use paper trading (default: True)
            auto_execute: Automatically execute trades (default: False for safety)
            sync_positions: Sync positions from Moomoo before making decisions
        """
        self.tickers = tickers or ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        self.paper_trading_only = paper_trading_only
        self.auto_execute = auto_execute
        self.sync_positions = sync_positions
        
        # Safety check
        if not paper_trading_only:
            raise ValueError("🚨 SAFETY: This script only supports paper trading! Set paper_trading_only=True")
        
        # Initialize components
        self.moomoo_integration = None
        init_logger("logs", f"simulation_trading_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.logger = get_logger()
        
        # Results storage
        self.results = {
            "interrupted": False,
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "start_time": datetime.now().isoformat(),
            "tickers": self.tickers,
            "config": {
                "paper_trading_only": self.paper_trading_only,
                "auto_execute": self.auto_execute,
                "sync_positions": self.sync_positions
            },
            "ai_decisions": {},
            "moomoo_execution": {},
            "portfolio_before": {},
            "portfolio_after": {},
            "performance": {}
        }
    
    def initialize_moomoo(self) -> bool:
        """Initialize Moomoo connection with safety checks"""
        print("🔌 Initializing Moomoo connection...")
        
        try:
            # Create Moomoo integration with paper trading ONLY
            self.moomoo_integration = create_moomoo_integration(
                paper_trading=True,  # FORCE paper trading
                auto_execute=False   # Manual execution for safety
            )
            
            if not self.moomoo_integration:
                print("❌ Failed to create Moomoo integration")
                return False
            
            # Connect to Moomoo
            if not self.moomoo_integration.connect():
                print("❌ Failed to connect to Moomoo")
                return False
            
            # Verify it's paper trading
            account_info = self.moomoo_integration.client.get_account_info()
            if not account_info:
                print("⚠️ Could not get account info, but connection successful")
                # Continue anyway since connection works
            
            # Double-check paper trading mode
            if not self.moomoo_integration.client.paper_trading:
                print("🚨 SAFETY ERROR: Not in paper trading mode!")
                return False
            
            print("✅ Moomoo paper trading connection established")
            if account_info:
                print(f"   💰 Paper Trading Balance: ${account_info.get('cash', 0):,.2f}")
                print(f"   📊 Total Assets: ${account_info.get('total_assets', 0):,.2f}")
            else:
                print("   💰 Paper Trading Balance: $1,000,000.00 (default)")
                print("   📊 Total Assets: $1,000,000.00 (default)")
            
            # Store initial portfolio
            try:
                self.results["portfolio_before"] = self.moomoo_integration.get_portfolio_sync()
            except Exception as e:
                print(f"⚠️ Could not sync portfolio: {e}")
                self.results["portfolio_before"] = {"cash": 1000000, "total_assets": 1000000, "positions": {}}
            
            return True
            
        except Exception as e:
            print(f"❌ Error initializing Moomoo: {e}")
            return False
    
    def run_ai_analysis(self) -> Dict:
        """Run simplified AI analysis for simulation"""
        print("🤖 Running simplified AI analysis...")
        
        try:
            # For now, create mock analysis results
            # TODO: Integrate with actual AI agents later
            mock_analysis = {
                "analyst_signals": {
                    ticker: {
                        "signal": "buy" if i % 2 == 0 else "hold",
                        "confidence": 75.0 + (i * 5),
                        "reasoning": f"Mock analysis for {ticker}"
                    }
                    for i, ticker in enumerate(self.tickers)
                },
                "market_sentiment": "neutral",
                "risk_level": "moderate"
            }
            
            print("✅ AI analysis completed (mock data)")
            return mock_analysis
            
        except Exception as e:
            print(f"❌ Error in AI analysis: {e}")
            return None
    
    def generate_trading_decisions(self, analysis_state: Dict) -> Dict:
        """Generate trading decisions based on analysis"""
        print("🎯 Generating trading decisions...")
        
        try:
            # Convert analysis signals to trading decisions
            decisions = {}
            
            for ticker, signal_data in analysis_state.get("analyst_signals", {}).items():
                signal = signal_data.get("signal", "hold")
                confidence = signal_data.get("confidence", 50.0)
                reasoning = signal_data.get("reasoning", "No reasoning provided")
                
                # Simple decision logic
                if signal == "buy" and confidence > 70:
                    quantity = 1  # Small quantity for safety
                    action = "buy"
                elif signal == "sell" and confidence > 70:
                    quantity = 1
                    action = "sell"
                else:
                    quantity = 0
                    action = "hold"
                
                decisions[ticker] = {
                    "action": action,
                    "quantity": quantity,
                    "confidence": confidence,
                    "reasoning": reasoning
                }
            
            decisions_data = {
                "decisions": decisions,
                "portfolio_summary": "Mock portfolio management",
                "risk_assessment": "Low risk simulation"
            }
            
            self.results["ai_decisions"] = decisions
            
            print("✅ Trading decisions generated")
            self._print_decisions(decisions)
            
            return decisions_data
            
        except Exception as e:
            print(f"❌ Error generating decisions: {e}")
            return {}
    
    def execute_trades(self, decisions_data: Dict) -> Dict:
        """Execute trades on Moomoo paper trading platform"""
        print("💼 Executing trades on Moomoo paper trading...")
        
        if not self.auto_execute:
            # Ask for confirmation
            print("\n🤔 Review the trading decisions above.")
            print("⚠️  These will be executed on Moomoo PAPER TRADING account.")
            
            while True:
                response = input("\nProceed with execution? (yes/no/show): ").lower().strip()
                if response in ['yes', 'y']:
                    break
                elif response in ['no', 'n']:
                    print("❌ Execution cancelled by user")
                    return {}
                elif response in ['show', 's']:
                    self._print_decisions(self.results["ai_decisions"])
                else:
                    print("Please enter 'yes', 'no', or 'show'")
        
        try:
            # Get current prices (with fallback to mock prices for testing)
            current_prices = {}
            mock_prices = {
                "AAPL": 175.50,
                "MSFT": 335.20,
                "GOOGL": 138.75,
                "TSLA": 248.90,
                "NVDA": 465.30,
                "AMZN": 145.80,
                "META": 298.50,
                "NFLX": 425.60
            }
            
            for ticker in self.tickers:
                price = self.moomoo_integration.client.get_current_price(ticker)
                if price:
                    current_prices[ticker] = price
                    print(f"   📈 {ticker}: ${price:.2f} (real-time)")
                elif ticker in mock_prices:
                    current_prices[ticker] = mock_prices[ticker]
                    print(f"   📈 {ticker}: ${mock_prices[ticker]:.2f} (mock price - no market data access)")
                else:
                    print(f"   ❌ {ticker}: Price not available")
            
            # Execute the decisions
            execution_results = self.moomoo_integration.execute_decisions(
                decisions=self.results["ai_decisions"],
                current_prices=current_prices
            )
            
            # Store results
            self.results["moomoo_execution"] = {
                ticker: {
                    "success": result.success,
                    "message": result.message,
                    "order_id": result.order_id,
                    "executed_price": result.executed_price,
                    "executed_quantity": result.executed_quantity
                }
                for ticker, result in execution_results.items()
            }
            
            # Save execution log
            self.moomoo_integration.save_execution_log(
                f"simulation_execution_{self.results['session_id']}.json"
            )
            
            print("✅ Trade execution completed")
            return execution_results
            
        except Exception as e:
            print(f"❌ Error executing trades: {e}")
            return {}
    
    def analyze_performance(self) -> Dict:
        """Analyze trading performance"""
        print("📊 Analyzing performance...")
        
        try:
            # Wait a moment for orders to settle
            time.sleep(2)
            
            # Get updated portfolio
            portfolio_after = self.moomoo_integration.get_portfolio_sync()
            self.results["portfolio_after"] = portfolio_after
            
            # Calculate performance metrics
            before = self.results["portfolio_before"]
            after = portfolio_after
            
            performance = {
                "cash_change": after.get("cash", 0) - before.get("cash", 0),
                "total_assets_change": after.get("total_assets", 0) - before.get("total_assets", 0),
                "positions_before": len(before.get("positions", {})),
                "positions_after": len(after.get("positions", {})),
                "successful_trades": sum(1 for r in self.results["moomoo_execution"].values() if r.get("success")),
                "total_trades": len(self.results["moomoo_execution"]),
                "execution_rate": 0
            }
            
            if performance["total_trades"] > 0:
                performance["execution_rate"] = performance["successful_trades"] / performance["total_trades"] * 100
            
            self.results["performance"] = performance
            
            print("✅ Performance analysis completed")
            self._print_performance(performance)
            
            return performance
            
        except Exception as e:
            print(f"❌ Error analyzing performance: {e}")
            return {}
    
    def save_results(self) -> str:
        """Save simulation results to file"""
        try:
            self.results["end_time"] = datetime.now().isoformat()
            
            filename = f"simulation_results_{self.results['session_id']}.json"
            filepath = Path("results") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Results saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            return ""
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n⚠️  Shutdown requested (Ctrl+C). Cleaning up...")
        self._shutdown_requested = True
        
        # Disconnect from Moomoo if connected
        if self.moomoo_integration:
            try:
                print("🔌 Disconnecting from Moomoo...")
                self.moomoo_integration.disconnect()
                print("✅ Disconnected successfully")
            except Exception as e:
                print(f"⚠️  Error during disconnect: {e}")
        
        # Mark results as interrupted
        self.results["interrupted"] = True
        self.results["end_time"] = datetime.now().isoformat()
        
        # Try to save partial results
        try:
            self.save_results()
            print("💾 Partial results saved")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")
        
        print("👋 Goodbye!")
        sys.exit(0)
    
    def _check_shutdown(self):
        """Check if shutdown was requested"""
        if self._shutdown_requested:
            raise KeyboardInterrupt("Shutdown requested")
    
    def run_complete_simulation(self) -> Dict:
        """Run complete simulation trading workflow"""
        print("🚀 Starting AI Hedge Fund Simulation Trading")
        print("=" * 60)
        print(f"📅 Session: {self.results['session_id']}")
        print(f"📊 Tickers: {', '.join(self.tickers)}")
        print(f"🔒 Paper Trading Only: {self.paper_trading_only}")
        print(f"⚡ Auto Execute: {self.auto_execute}")
        print("=" * 60)
        
        try:
            # Step 1: Initialize Moomoo
            self._check_shutdown()
            if not self.initialize_moomoo():
                return {"error": "Failed to initialize Moomoo"}
            
            # Step 2: Run AI analysis
            self._check_shutdown()
            analysis_state = self.run_ai_analysis()
            if not analysis_state:
                return {"error": "Failed to run AI analysis"}
            
            # Step 3: Generate trading decisions
            self._check_shutdown()
            decisions_data = self.generate_trading_decisions(analysis_state)
            if not decisions_data:
                return {"error": "Failed to generate decisions"}
            
            # Step 4: Execute trades
            self._check_shutdown()
            execution_results = self.execute_trades(decisions_data)
            
            # Step 5: Analyze performance
            self._check_shutdown()
            performance = self.analyze_performance()
            
            # Step 6: Save results
            results_file = self.save_results()
            
            print("\n" + "=" * 60)
            print("🎉 Simulation Trading Completed Successfully!")
            print(f"📄 Results saved to: {results_file}")
            print("=" * 60)
            
            return self.results
            
        except Exception as e:
            print(f"\n❌ Simulation failed: {e}")
            return {"error": str(e)}
        
        finally:
            # Always disconnect
            if self.moomoo_integration:
                self.moomoo_integration.disconnect()
    
    def _print_decisions(self, decisions: Dict):
        """Print trading decisions in a formatted way"""
        print("\n📋 Trading Decisions:")
        print("-" * 50)
        
        for ticker, decision in decisions.items():
            action = decision.get("action", "hold").upper()
            quantity = decision.get("quantity", 0)
            confidence = decision.get("confidence", 0)
            reasoning = decision.get("reasoning", "")
            
            # Action emoji
            action_emoji = {
                "BUY": "🟢",
                "SELL": "🔴", 
                "SHORT": "🟠",
                "COVER": "🟡",
                "HOLD": "⚪"
            }.get(action, "❓")
            
            print(f"{action_emoji} {ticker}: {action} {quantity} shares (confidence: {confidence:.1f}%)")
            if reasoning:
                print(f"   💭 {reasoning}")
        
        print("-" * 50)
    
    def _print_performance(self, performance: Dict):
        """Print performance metrics"""
        print("\n📊 Performance Summary:")
        print("-" * 40)
        print(f"💰 Cash Change: ${performance.get('cash_change', 0):,.2f}")
        print(f"📈 Total Assets Change: ${performance.get('total_assets_change', 0):,.2f}")
        print(f"📊 Positions Before: {performance.get('positions_before', 0)}")
        print(f"📊 Positions After: {performance.get('positions_after', 0)}")
        print(f"✅ Successful Trades: {performance.get('successful_trades', 0)}/{performance.get('total_trades', 0)}")
        print(f"📊 Execution Rate: {performance.get('execution_rate', 0):.1f}%")
        print("-" * 40)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Hedge Fund Simulation Trading")
    parser.add_argument("--tickers", "-t", nargs="+", 
                       default=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                       help="Tickers to analyze and trade")
    parser.add_argument("--auto-execute", "-e", action="store_true",
                       help="Automatically execute trades without confirmation")
    parser.add_argument("--no-sync", action="store_true",
                       help="Don't sync positions from Moomoo before trading")
    
    args = parser.parse_args()
    
    # Safety warning
    print("⚠️  SIMULATION TRADING MODE")
    print("   This script uses Moomoo PAPER TRADING only")
    print("   No real money will be used")
    print()
    
    # Create and run simulation
    runner = SimulationTradingRunner(
        tickers=args.tickers,
        paper_trading_only=True,  # ALWAYS True for safety
        auto_execute=args.auto_execute,
        sync_positions=not args.no_sync
    )
    
    results = runner.run_complete_simulation()
    
    if "error" in results:
        print(f"❌ Simulation failed: {results['error']}")
        sys.exit(1)
    else:
        print("🎉 Simulation completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()