"""
Portfolio Manager with Moomoo Integration
Enhanced version that can sync with and execute trades on Moomoo platform
"""

import json
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from src.graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
from typing_extensions import Literal
from src.utils.progress import progress
from src.utils.llm import call_llm
from src.integrations.moomoo_client import MoomooIntegration, TradingDecision


class PortfolioDecision(BaseModel):
    action: Literal["buy", "sell", "short", "cover", "hold"]
    quantity: int = Field(description="Number of shares to trade")
    confidence: float = Field(description="Confidence in the decision, between 0.0 and 100.0")
    reasoning: str = Field(description="Reasoning for the decision")


class PortfolioManagerOutput(BaseModel):
    decisions: dict[str, PortfolioDecision] = Field(description="Dictionary of ticker to trading decisions")


##### Portfolio Management Agent with Moomoo Integration #####
def portfolio_management_agent_moomoo(state: AgentState, 
                                    agent_id: str = "portfolio_manager_moomoo",
                                    moomoo_integration: MoomooIntegration = None,
                                    sync_positions: bool = True,
                                    execute_trades: bool = False):
    """
    Makes final trading decisions with optional Moomoo platform integration
    
    Args:
        state: Agent state
        agent_id: Agent identifier
        moomoo_integration: Moomoo integration instance (optional)
        sync_positions: Whether to sync positions from Moomoo before making decisions
        execute_trades: Whether to automatically execute trades on Moomoo
    """

    # Get the portfolio and analyst signals
    portfolio = state["data"]["portfolio"]
    analyst_signals = state["data"]["analyst_signals"]
    tickers = state["data"]["tickers"]

    # Sync with Moomoo if integration is available and enabled
    if moomoo_integration and sync_positions:
        try:
            progress.update_status(agent_id, None, "Syncing positions from Moomoo")
            moomoo_portfolio = moomoo_integration.get_portfolio_sync()
            
            if moomoo_portfolio:
                # Update portfolio with Moomoo data
                portfolio.update({
                    "cash": moomoo_portfolio.get("cash", portfolio.get("cash", 0)),
                    "total_assets": moomoo_portfolio.get("total_assets", 0),
                })
                
                # Update positions with Moomoo data
                moomoo_positions = moomoo_portfolio.get("positions", {})
                for ticker in tickers:
                    if ticker in moomoo_positions:
                        if "positions" not in portfolio:
                            portfolio["positions"] = {}
                        portfolio["positions"][ticker] = moomoo_positions[ticker]
                
                print(f"✅ Synced portfolio from Moomoo: ${moomoo_portfolio.get('total_assets', 0):,.2f} total assets")
                
        except Exception as e:
            print(f"⚠️ Failed to sync with Moomoo: {e}")
            progress.update_status(agent_id, None, "Moomoo sync failed, using local portfolio")

    # Get position limits, current prices, and signals for every ticker
    position_limits = {}
    current_prices = {}
    max_shares = {}
    signals_by_ticker = {}
    
    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Processing analyst signals")

        # Get position limits and current prices for the ticker
        # Find the corresponding risk manager for this portfolio manager
        if agent_id.startswith("portfolio_manager_"):
            suffix = agent_id.split('_')[-1]
            risk_manager_id = f"risk_management_agent_{suffix}"
        else:
            risk_manager_id = "risk_management_agent"  # Fallback for CLI
        
        risk_data = analyst_signals.get(risk_manager_id, {}).get(ticker, {})
        position_limits[ticker] = risk_data.get("remaining_position_limit", 0)
        
        # Try to get current price from Moomoo first, then fallback to risk data
        if moomoo_integration:
            try:
                moomoo_price = moomoo_integration.client.get_current_price(ticker)
                current_prices[ticker] = moomoo_price or risk_data.get("current_price", 0)
            except:
                current_prices[ticker] = risk_data.get("current_price", 0)
        else:
            current_prices[ticker] = risk_data.get("current_price", 0)

        # Calculate maximum shares allowed based on position limit and price
        if current_prices[ticker] > 0:
            max_shares[ticker] = int(position_limits[ticker] / current_prices[ticker])
        else:
            max_shares[ticker] = 0

        # Get signals for the ticker
        ticker_signals = {}
        for agent, signals in analyst_signals.items():
            # Skip all risk management agents (they have different signal structure)
            if not agent.startswith("risk_management_agent") and ticker in signals:
                ticker_signals[agent] = {"signal": signals[ticker]["signal"], "confidence": signals[ticker]["confidence"]}
        signals_by_ticker[ticker] = ticker_signals

    # Add current_prices to the state data so it's available throughout the workflow
    state["data"]["current_prices"] = current_prices

    progress.update_status(agent_id, None, "Generating trading decisions")

    # Generate the trading decision
    result = generate_trading_decision_moomoo(
        tickers=tickers,
        signals_by_ticker=signals_by_ticker,
        current_prices=current_prices,
        max_shares=max_shares,
        portfolio=portfolio,
        agent_id=agent_id,
        state=state,
    )

    # Execute trades on Moomoo if enabled
    execution_results = {}
    if moomoo_integration and execute_trades:
        try:
            progress.update_status(agent_id, None, "Executing trades on Moomoo")
            
            # Convert decisions to dictionary format
            decisions_dict = {ticker: decision.model_dump() for ticker, decision in result.decisions.items()}
            
            # Execute on Moomoo
            execution_results = moomoo_integration.execute_decisions(decisions_dict, current_prices)
            
            # Save execution log
            moomoo_integration.save_execution_log()
            
            print(f"✅ Executed {len(execution_results)} trading decisions on Moomoo")
            
        except Exception as e:
            print(f"❌ Failed to execute trades on Moomoo: {e}")
            progress.update_status(agent_id, None, "Trade execution failed")

    # Create the portfolio management message
    message_content = {
        "decisions": {ticker: decision.model_dump() for ticker, decision in result.decisions.items()},
        "moomoo_integration": {
            "enabled": moomoo_integration is not None,
            "sync_positions": sync_positions,
            "execute_trades": execute_trades,
            "execution_results": {ticker: {"success": result.success, "message": result.message} 
                                for ticker, result in execution_results.items()} if execution_results else {}
        }
    }
    
    message = HumanMessage(
        content=json.dumps(message_content),
        name=agent_id,
    )

    # Print the decision if the flag is set
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(message_content, "Portfolio Manager (Moomoo)")

    progress.update_status(agent_id, None, "Done")

    return {
        "messages": state["messages"] + [message],
        "data": state["data"],
    }


