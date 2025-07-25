"""
Database management for StockAnalyzer Pro with comprehensive content storage
"""

import sqlite3
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Optional, Any, Tuple
import logging
from pathlib import Path
from dataclasses import dataclass
import json

from src.utils.helpers import load_config

logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    """News article data container"""
    symbol: str
    title: str
    summary: str
    content: str
    publisher: str
    publish_date: datetime
    url: str
    sentiment_score: float
    confidence_score: float

@dataclass
class RedditPost:
    """Reddit post data container"""
    symbol: str
    post_id: str
    title: str
    content: str
    subreddit: str
    author: str
    score: int
    upvote_ratio: float
    num_comments: int
    created_utc: datetime
    url: str
    sentiment_score: float
    confidence_score: float

@dataclass
class DailySentiment:
    """Daily aggregated sentiment data"""
    symbol: str
    date: date
    news_sentiment: float
    news_count: int
    reddit_sentiment: float
    reddit_count: int
    combined_sentiment: float
    confidence: float

class DatabaseManager:
    """
    Comprehensive database manager for stock analysis data
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        self.db_path = self.config.get('database', {}).get('path', 'data/stock_data.db')
        
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.connection = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            
    def create_tables(self):
        """Create all required database tables"""
        if not self.connection:
            if not self.connect():
                raise RuntimeError("Cannot create tables without database connection")
        
        # SQL for creating all tables
        table_schemas = {
            'stocks': '''
                CREATE TABLE IF NOT EXISTS stocks (
                    symbol VARCHAR(10) PRIMARY KEY,
                    company_name VARCHAR(255),
                    sector VARCHAR(100),
                    industry VARCHAR(100),
                    market_cap BIGINT,
                    listing_exchange VARCHAR(20),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            
            'price_data': '''
                CREATE TABLE IF NOT EXISTS price_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10),
                    date DATE NOT NULL,
                    open DECIMAL(10,2),
                    high DECIMAL(10,2),
                    low DECIMAL(10,2),
                    close DECIMAL(10,2),
                    volume BIGINT,
                    adjusted_close DECIMAL(10,2),
                    source VARCHAR(50),
                    quality_score DECIMAL(3,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol),
                    UNIQUE(symbol, date, source)
                )
            ''',
            
            'fundamental_data': '''
                CREATE TABLE IF NOT EXISTS fundamental_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10),
                    reporting_date DATE NOT NULL,
                    period_type VARCHAR(10),
                    
                    -- Core financials
                    total_revenue BIGINT,
                    net_income BIGINT,
                    total_assets BIGINT,
                    total_debt BIGINT,
                    shareholders_equity BIGINT,
                    shares_outstanding BIGINT,
                    free_cash_flow BIGINT,
                    operating_cash_flow BIGINT,
                    
                    -- Key ratios (pre-calculated for efficiency)
                    eps DECIMAL(10,4),
                    book_value_per_share DECIMAL(10,4),
                    pe_ratio DECIMAL(8,2),
                    forward_pe DECIMAL(8,2),
                    peg_ratio DECIMAL(8,2),
                    price_to_book DECIMAL(8,2),
                    enterprise_value BIGINT,
                    ev_to_ebitda DECIMAL(8,2),
                    
                    -- Quality metrics
                    return_on_equity DECIMAL(6,4),
                    return_on_assets DECIMAL(6,4),
                    debt_to_equity DECIMAL(6,4),
                    current_ratio DECIMAL(6,4),
                    quick_ratio DECIMAL(6,4),
                    
                    -- Growth metrics
                    revenue_growth DECIMAL(6,4),
                    earnings_growth DECIMAL(6,4),
                    revenue_per_share DECIMAL(10,4),
                    
                    -- Market data
                    current_price DECIMAL(10,2),
                    market_cap BIGINT,
                    beta DECIMAL(6,4),
                    dividend_yield DECIMAL(6,4),
                    week_52_high DECIMAL(10,2),
                    week_52_low DECIMAL(10,2),
                    
                    -- Metadata
                    source VARCHAR(50),
                    quality_score DECIMAL(3,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol),
                    UNIQUE(symbol, reporting_date, period_type, source)
                )
            ''',
            
            'news_articles': '''
                CREATE TABLE IF NOT EXISTS news_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10),
                    title TEXT NOT NULL,
                    summary TEXT,
                    content TEXT,
                    publisher VARCHAR(100),
                    publish_date TIMESTAMP,
                    url TEXT,
                    sentiment_score DECIMAL(4,3),
                    confidence_score DECIMAL(4,3),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
                )
            ''',
            
            'reddit_posts': '''
                CREATE TABLE IF NOT EXISTS reddit_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10),
                    post_id VARCHAR(20) UNIQUE,
                    title TEXT NOT NULL,
                    content TEXT,
                    subreddit VARCHAR(50),
                    author VARCHAR(50),
                    score INTEGER,
                    upvote_ratio DECIMAL(3,2),
                    num_comments INTEGER,
                    created_utc TIMESTAMP,
                    url TEXT,
                    sentiment_score DECIMAL(4,3),
                    confidence_score DECIMAL(4,3),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
                )
            ''',
            
            'daily_sentiment': '''
                CREATE TABLE IF NOT EXISTS daily_sentiment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10),
                    date DATE,
                    news_sentiment DECIMAL(4,3),
                    news_count INTEGER,
                    reddit_sentiment DECIMAL(4,3),
                    reddit_count INTEGER,
                    combined_sentiment DECIMAL(4,3),
                    confidence DECIMAL(4,3),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol),
                    UNIQUE(symbol, date)
                )
            ''',
            
            'calculated_metrics': '''
                CREATE TABLE IF NOT EXISTS calculated_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10),
                    calculation_date DATE NOT NULL,
                    
                    -- Component scores (0-100)
                    fundamental_score DECIMAL(5,2),
                    quality_score DECIMAL(5,2),
                    growth_score DECIMAL(5,2),
                    sentiment_score DECIMAL(5,2),
                    
                    -- Composite score
                    composite_score DECIMAL(5,2),
                    sector_percentile DECIMAL(5,2),
                    confidence_interval_lower DECIMAL(5,2),
                    confidence_interval_upper DECIMAL(5,2),
                    
                    -- Metadata
                    methodology_version VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol),
                    UNIQUE(symbol, calculation_date)
                )
            '''
        }
        
        # Create tables
        cursor = self.connection.cursor()
        for table_name, schema in table_schemas.items():
            try:
                cursor.execute(schema)
                logger.info(f"Created/verified table: {table_name}")
            except Exception as e:
                logger.error(f"Error creating table {table_name}: {str(e)}")
                raise
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_price_data_symbol_date ON price_data(symbol, date)",
            "CREATE INDEX IF NOT EXISTS idx_fundamental_data_symbol_date ON fundamental_data(symbol, reporting_date)",
            "CREATE INDEX IF NOT EXISTS idx_news_articles_symbol_date ON news_articles(symbol, publish_date)",
            "CREATE INDEX IF NOT EXISTS idx_reddit_posts_symbol_date ON reddit_posts(symbol, created_utc)",
            "CREATE INDEX IF NOT EXISTS idx_daily_sentiment_symbol_date ON daily_sentiment(symbol, date)",
            "CREATE INDEX IF NOT EXISTS idx_calculated_metrics_symbol_date ON calculated_metrics(symbol, calculation_date)"
        ]
        
        for index in indexes:
            try:
                cursor.execute(index)
            except Exception as e:
                logger.debug(f"Index creation note: {str(e)}")
        
        self.connection.commit()
        cursor.close()
        logger.info("Database schema creation completed successfully")
    
    def insert_stock(self, symbol: str, company_name: str, sector: str = None, 
                    industry: str = None, market_cap: int = None, 
                    listing_exchange: str = None):
        """Insert or update stock information"""
        cursor = self.connection.cursor()
        
        sql = '''
            INSERT OR REPLACE INTO stocks 
            (symbol, company_name, sector, industry, market_cap, listing_exchange, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        '''
        
        cursor.execute(sql, (symbol, company_name, sector, industry, market_cap, listing_exchange))
        self.connection.commit()
        cursor.close()
        
        logger.debug(f"Inserted/updated stock: {symbol}")
    
    def insert_price_data(self, symbol: str, price_df: pd.DataFrame, source: str = "yahoo_finance"):
        """Insert price data from pandas DataFrame"""
        cursor = self.connection.cursor()
        
        for index, row in price_df.iterrows():
            sql = '''
                INSERT OR REPLACE INTO price_data
                (symbol, date, open, high, low, close, volume, adjusted_close, source, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            # Handle adjusted close if available
            adj_close = row.get('Adj Close', row['Close'])
            
            cursor.execute(sql, (
                symbol, index.date(), row['Open'], row['High'], 
                row['Low'], row['Close'], row['Volume'], adj_close, 
                source, 1.0  # Assume good quality for Yahoo Finance
            ))
        
        self.connection.commit()
        cursor.close()
        logger.info(f"Inserted {len(price_df)} price records for {symbol}")
    
    def insert_fundamental_data(self, symbol: str, fundamental_dict: Dict[str, Any]):
        """Insert fundamental data from dictionary"""
        cursor = self.connection.cursor()
        
        # Map dictionary keys to database columns
        sql = '''
            INSERT OR REPLACE INTO fundamental_data
            (symbol, reporting_date, total_revenue, net_income, total_assets, total_debt,
             shareholders_equity, shares_outstanding, free_cash_flow, operating_cash_flow,
             eps, pe_ratio, forward_pe, peg_ratio, price_to_book, enterprise_value, ev_to_ebitda,
             return_on_equity, return_on_assets, debt_to_equity, current_ratio, quick_ratio,
             revenue_growth, earnings_growth, current_price, market_cap, beta, dividend_yield,
             week_52_high, week_52_low, source, quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        # Extract values with defaults
        values = (
            symbol,
            datetime.now().date(),  # Use current date as reporting date
            fundamental_dict.get('total_revenue'),
            fundamental_dict.get('net_income'),
            fundamental_dict.get('total_assets'),
            fundamental_dict.get('total_debt'),
            fundamental_dict.get('shareholders_equity'),
            fundamental_dict.get('shares_outstanding'),
            fundamental_dict.get('free_cash_flow'),
            fundamental_dict.get('operating_cash_flow'),
            fundamental_dict.get('eps_trailing_12m'),
            fundamental_dict.get('pe_ratio'),
            fundamental_dict.get('forward_pe'),
            fundamental_dict.get('peg_ratio'),
            fundamental_dict.get('price_to_book'),
            fundamental_dict.get('enterprise_value'),
            fundamental_dict.get('ev_to_ebitda'),
            fundamental_dict.get('return_on_equity'),
            fundamental_dict.get('return_on_assets'),
            fundamental_dict.get('debt_to_equity'),
            fundamental_dict.get('current_ratio'),
            fundamental_dict.get('quick_ratio'),
            fundamental_dict.get('revenue_growth'),
            fundamental_dict.get('earnings_growth'),
            fundamental_dict.get('current_price'),
            fundamental_dict.get('market_cap'),
            fundamental_dict.get('beta'),
            fundamental_dict.get('dividend_yield'),
            fundamental_dict.get('52_week_high'),
            fundamental_dict.get('52_week_low'),
            fundamental_dict.get('data_source', 'yahoo_finance'),
            1.0  # Quality score
        )
        
        cursor.execute(sql, values)
        self.connection.commit()
        cursor.close()
        logger.info(f"Inserted fundamental data for {symbol}")
    
    def insert_news_articles(self, articles: List[NewsArticle]):
        """Insert news articles"""
        cursor = self.connection.cursor()
        
        sql = '''
            INSERT OR REPLACE INTO news_articles
            (symbol, title, summary, content, publisher, publish_date, url, sentiment_score, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        for article in articles:
            cursor.execute(sql, (
                article.symbol, article.title, article.summary, article.content,
                article.publisher, article.publish_date, article.url,
                article.sentiment_score, article.confidence_score
            ))
        
        self.connection.commit()
        cursor.close()
        logger.info(f"Inserted {len(articles)} news articles")
    
    def insert_reddit_posts(self, posts: List[RedditPost]):
        """Insert Reddit posts"""
        cursor = self.connection.cursor()
        
        sql = '''
            INSERT OR REPLACE INTO reddit_posts
            (symbol, post_id, title, content, subreddit, author, score, upvote_ratio, 
             num_comments, created_utc, url, sentiment_score, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        for post in posts:
            cursor.execute(sql, (
                post.symbol, post.post_id, post.title, post.content, post.subreddit,
                post.author, post.score, post.upvote_ratio, post.num_comments,
                post.created_utc, post.url, post.sentiment_score, post.confidence_score
            ))
        
        self.connection.commit()
        cursor.close()
        logger.info(f"Inserted {len(posts)} Reddit posts")
    
    def insert_daily_sentiment(self, sentiment: DailySentiment):
        """Insert daily aggregated sentiment"""
        cursor = self.connection.cursor()
        
        sql = '''
            INSERT OR REPLACE INTO daily_sentiment
            (symbol, date, news_sentiment, news_count, reddit_sentiment, reddit_count,
             combined_sentiment, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        cursor.execute(sql, (
            sentiment.symbol, sentiment.date, sentiment.news_sentiment, sentiment.news_count,
            sentiment.reddit_sentiment, sentiment.reddit_count, sentiment.combined_sentiment,
            sentiment.confidence
        ))
        
        self.connection.commit()
        cursor.close()
        logger.info(f"Inserted daily sentiment for {sentiment.symbol} on {sentiment.date}")
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock information"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM stocks WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        cursor.close()
        
        return dict(row) if row else None
    
    def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest price data for a symbol"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM price_data 
            WHERE symbol = ? 
            ORDER BY date DESC 
            LIMIT 1
        ''', (symbol,))
        row = cursor.fetchone()
        cursor.close()
        
        return dict(row) if row else None
    
    def get_latest_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest fundamental data for a symbol"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM fundamental_data 
            WHERE symbol = ? 
            ORDER BY reporting_date DESC 
            LIMIT 1
        ''', (symbol,))
        row = cursor.fetchone()
        cursor.close()
        
        return dict(row) if row else None
    
    def get_recent_news(self, symbol: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent news articles for a symbol"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM news_articles 
            WHERE symbol = ? AND publish_date >= date('now', '-{} days')
            ORDER BY publish_date DESC
        '''.format(days), (symbol,))
        rows = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in rows]
    
    def get_recent_reddit_posts(self, symbol: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent Reddit posts for a symbol"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM reddit_posts 
            WHERE symbol = ? AND created_utc >= datetime('now', '-{} days')
            ORDER BY created_utc DESC
        '''.format(days), (symbol,))
        rows = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in rows]
    
    def get_daily_sentiment(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily sentiment history for a symbol"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM daily_sentiment 
            WHERE symbol = ? AND date >= date('now', '-{} days')
            ORDER BY date DESC
        '''.format(days), (symbol,))
        rows = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in rows]
    
    def get_all_stocks(self) -> List[str]:
        """Get list of all stock symbols in database"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT symbol FROM stocks WHERE is_active = TRUE ORDER BY symbol")
        rows = cursor.fetchall()
        cursor.close()
        
        return [row[0] for row in rows]
    
    def init_sample_stocks(self):
        """Initialize database with sample S&P 500 stocks from config"""
        sample_symbols = self.config.get('stocks', {}).get('sample_symbols', [])
        
        for symbol in sample_symbols:
            # Insert with placeholder data - will be updated when we collect real data
            self.insert_stock(
                symbol=symbol,
                company_name=f"{symbol} Inc.",  # Placeholder
                sector="Technology",  # Will be updated
                industry="Software"  # Will be updated
            )
        
        logger.info(f"Initialized {len(sample_symbols)} sample stocks")

# Convenience functions
def init_database(config_path: Optional[str] = None) -> DatabaseManager:
    """Initialize database with all tables and sample data"""
    db = DatabaseManager(config_path)
    db.connect()
    db.create_tables()
    db.init_sample_stocks()
    return db

def get_database_connection(config_path: Optional[str] = None) -> DatabaseManager:
    """Get connected database manager"""
    db = DatabaseManager(config_path)
    db.connect()
    return db