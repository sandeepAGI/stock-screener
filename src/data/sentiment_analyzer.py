"""
Sentiment analysis module for news headlines and Reddit posts
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import re

# Sentiment analysis libraries
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class SentimentScore:
    """Container for sentiment analysis results"""
    text: str
    sentiment_score: float  # -1 (negative) to 1 (positive)
    confidence: float      # 0 to 1
    method: str           # 'textblob', 'vader', or 'combined'
    
class SentimentAnalyzer:
    """
    Multi-method sentiment analysis for financial text
    """
    
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        
        # Financial keywords that modify sentiment
        self.positive_financial_terms = {
            'beat', 'beats', 'exceeded', 'outperform', 'bullish', 'growth', 
            'profit', 'revenue', 'earnings', 'upgrade', 'buy', 'strong',
            'positive', 'gain', 'rise', 'surge', 'rally', 'breakthrough'
        }
        
        self.negative_financial_terms = {
            'miss', 'missed', 'disappointed', 'bearish', 'decline', 'loss',
            'downgrade', 'sell', 'weak', 'negative', 'drop', 'fall', 'crash',
            'plunge', 'concern', 'warning', 'risk', 'volatility'
        }
        
    def analyze_text(self, text: str, method: str = 'combined') -> SentimentScore:
        """
        Analyze sentiment of a text string
        
        Args:
            text: Text to analyze
            method: 'textblob', 'vader', or 'combined'
            
        Returns:
            SentimentScore object
        """
        if not text or not text.strip():
            return SentimentScore(text, 0.0, 0.0, method)
            
        try:
            if method == 'textblob':
                return self._textblob_analysis(text)
            elif method == 'vader':
                return self._vader_analysis(text)
            else:  # combined
                return self._combined_analysis(text)
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return SentimentScore(text, 0.0, 0.0, method)
            
    def _textblob_analysis(self, text: str) -> SentimentScore:
        """TextBlob sentiment analysis"""
        blob = TextBlob(text)
        
        # TextBlob returns polarity (-1 to 1) and subjectivity (0 to 1)
        sentiment_score = blob.sentiment.polarity
        confidence = blob.sentiment.subjectivity
        
        return SentimentScore(text, sentiment_score, confidence, 'textblob')
        
    def _vader_analysis(self, text: str) -> SentimentScore:
        """VADER sentiment analysis (better for financial text)"""
        scores = self.vader.polarity_scores(text)
        
        # VADER returns compound score (-1 to 1)
        sentiment_score = scores['compound']
        
        # Calculate confidence based on the strength of positive/negative scores
        confidence = max(scores['pos'], scores['neg'])
        
        return SentimentScore(text, sentiment_score, confidence, 'vader')
        
    def _combined_analysis(self, text: str) -> SentimentScore:
        """Combined analysis using both methods with financial term weighting"""
        
        # Get both analyses
        textblob_result = self._textblob_analysis(text)
        vader_result = self._vader_analysis(text)
        
        # Apply financial term weighting
        financial_weight = self._calculate_financial_weight(text)
        
        # Combine scores (VADER gets more weight for financial text)
        combined_sentiment = (vader_result.sentiment_score * 0.7 + 
                            textblob_result.sentiment_score * 0.3)
        
        # Apply financial term adjustment
        combined_sentiment *= financial_weight
        
        # Combine confidence scores
        combined_confidence = (vader_result.confidence + textblob_result.confidence) / 2
        
        # Ensure bounds
        combined_sentiment = max(-1.0, min(1.0, combined_sentiment))
        combined_confidence = max(0.0, min(1.0, combined_confidence))
        
        return SentimentScore(text, combined_sentiment, combined_confidence, 'combined')
        
    def _calculate_financial_weight(self, text: str) -> float:
        """
        Calculate weighting factor based on financial terms
        
        Returns:
            Multiplier between 0.5 and 1.5 based on financial term presence
        """
        text_lower = text.lower()
        
        # Count positive and negative financial terms
        positive_count = sum(1 for term in self.positive_financial_terms 
                           if term in text_lower)
        negative_count = sum(1 for term in self.negative_financial_terms 
                           if term in text_lower)
        
        # Calculate weight (neutral = 1.0)
        if positive_count > negative_count:
            weight = 1.0 + (positive_count - negative_count) * 0.1
        elif negative_count > positive_count:
            weight = 1.0 - (negative_count - positive_count) * 0.1
        else:
            weight = 1.0
            
        return max(0.5, min(1.5, weight))
        
    def analyze_news_headlines(self, headlines: List[Dict[str, str]]) -> Dict[str, float]:
        """
        Analyze sentiment for a list of news headlines
        
        Args:
            headlines: List of headline dictionaries with 'title' and 'summary' keys
            
        Returns:
            Dictionary with aggregated sentiment metrics
        """
        if not headlines:
            return {
                'avg_sentiment': 0.0,
                'sentiment_std': 0.0,
                'confidence': 0.0,
                'headline_count': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0
            }
            
        try:
            sentiments = []
            confidences = []
            
            for headline in headlines:
                # Combine title and summary for analysis
                text = f"{headline.get('title', '')} {headline.get('summary', '')}"
                
                if text.strip():
                    result = self.analyze_text(text)
                    sentiments.append(result.sentiment_score)
                    confidences.append(result.confidence)
                    
            if not sentiments:
                return self.analyze_news_headlines([])  # Return empty result
                
            # Calculate aggregate metrics
            sentiments_series = pd.Series(sentiments)
            
            avg_sentiment = sentiments_series.mean()
            sentiment_std = sentiments_series.std()
            avg_confidence = pd.Series(confidences).mean()
            
            # Count sentiment categories
            positive_count = sum(1 for s in sentiments if s > 0.1)
            negative_count = sum(1 for s in sentiments if s < -0.1)
            neutral_count = len(sentiments) - positive_count - negative_count
            
            return {
                'avg_sentiment': float(avg_sentiment),
                'sentiment_std': float(sentiment_std) if not pd.isna(sentiment_std) else 0.0,
                'confidence': float(avg_confidence),
                'headline_count': len(sentiments),
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count
            }
            
        except Exception as e:
            logger.error(f"Error analyzing news headlines: {str(e)}")
            return self.analyze_news_headlines([])  # Return empty result
            
    def analyze_reddit_posts(self, posts: List[Dict[str, any]]) -> Dict[str, float]:
        """
        Analyze sentiment for Reddit posts with vote weighting
        
        Args:
            posts: List of Reddit post dictionaries
            
        Returns:
            Dictionary with aggregated sentiment metrics
        """
        if not posts:
            return {
                'avg_sentiment': 0.0,
                'weighted_sentiment': 0.0,
                'confidence': 0.0,
                'post_count': 0,
                'total_score': 0,
                'avg_score': 0.0
            }
            
        try:
            sentiments = []
            confidences = []
            scores = []
            weighted_sentiments = []
            
            for post in posts:
                # Combine title and text for analysis
                text = f"{post.get('title', '')} {post.get('text', '')}"
                post_score = post.get('score', 0)
                
                if text.strip():
                    result = self.analyze_text(text)
                    
                    sentiments.append(result.sentiment_score)
                    confidences.append(result.confidence)
                    scores.append(post_score)
                    
                    # Weight sentiment by post score (upvotes - downvotes)
                    weight = max(1, abs(post_score))  # Minimum weight of 1
                    weighted_sentiments.append(result.sentiment_score * weight)
                    
            if not sentiments:
                return self.analyze_reddit_posts([])  # Return empty result
                
            # Calculate aggregate metrics
            total_weight = sum(max(1, abs(score)) for score in scores)
            
            avg_sentiment = pd.Series(sentiments).mean()
            weighted_sentiment = sum(weighted_sentiments) / total_weight if total_weight > 0 else 0
            avg_confidence = pd.Series(confidences).mean()
            
            return {
                'avg_sentiment': float(avg_sentiment),
                'weighted_sentiment': float(weighted_sentiment),
                'confidence': float(avg_confidence),
                'post_count': len(sentiments),
                'total_score': sum(scores),
                'avg_score': float(pd.Series(scores).mean())
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Reddit posts: {str(e)}")
            return self.analyze_reddit_posts([])  # Return empty result

class StockSentimentCollector:
    """
    Combines news and Reddit sentiment for a comprehensive stock sentiment score
    """
    
    def __init__(self):
        self.analyzer = SentimentAnalyzer()
        
    def collect_stock_sentiment(self, stock_data, reddit_posts: List[Dict] = None) -> Dict[str, float]:
        """
        Collect comprehensive sentiment analysis for a stock
        
        Args:
            stock_data: StockData object with news headlines
            reddit_posts: Optional list of Reddit posts
            
        Returns:
            Dictionary with comprehensive sentiment metrics
        """
        try:
            # Analyze news sentiment
            news_sentiment = self.analyzer.analyze_news_headlines(stock_data.news_headlines)
            
            # Analyze Reddit sentiment if available
            reddit_sentiment = {}
            if reddit_posts:
                reddit_sentiment = self.analyzer.analyze_reddit_posts(reddit_posts)
            
            # Combine sentiments (news weighted 60%, Reddit 40%)
            if reddit_sentiment and reddit_sentiment['post_count'] > 0:
                combined_sentiment = (news_sentiment['avg_sentiment'] * 0.6 + 
                                    reddit_sentiment['weighted_sentiment'] * 0.4)
                combined_confidence = (news_sentiment['confidence'] * 0.6 + 
                                     reddit_sentiment['confidence'] * 0.4)
            else:
                combined_sentiment = news_sentiment['avg_sentiment']
                combined_confidence = news_sentiment['confidence']
                
            return {
                # Combined metrics
                'combined_sentiment': combined_sentiment,
                'combined_confidence': combined_confidence,
                
                # News metrics
                'news_sentiment': news_sentiment['avg_sentiment'],
                'news_confidence': news_sentiment['confidence'],
                'news_count': news_sentiment['headline_count'],
                'news_positive': news_sentiment['positive_count'],
                'news_negative': news_sentiment['negative_count'],
                
                # Reddit metrics
                'reddit_sentiment': reddit_sentiment.get('weighted_sentiment', 0.0),
                'reddit_confidence': reddit_sentiment.get('confidence', 0.0),
                'reddit_count': reddit_sentiment.get('post_count', 0),
                'reddit_score': reddit_sentiment.get('total_score', 0),
                
                # Metadata
                'analysis_date': datetime.now().isoformat(),
                'symbol': stock_data.symbol
            }
            
        except Exception as e:
            logger.error(f"Error collecting sentiment for {stock_data.symbol}: {str(e)}")
            return {
                'combined_sentiment': 0.0,
                'combined_confidence': 0.0,
                'news_sentiment': 0.0,
                'news_confidence': 0.0,
                'news_count': 0,
                'reddit_sentiment': 0.0,
                'reddit_confidence': 0.0,
                'reddit_count': 0,
                'analysis_date': datetime.now().isoformat(),
                'symbol': stock_data.symbol
            }