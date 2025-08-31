"""
Moomoo Trading Integration
Provides unified interface for Moomoo trading operations
"""

from .client import MoomooClient
from .executor import MoomooExecutor
from .config import MoomooConfig

class MoomooTrading:
    """Main interface for Moomoo trading operations"""
    
    def __init__(self, config_path=None):
        """Initialize Moomoo trading interface"""
        self.config = MoomooConfig(config_path)
        self.client = MoomooClient(self.config)
        self.executor = MoomooExecutor(self.client)
        self.connected = False
    
    def connect(self):
        """Connect to Moomoo OpenD"""
        try:
            self.connected = self.client.connect()
            return self.connected
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Moomoo OpenD"""
        if self.connected:
            self.client.disconnect()
            self.connected = False
    
    def get_account_info(self):
        """Get account information"""
        if not self.connected:
            return None
        return self.client.get_account_info()
    
    def get_positions(self):
        """Get current positions"""
        if not self.connected:
            return {}
        return self.client.get_positions()
    
    def get_current_price(self, ticker):
        """Get current price for a ticker"""
        if not self.connected:
            return None
        return self.client.get_current_price(ticker)
    
    def execute_decisions(self, decisions, current_prices=None):
        """Execute trading decisions"""
        if not self.connected:
            return {}
        return self.executor.execute_decisions(decisions, current_prices)
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Convenience function
def create_moomoo_trading(config_path=None):
    """Create and return MoomooTrading instance"""
    return MoomooTrading(config_path)