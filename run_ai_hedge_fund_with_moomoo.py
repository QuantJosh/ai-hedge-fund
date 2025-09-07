#!/usr/bin/env python3
"""
AI Hedge Fund with Moomoo Integration
Runs the complete AI hedge fund analysis and executes decisions on Moomoo paper trading
"""

import sys
import json
import signal
from pathlib import Path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, List, Optional

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    # AI Hedge Fund imports
    from src.main import run_hedge_fund
    from src.utils.analysts import ANALYST_ORDER
    
    # Moomoo integration imports
    from src.integrations.moomoo_client import MoomooIntegration
    from src.utils.logger import init_logger, get_logger
    
    # Portfolio manager with Moomoo
    from src.agents.portfolio_manager_moomoo import portfolio_management_agent_moomoo
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class AIHedgeFundMoomooRunner:
    """Runs AI hedge fund analysis and executes on Moomoo paper trading"""
    
    def __init__(self, 
                 tickers: List[str],
                 start_date: str = None,
                 end_date: str = None,
                 selected_analysts: List[str] = None,
                 paper_trading_only: bool = True,
                 auto_execute: bool = False,
                 show_reasoning: bool = True,
                 model_name: str | None = None,
                 model_provider: str | None = None):
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        self._shutdown_requested = False
        
        # Configuration
        self.tickers = tickers
        self.start_date = start_date or self._get_default_start_date()
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")
        self.selected_analysts = selected_analysts or self._get_default_analysts()
        self.paper_trading_only = paper_trading_only
        self.auto_execute = auto_execute
        self.show_reasoning = show_reasoning
        # LLM selection (defaults to OpenRouter gpt-4o-mini if not provided)
        self.model_name = model_name or "openai/gpt-4o-mini"
        self.model_provider = model_provider or "OpenRouter"
        
        # Safety check
        if not paper_trading_only:
            raise ValueError("🚨 SAFETY: This script only supports paper trading!")
        
        # Initialize components
        self.moomoo_integration = None
        init_logger("logs", f"ai_hedge_fund_moomoo_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.logger = get_logger()
        
        # Results storage
        self.results = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "start_time": datetime.now().isoformat(),
            "config": {
                "tickers": self.tickers,
                "start_date": self.start_date,
                "end_date": self.end_date,
                "selected_analysts": self.selected_analysts,
                "paper_trading_only": self.paper_trading_only,
                "auto_execute": self.auto_execute,
                "show_reasoning": self.show_reasoning,
                "model_name": self.model_name,
                "model_provider": self.model_provider,
            },
            "ai_analysis": {},
            "trading_decisions": {},
            "moomoo_execution": {},
            "portfolio_before": {},
            "portfolio_after": {},
            "performance": {},
            "interrupted": False
        }
    
    def _get_default_start_date(self) -> str:
        """Get default start date (3 months ago)"""
        end_date_obj = datetime.now()
        start_date_obj = end_date_obj - relativedelta(months=3)
        return start_date_obj.strftime("%Y-%m-%d")
    
    def _get_default_analysts(self) -> List[str]:
        """Get default analysts (top 5 most important)"""
        return [
            "warren_buffett",
            "ben_graham", 
            "charlie_munger",
            "peter_lynch",
            "fundamentals_analyst"
        ]
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n⚠️  AI Hedge Fund interrupted (Ctrl+C). Cleaning up...")
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
    
    def initialize_moomoo(self) -> bool:
        """Initialize Moomoo connection"""
        print("🔌 Initializing Moomoo connection...")
        
        try:
            self.moomoo_integration = MoomooIntegration(
                host="127.0.0.1",
                port=11111,
                paper_trading=True,
                auto_execute=False
            )
            
            if not self.moomoo_integration.connect():
                print("❌ Failed to connect to Moomoo")
                return False
            
            print("✅ Moomoo paper trading connection established")
            
            # Store initial portfolio
            try:
                self.results["portfolio_before"] = self.moomoo_integration.get_portfolio_sync()
                portfolio = self.results["portfolio_before"]
                print(f"   💰 Paper Trading Balance: ${portfolio.get('cash', 0):,.2f}")
                print(f"   📊 Total Assets: ${portfolio.get('total_assets', 0):,.2f}")
            except Exception as e:
                print(f"⚠️ Could not sync portfolio: {e}")
                self.results["portfolio_before"] = {"cash": 1000000, "total_assets": 1000000, "positions": {}}
            
            return True
            
        except Exception as e:
            print(f"❌ Error initializing Moomoo: {e}")
            return False
    
    def run_ai_hedge_fund_analysis(self) -> Dict:
        """Run the complete AI hedge fund analysis"""
        print("🤖 Running AI Hedge Fund Analysis...")
        print(f"   📊 Analyzing {len(self.tickers)} tickers: {', '.join(self.tickers)}")
        print(f"   📅 Period: {self.start_date} to {self.end_date}")
        print(f"   🧠 Using {len(self.selected_analysts)} AI analysts")
        
        self._check_shutdown()
        
        try:
            # Build initial portfolio using synced data from Moomoo when available
            before = self.results.get("portfolio_before", {}) or {}
            initial_positions = self._translate_moomoo_positions(
                before.get("positions", {}), self.tickers
            )
            initial_portfolio = {
                "cash": before.get("cash", 1000000),
                "margin_requirement": before.get("margin_requirement", 0.0),
                "margin_used": before.get("margin_used", 0.0),
                "positions": initial_positions,
                "realized_gains": {
                    ticker: {"long": 0.0, "short": 0.0}
                    for ticker in self.tickers
                },
            }
            
            # Run the AI hedge fund analysis
            print("   🔍 Running analyst agents...")
            result = run_hedge_fund(
                tickers=self.tickers,
                start_date=self.start_date,
                end_date=self.end_date,
                portfolio=initial_portfolio,
                show_reasoning=self.show_reasoning,
                selected_analysts=self.selected_analysts,
                model_name=self.model_name,
                model_provider=self.model_provider
            )
            
            self.results["ai_analysis"] = {
                "decisions": result.get("decisions", {}),
                "analyst_signals": result.get("analyst_signals", {})
            }
            
            print("✅ AI hedge fund analysis completed")
            return result
            
        except Exception as e:
            print(f"❌ Error in AI analysis: {e}")
            return {}

    def _translate_moomoo_positions(self, mm_positions: Dict, tickers: List[str]) -> Dict[str, Dict]:
        """Translate Moomoo positions dict into PortfolioManager schema per ticker.
        Expected Moomoo input shape per ticker (best-effort):
          { ticker: { quantity, cost_price, ... } }
        Output per ticker:
          { 'long': int, 'short': int, 'long_cost_basis': float, 'short_cost_basis': float, 'short_margin_used': float }
        Missing tickers will be filled with zero positions.
        """
        out: Dict[str, Dict] = {}
        try:
            for t in tickers:
                p = mm_positions.get(t) or mm_positions.get(t.upper()) or mm_positions.get(t.lower()) or {}
                qty = int(p.get("quantity", 0) or 0)
                cost = float(p.get("cost_price", 0.0) or 0.0)
                if qty >= 0:
                    out[t] = {
                        "long": qty,
                        "short": 0,
                        "long_cost_basis": cost,
                        "short_cost_basis": 0.0,
                        "short_margin_used": 0.0,
                    }
                else:
                    # Negative quantity treated as short (if ever provided)
                    out[t] = {
                        "long": 0,
                        "short": abs(qty),
                        "long_cost_basis": 0.0,
                        "short_cost_basis": cost,
                        "short_margin_used": 0.0,
                    }
            # Ensure all tickers present
            for t in tickers:
                out.setdefault(t, {
                    "long": 0,
                    "short": 0,
                    "long_cost_basis": 0.0,
                    "short_cost_basis": 0.0,
                    "short_margin_used": 0.0,
                })
        except Exception:
            # Fallback: zero positions
            out = {
                t: {
                    "long": 0,
                    "short": 0,
                    "long_cost_basis": 0.0,
                    "short_cost_basis": 0.0,
                    "short_margin_used": 0.0,
                } for t in tickers
            }
        return out
    
    def convert_ai_decisions_to_moomoo_format(self, ai_decisions: Dict) -> Dict:
        """Convert AI hedge fund decisions to Moomoo trading format"""
        print("🔄 Converting AI decisions to Moomoo format...")
        
        moomoo_decisions = {}
        
        for ticker, decision_data in ai_decisions.items():
            action = decision_data.get("action", "hold")
            quantity = decision_data.get("quantity", 0)
            confidence = decision_data.get("confidence", 0.0)
            reasoning = decision_data.get("reasoning", "No reasoning provided")
            
            moomoo_decisions[ticker] = {
                "action": action,
                "quantity": quantity,
                "confidence": confidence,
                "reasoning": f"AI Hedge Fund Decision: {reasoning}"
            }
        
        self.results["trading_decisions"] = moomoo_decisions
        
        print("✅ AI decisions converted to Moomoo format")
        self._print_decisions(moomoo_decisions)
        
        return moomoo_decisions
    
    def execute_trades_on_moomoo(self, decisions: Dict) -> Dict:
        """Execute trading decisions on Moomoo paper trading"""
        print("💼 Executing trades on Moomoo paper trading...")
        
        if not self.auto_execute:
            print("\n🤔 Review the AI hedge fund decisions above.")
            print("⚠️  These will be executed on Moomoo PAPER TRADING account.")
            
            while True:
                response = input("\nProceed with execution? (yes/no/show): ").lower().strip()
                if response in ['yes', 'y']:
                    break
                elif response in ['no', 'n']:
                    print("❌ Execution cancelled by user")
                    return {}
                elif response in ['show', 's']:
                    self._print_decisions(decisions)
                else:
                    print("Please enter 'yes', 'no', or 'show'")
        
        self._check_shutdown()
        
        try:
            # Get current prices (with fallback to mock prices)
            current_prices = {}
            mock_prices = {
                "AAPL": 175.50, "MSFT": 335.20, "GOOGL": 138.75,
                "TSLA": 248.90, "NVDA": 465.30, "AMZN": 145.80,
                "META": 298.50, "NFLX": 425.60, "BRK.B": 425.00,
                "JPM": 155.30, "V": 265.80, "JNJ": 162.40
            }
            
            for ticker in self.tickers:
                price = self.moomoo_integration.client.get_current_price(ticker)
                if price:
                    current_prices[ticker] = price
                    print(f"   📈 {ticker}: ${price:.2f} (real-time)")
                elif ticker in mock_prices:
                    current_prices[ticker] = mock_prices[ticker]
                    print(f"   📈 {ticker}: ${mock_prices[ticker]:.2f} (mock price)")
                else:
                    print(f"   ❌ {ticker}: Price not available")
            
            # Execute the decisions
            execution_results = self.moomoo_integration.execute_decisions(
                decisions=decisions,
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
            
            print("✅ Trade execution completed")
            return execution_results
            
        except Exception as e:
            print(f"❌ Error executing trades: {e}")
            return {}
    
    def analyze_performance(self) -> Dict:
        """Analyze trading performance"""
        print("📊 Analyzing performance...")
        
        try:
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
        """Save complete results to file"""
        try:
            self.results["end_time"] = datetime.now().isoformat()
            
            filename = f"ai_hedge_fund_moomoo_results_{self.results['session_id']}.json"
            filepath = Path("results") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Results saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            return ""
    
    def run_complete_workflow(self) -> Dict:
        """Run the complete AI hedge fund + Moomoo workflow"""
        print("🚀 AI Hedge Fund + Moomoo Integration")
        print("=" * 60)
        print(f"📅 Session: {self.results['session_id']}")
        print(f"📊 Tickers: {', '.join(self.tickers)}")
        print(f"📅 Analysis Period: {self.start_date} to {self.end_date}")
        print(f"🧠 AI Analysts: {len(self.selected_analysts)} selected")
        print(f"🔒 Paper Trading Only: {self.paper_trading_only}")
        print(f"⚡ Auto Execute: {self.auto_execute}")
        print("=" * 60)
        
        try:
            # Step 1: Initialize Moomoo
            self._check_shutdown()
            if not self.initialize_moomoo():
                return {"error": "Failed to initialize Moomoo"}
            
            # Step 2: Run AI hedge fund analysis
            self._check_shutdown()
            ai_result = self.run_ai_hedge_fund_analysis()
            if not ai_result or not ai_result.get("decisions"):
                return {"error": "Failed to run AI analysis"}
            
            # Step 3: Convert AI decisions to Moomoo format
            self._check_shutdown()
            moomoo_decisions = self.convert_ai_decisions_to_moomoo_format(ai_result["decisions"])
            if not moomoo_decisions:
                return {"error": "Failed to convert decisions"}
            
            # Step 4: Execute trades on Moomoo
            self._check_shutdown()
            execution_results = self.execute_trades_on_moomoo(moomoo_decisions)
            
            # Step 5: Analyze performance
            self._check_shutdown()
            performance = self.analyze_performance()
            
            # Step 6: Save results
            results_file = self.save_results()
            
            print("\n" + "=" * 60)
            print("🎉 AI Hedge Fund + Moomoo Integration Completed!")
            print(f"📄 Results saved to: {results_file}")
            print("=" * 60)
            
            return self.results
            
        except Exception as e:
            print(f"\n❌ Workflow failed: {e}")
            return {"error": str(e)}
        
        finally:
            # Always disconnect
            if self.moomoo_integration:
                self.moomoo_integration.disconnect()
    
    def _print_decisions(self, decisions: Dict):
        """Print trading decisions in a formatted way"""
        print("\n📋 AI Hedge Fund Trading Decisions:")
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
        print("\n📊 AI Hedge Fund Performance Summary:")
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
    
    parser = argparse.ArgumentParser(description="AI Hedge Fund with Moomoo Integration")
    parser.add_argument("--tickers", "-t", nargs="+", 
                       default=["AAPL", "MSFT", "GOOGL", "TSLA"],
                       help="Tickers to analyze and trade")
    parser.add_argument("--start-date", 
                       help="Start date (YYYY-MM-DD), defaults to 3 months ago")
    parser.add_argument("--end-date", 
                       help="End date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--analysts", nargs="+",
                       help="Selected analysts (defaults to top 5)")
    parser.add_argument("--auto-execute", "-e", action="store_true",
                       help="Automatically execute trades without confirmation")
    parser.add_argument("--no-reasoning", action="store_true",
                       help="Don't show AI reasoning")
    
    args = parser.parse_args()
    
    # Safety warning
    print("⚠️  AI HEDGE FUND + MOOMOO INTEGRATION")
    print("   This uses REAL AI analysis with Moomoo PAPER TRADING")
    print("   No real money will be used")
    print()
    
    # Create and run the AI hedge fund
    runner = AIHedgeFundMoomooRunner(
        tickers=args.tickers,
        start_date=args.start_date,
        end_date=args.end_date,
        selected_analysts=args.analysts,
        paper_trading_only=True,  # ALWAYS True for safety
        auto_execute=args.auto_execute,
        show_reasoning=not args.no_reasoning
    )
    
    results = runner.run_complete_workflow()
    
    if "error" in results:
        print(f"❌ AI Hedge Fund failed: {results['error']}")
        sys.exit(1)
    else:
        print("🎉 AI Hedge Fund + Moomoo integration completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()