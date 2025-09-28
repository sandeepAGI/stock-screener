"""
Sentiment analysis module for news headlines and Reddit posts
Enhanced with Claude LLM support for superior financial sentiment analysis
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import re
import os
import json
import time

# Sentiment analysis libraries
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# LLM support
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("Anthropic library not available. LLM sentiment analysis will be disabled.")

logger = logging.getLogger(__name__)

@dataclass
class SentimentScore:
    """Container for sentiment analysis results"""
    text: str
    sentiment_score: float  # -1 (negative) to 1 (positive)
    data_quality: float      # 0 to 1
    method: str           # 'textblob', 'vader', 'combined', 'claude', or 'claude_fallback'
    confidence: Optional[float] = None  # LLM confidence score
    reasoning: Optional[str] = None     # LLM reasoning (for debugging)
    
class SentimentAnalyzer:
    """
    Multi-method sentiment analysis for financial text
    Enhanced with Claude LLM for superior financial context understanding
    """

    def __init__(self, anthropic_api_key: Optional[str] = None, use_llm: bool = True):
        self.vader = SentimentIntensityAnalyzer()
        self.use_llm = use_llm and ANTHROPIC_AVAILABLE
        self.claude_client = None

        # Initialize Claude client if available
        if self.use_llm:
            api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY') or os.getenv('NEWS_API_KEY')
            if api_key:
                try:
                    self.claude_client = anthropic.Anthropic(api_key=api_key)
                    logger.info("Claude LLM sentiment analysis enabled")
                except Exception as e:
                    logger.warning(f"Failed to initialize Claude client: {e}")
                    self.use_llm = False
            else:
                logger.warning("No Anthropic API key found. Set ANTHROPIC_API_KEY environment variable.")
                self.use_llm = False
        
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
        
    def analyze_text(self, text: str, method: str = 'auto') -> SentimentScore:
        """
        Analyze sentiment of a text string

        Args:
            text: Text to analyze
            method: 'auto', 'claude', 'textblob', 'vader', 'combined', or 'claude_fallback'
                   'auto' uses Claude if available, otherwise falls back to combined

        Returns:
            SentimentScore object
        """
        if not text or not text.strip():
            return SentimentScore(text, 0.0, 0.0, method)

        try:
            # Auto method: prefer Claude if available, fallback to combined
            if method == 'auto':
                if self.use_llm and self.claude_client:
                    try:
                        return self._claude_analysis(text)
                    except Exception as e:
                        logger.warning(f"Claude analysis failed, falling back to combined: {e}")
                        return self._combined_analysis(text)
                else:
                    return self._combined_analysis(text)
            elif method == 'claude':
                return self._claude_analysis(text)
            elif method == 'claude_fallback':
                # Try Claude first, fallback to combined if it fails
                try:
                    return self._claude_analysis(text)
                except Exception as e:
                    logger.debug(f"Claude analysis failed, using combined method: {e}")
                    result = self._combined_analysis(text)
                    result.method = 'claude_fallback'
                    return result
            elif method == 'textblob':
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
        data_quality = blob.sentiment.subjectivity
        
        return SentimentScore(text, sentiment_score, data_quality, 'textblob')
        
    def _vader_analysis(self, text: str) -> SentimentScore:
        """VADER sentiment analysis (better for financial text)"""
        scores = self.vader.polarity_scores(text)
        
        # VADER returns compound score (-1 to 1)
        sentiment_score = scores['compound']
        
        # Calculate data quality based on the strength of positive/negative scores
        data_quality = max(scores['pos'], scores['neg'])
        
        return SentimentScore(text, sentiment_score, data_quality, 'vader')
        
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
        
        # Combine data quality scores
        combined_data_quality = (vader_result.data_quality + textblob_result.data_quality) / 2
        
        # Ensure bounds
        combined_sentiment = max(-1.0, min(1.0, combined_sentiment))
        combined_data_quality = max(0.0, min(1.0, combined_data_quality))
        
        return SentimentScore(text, combined_sentiment, combined_data_quality, 'combined')

    def _claude_analysis(self, text: str) -> SentimentScore:
        """
        Claude LLM sentiment analysis for superior financial text understanding
        """
        if not self.claude_client:
            raise Exception("Claude client not initialized")

        # Determine the text type for appropriate prompting
        text_type = self._detect_text_type(text)

        # Create specialized prompt based on text type
        prompt = self._create_claude_prompt(text, text_type)

        try:
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",  # Fast and cost-effective
                max_tokens=200,
                temperature=0.1,  # Low temperature for consistent results
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse Claude's response
            result = self._parse_claude_response(response.content[0].text, text)
            return result

        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            raise

    def _detect_text_type(self, text: str) -> str:
        """Detect the type of financial text for appropriate prompting"""
        text_lower = text.lower()

        if any(term in text_lower for term in ['reddit', 'comment', 'wsb', 'stonks', 'ape', 'diamond hands', 'to the moon']):
            return 'social_media'
        elif any(term in text_lower for term in ['earnings', 'quarterly', 'revenue', 'eps', 'guidance', 'analyst']):
            return 'earnings_news'
        elif any(term in text_lower for term in ['sec filing', '10-k', '10-q', 'proxy', 'form']):
            return 'regulatory_filing'
        elif any(term in text_lower for term in ['fed', 'interest rate', 'inflation', 'gdp', 'unemployment']):
            return 'macro_economic'
        else:
            return 'general_financial'

    def _create_claude_prompt(self, text: str, text_type: str) -> str:
        """Create specialized prompts for different types of financial text"""

        base_instruction = """You are a financial sentiment analysis expert. Analyze the following text and provide a sentiment score.