def generate_trading_decision_moomoo(
    tickers: list[str],
    signals_by_ticker: dict[str, dict],
    current_prices: dict[str, float],
    max_shares: dict[str, int],
    portfolio: dict[str, float],
    agent_id: str,
    state: AgentState,
) -> PortfolioManagerOutput:
    """Generate trading decisions with Moomoo integration context"""
    
    # Create the prompt template with Moomoo context
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a portfolio manager making final trading decisions that will be executed on the Moomoo trading platform.

              IMPORTANT: You are managing a REAL portfolio with current positions synced from Moomoo. The portfolio_positions shows:
              - "long": number of shares currently held long
              - "short": number of shares currently held short  
              - "long_cost_basis": average price paid for long shares
              - "short_cost_basis": average price received for short shares
              
              Trading Rules:
              - For long positions:
                * Only buy if you have available cash
                * Only sell if you currently hold long shares of that ticker
                * Sell quantity must be ≤ current long position shares
                * Buy quantity must be ≤ max_shares for that ticker
              
              - For short positions:
                * Only short if you have available margin (position value × margin requirement)
                * Only cover if you currently have short shares of that ticker
                * Cover quantity must be ≤ current short position shares
                * Short quantity must respect margin requirements
              
              - The max_shares values are pre-calculated to respect position limits
              - Consider both long and short opportunities based on signals
              - Maintain appropriate risk management with both long and short exposure
              - YOUR DECISIONS WILL BE AUTOMATICALLY EXECUTED ON MOOMOO - be careful and precise

              Available Actions:
              - "buy": Open or add to long position (will place BUY order on Moomoo)
              - "sell": Close or reduce long position (will place SELL order on Moomoo)
              - "short": Open or add to short position (will place SHORT order on Moomoo)
              - "cover": Close or reduce short position (will place COVER order on Moomoo)
              - "hold": Maintain current position without any changes (no order placed)

              Inputs:
              - signals_by_ticker: dictionary of ticker → analyst signals
              - max_shares: maximum shares allowed per ticker
              - portfolio_cash: current cash in portfolio (synced from Moomoo)
              - portfolio_positions: current positions (synced from Moomoo)
              - current_prices: real-time prices from Moomoo
              - margin_requirement: current margin requirement for short positions
              - total_margin_used: total margin currently in use
              """,
            ),
            (
                "human",
                """Based on the team's analysis, make your trading decisions for each ticker.
              
              REMINDER: These decisions will be AUTOMATICALLY EXECUTED on Moomoo paper trading platform.

              Here are the signals by ticker:
              {signals_by_ticker}

              Current Prices (Real-time from Moomoo):
              {current_prices}

              Maximum Shares Allowed For Purchases:
              {max_shares}

              Portfolio Cash (Synced from Moomoo): {portfolio_cash}
              Current Positions (Synced from Moomoo): {portfolio_positions}
              Current Margin Requirement: {margin_requirement}
              Total Margin Used: {total_margin_used}

              IMPORTANT DECISION RULES:
              - If you currently hold LONG shares of a ticker (long > 0), you can:
                * HOLD: Keep your current position (quantity = 0)
                * SELL: Reduce/close your long position (quantity = shares to sell)
                * BUY: Add to your long position (quantity = additional shares to buy)
                
              - If you currently hold SHORT shares of a ticker (short > 0), you can:
                * HOLD: Keep your current position (quantity = 0)
                * COVER: Reduce/close your short position (quantity = shares to cover)
                * SHORT: Add to your short position (quantity = additional shares to short)
                
              - If you currently hold NO shares of a ticker (long = 0, short = 0), you can:
                * HOLD: Stay out of the position (quantity = 0)
                * BUY: Open a new long position (quantity = shares to buy)
                * SHORT: Open a new short position (quantity = shares to short)

              Output strictly in JSON with the following structure:
              {{
                "decisions": {{
                  "TICKER1": {{
                    "action": "buy/sell/short/cover/hold",
                    "quantity": integer,
                    "confidence": float between 0 and 100,
                    "reasoning": "string explaining your decision considering current Moomoo position and real-time execution"
                  }},
                  "TICKER2": {{
                    ...
                  }},
                  ...
                }}
              }}
              """,
            ),
        ]
    )

    # Generate the prompt
    prompt_data = {
        "signals_by_ticker": json.dumps(signals_by_ticker, indent=2),
        "current_prices": json.dumps(current_prices, indent=2),
        "max_shares": json.dumps(max_shares, indent=2),
        "portfolio_cash": f"{portfolio.get('cash', 0):.2f}",
        "portfolio_positions": json.dumps(portfolio.get("positions", {}), indent=2),
        "margin_requirement": f"{portfolio.get('margin_requirement', 0):.2f}",
        "total_margin_used": f"{portfolio.get('margin_used', 0):.2f}",
    }
    
    prompt = template.invoke(prompt_data)

    # Create default factory for PortfolioManagerOutput
    def create_default_portfolio_output():
        return PortfolioManagerOutput(decisions={ticker: PortfolioDecision(action="hold", quantity=0, confidence=0.0, reasoning="Default decision: hold due to error") for ticker in tickers})

    return call_llm(
        prompt=prompt,
        pydantic_model=PortfolioManagerOutput,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_portfolio_output,
    )