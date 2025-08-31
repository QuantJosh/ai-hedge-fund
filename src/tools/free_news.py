"""
Free news data sources for AI hedge fund system.
Provides alternative news sources that don't require paid APIs.
"""

import yfinance as yf
import feedparser
import requests
import random
from datetime import datetime, timedelta
from typing import List, Optional
from src.data.models import CompanyNews
import time


class FreeNewsProvider:
    """Base class for free news providers"""
    
    def get_news(self, ticker: str, start_date: str, end_date: str, limit: int = 100) -> List[CompanyNews]:
        """Get news for a ticker within date range"""
        raise NotImplementedError


class YFinanceNewsProvider(FreeNewsProvider):
    """Yahoo Finance news provider using yfinance"""
    
    def get_news(self, ticker: str, start_date: str, end_date: str, limit: int = 100) -> List[CompanyNews]:
        """Get news from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            news_data = stock.news
            
            if not news_data:
                return []
            
            news_list = []
            for item in news_data[:limit]:
                # Convert timestamp to date string
                pub_date = datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d')
                
                # Simple sentiment analysis based on title keywords
                sentiment = self._analyze_sentiment(item.get('title', ''))
                
                news = CompanyNews(
                    ticker=ticker,
                    title=item.get('title', ''),
                    author=item.get('publisher', 'Unknown'),
                    source='Yahoo Finance',
                    date=pub_date,
                    url=item.get('link', ''),
                    sentiment=sentiment
                )
                news_list.append(news)
            
            return news_list
            
        except Exception as e:
            print(f"Error fetching Yahoo Finance news for {ticker}: {e}")
            return []
    
    def _analyze_sentiment(self, title: str) -> str:
        """Simple keyword-based sentiment analysis"""
        title_lower = title.lower()
        
        positive_words = ['up', 'rise', 'gain', 'profit', 'growth', 'strong', 'beat', 'exceed', 'positive', 'bull']
        negative_words = ['down', 'fall', 'loss', 'decline', 'weak', 'miss', 'cut', 'negative', 'bear', 'drop']
        
        positive_count = sum(1 for word in positive_words if word in title_lower)
        negative_count = sum(1 for word in negative_words if word in title_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'


class AlphaVantageNewsProvider(FreeNewsProvider):
    """Alpha Vantage news provider (free tier available)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "demo"  # Alpha Vantage provides demo key
    
    def get_news(self, ticker: str, start_date: str, end_date: str, limit: int = 100) -> List[CompanyNews]:
        """Get news from Alpha Vantage"""
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': ticker,
                'apikey': self.api_key,
                'limit': min(limit, 50)  # Alpha Vantage free tier limit
            }
            
            response = requests.get(url, params=params)
            if response.status_code != 200:
                return []
            
            data = response.json()
            feed = data.get('feed', [])
            
            news_list = []
            for item in feed:
                # Parse date
                pub_date = item.get('time_published', '')[:8]  # YYYYMMDD format
                if len(pub_date) == 8:
                    pub_date = f"{pub_date[:4]}-{pub_date[4:6]}-{pub_date[6:8]}"
                else:
                    pub_date = datetime.now().strftime('%Y-%m-%d')
                
                # Get sentiment score
                ticker_sentiments = item.get('ticker_sentiment', [])
                sentiment = 'neutral'
                for ts in ticker_sentiments:
                    if ts.get('ticker') == ticker:
                        sentiment_score = float(ts.get('sentiment_score', 0))
                        if sentiment_score > 0.1:
                            sentiment = 'positive'
                        elif sentiment_score < -0.1:
                            sentiment = 'negative'
                        break
                
                news = CompanyNews(
                    ticker=ticker,
                    title=item.get('title', ''),
                    author=item.get('authors', ['Unknown'])[0] if item.get('authors') else 'Unknown',
                    source=item.get('source', 'Alpha Vantage'),
                    date=pub_date,
                    url=item.get('url', ''),
                    sentiment=sentiment
                )
                news_list.append(news)
            
            return news_list
            
        except Exception as e:
            print(f"Error fetching Alpha Vantage news for {ticker}: {e}")
            return []


class MockNewsProvider(FreeNewsProvider):
    """Mock news provider for testing without API calls"""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.news_templates = [
            "{ticker} reports strong quarterly earnings",
            "{ticker} announces new product launch",
            "{ticker} stock price target raised by analysts",
            "{ticker} faces regulatory challenges",
            "{ticker} CEO announces strategic partnership",
            "{ticker} quarterly revenue beats expectations",
            "{ticker} stock downgraded by major bank",
            "{ticker} announces share buyback program",
            "{ticker} reports disappointing sales figures",
            "{ticker} expands into new market segment"
        ]
        
        self.sources = ['Reuters', 'Bloomberg', 'CNBC', 'MarketWatch', 'Financial Times']
        self.authors = ['John Smith', 'Jane Doe', 'Mike Johnson', 'Sarah Wilson', 'David Brown']
    
    def get_news(self, ticker: str, start_date: str, end_date: str, limit: int = 100) -> List[CompanyNews]:
        """Generate mock news data"""
        news_list = []
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Generate random news within date range
        for i in range(min(limit, 20)):  # Limit mock news to 20 items
            # Random date within range
            days_diff = (end_dt - start_dt).days
            if days_diff > 0:
                random_days = random.randint(0, days_diff)
                news_date = start_dt + timedelta(days=random_days)
            else:
                news_date = start_dt
            
            # Random news content
            title = random.choice(self.news_templates).format(ticker=ticker)
            sentiment = random.choice(['positive', 'negative', 'neutral'])
            
            news = CompanyNews(
                ticker=ticker,
                title=title,
                author=random.choice(self.authors),
                source=random.choice(self.sources),
                date=news_date.strftime('%Y-%m-%d'),
                url=f"https://example.com/news/{ticker.lower()}-{i}",
                sentiment=sentiment
            )
            news_list.append(news)
        
        return sorted(news_list, key=lambda x: x.date, reverse=True)


def get_free_news_provider(provider_name: str, **kwargs) -> FreeNewsProvider:
    """Factory function to get news provider by name"""
    providers = {
        'yfinance': YFinanceNewsProvider,
        'alpha_vantage': AlphaVantageNewsProvider,
        'mock': MockNewsProvider
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown news provider: {provider_name}")
    
    return providers[provider_name](**kwargs)


def get_company_news_free(
    ticker: str,
    end_date: str,
    start_date: str = None,
    limit: int = 100,
    provider: str = 'yfinance',
    **provider_kwargs
) -> List[CompanyNews]:
    """
    Get company news using free data sources
    
    Args:
        ticker: Stock ticker symbol
        end_date: End date (YYYY-MM-DD)
        start_date: Start date (YYYY-MM-DD), defaults to 30 days before end_date
        limit: Maximum number of news items
        provider: News provider ('yfinance', 'alpha_vantage', 'mock')
        **provider_kwargs: Additional arguments for the provider
    
    Returns:
        List of CompanyNews objects
    """
    if not start_date:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=30)
        start_date = start_dt.strftime('%Y-%m-%d')
    
    try:
        news_provider = get_free_news_provider(provider, **provider_kwargs)
        return news_provider.get_news(ticker, start_date, end_date, limit)
    except Exception as e:
        print(f"Error getting news from {provider}: {e}")
        # Fallback to mock provider
        mock_provider = MockNewsProvider()
        return mock_provider.get_news(ticker, start_date, end_date, limit)