Return your response in this exact JSON format:
{
    "sentiment_score": <float between -1.0 and 1.0>,
    "confidence": <float between 0.0 and 1.0>,
    "reasoning": "<brief explanation of sentiment factors>"
}

Where:
- sentiment_score: -1.0 = very negative, 0.0 = neutral, 1.0 = very positive
- confidence: How confident you are in this assessment
- reasoning: Key factors that influenced the sentiment

"""

        if text_type == 'social_media':
            specific_instruction = """This is social media content (Reddit/Twitter). Consider:
- Sarcasm, memes, and informal language
- Retail investor sentiment and speculation
- Community sentiment and herd mentality
- Emojis and slang (🚀, 💎, 🦍, HODL, etc.)
"""
        elif text_type == 'earnings_news':
            specific_instruction = """This is earnings/financial news. Consider:
- Actual vs expected performance
- Forward guidance and outlook
- Management commentary tone
- Market impact and implications
"""
        elif text_type == 'regulatory_filing':
            specific_instruction = """This is regulatory/SEC filing content. Consider:
- Risk factors and legal language
- Business outlook and strategy
- Compliance and governance issues
- Material changes or disclosures
"""
        elif text_type == 'macro_economic':
            specific_instruction = """This is macroeconomic news. Consider:
- Federal Reserve policy implications
- Economic indicators and trends
- Market-wide impact potential
- Sector-specific effects
"""
        else:
            specific_instruction = """This is general financial content. Consider:
