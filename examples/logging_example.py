#!/usr/bin/env python3
"""
AI Hedge Fund Logging Example
Demonstrates how to use the enhanced logging system with decorators.
"""

import time
import random
from src.utils.llm_logger import log_agent_execution, log_llm_call, log_data_operation, setup_logging


# Setup logging with human-readable console output
logger = setup_logging(console_format="human", console_level="INFO")


@log_data_operation("stock_price", "Yahoo_Finance")
def fetch_stock_data(ticker: str):
    """Example data fetching function"""
    print(f"Fetching stock data for {ticker}...")
    time.sleep(0.5)  # Simulate API call
    
    # Simulate some data
    return {
        "ticker": ticker,
        "data": [
            {"date": "2024-01-15", "price": 150.0 + random.random() * 10},
            {"date": "2024-01-16", "price": 151.0 + random.random() * 10},
            {"date": "2024-01-17", "price": 149.0 + random.random() * 10},
        ]
    }


@log_llm_call("Michael_Burry", "AAPL")
def analyze_with_llm(prompt: str, model: str = "gpt-4"):
    """Example LLM call function"""
    print(f"Calling {model} with prompt length: {len(prompt)}")
    time.sleep(1.0)  # Simulate LLM call
    
    # Simulate LLM response
    responses = [
        "Based on the analysis, I recommend a STRONG BUY with 85% confidence.",
        "The technical indicators suggest a HOLD position with 70% confidence.",
        "Market conditions indicate a SELL recommendation with 90% confidence."
    ]
    
    class MockResponse:
        def __init__(self, content):
            self.content = content
    
    return MockResponse(random.choice(responses))


@log_agent_execution("Michael_Burry")
def run_analysis(state: dict):
    """Example agent execution function"""
    ticker = state['data']['tickers'][0]
    
    # Fetch data
    stock_data = fetch_stock_data(ticker)
    
    # Analyze with LLM
    prompt = f"Analyze {ticker} stock data: {stock_data}"
    analysis = analyze_with_llm(prompt, model="gpt-4")
    
    # Simulate decision making
    time.sleep(0.5)
    
    return {
        "messages": [analysis],
        "data": {
            "analysis_results": {
                "signal": "BUY",
                "confidence": 85.0,
                "reasoning": analysis.content
            },
            "tickers": [ticker]
        }
    }


def main():
    """Run the logging example"""
    print("🚀 AI Hedge Fund Logging Example")
    print("=" * 50)
    
    # Example state
    state = {
        "data": {
            "tickers": ["AAPL"],
            "market_data": True,
            "news_data": False,
            "financial_data": True
        },
        "metadata": {
            "current_agent": "Michael_Burry"
        }
    }
    
    try:
        # Run analysis
        result = run_analysis(state)
        
        print("\n📋 Analysis completed successfully!")
        print(f"Decision: {result['data']['analysis_results']['signal']}")
        print(f"Confidence: {result['data']['analysis_results']['confidence']}%")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
    
    finally:
        # Close logger
        logger.close()
        print("\n📁 Logs saved to 'logs/' directory")
        print("💡 Use 'python tools/log_viewer.py --find' to view logs")


if __name__ == "__main__":
    main()