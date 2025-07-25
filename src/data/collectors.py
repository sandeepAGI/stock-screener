"""
Data collectors for Yahoo Finance and Reddit APIs
"""

import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import time
from dataclasses import dataclass
import praw

from src.utils.helpers import load_config, get_reddit_credentials, safe_divide

logger = logging.getLogger(__name__)

@dataclass
class StockData:
    """Container for all stock data"""
    symbol: str
    price_data: pd.DataFrame
    fundamental_data: Dict[str, Any]
    news_headlines: List[Dict[str, str]]
    
@dataclass
class SentimentData:
    """Container for sentiment analysis data"""
    symbol: str
    date: datetime
    news_sentiment: float
    reddit_sentiment: float
    combined_sentiment: float
    confidence: float
    source_count: int

class YahooFinanceCollector:
    """
    Collector for Yahoo Finance data including price, fundamentals, and news
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rate_limit = config.get('data_sources', {}).get('yahoo_finance', {}).get('rate_limit_per_hour', 2000)
        self.timeout = config.get('data_sources', {}).get('yahoo_finance', {}).get('timeout', 30)
        self.request_count = 0
        self.last_reset = datetime.now()
        
    def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = datetime.now()
        if (now - self.last_reset).seconds >= 3600:  # Reset every hour
            self.request_count = 0
            self.last_reset = now
            
        if self.request_count >= self.rate_limit:
            sleep_time = 3600 - (now - self.last_reset).seconds
            logger.warning(f"Rate limit reached. Sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
            self.request_count = 0
            self.last_reset = datetime.now()
            
    def collect_stock_data(self, symbol: str, period: str = "1y") -> Optional[StockData]:
        """
        Collect comprehensive stock data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            period: Data period ('1y', '2y', '5y', etc.)
            
        Returns:
            StockData object or None if collection fails
        """
        try:
            self._check_rate_limit()
            logger.info(f"Collecting data for {symbol}")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            self.request_count += 1
            
            # Get price data
            price_data = ticker.history(period=period)
            if price_data.empty:
                logger.warning(f"No price data found for {symbol}")
                return None
                
            # Get fundamental data
            fundamental_data = self._extract_fundamentals(ticker)
            
            # Get news headlines
            news_headlines = self._get_news_headlines(ticker, symbol)
            
            return StockData(
                symbol=symbol,
                price_data=price_data,
                fundamental_data=fundamental_data,
                news_headlines=news_headlines
            )
            
        except Exception as e:
            logger.error(f"Error collecting data for {symbol}: {str(e)}")
            return None
            
    def _extract_fundamentals(self, ticker: yf.Ticker) -> Dict[str, Any]:
        """Extract fundamental data from ticker info"""
        try:
            info = ticker.info
            
            # Key fundamental metrics for our calculations
            fundamentals = {
                # Basic info
                'company_name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap'),
                
                # Price metrics
                'current_price': info.get('currentPrice'),
                'previous_close': info.get('previousClose'),
                
                # Valuation metrics (40% weight)
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'price_to_book': info.get('priceToBook'),
                'enterprise_value': info.get('enterpriseValue'),
                'ev_to_ebitda': info.get('enterpriseToEbitda'),
                
                # Quality metrics (25% weight)
                'return_on_equity': info.get('returnOnEquity'),
                'return_on_assets': info.get('returnOnAssets'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                
                # Growth metrics (20% weight)
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                'revenue_per_share': info.get('revenuePerShare'),
                'eps_trailing_12m': info.get('trailingEps'),
                'eps_forward': info.get('forwardEps'),
                
                # Financial statement items
                'total_revenue': info.get('totalRevenue'),
                'total_cash': info.get('totalCash'),
                'total_debt': info.get('totalDebt'),
                'free_cash_flow': info.get('freeCashflow'),
                'operating_cash_flow': info.get('operatingCashflow'),
                'shares_outstanding': info.get('sharesOutstanding'),
                
                # Additional metrics
                'dividend_yield': info.get('dividendYield'),
                'payout_ratio': info.get('payoutRatio'),
                'beta': info.get('beta'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                
                # Collection metadata
                'data_date': datetime.now().isoformat(),
                'data_source': 'yahoo_finance'
            }
            
            return fundamentals
            
        except Exception as e:
            logger.error(f"Error extracting fundamentals: {str(e)}")
            return {}
            
    def _get_news_headlines(self, ticker: yf.Ticker, symbol: str, max_headlines: int = 20) -> List[Dict[str, str]]:
        """Get recent news headlines for sentiment analysis"""
        try:
            news = ticker.news
            headlines = []
            
            for article in news[:max_headlines]:
                # Yahoo Finance news has nested structure: article['content'] contains the data
                content = article.get('content', {})
                
                # Extract URL from nested clickThroughUrl structure
                click_through = content.get('clickThroughUrl', {})
                if isinstance(click_through, dict):
                    link = click_through.get('url', '')
                else:
                    link = content.get('canonicalUrl', '')
                
                # Extract provider information
                provider = content.get('provider', {})
                if isinstance(provider, dict):
                    publisher = provider.get('displayName', provider.get('name', ''))
                else:
                    publisher = str(provider) if provider else ''
                
                headlines.append({
                    'title': content.get('title', ''),
                    'summary': content.get('summary', ''),
                    'link': link,
                    'publish_time': content.get('pubDate', ''),
                    'publisher': publisher,
                    'symbol': symbol,
                    'content_type': content.get('contentType', ''),
                    'display_time': content.get('displayTime', '')
                })
                
            logger.info(f"Collected {len(headlines)} news headlines for {symbol}")
            return headlines
            
        except Exception as e:
            logger.error(f"Error getting news for {symbol}: {str(e)}")
            return []

class RedditCollector:
    """
    Collector for Reddit sentiment data
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.subreddits = config.get('data_sources', {}).get('reddit', {}).get('subreddits', ['investing', 'stocks'])
        self.rate_limit = config.get('data_sources', {}).get('reddit', {}).get('rate_limit_per_minute', 60)
        
        # Initialize Reddit API
        try:
            creds = get_reddit_credentials()
            self.reddit = praw.Reddit(
                client_id=creds['client_id'],
                client_secret=creds['client_secret'],
                user_agent=creds['user_agent']
            )
            logger.info("Reddit API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit API: {str(e)}")
            self.reddit = None
            
    def collect_stock_mentions(self, symbol: str, days_back: int = 7, max_posts: int = 100) -> List[Dict[str, Any]]:
        """
        Collect Reddit posts mentioning the stock symbol
        
        Args:
            symbol: Stock symbol to search for
            days_back: Number of days to look back
            max_posts: Maximum number of posts to collect
            
        Returns:
            List of post data dictionaries
        """
        if not self.reddit:
            logger.warning("Reddit API not available")
            return []
            
        try:
            posts = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Search terms for the symbol
            search_terms = [symbol, f"${symbol}", symbol.lower()]
            
            for subreddit_name in self.subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Search recent posts
                    for post in subreddit.search(f"{symbol} OR ${symbol}", 
                                               time_filter="week", 
                                               sort="new", 
                                               limit=max_posts // len(self.subreddits)):
                        
                        post_date = datetime.fromtimestamp(post.created_utc)
                        if post_date < cutoff_date:
                            continue
                            
                        # Check if symbol is actually mentioned in title or body
                        text_content = f"{post.title} {post.selftext}".upper()
                        if any(term.upper() in text_content for term in search_terms):
                            posts.append({
                                'id': post.id,
                                'title': post.title,
                                'text': post.selftext,
                                'score': post.score,
                                'upvote_ratio': post.upvote_ratio,
                                'num_comments': post.num_comments,
                                'created_utc': post.created_utc,
                                'subreddit': subreddit_name,
                                'url': post.url,
                                'symbol': symbol
                            })
                            
                except Exception as e:
                    logger.error(f"Error searching subreddit {subreddit_name}: {str(e)}")
                    continue
                    
            logger.info(f"Collected {len(posts)} Reddit posts for {symbol}")
            return posts
            
        except Exception as e:
            logger.error(f"Error collecting Reddit data for {symbol}: {str(e)}")
            return []

class DataCollectionOrchestrator:
    """
    Orchestrates data collection from multiple sources
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        self.yahoo_collector = YahooFinanceCollector(self.config)
        self.reddit_collector = RedditCollector(self.config)
        
    def collect_complete_dataset(self, symbols: List[str]) -> Dict[str, StockData]:
        """
        Collect complete dataset for multiple symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to StockData objects
        """
        results = {}
        
        logger.info(f"Starting data collection for {len(symbols)} symbols")
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"Processing {symbol} ({i}/{len(symbols)})")
            
            try:
                # Collect Yahoo Finance data
                stock_data = self.yahoo_collector.collect_stock_data(symbol)
                if stock_data:
                    results[symbol] = stock_data
                    logger.info(f"Successfully collected data for {symbol}")
                else:
                    logger.warning(f"Failed to collect data for {symbol}")
                    
                # Add small delay to be respectful to APIs
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
                
        logger.info(f"Data collection complete. Successfully collected {len(results)} out of {len(symbols)} symbols")
        return results
        
    def collect_sample_sp500(self) -> Dict[str, StockData]:
        """
        Collect data for sample S&P 500 stocks from config
        
        Returns:
            Dictionary mapping symbols to StockData objects
        """
        symbols = self.config.get('stocks', {}).get('sample_symbols', [])
        return self.collect_complete_dataset(symbols)

# Convenience functions
def collect_sp500_sample(config_path: Optional[str] = None) -> Dict[str, StockData]:
    """
    Convenience function to collect sample S&P 500 data
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary of collected stock data
    """
    orchestrator = DataCollectionOrchestrator(config_path)
    return orchestrator.collect_sample_sp500()

def collect_single_stock(symbol: str, config_path: Optional[str] = None) -> Optional[StockData]:
    """
    Convenience function to collect data for a single stock
    
    Args:
        symbol: Stock symbol
        config_path: Path to configuration file
        
    Returns:
        StockData object or None
    """
    orchestrator = DataCollectionOrchestrator(config_path)
    results = orchestrator.collect_complete_dataset([symbol])
    return results.get(symbol)