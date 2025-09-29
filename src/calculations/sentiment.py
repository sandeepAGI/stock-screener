"""
Sentiment Analysis Calculators - 15% Weight Component

Implements sentiment metrics for stock analysis:
- News Sentiment Analysis - Financial news sentiment scoring
- Social Media Sentiment - Reddit/community discussion sentiment
- Sentiment Momentum - Recent sentiment trend analysis
- Sentiment Volume - Quantity and engagement level of sentiment sources

Each metric is scored 0-100 with data quality weighting, then combined into composite sentiment score.
Sentiment metrics help identify market perception and potential momentum shifts.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, date, timedelta
import re

from src.data.database import DatabaseManager
from src.utils.helpers import load_config
from src.calculations.sector_adjustments import SectorAdjustmentEngine

# Import sentiment analyzers
try:
    from textblob import TextBlob
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False
    logger.warning("Sentiment analysis libraries not available. Install textblob and vaderSentiment.")

logger = logging.getLogger(__name__)

@dataclass
class SentimentMetrics:
    """Container for sentiment analysis results"""
    symbol: str
    calculation_date: date
    
    # Raw metrics
    news_sentiment: Optional[float]
    social_sentiment: Optional[float]
    sentiment_momentum: Optional[float]
    sentiment_volume: Optional[int]
    
    # Scored metrics (0-100)
    news_sentiment_score: float
    social_sentiment_score: float
    momentum_score: float
    volume_score: float
    
    # Composite score
    sentiment_score: float
    data_quality_score: float
    
    # Metadata
    sector: Optional[str]
    data_sources: int
    news_count: int
    social_count: int

class SentimentCalculator:
    """
    Calculates and scores sentiment analysis metrics
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = load_config(config_path)
        self.sector_engine = SectorAdjustmentEngine()
        
        # Initialize sentiment analyzers if available
        if SENTIMENT_AVAILABLE:
            self.vader_analyzer = SentimentIntensityAnalyzer()
        else:
            self.vader_analyzer = None
        
        # Sentiment component weights (sum to 100%)
        self.base_component_weights = {
            'news_sentiment': 0.45,      # 45% - Financial news most important
            'social_sentiment': 0.30,    # 30% - Community sentiment
            'momentum': 0.15,           # 15% - Recent trend direction
            'volume': 0.10              # 10% - Engagement level
        }
        
        # Base scoring thresholds for sentiment metrics
        self.scoring_thresholds = {
            'news_sentiment': {
                'excellent': 0.3,        # Very positive news sentiment
                'good': 0.1,             # Positive news sentiment
                'neutral': 0.0,          # Neutral news sentiment
                'poor': -0.1,            # Negative news sentiment
                'very_poor': -0.3        # Very negative news sentiment
            },
            'social_sentiment': {
                'excellent': 0.2,        # Very positive social sentiment
                'good': 0.05,            # Positive social sentiment
                'neutral': 0.0,          # Neutral social sentiment
                'poor': -0.05,           # Negative social sentiment
                'very_poor': -0.2        # Very negative social sentiment
            },
            'momentum': {
                'excellent': 0.15,       # Strong positive momentum
                'good': 0.05,            # Positive momentum
                'neutral': 0.0,          # No clear momentum
                'poor': -0.05,           # Negative momentum
                'very_poor': -0.15       # Strong negative momentum
            },
            'volume': {
                'excellent': 50,         # High engagement (50+ articles/posts)
                'good': 20,              # Good engagement (20+ articles/posts)
                'average': 10,           # Average engagement (10+ articles/posts)
                'poor': 5,               # Low engagement (5+ articles/posts)
                'very_poor': 1           # Very low engagement (1+ articles/posts)
            }
        }
    
    def get_sector_adjusted_weights(self, sector: Optional[str]) -> Dict[str, float]:
        """
        Get sector-adjusted component weights for sentiment metrics
        
        Args:
            sector: Sector name
            
        Returns:
            Adjusted component weights dictionary
        """
        weights = self.base_component_weights.copy()
        
        # Sector-specific weight adjustments
        if sector == 'Technology':
            # Tech: Social sentiment more important, momentum critical
            weights['news_sentiment'] = 0.40      # -5% (still important)
            weights['social_sentiment'] = 0.35    # +5% (community-driven)
            weights['momentum'] = 0.20            # +5% (momentum stocks)
            weights['volume'] = 0.05              # -5% (high base volume)
            
        elif sector == 'Financials':
            # Financials: News sentiment critical, regulation-sensitive
            weights['news_sentiment'] = 0.55      # +10% (regulatory news key)
            weights['social_sentiment'] = 0.20    # -10% (less retail driven)
            weights['momentum'] = 0.15            # Same
            weights['volume'] = 0.10              # Same
            
        elif sector == 'Healthcare':
            # Healthcare: News critical for approvals, social less relevant
            weights['news_sentiment'] = 0.50      # +5% (FDA/regulatory news)
            weights['social_sentiment'] = 0.25    # -5% (technical sector)
            weights['momentum'] = 0.15            # Same
            weights['volume'] = 0.10              # Same
            
        elif sector == 'Energy':
            # Energy: News and momentum important for commodity tracking
            weights['news_sentiment'] = 0.45      # Same
            weights['social_sentiment'] = 0.25    # -5% (commodity-driven)
            weights['momentum'] = 0.20            # +5% (cyclical timing)
            weights['volume'] = 0.10              # Same
            
        elif sector == 'Consumer Discretionary':
            # Consumer: Social sentiment more important, brand perception
            weights['news_sentiment'] = 0.35      # -10% (brand-driven)
            weights['social_sentiment'] = 0.40    # +10% (consumer opinion key)
            weights['momentum'] = 0.15            # Same
            weights['volume'] = 0.10              # Same
        
        return weights
    
    def analyze_text_sentiment(self, text: str) -> Tuple[float, float]:
        """
        Analyze sentiment of text using both TextBlob and VADER
        
        Args:
            text: Text to analyze
            
        Returns:
            (sentiment_score, reliability): Combined sentiment score and reliability measure
        """
        if not SENTIMENT_AVAILABLE:
            logger.warning("Sentiment analysis libraries not available")
            return 0.0, 0.0
        
        try:
            # Clean text
            cleaned_text = re.sub(r'[^\w\s]', '', text.lower())
            if len(cleaned_text.strip()) < 10:  # Too short for meaningful analysis
                return 0.0, 0.0
            
            # TextBlob analysis (polarity ranges from -1 to 1)
            textblob_sentiment = TextBlob(text).sentiment.polarity
            
            # VADER analysis (compound score ranges from -1 to 1)
            vader_scores = self.vader_analyzer.polarity_scores(text)
            vader_sentiment = vader_scores['compound']
            
            # Combine scores with equal weighting
            combined_sentiment = (textblob_sentiment + vader_sentiment) / 2
            
            # Calculate reliability based on agreement between methods
            agreement = 1 - abs(textblob_sentiment - vader_sentiment) / 2
            reliability = max(0.5, agreement)  # Minimum 50% reliability
            
            return combined_sentiment, reliability
            
        except Exception as e:
            logger.error(f"Error analyzing text sentiment: {str(e)}")
            return 0.0, 0.0
    
    def calculate_news_sentiment(self, symbol: str, db: DatabaseManager, days_back: int = 30) -> Tuple[Optional[float], float, int]:
        """
        Calculate and score news sentiment from stored articles

        Args:
            symbol: Stock symbol
            db: Database manager instance
            days_back: Number of days to look back for news

        Returns:
            (news_sentiment, news_sentiment_score, article_count): Raw sentiment, score, and count
        """
        try:
            # Get recent news articles WITH EXISTING SENTIMENT SCORES from database
            cutoff_date = datetime.now() - timedelta(days=days_back)

            cursor = db.connection.cursor()
            cursor.execute('''
                SELECT sentiment_score, data_quality_score
                FROM news_articles
                WHERE symbol = ?
                AND publish_date >= ?
                AND sentiment_score IS NOT NULL
                ORDER BY publish_date DESC
            ''', (symbol, cutoff_date))

            articles = cursor.fetchall()
            cursor.close()

            if not articles:
                logger.warning(f"No recent news articles with sentiment found for {symbol}")
                return None, 0.0, 0

            # Use EXISTING sentiment scores (from Claude API batch processing)
            sentiments = []
            reliabilities = []

            for sentiment_score, quality_score in articles:
                # Use the pre-calculated sentiment scores
                if sentiment_score is not None and quality_score is not None:
                    sentiments.append(sentiment_score)
                    reliabilities.append(quality_score)

            if not sentiments:
                logger.warning(f"No valid sentiment scores for {symbol} news")
                return None, 0.0, len(articles)
            
            # Calculate weighted average sentiment
            weights = np.array(reliabilities)
            avg_sentiment = np.average(sentiments, weights=weights)
            
            # Score news sentiment
            thresholds = self.scoring_thresholds['news_sentiment']
            
            if avg_sentiment >= thresholds['excellent']:
                score = 90 + min(10, (avg_sentiment - thresholds['excellent']) / 0.2 * 10)
            elif avg_sentiment >= thresholds['good']:
                score = 70 + (avg_sentiment - thresholds['good']) / (thresholds['excellent'] - thresholds['good']) * 20
            elif avg_sentiment >= thresholds['neutral']:
                score = 50 + (avg_sentiment - thresholds['neutral']) / (thresholds['good'] - thresholds['neutral']) * 20
            elif avg_sentiment >= thresholds['poor']:
                score = 30 + (avg_sentiment - thresholds['poor']) / (thresholds['neutral'] - thresholds['poor']) * 20
            elif avg_sentiment >= thresholds['very_poor']:
                score = 10 + (avg_sentiment - thresholds['very_poor']) / (thresholds['poor'] - thresholds['very_poor']) * 20
            else:
                score = max(0, 10 + (avg_sentiment - thresholds['very_poor']) / 0.2 * 10)
            
            return avg_sentiment, max(0, min(100, score)), len(articles)
            
        except Exception as e:
            logger.error(f"Error calculating news sentiment for {symbol}: {str(e)}")
            return None, 0.0, 0
    
    def calculate_social_sentiment(self, symbol: str, db: DatabaseManager, days_back: int = 14) -> Tuple[Optional[float], float, int]:
        """
        Calculate and score social media sentiment from Reddit posts
        
        Args:
            symbol: Stock symbol
            db: Database manager instance
            days_back: Number of days to look back for posts
            
        Returns:
            (social_sentiment, social_sentiment_score, post_count): Raw sentiment, score, and count
        """
        try:
            # Get recent Reddit posts WITH EXISTING SENTIMENT SCORES from database
            cutoff_date = datetime.now() - timedelta(days=days_back)

            cursor = db.connection.cursor()
            cursor.execute('''
                SELECT sentiment_score, data_quality_score, score, num_comments
                FROM reddit_posts
                WHERE symbol = ?
                AND created_utc >= ?
                AND sentiment_score IS NOT NULL
                ORDER BY created_utc DESC
            ''', (symbol, cutoff_date))

            posts = cursor.fetchall()
            cursor.close()

            if not posts:
                logger.warning(f"No recent Reddit posts with sentiment found for {symbol}")
                return None, 0.0, 0

            # Use EXISTING sentiment scores (from Claude API batch processing)
            sentiments = []
            weights = []

            for sentiment_score, quality_score, reddit_score, num_comments in posts:
                if sentiment_score is not None and quality_score is not None:
                    # Use the pre-calculated sentiment scores
                    sentiments.append(sentiment_score)

                    # Weight by post engagement (score + comments) and quality
                    engagement = max(1, (reddit_score or 0) + (num_comments or 0))
                    post_weight = quality_score * np.log(1 + engagement)
                    weights.append(post_weight)

            if not sentiments:
                logger.warning(f"No valid sentiment scores for {symbol} social posts")
                return None, 0.0, len(posts)
            
            # Calculate weighted average sentiment
            avg_sentiment = np.average(sentiments, weights=weights)
            
            # Score social sentiment (generally more neutral than news)
            thresholds = self.scoring_thresholds['social_sentiment']
            
            if avg_sentiment >= thresholds['excellent']:
                score = 90 + min(10, (avg_sentiment - thresholds['excellent']) / 0.1 * 10)
            elif avg_sentiment >= thresholds['good']:
                score = 70 + (avg_sentiment - thresholds['good']) / (thresholds['excellent'] - thresholds['good']) * 20
            elif avg_sentiment >= thresholds['neutral']:
                score = 50 + (avg_sentiment - thresholds['neutral']) / (thresholds['good'] - thresholds['neutral']) * 20
            elif avg_sentiment >= thresholds['poor']:
                score = 30 + (avg_sentiment - thresholds['poor']) / (thresholds['neutral'] - thresholds['poor']) * 20
            elif avg_sentiment >= thresholds['very_poor']:
                score = 10 + (avg_sentiment - thresholds['very_poor']) / (thresholds['poor'] - thresholds['very_poor']) * 20
            else:
                score = max(0, 10 + (avg_sentiment - thresholds['very_poor']) / 0.1 * 10)
            
            return avg_sentiment, max(0, min(100, score)), len(posts)
            
        except Exception as e:
            logger.error(f"Error calculating social sentiment for {symbol}: {str(e)}")
            return None, 0.0, 0
    
    def calculate_sentiment_momentum(self, symbol: str, db: DatabaseManager) -> Tuple[Optional[float], float]:
        """
        Calculate sentiment momentum by comparing recent vs older sentiment
        
        Args:
            symbol: Stock symbol
            db: Database manager instance
            
        Returns:
            (momentum, momentum_score): Raw momentum and normalized score
        """
        try:
            # Get recent sentiment (last 7 days)
            recent_cutoff = datetime.now() - timedelta(days=7)
            older_cutoff = datetime.now() - timedelta(days=21)
            
            cursor = db.connection.cursor()
            
            # Recent news sentiment (use existing sentiment scores)
            cursor.execute('''
                SELECT sentiment_score FROM news_articles
                WHERE symbol = ? AND publish_date >= ? AND sentiment_score IS NOT NULL
            ''', (symbol, recent_cutoff))
            recent_news = cursor.fetchall()

            # Older news sentiment (use existing sentiment scores)
            cursor.execute('''
                SELECT sentiment_score FROM news_articles
                WHERE symbol = ? AND publish_date >= ? AND publish_date < ? AND sentiment_score IS NOT NULL
            ''', (symbol, older_cutoff, recent_cutoff))
            older_news = cursor.fetchall()
            
            cursor.close()
            
            # Calculate average sentiment for each period using EXISTING scores
            def get_period_sentiment(sentiment_scores):
                if not sentiment_scores:
                    return None
                scores = [score[0] for score in sentiment_scores if score[0] is not None]
                return np.mean(scores) if scores else None

            recent_sentiment = get_period_sentiment(recent_news)
            older_sentiment = get_period_sentiment(older_news)
            
            if recent_sentiment is None or older_sentiment is None:
                logger.warning(f"Insufficient data for momentum calculation for {symbol}")
                return None, 0.0
            
            # Calculate momentum as difference
            momentum = recent_sentiment - older_sentiment
            
            # Score momentum
            thresholds = self.scoring_thresholds['momentum']
            
            if momentum >= thresholds['excellent']:
                score = 90 + min(10, (momentum - thresholds['excellent']) / 0.1 * 10)
            elif momentum >= thresholds['good']:
                score = 70 + (momentum - thresholds['good']) / (thresholds['excellent'] - thresholds['good']) * 20
            elif momentum >= thresholds['neutral']:
                score = 50 + (momentum - thresholds['neutral']) / (thresholds['good'] - thresholds['neutral']) * 20
            elif momentum >= thresholds['poor']:
                score = 30 + (momentum - thresholds['poor']) / (thresholds['neutral'] - thresholds['poor']) * 20
            elif momentum >= thresholds['very_poor']:
                score = 10 + (momentum - thresholds['very_poor']) / (thresholds['poor'] - thresholds['very_poor']) * 20
            else:
                score = max(0, 10 + (momentum - thresholds['very_poor']) / 0.1 * 10)
            
            return momentum, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating sentiment momentum for {symbol}: {str(e)}")
            return None, 0.0
    
    def calculate_sentiment_volume(self, symbol: str, db: DatabaseManager, days_back: int = 30) -> Tuple[int, float]:
        """
        Calculate sentiment volume score based on quantity of mentions
        
        Args:
            symbol: Stock symbol
            db: Database manager instance
            days_back: Number of days to count mentions
            
        Returns:
            (total_volume, volume_score): Total mentions and normalized score
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            cursor = db.connection.cursor()
            
            # Count news articles
            cursor.execute('''
                SELECT COUNT(*) FROM news_articles 
                WHERE symbol = ? AND publish_date >= ?
            ''', (symbol, cutoff_date))
            news_count = cursor.fetchone()[0]
            
            # Count Reddit posts
            cursor.execute('''
                SELECT COUNT(*) FROM reddit_posts 
                WHERE symbol = ? AND created_utc >= ?
            ''', (symbol, cutoff_date))
            reddit_count = cursor.fetchone()[0]
            
            cursor.close()
            
            total_volume = news_count + reddit_count
            
            # Score volume
            thresholds = self.scoring_thresholds['volume']
            
            if total_volume >= thresholds['excellent']:
                score = 90 + min(10, (total_volume - thresholds['excellent']) / thresholds['excellent'] * 10)
            elif total_volume >= thresholds['good']:
                score = 70 + (total_volume - thresholds['good']) / (thresholds['excellent'] - thresholds['good']) * 20
            elif total_volume >= thresholds['average']:
                score = 50 + (total_volume - thresholds['average']) / (thresholds['good'] - thresholds['average']) * 20
            elif total_volume >= thresholds['poor']:
                score = 30 + (total_volume - thresholds['poor']) / (thresholds['average'] - thresholds['poor']) * 20
            elif total_volume >= thresholds['very_poor']:
                score = 10 + (total_volume - thresholds['very_poor']) / (thresholds['poor'] - thresholds['very_poor']) * 20
            else:
                score = max(5, total_volume / thresholds['very_poor'] * 10)
            
            return total_volume, max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating sentiment volume for {symbol}: {str(e)}")
            return 0, 0.0
    
    def calculate_sentiment_metrics(self, symbol: str, db: DatabaseManager) -> Optional[SentimentMetrics]:
        """
        Calculate all sentiment metrics for a stock
        
        Args:
            symbol: Stock symbol
            db: Database manager instance
            
        Returns:
            SentimentMetrics object or None if insufficient data
        """
        try:
            # Get stock info for sector
            stock_info = db.get_stock_info(symbol)
            sector = stock_info.get('sector') if stock_info else None
            logger.info(f"Calculating sentiment metrics for {symbol} (Sector: {sector})")
            
            # Calculate individual metrics
            news_sentiment, news_score, news_count = self.calculate_news_sentiment(symbol, db)
            social_sentiment, social_score, social_count = self.calculate_social_sentiment(symbol, db)
            momentum, momentum_score = self.calculate_sentiment_momentum(symbol, db)
            volume, volume_score = self.calculate_sentiment_volume(symbol, db)
            
            # Get sector-adjusted weights
            component_weights = self.get_sector_adjusted_weights(sector)
            
            # Calculate weighted composite score
            scores = [news_score, social_score, momentum_score, volume_score]
            weights = list(component_weights.values())
            
            # Only include valid scores (non-zero) in composite
            valid_scores = [(score, weight) for score, weight in zip(scores, weights) if score > 0]
            
            if not valid_scores:
                logger.warning(f"No valid sentiment metrics for {symbol}")
                return None
            
            # Recalculate weights for available metrics
            total_weight = sum(weight for _, weight in valid_scores)
            normalized_scores = [(score * weight / total_weight) for score, weight in valid_scores]
            
            sentiment_score = sum(normalized_scores)
            data_quality_score = len(valid_scores) / len(scores)  # Data quality based on completeness
            
            # Adjust data quality based on data volume
            data_sources = sum([1 for x in [news_count, social_count] if x > 0])
            volume_adjustment = min(1.0, (news_count + social_count) / 10)  # Full quality at 10+ sources
            final_data_quality = data_quality_score * volume_adjustment
            
            return SentimentMetrics(
                symbol=symbol,
                calculation_date=date.today(),
                news_sentiment=news_sentiment,
                social_sentiment=social_sentiment,
                sentiment_momentum=momentum,
                sentiment_volume=volume,
                news_sentiment_score=news_score,
                social_sentiment_score=social_score,
                momentum_score=momentum_score,
                volume_score=volume_score,
                sentiment_score=sentiment_score,
                data_quality_score=final_data_quality,
                sector=sector,
                data_sources=data_sources,
                news_count=news_count,
                social_count=social_count
            )
            
        except Exception as e:
            logger.error(f"Error calculating sentiment metrics for {symbol}: {str(e)}")
            return None
    
    def calculate_batch_sentiment(self, symbols: List[str], db: DatabaseManager) -> Dict[str, SentimentMetrics]:
        """
        Calculate sentiment metrics for multiple stocks
        
        Args:
            symbols: List of stock symbols
            db: Database manager instance
            
        Returns:
            Dictionary mapping symbols to SentimentMetrics
        """
        results = {}
        
        for symbol in symbols:
            try:
                metrics = self.calculate_sentiment_metrics(symbol, db)
                if metrics:
                    results[symbol] = metrics
                    logger.info(f"✅ Calculated sentiment metrics for {symbol}: {metrics.sentiment_score:.1f}")
                else:
                    logger.warning(f"❌ Failed to calculate sentiment metrics for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        logger.info(f"Completed sentiment analysis for {len(results)}/{len(symbols)} stocks")
        return results
    
    def save_sentiment_metrics(self, metrics: SentimentMetrics, db: DatabaseManager):
        """
        Save sentiment metrics to calculated_metrics table
        
        Args:
            metrics: SentimentMetrics object
            db: Database manager instance
        """
        try:
            cursor = db.connection.cursor()
            
            sql = '''
                INSERT OR REPLACE INTO calculated_metrics
                (symbol, calculation_date, sentiment_score, methodology_version)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(symbol, calculation_date) DO UPDATE SET
                    sentiment_score = excluded.sentiment_score,
                    methodology_version = excluded.methodology_version
            '''
            
            cursor.execute(sql, (
                metrics.symbol,
                metrics.calculation_date,
                metrics.sentiment_score,
                'v1.0'
            ))
            
            db.connection.commit()
            cursor.close()
            
            logger.info(f"Saved sentiment metrics for {metrics.symbol}")
            
        except Exception as e:
            logger.error(f"Error saving sentiment metrics for {metrics.symbol}: {str(e)}")

# Convenience functions
def calculate_single_sentiment(symbol: str, config_path: Optional[str] = None) -> Optional[SentimentMetrics]:
    """Calculate sentiment metrics for a single stock"""
    calculator = SentimentCalculator(config_path)
    
    from src.data.database import get_database_connection
    db = get_database_connection(config_path)
    
    try:
        return calculator.calculate_sentiment_metrics(symbol, db)
    finally:
        db.close()

def calculate_all_sentiment(config_path: Optional[str] = None) -> Dict[str, SentimentMetrics]:
    """Calculate sentiment metrics for all stocks in database"""
    calculator = SentimentCalculator(config_path)
    
    from src.data.database import get_database_connection
    db = get_database_connection(config_path)
    
    try:
        symbols = db.get_all_stocks()
        return calculator.calculate_batch_sentiment(symbols, db)
    finally:
        db.close()