- Overall market sentiment
- Company-specific factors
- Industry trends and competition
- Investment implications
"""

        return f"{base_instruction}\n{specific_instruction}\n\nText to analyze:\n\"{text}\""

    def _parse_claude_response(self, response: str, original_text: str) -> SentimentScore:
        """Parse Claude's JSON response into SentimentScore object"""
        try:
            # Extract JSON from response (in case there's extra text)
            import json
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")

            sentiment_score = float(data.get('sentiment_score', 0.0))
            confidence = float(data.get('confidence', 0.5))
            reasoning = data.get('reasoning', 'No reasoning provided')

            # Ensure bounds
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            confidence = max(0.0, min(1.0, confidence))

            return SentimentScore(
                text=original_text,
                sentiment_score=sentiment_score,
                data_quality=confidence,  # Use confidence as data quality
                method='claude',
                confidence=confidence,
                reasoning=reasoning
            )

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse Claude response: {e}. Response: {response}")
            # Fallback: try to extract just the number
            try:
                import re
                numbers = re.findall(r'-?\d+\.?\d*', response)
                if numbers:
                    sentiment_score = max(-1.0, min(1.0, float(numbers[0])))
                    return SentimentScore(original_text, sentiment_score, 0.3, 'claude', 0.3, "Parsed from malformed response")
            except:
                pass

            # Final fallback
            return SentimentScore(original_text, 0.0, 0.1, 'claude', 0.1, f"Parse error: {str(e)}")

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
                'data_quality': 0.0,
                'headline_count': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0
            }
            
        try:
            sentiments = []
            data_qualities = []
            
            for headline in headlines:
                # Combine title and summary for analysis
                text = f"{headline.get('title', '')} {headline.get('summary', '')}"
                
                if text.strip():
                    result = self.analyze_text(text)
                    sentiments.append(result.sentiment_score)
                    data_qualities.append(result.data_quality)
                    
            if not sentiments:
                return self.analyze_news_headlines([])  # Return empty result
                
            # Calculate aggregate metrics
            sentiments_series = pd.Series(sentiments)
            
            avg_sentiment = sentiments_series.mean()
            sentiment_std = sentiments_series.std()
            avg_data_quality = pd.Series(data_qualities).mean()
            
            # Count sentiment categories
            positive_count = sum(1 for s in sentiments if s > 0.1)
            negative_count = sum(1 for s in sentiments if s < -0.1)
            neutral_count = len(sentiments) - positive_count - negative_count
            
            return {
                'avg_sentiment': float(avg_sentiment),
                'sentiment_std': float(sentiment_std) if not pd.isna(sentiment_std) else 0.0,
                'data_quality': float(avg_data_quality),
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
                'data_quality': 0.0,
                'post_count': 0,
                'total_score': 0,
                'avg_score': 0.0
            }
            
        try:
            sentiments = []
            data_qualities = []
            scores = []
            weighted_sentiments = []
            
            for post in posts:
                # Combine title and text for analysis
                text = f"{post.get('title', '')} {post.get('text', '')}"
                post_score = post.get('score', 0)
                
                if text.strip():
                    result = self.analyze_text(text)
                    
                    sentiments.append(result.sentiment_score)
                    data_qualities.append(result.data_quality)
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
            avg_data_quality = pd.Series(data_qualities).mean()
            
            return {
                'avg_sentiment': float(avg_sentiment),
                'weighted_sentiment': float(weighted_sentiment),
                'data_quality': float(avg_data_quality),
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
                combined_data_quality = (news_sentiment['data_quality'] * 0.6 + 
                                     reddit_sentiment['data_quality'] * 0.4)
            else:
                combined_sentiment = news_sentiment['avg_sentiment']
                combined_data_quality = news_sentiment['data_quality']
                
            return {
                # Combined metrics
                'combined_sentiment': combined_sentiment,
                'combined_data_quality': combined_data_quality,
                
                # News metrics
                'news_sentiment': news_sentiment['avg_sentiment'],
                'news_data_quality': news_sentiment['data_quality'],
                'news_count': news_sentiment['headline_count'],
                'news_positive': news_sentiment['positive_count'],
                'news_negative': news_sentiment['negative_count'],
                
                # Reddit metrics
                'reddit_sentiment': reddit_sentiment.get('weighted_sentiment', 0.0),
                'reddit_data_quality': reddit_sentiment.get('data_quality', 0.0),
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
                'combined_data_quality': 0.0,
                'news_sentiment': 0.0,
                'news_data_quality': 0.0,
                'news_count': 0,
                'reddit_sentiment': 0.0,
                'reddit_data_quality': 0.0,
                'reddit_count': 0,
                'analysis_date': datetime.now().isoformat(),
                'symbol': stock_data.symbol
            }