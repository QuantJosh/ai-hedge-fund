#!/usr/bin/env python3
"""
AI Hedge Fund - Quick Start Simulation Trading
One-click simulation trading with popular stocks
"""

import sys
import signal
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from run_simulation_trading import SimulationTradingRunner

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n⚠️ Quick start interrupted by user (Ctrl+C)")
    print("👋 Goodbye!")
    sys.exit(1)

def main():
    """Quick start simulation with popular stocks"""
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 AI Hedge Fund - Quick Start Simulation")
    print("=" * 50)
    print("⚠️  PAPER TRADING ONLY - No real money used")
    print("=" * 50)
    
    # Popular stock combinations
    stock_sets = {
        "1": {
            "name": "Tech Giants",
            "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN"],
            "description": "Apple, Microsoft, Google, Amazon"
        },
        "2": {
            "name": "AI & Innovation", 
            "tickers": ["NVDA", "TSLA", "META", "NFLX"],
            "description": "NVIDIA, Tesla, Meta, Netflix"
        },
        "3": {
            "name": "Market Leaders",
            "tickers": ["AAPL", "MSFT", "NVDA", "TSLA"],
            "description": "Top 4 by market cap"
        },
        "4": {
            "name": "Diversified Mix",
            "tickers": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META"],
            "description": "6 major tech stocks"
        },
        "5": {
            "name": "Custom",
            "tickers": [],
            "description": "Enter your own tickers"
        }
    }
    
    print("\n📊 Choose a stock portfolio:")
    for key, stock_set in stock_sets.items():
        print(f"   {key}. {stock_set['name']}: {stock_set['description']}")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice in stock_sets:
                selected_set = stock_sets[choice]
                
                if choice == "5":  # Custom
                    print("\nEnter stock tickers separated by spaces (e.g., AAPL MSFT GOOGL):")
                    custom_input = input("Tickers: ").strip().upper()
                    if custom_input:
                        tickers = custom_input.split()
                    else:
                        print("❌ No tickers entered. Using default.")
                        tickers = ["AAPL", "MSFT"]
                else:
                    tickers = selected_set["tickers"]
                
                break
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            signal_handler(None, None)
    
    print(f"\n✅ Selected: {', '.join(tickers)}")
    
    # Ask for execution mode
    print("\n⚡ Execution mode:")
    print("   1. Manual confirmation (recommended)")
    print("   2. Auto-execute (faster)")
    
    while True:
        try:
            exec_choice = input("\nEnter execution mode (1-2): ").strip()
            
            if exec_choice == "1":
                auto_execute = False
                break
            elif exec_choice == "2":
                auto_execute = True
                break
            else:
                print("❌ Invalid choice. Please enter 1 or 2.")
                
        except KeyboardInterrupt:
            signal_handler(None, None)
    
    print(f"\n🎯 Starting simulation with {len(tickers)} stocks...")
    print(f"⚡ Auto-execute: {'Yes' if auto_execute else 'No'}")
    print("\n" + "=" * 50)
    
    try:
        # Create and run simulation
        runner = SimulationTradingRunner(
            tickers=tickers,
            paper_trading_only=True,
            auto_execute=auto_execute,
            sync_positions=True
        )
        
        result = runner.run_complete_simulation()
        
        if "error" not in result:
            print("\n🎉 Quick start simulation completed successfully!")
            
            # Show quick summary
            performance = result.get("performance", {})
            successful_trades = performance.get("successful_trades", 0)
            total_trades = performance.get("total_trades", 0)
            execution_rate = performance.get("execution_rate", 0)
            
            print(f"\n📊 Quick Summary:")
            print(f"   ✅ Successful trades: {successful_trades}/{total_trades}")
            print(f"   📈 Execution rate: {execution_rate:.1f}%")
            print(f"   📄 Results saved to: results/simulation_results_{result['session_id']}.json")
            
        else:
            print(f"\n❌ Simulation failed: {result['error']}")
            
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()