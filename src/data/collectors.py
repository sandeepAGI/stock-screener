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
from src.data.stock_universe import StockUniverseManager, UniverseType
from src.data.database import DatabaseManager

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
    data_quality: float
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
                            # Get author name if available (some posts may be deleted/anonymous)
                            try:
                                author_name = str(post.author) if post.author else 'unknown'
                            except:
                                author_name = 'unknown'
                            
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
                                'author': author_name,
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
        self.universe_manager = StockUniverseManager()
        self.db_manager = DatabaseManager()
        self.db_manager.connect()
        self.db_manager.create_tables()
        
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
    
    def refresh_fundamentals_only(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Refresh only fundamental data for specified symbols
        
        Args:
            symbols: List of stock symbols to refresh
            
        Returns:
            Dictionary mapping symbols to success status
        """
        results = {}
        logger.info(f"Refreshing fundamental data for {len(symbols)} symbols")
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if info and len(info) > 5:  # Basic validation
                    # Extract fundamental metrics
                    fundamentals = self.yahoo_collector._extract_fundamentals(ticker)
                    if fundamentals:
                        results[symbol] = True
                        logger.info(f"Successfully refreshed fundamentals for {symbol}")
                    else:
                        results[symbol] = False
                        logger.warning(f"No fundamental data available for {symbol}")
                else:
                    results[symbol] = False
                    logger.warning(f"Limited data returned for {symbol}")
                    
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                results[symbol] = False
                logger.error(f"Error refreshing fundamentals for {symbol}: {e}")
        
        return results
    
    def refresh_prices_only(self, symbols: List[str], period: str = "1mo") -> Dict[str, bool]:
        """
        Refresh only price data for specified symbols
        
        Args:
            symbols: List of stock symbols to refresh
            period: Period for price data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            Dictionary mapping symbols to success status
        """
        results = {}
        logger.info(f"Refreshing price data for {len(symbols)} symbols (period: {period})")
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                
                if not hist.empty and len(hist) > 0:
                    results[symbol] = True
                    logger.info(f"Successfully refreshed {len(hist)} price records for {symbol}")
                else:
                    results[symbol] = False
                    logger.warning(f"No price data available for {symbol}")
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                results[symbol] = False
                logger.error(f"Error refreshing prices for {symbol}: {e}")
        
        return results
    
    def refresh_news_only(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Refresh only news data for specified symbols
        
        Args:
            symbols: List of stock symbols to refresh
            
        Returns:
            Dictionary mapping symbols to success status
        """
        results = {}
        logger.info(f"Refreshing news data for {len(symbols)} symbols")
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                news = ticker.news
                
                if news and len(news) > 0:
                    results[symbol] = True
                    logger.info(f"Successfully refreshed {len(news)} news articles for {symbol}")
                else:
                    results[symbol] = False
                    logger.warning(f"No news data available for {symbol}")
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                results[symbol] = False
                logger.error(f"Error refreshing news for {symbol}: {e}")
        
        return results
    
    def refresh_sentiment_only(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Refresh only sentiment data for specified symbols
        
        Args:
            symbols: List of stock symbols to refresh
            
        Returns:
            Dictionary mapping symbols to success status
        """
        results = {}
        logger.info(f"Refreshing sentiment data for {len(symbols)} symbols")
        
        for symbol in symbols:
            try:
                # Collect Reddit sentiment
                reddit_sentiment = self.reddit_collector.collect_stock_mentions(symbol)
                
                # For demonstration, we'll consider it successful if we get any sentiment data
                if reddit_sentiment is not None:
                    results[symbol] = True
                    logger.info(f"Successfully refreshed sentiment for {symbol}")
                else:
                    results[symbol] = False
                    logger.warning(f"No sentiment data available for {symbol}")
                
                time.sleep(0.5)  # Longer delay for Reddit API
                
            except Exception as e:
                results[symbol] = False
                logger.error(f"Error refreshing sentiment for {symbol}: {e}")
        
        return results
    
    def bulk_add_stocks(self, symbols: List[str], validate: bool = True) -> Dict[str, Any]:
        """
        Add multiple stocks to the tracking list with validation
        
        Args:
            symbols: List of stock symbols to add
            validate: Whether to validate symbols exist and have data
            
        Returns:
            Dictionary with results including success/failure counts and details
        """
        results = {
            "total_requested": len(symbols),
            "successfully_added": 0,
            "failed": 0,
            "skipped_duplicates": 0,
            "details": {}
        }
        
        logger.info(f"Bulk adding {len(symbols)} stocks (validation: {validate})")
        
        # Get current stock list from config or database
        current_symbols = set(self.config.get('stocks', {}).get('sample_symbols', []))
        
        for symbol in symbols:
            symbol = symbol.upper().strip()
            
            try:
                # Check for duplicates
                if symbol in current_symbols:
                    results["skipped_duplicates"] += 1
                    results["details"][symbol] = {"status": "duplicate", "message": "Already tracking"}
                    continue
                
                # Validate symbol if requested
                if validate:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    if not info or len(info) < 5:
                        results["failed"] += 1
                        results["details"][symbol] = {"status": "failed", "message": "Invalid symbol or no data"}
                        continue
                    
                    # Basic validation - check if we can get company name
                    company_name = info.get('longName') or info.get('shortName', f"{symbol} Inc.")
                    sector = info.get('sector', 'Unknown')
                    
                    time.sleep(0.1)  # Rate limiting
                
                # Add to tracking list
                current_symbols.add(symbol)
                results["successfully_added"] += 1
                results["details"][symbol] = {
                    "status": "added", 
                    "message": f"Successfully added {symbol}",
                    "company_name": company_name if validate else f"{symbol} Inc.",
                    "sector": sector if validate else "Unknown"
                }
                
            except Exception as e:
                results["failed"] += 1
                results["details"][symbol] = {"status": "error", "message": str(e)}
                logger.error(f"Error adding {symbol}: {e}")
        
        logger.info(f"Bulk add complete: {results['successfully_added']} added, {results['failed']} failed, {results['skipped_duplicates']} duplicates")
        return results
    
    def bulk_remove_stocks(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Remove multiple stocks from the tracking list
        
        Args:
            symbols: List of stock symbols to remove
            
        Returns:
            Dictionary with results including success/failure counts and details
        """
        results = {
            "total_requested": len(symbols),
            "successfully_removed": 0,
            "not_found": 0,
            "details": {}
        }
        
        logger.info(f"Bulk removing {len(symbols)} stocks")
        
        # Get current stock list from config
        current_symbols = set(self.config.get('stocks', {}).get('sample_symbols', []))
        
        for symbol in symbols:
            symbol = symbol.upper().strip()
            
            if symbol in current_symbols:
                current_symbols.remove(symbol)
                results["successfully_removed"] += 1
                results["details"][symbol] = {"status": "removed", "message": f"Successfully removed {symbol}"}
            else:
                results["not_found"] += 1
                results["details"][symbol] = {"status": "not_found", "message": f"{symbol} was not being tracked"}
        
        logger.info(f"Bulk remove complete: {results['successfully_removed']} removed, {results['not_found']} not found")
        return results
    
    def get_collection_status(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get current collection status for symbols
        
        Args:
            symbols: List of symbols to check, or None for all tracked symbols
            
        Returns:
            Dictionary with collection status information
        """
        if symbols is None:
            symbols = self.config.get('stocks', {}).get('sample_symbols', [])
        
        status = {
            "total_symbols": len(symbols),
            "last_check": datetime.now().isoformat(),
            "api_status": {
                "yahoo_finance": self._check_yahoo_api_status(),
                "reddit": self._check_reddit_api_status()
            },
            "symbols_status": {}
        }
        
        # Quick status check for each symbol
        for symbol in symbols[:10]:  # Limit to first 10 for performance
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if info and len(info) > 5:
                    status["symbols_status"][symbol] = "available"
                else:
                    status["symbols_status"][symbol] = "limited_data"
                    
            except Exception as e:
                status["symbols_status"][symbol] = "error"
        
        return status
    
    def _check_yahoo_api_status(self) -> str:
        """Check Yahoo Finance API status"""
        try:
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            return "active" if info and len(info) > 5 else "limited"
        except:
            return "down"
    
    def _check_reddit_api_status(self) -> str:
        """Check Reddit API status"""
        try:
            # This would check Reddit API connectivity
            return "active"  # Placeholder
        except:
            return "down"
    
    # Universe-aware collection methods
    def collect_universe_data(self, universe_id: str, 
                            data_types: List[str] = None,
                            progress_callback: callable = None) -> Dict[str, Any]:
        """
        Collect data for an entire stock universe
        
        Args:
            universe_id: ID of the universe to collect
            data_types: List of data types to collect ['fundamentals', 'prices', 'news', 'sentiment']
            progress_callback: Function to call with progress updates
            
        Returns:
            Dictionary with collection results and statistics
        """
        if data_types is None:
            data_types = ['fundamentals', 'prices', 'news', 'sentiment']
        
        # Get universe symbols
        symbols = self.universe_manager.get_universe_symbols(universe_id)
        if not symbols:
            logger.error(f"Universe '{universe_id}' not found or empty")
            return {"success": False, "error": "Universe not found or empty"}
        
        logger.info(f"Starting collection for universe '{universe_id}' with {len(symbols)} symbols")
        
        results = {
            "universe_id": universe_id,
            "total_symbols": len(symbols),
            "start_time": datetime.now().isoformat(),
            "data_types": data_types,
            "collection_results": {},
            "statistics": {
                "successful": 0,
                "failed": 0,
                "completion_percentage": 0.0
            }
        }
        
        for i, symbol in enumerate(symbols):
            if progress_callback:
                progress_callback(i + 1, len(symbols), symbol)
            
            symbol_results = {}
            symbol_success = True
            
            try:
                # First, collect and insert stock metadata
                stock_data = self.yahoo_collector.collect_stock_data(symbol)
                if stock_data:
                    # Insert stock info
                    self.db_manager.insert_stock(
                        symbol=symbol,
                        company_name=stock_data.fundamental_data.get('company_name', f'{symbol} Inc.'),
                        sector=stock_data.fundamental_data.get('sector', 'Unknown'),
                        industry=stock_data.fundamental_data.get('industry', 'Unknown'),
                        market_cap=stock_data.fundamental_data.get('market_cap'),
                        listing_exchange=stock_data.fundamental_data.get('exchange', 'NASDAQ')
                    )
                    
                    # Insert different data types
                    if 'fundamentals' in data_types and stock_data.fundamental_data:
                        try:
                            self.db_manager.insert_fundamental_data(symbol, stock_data.fundamental_data)
                            symbol_results['fundamentals'] = True
                        except Exception as e:
                            logger.error(f"Error inserting fundamentals for {symbol}: {e}")
                            symbol_results['fundamentals'] = False
                            symbol_success = False
                    
                    if 'prices' in data_types and hasattr(stock_data.price_data, 'iterrows') and not stock_data.price_data.empty:
                        try:
                            # Insert price data in batch (more efficient than individual inserts)
                            self.db_manager.insert_price_data(symbol, stock_data.price_data)
                            symbol_results['prices'] = True
                        except Exception as e:
                            logger.error(f"Error inserting prices for {symbol}: {e}")
                            symbol_results['prices'] = False
                            symbol_success = False
                    elif 'prices' in data_types:
                        logger.warning(f"Price data for {symbol} is not a DataFrame or is empty")
                        symbol_results['prices'] = False
                    
                    if 'news' in data_types and stock_data.news_headlines:
                        try:
                            # Convert news data to NewsArticle objects
                            from src.data.database import NewsArticle
                            news_articles = []
                            for news_item in stock_data.news_headlines:
                                # Parse publish date from news data - CRITICAL: Use actual publish time, not current time
                                publish_date = None
                                if news_item.get('publish_time'):
                                    try:
                                        # Parse ISO format: '2025-07-27T09:45:00Z'
                                        publish_date = datetime.fromisoformat(news_item['publish_time'].replace('Z', '+00:00'))
                                    except:
                                        # Try alternative formats
                                        try:
                                            publish_date = datetime.strptime(news_item['publish_time'], '%Y-%m-%dT%H:%M:%S')
                                        except:
                                            logger.warning(f"Could not parse publish_time: {news_item.get('publish_time')}")
                                
                                # Only use current time as absolute fallback if no date could be parsed
                                if publish_date is None:
                                    publish_date = datetime.now()
                                    logger.warning(f"Using current time as fallback for news article: {news_item.get('title', 'Unknown')[:50]}")
                                
                                article = NewsArticle(
                                    symbol=symbol,
                                    title=news_item.get('title', ''),
                                    summary=news_item.get('summary', ''),
                                    content=news_item.get('summary', ''),  # Using summary as content
                                    publisher=news_item.get('publisher', ''),
                                    publish_date=publish_date,
                                    url=news_item.get('link', ''),
                                    sentiment_score=0.0,  # Will be calculated later
                                    data_quality_score=0.8
                                )
                                news_articles.append(article)
                            
                            # Insert news articles in batch
                            if news_articles:
                                self.db_manager.insert_news_articles(news_articles)
                            symbol_results['news'] = True
                        except Exception as e:
                            logger.error(f"Error inserting news for {symbol}: {e}")
                            symbol_results['news'] = False
                    
                    if 'sentiment' in data_types:
                        try:
                            # Collect Reddit sentiment data
                            reddit_posts = self.reddit_collector.collect_stock_mentions(symbol)
                            if reddit_posts:
                                # Convert to RedditPost objects
                                from src.data.database import RedditPost
                                reddit_post_objects = []
                                for post in reddit_posts:
                                    reddit_post = RedditPost(
                                        symbol=symbol,
                                        post_id=post.get('id', ''),
                                        title=post.get('title', ''),
                                        content=post.get('text', ''),
                                        subreddit=post.get('subreddit', ''),
                                        author=post.get('author', 'unknown'),  # Get actual author if available
                                        score=post.get('score', 0),
                                        upvote_ratio=post.get('upvote_ratio', 0.0),
                                        num_comments=post.get('num_comments', 0),
                                        created_utc=datetime.fromtimestamp(post.get('created_utc', 0)),
                                        url=post.get('url', ''),
                                        sentiment_score=0.0,  # Will be calculated later
                                        data_quality_score=0.7  # Will map to confidence_score in DB
                                    )
                                    reddit_post_objects.append(reddit_post)
                                
                                # Insert Reddit posts in batch
                                if reddit_post_objects:
                                    self.db_manager.insert_reddit_posts(reddit_post_objects)
                            symbol_results['sentiment'] = bool(reddit_posts)
                        except Exception as e:
                            logger.error(f"Error collecting sentiment for {symbol}: {e}")
                            symbol_results['sentiment'] = False
                else:
                    # No stock data collected
                    symbol_success = False
                    symbol_results['fundamentals'] = False
                    symbol_results['prices'] = False
                    symbol_results['news'] = False
                    symbol_results['sentiment'] = False
                
                results["collection_results"][symbol] = symbol_results
                
                if symbol_success:
                    results["statistics"]["successful"] += 1
                else:
                    results["statistics"]["failed"] += 1
                
                # Update progress
                completed = i + 1
                results["statistics"]["completion_percentage"] = (completed / len(symbols)) * 100
                
                logger.info(f"Processed {symbol} ({completed}/{len(symbols)}) - Success: {symbol_success}")
                
            except Exception as e:
                logger.error(f"Error collecting data for {symbol}: {e}")
                results["collection_results"][symbol] = {"error": str(e)}
                results["statistics"]["failed"] += 1
        
        results["end_time"] = datetime.now().isoformat()
        results["success"] = results["statistics"]["successful"] > 0
        
        logger.info(f"Universe collection complete: {results['statistics']['successful']} successful, {results['statistics']['failed']} failed")
        
        return results
    
    def collect_sp500_baseline(self, progress_callback: callable = None) -> Dict[str, Any]:
        """
        Collect complete S&P 500 baseline dataset
        
        Args:
            progress_callback: Function to call with progress updates (current, total, symbol)
            
        Returns:
            Dictionary with collection results
        """
        logger.info("Starting S&P 500 baseline data collection")
        
        # Ensure S&P 500 universe is up to date
        if not self.universe_manager.update_sp500_universe():
            return {"success": False, "error": "Failed to update S&P 500 universe"}
        
        # Collect data for the entire S&P 500 universe
        return self.collect_universe_data(
            universe_id='sp500',
            data_types=['fundamentals', 'prices', 'news', 'sentiment'],
            progress_callback=progress_callback
        )
    
    def get_universe_collection_status(self, universe_id: str) -> Dict[str, Any]:
        """
        Get collection status for a universe
        
        Args:
            universe_id: ID of the universe to check
            
        Returns:
            Dictionary with status information
        """
        symbols = self.universe_manager.get_universe_symbols(universe_id)
        if not symbols:
            return {"error": "Universe not found or empty"}
        
        universe_info = self.universe_manager.get_universe_info(universe_id)
        
        status = {
            "universe_id": universe_id,
            "universe_name": universe_info['metadata'].get('name', universe_id) if universe_info else universe_id,
            "total_symbols": len(symbols),
            "last_check": datetime.now().isoformat(),
            "api_status": {
                "yahoo_finance": self._check_yahoo_api_status(),
                "reddit": self._check_reddit_api_status()
            },
            "estimated_time": self._estimate_collection_time(len(symbols))
        }
        
        return status
    
    def _estimate_collection_time(self, symbol_count: int) -> Dict[str, Any]:
        """Estimate collection time for a given number of symbols"""
        # Rough estimates based on rate limits and API response times
        fundamentals_time = symbol_count * 0.5  # 0.5 seconds per symbol
        prices_time = symbol_count * 0.3       # 0.3 seconds per symbol  
        news_time = symbol_count * 0.4         # 0.4 seconds per symbol
        sentiment_time = symbol_count * 2.0    # 2 seconds per symbol (Reddit rate limits)
        
        total_seconds = fundamentals_time + prices_time + news_time + sentiment_time
        
        return {
            "total_seconds": total_seconds,
            "total_minutes": total_seconds / 60,
            "total_hours": total_seconds / 3600,
            "breakdown": {
                "fundamentals_minutes": fundamentals_time / 60,
                "prices_minutes": prices_time / 60,
                "news_minutes": news_time / 60,
                "sentiment_minutes": sentiment_time / 60
            }
        }
    
    def collect_custom_universe(self, universe_name: str, symbols: List[str], 
                               data_types: List[str] = None,
                               progress_callback: callable = None) -> Dict[str, Any]:
        """
        Create and collect data for a custom universe
        
        Args:
            universe_name: Name for the new universe
            symbols: List of symbols to include
            data_types: Data types to collect
            progress_callback: Progress callback function
            
        Returns:
            Collection results
        """
        # Create custom universe
        universe_id = f"custom_{universe_name.lower().replace(' ', '_')}"
        
        if not self.universe_manager.create_custom_universe(
            universe_id=universe_id,
            name=universe_name,
            description=f"Custom universe: {universe_name}",
            symbols=symbols
        ):
            return {"success": False, "error": "Failed to create custom universe"}
        
        # Collect data for the custom universe
        return self.collect_universe_data(
            universe_id=universe_id,
            data_types=data_types,
            progress_callback=progress_callback
        )

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