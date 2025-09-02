"""
Moomoo Trading Platform Integration
Connects Portfolio Manager decisions with Moomoo paper trading
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import moomoo
    from moomoo import (
        OpenQuoteContext, OpenUSTradeContext, OpenHKTradeContext, OpenCNTradeContext,
        Market, TrdEnv, TrdSide, OrderType as MoomooOrderType, RET_OK
    )
except ImportError:
    print("Warning: moomoo-api package not installed. Run: pip install moomoo-api")
    moomoo = None
    OpenQuoteContext = None
    OpenUSTradeContext = None
    OpenHKTradeContext = None
    OpenCNTradeContext = None
    Market = None
    TrdEnv = None
    TrdSide = None
    MoomooOrderType = None
    RET_OK = None


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


@dataclass
class TradingDecision:
    """Trading decision from Portfolio Manager"""
    ticker: str
    action: str  # buy, sell, short, cover, hold
    quantity: int
    confidence: float
    reasoning: str
    current_price: Optional[float] = None


@dataclass
class OrderResult:
    """Result of placing an order"""
    success: bool
    order_id: Optional[str] = None
    message: str = ""
    executed_price: Optional[float] = None
    executed_quantity: Optional[int] = None
    timestamp: Optional[datetime] = None


class MoomooClient:
    """Moomoo trading client for paper trading integration"""
    
    def __init__(self, 
                 host: str = "127.0.0.1", 
                 port: int = 11111,
                 paper_trading: bool = True,
                 market: str = "US"):
        """
        Initialize Moomoo client
        
        Args:
            host: Moomoo OpenD host (default: 127.0.0.1)
            port: Moomoo OpenD port (default: 11111)
            paper_trading: Use paper trading account (default: True)
            market: Market to trade (US, HK, CN)
        """
        self.host = host
        self.port = port
        self.paper_trading = paper_trading
        self.market = market
        
        # Trading contexts
        self.quote_ctx = None
        self.trade_ctx = None
        
        # Connection status
        self.connected = False
        
        # Market mapping
        if moomoo:
            self.market_map = {
                "US": Market.US,
                "HK": Market.HK, 
                "CN": Market.SH
            }
            # Environment mapping
            self.env_type = TrdEnv.SIMULATE if paper_trading else TrdEnv.REAL
        else:
            self.market_map = {}
            self.env_type = None
        
    def connect(self) -> bool:
        """Connect to Moomoo OpenD"""
        try:
            if OpenQuoteContext is None:
                raise ImportError("moomoo-api package not installed")
            
            # Initialize quote context
            self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)
            
            # Initialize trading context (use US trading context for US market)
            if self.market == "US":
                self.trade_ctx = moomoo.OpenUSTradeContext(host=self.host, port=self.port)
            elif self.market == "HK":
                self.trade_ctx = moomoo.OpenHKTradeContext(host=self.host, port=self.port)
            else:
                self.trade_ctx = moomoo.OpenCNTradeContext(host=self.host, port=self.port)
            
            # Test connection with a simple query instead of market state
            # Market state query seems to have format issues, so we skip it
            # The connection will be tested when we actually use it
            
            # Unlock trading (for paper trading)
            if self.paper_trading:
                ret, data = self.trade_ctx.unlock_trade("123456")  # Default paper trading password
                if ret != RET_OK:
                    print(f"Warning: Failed to unlock trading: {data}")
            
            self.connected = True
            print(f"✅ Connected to Moomoo OpenD (Paper Trading: {self.paper_trading})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Moomoo: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Moomoo OpenD"""
        try:
            if self.quote_ctx:
                self.quote_ctx.close()
            if self.trade_ctx:
                self.trade_ctx.close()
            self.connected = False
            print("✅ Disconnected from Moomoo")
        except Exception as e:
            print(f"Warning: Error during disconnect: {e}")
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price for a ticker"""
        try:
            if not self.connected:
                return None
            
            # Convert ticker format (AAPL -> US.AAPL)
            full_ticker = f"{self.market}.{ticker}"
            
            ret, data = self.quote_ctx.get_market_snapshot([full_ticker])
            if ret != RET_OK:
                print(f"Failed to get price for {ticker}: {data}")
                return None
            
            if not data.empty:
                return float(data.iloc[0]['last_price'])
            
            return None
            
        except Exception as e:
            print(f"Error getting price for {ticker}: {e}")
            return None
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            if not self.connected:
                return {}
            
            ret, data = self.trade_ctx.accinfo_query(trd_env=self.env_type)
            if ret != RET_OK:
                print(f"Failed to get account info: {data}")
                return {}
            
            if not data.empty:
                account_info = data.iloc[0]
                return {
                    "total_assets": float(account_info.get('total_assets', 0)),
                    "cash": float(account_info.get('cash', 0)),
                    "market_value": float(account_info.get('market_val', 0)),
                    "unrealized_pnl": float(account_info.get('unrealized_pl', 0)),
                    "realized_pnl": float(account_info.get('realized_pl', 0)),
                    "currency": account_info.get('currency', 'USD')
                }
            
            return {}
            
        except Exception as e:
            print(f"Error getting account info: {e}")
            return {}
    
    def get_positions(self) -> Dict[str, Dict]:
        """Get current positions"""
        try:
            if not self.connected:
                return {}
            
            ret, data = self.trade_ctx.position_list_query(trd_env=self.env_type)
            if ret != RET_OK:
                print(f"Failed to get positions: {data}")
                return {}
            
            positions = {}
            if not data.empty:
                for _, row in data.iterrows():
                    ticker = row['code'].split('.')[-1]  # Extract ticker from US.AAPL
                    positions[ticker] = {
                        "quantity": int(row.get('qty', 0)),
                        "market_value": float(row.get('market_val', 0)),
                        "cost_price": float(row.get('cost_price', 0)),
                        "current_price": float(row.get('nominal_price', 0)),
                        "unrealized_pnl": float(row.get('unrealized_pl', 0)),
                        "unrealized_pnl_ratio": float(row.get('unrealized_pl_ratio', 0))
                    }
            
            return positions
            
        except Exception as e:
            print(f"Error getting positions: {e}")
            return {}
    
    def place_order(self, 
                   ticker: str, 
                   side: OrderSide, 
                   quantity: int,
                   order_type: OrderType = OrderType.MARKET,
                   price: Optional[float] = None) -> OrderResult:
        """Place a trading order"""
        try:
            if not self.connected:
                return OrderResult(
                    success=False,
                    message="Not connected to Moomoo"
                )
            
            # Convert ticker format
            full_ticker = f"{self.market}.{ticker}"
            
            # Convert order side
            trd_side = TrdSide.BUY if side == OrderSide.BUY else TrdSide.SELL
            
            # Convert order type
            if order_type == OrderType.MARKET:
                order_type_moomoo = MoomooOrderType.MARKET
                order_price = 0.0  # Market orders use 0 price
            else:
                order_type_moomoo = MoomooOrderType.NORMAL  # Limit order
                order_price = price or 0.0
            
            # Place order
            ret, data = self.trade_ctx.place_order(
                price=order_price,
                qty=quantity,
                code=full_ticker,
                trd_side=trd_side,
                order_type=order_type_moomoo,
                trd_env=self.env_type
            )
            
            if ret != RET_OK:
                return OrderResult(
                    success=False,
                    message=f"Order failed: {data}"
                )
            
            # Extract order info
            if not data.empty:
                order_info = data.iloc[0]
                return OrderResult(
                    success=True,
                    order_id=str(order_info.get('order_id', '')),
                    message="Order placed successfully",
                    timestamp=datetime.now()
                )
            
            return OrderResult(
                success=False,
                message="No order data returned"
            )
            
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"Error placing order: {e}"
            )
    
    def execute_trading_decision(self, decision: TradingDecision) -> OrderResult:
        """Execute a trading decision from Portfolio Manager"""
        try:
            # Skip hold decisions
            if decision.action.lower() == "hold":
                return OrderResult(
                    success=True,
                    message=f"Hold decision for {decision.ticker} - no action taken"
                )
            
            # Get current price if not provided
            if decision.current_price is None:
                decision.current_price = self.get_current_price(decision.ticker)
            
            # Determine order side based on action
            if decision.action.lower() in ["buy", "cover"]:
                side = OrderSide.BUY
            elif decision.action.lower() in ["sell", "short"]:
                side = OrderSide.SELL
            else:
                return OrderResult(
                    success=False,
                    message=f"Unknown action: {decision.action}"
                )
            
            # Place the order
            result = self.place_order(
                ticker=decision.ticker,
                side=side,
                quantity=decision.quantity,
                order_type=OrderType.MARKET
            )
            
            # Add decision context to result
            if result.success:
                result.message += f" | Action: {decision.action} | Confidence: {decision.confidence}%"
                result.executed_price = decision.current_price
                result.executed_quantity = decision.quantity
            
            return result
            
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"Error executing decision: {e}"
            )
    
    def sync_portfolio_positions(self) -> Dict[str, Dict]:
        """Sync and return portfolio positions in our format"""
        try:
            moomoo_positions = self.get_positions()
            account_info = self.get_account_info()
            
            # Convert to our portfolio format
            portfolio_positions = {}
            
            for ticker, pos_info in moomoo_positions.items():
                quantity = pos_info["quantity"]
                portfolio_positions[ticker] = {
                    "long": max(0, quantity),  # Positive quantity = long
                    "short": max(0, -quantity),  # Negative quantity = short
                    "long_cost_basis": pos_info["cost_price"] if quantity > 0 else 0.0,
                    "short_cost_basis": pos_info["cost_price"] if quantity < 0 else 0.0,
                    "short_margin_used": 0.0,  # Moomoo handles margin internally
                    "market_value": pos_info["market_value"],
                    "unrealized_pnl": pos_info["unrealized_pnl"]
                }
            
            return {
                "cash": account_info.get("cash", 0.0),
                "total_assets": account_info.get("total_assets", 0.0),
                "positions": portfolio_positions,
                "margin_requirement": 0.0,  # Moomoo handles this
                "margin_used": 0.0
            }
            
        except Exception as e:
            print(f"Error syncing portfolio: {e}")
            return {}


class MoomooIntegration:
    """High-level integration between Portfolio Manager and Moomoo"""
    
    def __init__(self, 
                 host: str = "127.0.0.1",
                 port: int = 11111,
                 paper_trading: bool = True,
                 auto_execute: bool = False):
        """
        Initialize Moomoo integration
        
        Args:
            host: Moomoo OpenD host
            port: Moomoo OpenD port  
            paper_trading: Use paper trading
            auto_execute: Automatically execute all decisions
        """
        self.client = MoomooClient(host, port, paper_trading)
        self.auto_execute = auto_execute
        self.execution_log = []
        
    def connect(self) -> bool:
        """Connect to Moomoo"""
        return self.client.connect()
    
    def disconnect(self):
        """Disconnect from Moomoo"""
        self.client.disconnect()
    
    def execute_decisions(self, decisions: Dict[str, Dict], 
                         current_prices: Dict[str, float] = None) -> Dict[str, OrderResult]:
        """
        Execute multiple trading decisions
        
        Args:
            decisions: Dictionary of ticker -> decision data
            current_prices: Dictionary of ticker -> current price
            
        Returns:
            Dictionary of ticker -> OrderResult
        """
        results = {}
        
        for ticker, decision_data in decisions.items():
            # Convert to TradingDecision object
            decision = TradingDecision(
                ticker=ticker,
                action=decision_data.get("action", "hold"),
                quantity=decision_data.get("quantity", 0),
                confidence=decision_data.get("confidence", 0.0),
                reasoning=decision_data.get("reasoning", ""),
                current_price=current_prices.get(ticker) if current_prices else None
            )
            
            # Execute the decision
            result = self.client.execute_trading_decision(decision)
            results[ticker] = result
            
            # Log the execution
            self.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "ticker": ticker,
                "decision": decision_data,
                "result": {
                    "success": result.success,
                    "message": result.message,
                    "order_id": result.order_id
                }
            })
            
            # Print result
            status = "✅" if result.success else "❌"
            print(f"{status} {ticker}: {decision.action} {decision.quantity} shares - {result.message}")
        
        return results
    
    def get_portfolio_sync(self) -> Dict:
        """Get synchronized portfolio data from Moomoo"""
        return self.client.sync_portfolio_positions()
    
    def save_execution_log(self, filename: str = None):
        """Save execution log to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"moomoo_execution_log_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.execution_log, f, indent=2, ensure_ascii=False)
            print(f"✅ Execution log saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save execution log: {e}")


# Convenience functions
def create_moomoo_integration(paper_trading: bool = True, 
                            auto_execute: bool = False) -> MoomooIntegration:
    """Create and connect Moomoo integration"""
    integration = MoomooIntegration(paper_trading=paper_trading, auto_execute=auto_execute)
    
    if integration.connect():
        print("🚀 Moomoo integration ready!")
        return integration
    else:
        print("❌ Failed to initialize Moomoo integration")
        return None


def execute_portfolio_decisions(decisions: Dict, 
                              current_prices: Dict = None,
                              paper_trading: bool = True) -> Dict:
    """
    Quick function to execute portfolio decisions on Moomoo
    
    Args:
        decisions: Portfolio Manager decisions
        current_prices: Current market prices
        paper_trading: Use paper trading account
        
    Returns:
        Execution results
    """
    integration = create_moomoo_integration(paper_trading=paper_trading)
    
    if integration:
        try:
            results = integration.execute_decisions(decisions, current_prices)
            integration.save_execution_log()
            return results
        finally:
            integration.disconnect()
    
    return {}