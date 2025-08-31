"""
Moomoo Trading Executor
Executes Portfolio Manager decisions on Moomoo platform
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class ExecutionResult:
    """Result of trade execution"""
    ticker: str
    action: str
    quantity: int
    success: bool
    message: str
    order_id: Optional[str] = None
    executed_price: Optional[float] = None
    executed_quantity: Optional[int] = None
    timestamp: Optional[datetime] = None
    confidence: Optional[float] = None


class MoomooExecutor:
    """Executes trading decisions on Moomoo platform"""
    
    def __init__(self, client):
        """
        Initialize executor
        
        Args:
            client: MoomooClient instance
        """
        self.client = client
        self.execution_log = []
    
    def execute_decisions(self, 
                         decisions: Dict[str, Dict], 
                         current_prices: Optional[Dict[str, float]] = None) -> Dict[str, ExecutionResult]:
        """
        Execute multiple trading decisions
        
        Args:
            decisions: Dictionary of ticker -> decision data
            current_prices: Dictionary of ticker -> current price (optional)
            
        Returns:
            Dictionary of ticker -> ExecutionResult
        """
        results = {}
        
        print(f"\n🚀 Executing {len(decisions)} trading decisions...")
        print("-" * 50)
        
        for ticker, decision_data in decisions.items():
            result = self._execute_single_decision(ticker, decision_data, current_prices)
            results[ticker] = result
            
            # Log the execution
            self._log_execution(result)
            
            # Print result
            self._print_execution_result(result)
            
            # Small delay between orders
            time.sleep(0.5)
        
        print("-" * 50)
        print(f"✅ Execution completed: {sum(1 for r in results.values() if r.success)}/{len(results)} successful")
        
        return results
    
    def _execute_single_decision(self, 
                                ticker: str, 
                                decision_data: Dict, 
                                current_prices: Optional[Dict[str, float]] = None) -> ExecutionResult:
        """Execute a single trading decision"""
        
        action = decision_data.get("action", "hold").lower()
        quantity = decision_data.get("quantity", 0)
        confidence = decision_data.get("confidence", 0.0)
        reasoning = decision_data.get("reasoning", "")
        
        # Skip hold decisions
        if action == "hold" or quantity == 0:
            return ExecutionResult(
                ticker=ticker,
                action=action,
                quantity=quantity,
                success=True,
                message="Hold decision - no action taken",
                timestamp=datetime.now(),
                confidence=confidence
            )
        
        # Get current price
        current_price = None
        if current_prices and ticker in current_prices:
            current_price = current_prices[ticker]
        else:
            current_price = self.client.get_current_price(ticker)
        
        # Determine order side
        if action in ["buy", "cover"]:
            side = "BUY"
        elif action in ["sell", "short"]:
            side = "SELL"
        else:
            return ExecutionResult(
                ticker=ticker,
                action=action,
                quantity=quantity,
                success=False,
                message=f"Unknown action: {action}",
                timestamp=datetime.now(),
                confidence=confidence
            )
        
        # Validate order
        validation_result = self._validate_order(ticker, side, quantity, current_price)
        if not validation_result[0]:
            return ExecutionResult(
                ticker=ticker,
                action=action,
                quantity=quantity,
                success=False,
                message=validation_result[1],
                timestamp=datetime.now(),
                confidence=confidence
            )
        
        # Place the order
        success, message, order_id = self.client.place_order(
            ticker=ticker,
            side=side,
            quantity=quantity,
            order_type="MARKET"
        )
        
        result = ExecutionResult(
            ticker=ticker,
            action=action,
            quantity=quantity,
            success=success,
            message=message,
            order_id=order_id,
            executed_price=current_price,
            executed_quantity=quantity if success else 0,
            timestamp=datetime.now(),
            confidence=confidence
        )
        
        # For successful orders, try to get execution details
        if success and order_id:
            time.sleep(1)  # Wait a moment for order processing
            order_status = self.client.get_order_status(order_id)
            if order_status:
                result.executed_quantity = order_status.get('filled_qty', quantity)
                if order_status.get('avg_price', 0) > 0:
                    result.executed_price = order_status['avg_price']
        
        return result
    
    def _validate_order(self, ticker: str, side: str, quantity: int, price: Optional[float]) -> tuple[bool, str]:
        """Validate order parameters"""
        
        # Basic validation
        if quantity <= 0:
            return False, "Quantity must be positive"
        
        if price is None or price <= 0:
            return False, f"Invalid price for {ticker}: {price}"
        
        # Check market state
        market_state = self.client.get_market_state()
        if market_state and market_state not in ['TRADING', 'PRE_MARKET_TRADING', 'AFTER_HOURS_TRADING']:
            return False, f"Market is not open: {market_state}"
        
        # Get account info for validation
        account_info = self.client.get_account_info()
        if not account_info:
            return False, "Cannot get account information"
        
        # For buy orders, check available cash
        if side == "BUY":
            required_cash = quantity * price
            if account_info.cash < required_cash:
                return False, f"Insufficient cash: need ${required_cash:.2f}, have ${account_info.cash:.2f}"
        
        # For sell orders, check position
        elif side == "SELL":
            positions = self.client.get_positions()
            if ticker not in positions:
                return False, f"No position in {ticker} to sell"
            
            current_position = positions[ticker].quantity
            if current_position < quantity:
                return False, f"Insufficient shares: trying to sell {quantity}, have {current_position}"
        
        return True, "Order validation passed"
    
    def _log_execution(self, result: ExecutionResult):
        """Log execution result"""
        log_entry = {
            "timestamp": result.timestamp.isoformat() if result.timestamp else None,
            "ticker": result.ticker,
            "action": result.action,
            "quantity": result.quantity,
            "success": result.success,
            "message": result.message,
            "order_id": result.order_id,
            "executed_price": result.executed_price,
            "executed_quantity": result.executed_quantity,
            "confidence": result.confidence
        }
        
        self.execution_log.append(log_entry)
    
    def _print_execution_result(self, result: ExecutionResult):
        """Print execution result to console"""
        status = "✅" if result.success else "❌"
        
        if result.action == "hold":
            print(f"{status} {result.ticker}: HOLD - {result.message}")
        else:
            price_info = f" @ ${result.executed_price:.2f}" if result.executed_price else ""
            confidence_info = f" (confidence: {result.confidence:.1f}%)" if result.confidence else ""
            
            print(f"{status} {result.ticker}: {result.action.upper()} {result.quantity} shares{price_info}{confidence_info}")
            
            if not result.success:
                print(f"   Error: {result.message}")
            elif result.order_id:
                print(f"   Order ID: {result.order_id}")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of all executions"""
        if not self.execution_log:
            return {"total": 0, "successful": 0, "failed": 0, "executions": []}
        
        successful = sum(1 for log in self.execution_log if log["success"])
        failed = len(self.execution_log) - successful
        
        return {
            "total": len(self.execution_log),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(self.execution_log) if self.execution_log else 0,
            "executions": self.execution_log
        }
    
    def save_execution_log(self, filename: Optional[str] = None):
        """Save execution log to file"""
        if not self.execution_log:
            print("No executions to save")
            return False
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"moomoo_execution_log_{timestamp}.json"
        
        try:
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "summary": self.get_execution_summary(),
                    "executions": self.execution_log
                }, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Execution log saved to: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save execution log: {e}")
            return False
    
    def clear_log(self):
        """Clear execution log"""
        self.execution_log.clear()
        print("Execution log cleared")