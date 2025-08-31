"""
Moomoo API Client
Handles low-level communication with Moomoo OpenD
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

try:
    import moomoo
except ImportError:
    try:
        # Try alternative import name
        import moomoo_api as moomoo
    except ImportError:
        print("Warning: moomoo-api package not installed. Run: pip install moomoo-api")
        moomoo = None


@dataclass
class AccountInfo:
    """Account information structure"""
    cash: float
    total_assets: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    currency: str


@dataclass
class Position:
    """Position information structure"""
    ticker: str
    quantity: int
    market_value: float
    cost_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_ratio: float


class MoomooClient:
    """Moomoo API client for trading operations"""
    
    def __init__(self, config):
        """
        Initialize Moomoo client
        
        Args:
            config: MoomooConfig instance
        """
        self.config = config
        self.quote_ctx = None
        self.trade_ctx = None
        self.connected = False
        
        if moomoo is None:
            raise ImportError("moomoo-api package is required")
    
    def connect(self) -> bool:
        """Connect to Moomoo OpenD"""
        import signal
        
        def signal_handler(signum, frame):
            print("\n⚠️ Interrupted by user. Cleaning up...")
            self.disconnect()
            raise KeyboardInterrupt("Connection interrupted by user")
        
        # Set up signal handler for Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            print(f"Connecting to Moomoo OpenD at {self.config.host}:{self.config.port}...")
            print("Press Ctrl+C to cancel connection...")
            
            # Initialize quote context with timeout
            self.quote_ctx = moomoo.OpenQuoteContext(
                host=self.config.host, 
                port=self.config.port
            )
            
            # Initialize trading context
            self.trade_ctx = moomoo.OpenUSTradeContext(
                host=self.config.host, 
                port=self.config.port
            )
            
            # Test quote connection with a simple call
            try:
                ret, data = self.quote_ctx.get_market_state(self.config.get_market_enum())
                if ret != moomoo.RET_OK:
                    print(f"Warning: Market state query failed: {data}")
                    # Continue anyway, connection is established
            except Exception as e:
                print(f"Warning: Market state test failed: {e}")
                # Continue anyway, connection is established
            
            # Unlock trading
            try:
                ret, data = self.trade_ctx.unlock_trade(password=self.config.trade_password)
                if ret != moomoo.RET_OK:
                    print(f"Warning: Trading unlock failed: {data}")
                    # Continue anyway for quote-only operations
                else:
                    print("✅ Trading unlocked successfully")
            except Exception as e:
                print(f"Warning: Trading unlock error: {e}")
            
            self.connected = True
            print("✅ Connected to Moomoo OpenD successfully")
            return True
            
        except KeyboardInterrupt:
            print("\n❌ Connection cancelled by user")
            self.connected = False
            return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False
            return False
        finally:
            # Restore default signal handler
            signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    def disconnect(self):
        """Disconnect from Moomoo OpenD"""
        try:
            if self.quote_ctx:
                self.quote_ctx.close()
                self.quote_ctx = None
            
            if self.trade_ctx:
                self.trade_ctx.close()
                self.trade_ctx = None
            
            self.connected = False
            print("✅ Disconnected from Moomoo OpenD")
            
        except Exception as e:
            print(f"Warning: Error during disconnect: {e}")
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price for a ticker"""
        try:
            if not self.connected or not self.quote_ctx:
                return None
            
            # Convert ticker format (AAPL -> US.AAPL)
            full_ticker = f"{self.config.market}.{ticker}"
            
            ret, data = self.quote_ctx.get_market_snapshot([full_ticker])
            if ret != moomoo.RET_OK:
                print(f"Failed to get price for {ticker}: {data}")
                return None
            
            if not data.empty:
                return float(data.iloc[0]['last_price'])
            
            return None
            
        except Exception as e:
            print(f"Error getting price for {ticker}: {e}")
            return None
    
    def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        try:
            if not self.connected or not self.trade_ctx:
                return None
            
            ret, data = self.trade_ctx.accinfo_query(trd_env=self.config.get_trd_env())
            if ret != moomoo.RET_OK:
                print(f"Failed to get account info: {data}")
                return None
            
            if not data.empty:
                account_data = data.iloc[0]
                
                def safe_float(value, default=0.0):
                    """Safely convert value to float, handling 'N/A' and other non-numeric values"""
                    if value is None or value == 'N/A' or value == '':
                        return default
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                return AccountInfo(
                    cash=safe_float(account_data.get('cash', 0)),
                    total_assets=safe_float(account_data.get('total_assets', 0)),
                    market_value=safe_float(account_data.get('market_val', 0)),
                    unrealized_pnl=safe_float(account_data.get('unrealized_pl', 0)),
                    realized_pnl=safe_float(account_data.get('realized_pl', 0)),
                    currency=account_data.get('currency', 'USD')
                )
            
            return None
            
        except Exception as e:
            print(f"Error getting account info: {e}")
            return None
    
    def get_positions(self) -> Dict[str, Position]:
        """Get current positions"""
        try:
            if not self.connected or not self.trade_ctx:
                return {}
            
            ret, data = self.trade_ctx.position_list_query(trd_env=self.config.get_trd_env())
            if ret != moomoo.RET_OK:
                print(f"Failed to get positions: {data}")
                return {}
            
            positions = {}
            if not data.empty:
                for _, row in data.iterrows():
                    # Extract ticker from full code (US.AAPL -> AAPL)
                    full_code = row['code']
                    ticker = full_code.split('.')[-1] if '.' in full_code else full_code
                    
                    positions[ticker] = Position(
                        ticker=ticker,
                        quantity=int(row.get('qty', 0)),
                        market_value=float(row.get('market_val', 0)),
                        cost_price=float(row.get('cost_price', 0)),
                        current_price=float(row.get('nominal_price', 0)),
                        unrealized_pnl=float(row.get('unrealized_pl', 0)),
                        unrealized_pnl_ratio=float(row.get('unrealized_pl_ratio', 0))
                    )
            
            return positions
            
        except Exception as e:
            print(f"Error getting positions: {e}")
            return {}
    
    def place_order(self, 
                   ticker: str, 
                   side: str,  # 'BUY' or 'SELL'
                   quantity: int,
                   order_type: str = 'MARKET',
                   price: Optional[float] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Place a trading order
        
        Args:
            ticker: Stock ticker symbol
            side: 'BUY' or 'SELL'
            quantity: Number of shares
            order_type: 'MARKET' or 'LIMIT'
            price: Price for limit orders
            
        Returns:
            Tuple of (success, message, order_id)
        """
        try:
            if not self.connected or not self.trade_ctx:
                return False, "Not connected to Moomoo", None
            
            # Convert ticker format
            full_ticker = f"{self.config.market}.{ticker}"
            
            # Convert order parameters
            trd_side = moomoo.TrdSide.BUY if side.upper() == 'BUY' else moomoo.TrdSide.SELL
            
            if order_type.upper() == 'MARKET':
                order_type_moomoo = moomoo.OrderType.MARKET
                order_price = 0.0  # Market orders use 0 price
            else:
                order_type_moomoo = moomoo.OrderType.NORMAL  # Limit order
                order_price = price or 0.0
            
            # Place order
            ret, data = self.trade_ctx.place_order(
                price=order_price,
                qty=quantity,
                code=full_ticker,
                trd_side=trd_side,
                order_type=order_type_moomoo,
                trd_env=self.config.get_trd_env()
            )
            
            if ret != moomoo.RET_OK:
                return False, f"Order failed: {data}", None
            
            # Extract order info
            if not data.empty:
                order_info = data.iloc[0]
                order_id = str(order_info.get('order_id', ''))
                return True, "Order placed successfully", order_id
            
            return False, "No order data returned", None
            
        except Exception as e:
            return False, f"Error placing order: {e}", None
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get order status by order ID"""
        try:
            if not self.connected or not self.trade_ctx:
                return None
            
            ret, data = self.trade_ctx.order_list_query(
                trd_env=self.config.get_trd_env()
            )
            
            if ret != moomoo.RET_OK:
                return None
            
            if not data.empty:
                # Find order by ID
                order_row = data[data['order_id'] == order_id]
                if not order_row.empty:
                    order_info = order_row.iloc[0]
                    return {
                        'order_id': order_info.get('order_id'),
                        'status': order_info.get('order_status'),
                        'filled_qty': int(order_info.get('dealt_qty', 0)),
                        'avg_price': float(order_info.get('dealt_avg_price', 0)),
                        'create_time': order_info.get('create_time'),
                        'update_time': order_info.get('updated_time')
                    }
            
            return None
            
        except Exception as e:
            print(f"Error getting order status: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> Tuple[bool, str]:
        """Cancel an order"""
        try:
            if not self.connected or not self.trade_ctx:
                return False, "Not connected to Moomoo"
            
            ret, data = self.trade_ctx.modify_order(
                modify_order_op=moomoo.ModifyOrderOp.CANCEL,
                order_id=order_id,
                trd_env=self.config.get_trd_env()
            )
            
            if ret != moomoo.RET_OK:
                return False, f"Cancel failed: {data}"
            
            return True, "Order cancelled successfully"
            
        except Exception as e:
            return False, f"Error cancelling order: {e}"
    
    def get_market_state(self) -> Optional[str]:
        """Get current market state"""
        try:
            if not self.connected or not self.quote_ctx:
                return None
            
            ret, data = self.quote_ctx.get_market_state(self.config.get_market_enum())
            if ret != moomoo.RET_OK:
                return None
            
            if not data.empty:
                return data.iloc[0]['market_state']
            
            return None
            
        except Exception as e:
            print(f"Error getting market state: {e}")
            return None