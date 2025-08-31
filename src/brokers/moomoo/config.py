"""
Moomoo Configuration Management
Handles loading and validation of Moomoo trading configuration
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Optional


class MoomooConfig:
    """Moomoo configuration manager"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        self._validate_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        # Look for config in current directory first
        current_dir = Path.cwd()
        config_file = current_dir / "src" / "brokers" / "moomoo" / "trading_keys.yaml"
        
        if config_file.exists():
            return str(config_file)
        
        # Fallback to package directory
        package_dir = Path(__file__).parent
        return str(package_dir / "trading_keys.yaml")
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return config.get('moomoo', {})
            else:
                print(f"Config file not found: {self.config_path}")
                return self._get_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'host': '127.0.0.1',
            'port': 11111,
            'trade_password': '123456',
            'market': 'US',
            'paper_trading': True,
            'timeout': 30,
            'retry_count': 3
        }
    
    def _validate_config(self):
        """Validate configuration parameters"""
        required_fields = ['host', 'port', 'trade_password', 'market']
        
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required config field: {field}")
        
        # Validate port
        if not isinstance(self.config['port'], int) or self.config['port'] <= 0:
            raise ValueError("Port must be a positive integer")
        
        # Validate market
        valid_markets = ['US', 'HK', 'CN']
        if self.config['market'] not in valid_markets:
            raise ValueError(f"Market must be one of: {valid_markets}")
    
    @property
    def host(self) -> str:
        """Get host address"""
        return self.config['host']
    
    @property
    def port(self) -> int:
        """Get port number"""
        return self.config['port']
    
    @property
    def trade_password(self) -> str:
        """Get trading password"""
        return self.config['trade_password']
    
    @property
    def market(self) -> str:
        """Get market"""
        return self.config['market']
    
    @property
    def paper_trading(self) -> bool:
        """Get paper trading flag"""
        return self.config.get('paper_trading', True)
    
    @property
    def timeout(self) -> int:
        """Get connection timeout"""
        return self.config.get('timeout', 30)
    
    @property
    def retry_count(self) -> int:
        """Get retry count"""
        return self.config.get('retry_count', 3)
    
    def get_market_enum(self):
        """Get market enum for moomoo API"""
        try:
            import moomoo
            market_map = {
                'US': moomoo.Market.US,
                'HK': moomoo.Market.HK,
                'CN': moomoo.Market.SH
            }
            return market_map.get(self.market, moomoo.Market.US)
        except ImportError:
            return None
    
    def get_trd_env(self):
        """Get trading environment enum"""
        try:
            import moomoo
            return moomoo.TrdEnv.SIMULATE if self.paper_trading else moomoo.TrdEnv.REAL
        except ImportError:
            return None
    
    def save_config(self, config_path: Optional[str] = None):
        """Save current configuration to file"""
        save_path = config_path or self.config_path
        
        config_data = {'moomoo': self.config}
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            print(f"Configuration saved to: {save_path}")
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def create_example_config(self, config_path: Optional[str] = None):
        """Create example configuration file"""
        example_config = {
            'moomoo': {
                'host': '127.0.0.1',
                'port': 11111,
                'trade_password': '123456',  # Default paper trading password
                'market': 'US',  # US, HK, CN
                'paper_trading': True,  # Use paper trading account
                'timeout': 30,  # Connection timeout in seconds
                'retry_count': 3,  # Number of retry attempts
                
                # Optional settings
                'max_position_size': 0.2,  # Maximum 20% per position
                'order_timeout': 60,  # Order timeout in seconds
                'price_tolerance': 0.01,  # Price tolerance for market orders
            }
        }
        
        save_path = config_path or (Path(__file__).parent / "trading_keys.example.yaml")
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(example_config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            print(f"Example configuration created: {save_path}")
            return True
        except Exception as e:
            print(f"Error creating example config: {e}")
            return False