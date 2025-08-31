"""
Data source configuration manager for AI hedge fund system.
Handles enabling/disabling different data sources and mock data generation.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from src.data.models import (
    CompanyNews, FinancialMetrics, InsiderTrade, Price
)


class DataSourceConfig:
    """Configuration manager for data sources"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('data_sources', {})
        
        # Data source flags
        self.enable_news = self.config.get('enable_news', True)
        self.enable_financial_data = self.config.get('enable_financial_data', True)
        self.enable_insider_trades = self.config.get('enable_insider_trades', True)
        self.enable_price_data = self.config.get('enable_price_data', True)
        
        # News source configuration
        self.news_source = self.config.get('news_source', 'yfinance')
        
        # Mock data configuration
        self.use_mock_data = self.config.get('use_mock_data', False)
        self.mock_data_seed = self.config.get('mock_data_seed', 42)
        
        if self.use_mock_data:
            random.seed(self.mock_data_seed)
    
    def should_fetch_news(self) -> bool:
        """Check if news data should be fetched"""
        return self.enable_news and not self.use_mock_data
    
    def should_fetch_financial_data(self) -> bool:
        """Check if financial data should be fetched"""
        return self.enable_financial_data and not self.use_mock_data
    
    def should_fetch_insider_trades(self) -> bool:
        """Check if insider trades should be fetched"""
        return self.enable_insider_trades and not self.use_mock_data
    
    def should_fetch_price_data(self) -> bool:
        """Check if price data should be fetched"""
        return self.enable_price_data and not self.use_mock_data
    
    def get_news_source(self) -> str:
        """Get the configured news source"""
        return self.news_source
    
    def generate_mock_financial_metrics(self, ticker: str, periods: int = 10) -> List[FinancialMetrics]:
        """Generate mock financial metrics for testing"""
        if not self.use_mock_data:
            return []
        
        metrics_list = []
        base_date = datetime.now()
        
        for i in range(periods):
            # Generate realistic but random financial metrics
            report_date = (base_date - timedelta(days=90 * i)).strftime('%Y-%m-%d')
            
            metrics = FinancialMetrics(
                ticker=ticker,
                report_period=report_date,
                period='ttm',
                currency='USD',
                market_cap=random.uniform(50e9, 500e9),  # 50B to 500B
                enterprise_value=random.uniform(45e9, 480e9),
                price_to_earnings_ratio=random.uniform(15, 35),
                price_to_book_ratio=random.uniform(1.5, 8.0),
                price_to_sales_ratio=random.uniform(2, 12),
                enterprise_value_to_ebitda_ratio=random.uniform(8, 25),
                enterprise_value_to_revenue_ratio=random.uniform(2, 15),
                free_cash_flow_yield=random.uniform(0.02, 0.08),
                peg_ratio=random.uniform(0.5, 2.5),
                gross_margin=random.uniform(0.25, 0.65),
                operating_margin=random.uniform(0.10, 0.35),
                net_margin=random.uniform(0.05, 0.25),
                return_on_equity=random.uniform(0.08, 0.25),
                return_on_assets=random.uniform(0.04, 0.15),
                return_on_invested_capital=random.uniform(0.06, 0.20),
                asset_turnover=random.uniform(0.5, 2.0),
                inventory_turnover=random.uniform(4, 12),
                receivables_turnover=random.uniform(6, 15),
                days_sales_outstanding=random.uniform(20, 60),
                operating_cycle=random.uniform(40, 120),
                working_capital_turnover=random.uniform(3, 10),
                current_ratio=random.uniform(1.0, 3.0),
                quick_ratio=random.uniform(0.8, 2.5),
                cash_ratio=random.uniform(0.1, 1.0),
                operating_cash_flow_ratio=random.uniform(0.15, 0.40),
                debt_to_equity=random.uniform(0.2, 2.0),
                debt_to_assets=random.uniform(0.1, 0.6),
                interest_coverage=random.uniform(3, 20),
                revenue_growth=random.uniform(-0.1, 0.3),
                earnings_growth=random.uniform(-0.2, 0.4),
                book_value_growth=random.uniform(-0.05, 0.2),
                earnings_per_share_growth=random.uniform(-0.2, 0.4),
                free_cash_flow_growth=random.uniform(-0.15, 0.35),
                operating_income_growth=random.uniform(-0.1, 0.3),
                ebitda_growth=random.uniform(-0.1, 0.3),
                payout_ratio=random.uniform(0.0, 0.6),
                earnings_per_share=random.uniform(2, 15),
                book_value_per_share=random.uniform(20, 100),
                free_cash_flow_per_share=random.uniform(3, 20)
            )
            metrics_list.append(metrics)
        
        return metrics_list
    
    def generate_mock_insider_trades(self, ticker: str, count: int = 50) -> List[InsiderTrade]:
        """Generate mock insider trades for testing"""
        if not self.use_mock_data:
            return []
        
        trades_list = []
        base_date = datetime.now()
        
        names = ['John Smith', 'Jane Doe', 'Mike Johnson', 'Sarah Wilson', 'David Brown']
        titles = ['CEO', 'CFO', 'Director', 'VP Sales', 'VP Engineering']
        
        for i in range(count):
            trade_date = (base_date - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d')
            filing_date = (datetime.strptime(trade_date, '%Y-%m-%d') + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d')
            
            # Generate buy or sell transaction
            is_buy = random.choice([True, False])
            shares = random.randint(100, 10000) * (1 if is_buy else -1)
            price = random.uniform(50, 300)
            
            trade = InsiderTrade(
                ticker=ticker,
                issuer=f"{ticker} Inc.",
                name=random.choice(names),
                title=random.choice(titles),
                is_board_director=random.choice([True, False]),
                transaction_date=trade_date,
                transaction_shares=shares,
                transaction_price_per_share=price,
                transaction_value=abs(shares) * price,
                shares_owned_before_transaction=random.randint(1000, 50000),
                shares_owned_after_transaction=random.randint(1000, 50000),
                security_title='Common Stock',
                filing_date=filing_date
            )
            trades_list.append(trade)
        
        return sorted(trades_list, key=lambda x: x.filing_date, reverse=True)
    
    def generate_mock_prices(self, ticker: str, start_date: str, end_date: str) -> List[Price]:
        """Generate mock price data for testing"""
        if not self.use_mock_data:
            return []
        
        prices_list = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Starting price
        current_price = random.uniform(100, 300)
        
        while current_date <= end_dt:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
                # Generate realistic price movement
                daily_change = random.uniform(-0.05, 0.05)  # -5% to +5% daily change
                current_price *= (1 + daily_change)
                
                # Generate OHLC data
                high = current_price * random.uniform(1.0, 1.03)
                low = current_price * random.uniform(0.97, 1.0)
                open_price = current_price * random.uniform(0.98, 1.02)
                close_price = current_price
                volume = random.randint(1000000, 50000000)
                
                price = Price(
                    open=round(open_price, 2),
                    close=round(close_price, 2),
                    high=round(high, 2),
                    low=round(low, 2),
                    volume=volume,
                    time=current_date.strftime('%Y-%m-%d')
                )
                prices_list.append(price)
            
            current_date += timedelta(days=1)
        
        return prices_list
    
    def generate_mock_news(self, ticker: str, start_date: str, end_date: str, limit: int = 100) -> List[CompanyNews]:
        """Generate mock news data for testing"""
        if not self.use_mock_data:
            return []
        
        from src.tools.free_news import MockNewsProvider
        mock_provider = MockNewsProvider(seed=self.mock_data_seed)
        return mock_provider.get_news(ticker, start_date, end_date, limit)


def get_data_config(config: Dict[str, Any]) -> DataSourceConfig:
    """Factory function to create data source configuration"""
    return DataSourceConfig(config)