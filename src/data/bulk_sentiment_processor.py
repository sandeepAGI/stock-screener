#!/usr/bin/env python3
"""
Bulk Sentiment Processing using Anthropic's Message Batches API

This module implements efficient bulk sentiment analysis for news articles and Reddit posts
using Anthropic's Message Batches API, which provides:
- 50% cost reduction compared to individual API calls
- Massive speed improvements (6x faster)
- Processing up to 10,000 requests per batch
- Completion within 1 hour for most batches

Performance comparison:
- Individual calls: 500 stocks × 30 items = 15,000 calls = 6+ hours
- Batch processing: Same data in 1 batch = <1 hour + 50% cost savings
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import os

# Anthropic API
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from src.data.sentiment_analyzer import SentimentScore

logger = logging.getLogger(__name__)

@dataclass
class BatchSentimentRequest:
    """Container for a single sentiment analysis request in a batch"""
    custom_id: str
    text: str
    text_type: str  # 'news' or 'reddit'
    metadata: Dict[str, Any]  # Additional context (symbol, article_id, etc.)

@dataclass
class BatchSentimentResult:
    """Container for sentiment analysis results from batch processing"""
    custom_id: str
    sentiment_score: float
    confidence: float
    method: str
    success: bool
    error: Optional[str] = None

class BulkSentimentProcessor:
    """
    Efficient bulk sentiment processing using Anthropic's Message Batches API
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize bulk sentiment processor

        Args:
            anthropic_api_key: Anthropic API key (or from environment)
        """
        self.api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')

        if not self.api_key:
            logger.warning("No Anthropic API key provided - bulk processing disabled")
            self.client = None
        else:
            if ANTHROPIC_AVAILABLE:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("✅ Anthropic client initialized for bulk processing")
            else:
                logger.error("❌ Anthropic library not available - install anthropic package")
                self.client = None

    def create_sentiment_prompt(self, text: str, text_type: str) -> str:
        """
        Create specialized sentiment analysis prompt for different text types

        Args:
            text: Text to analyze
            text_type: Type of text ('news' or 'reddit')

        Returns:
            Formatted prompt string
        """
        base_instruction = """You are a financial sentiment analysis expert. Analyze the following text and provide a sentiment score.

Return your response in this exact JSON format:
{
    "sentiment_score": <float between -1.0 and 1.0>,
    "confidence": <float between 0.0 and 1.0>
}

Where:
- sentiment_score: -1.0 = very negative, 0.0 = neutral, 1.0 = very positive
- confidence: How confident you are in this assessment

"""

        if text_type == 'reddit':
            specific_instruction = """This is social media content (Reddit). Consider:
- Sarcasm, memes, and informal language
- Retail investor sentiment and speculation
- Community sentiment and herd mentality
- Emojis and slang (🚀, 💎, 🦍, HODL, etc.)
"""
        elif text_type == 'news':
            specific_instruction = """This is financial news content. Consider:
- Professional journalism standards
- Factual reporting vs opinion
- Market impact and implications
- Forward-looking statements and guidance
"""
        else:
            specific_instruction = ""

        return f"{base_instruction}\n{specific_instruction}\nText to analyze: {text}"

    def prepare_batch_requests(self,
                             news_articles: List[Tuple[str, str, str, Any]] = None,
                             reddit_posts: List[Tuple[str, str, str, Any]] = None) -> List[BatchSentimentRequest]:
        """
        Prepare sentiment analysis requests for batch processing

        Args:
            news_articles: List of (symbol, title, summary, metadata) tuples
            reddit_posts: List of (symbol, title, content, metadata) tuples

        Returns:
            List of BatchSentimentRequest objects
        """
        requests = []

        # Process news articles
        if news_articles:
            for symbol, title, summary, metadata in news_articles:
                text = f"{title}. {summary or ''}"
                custom_id = f"news_{symbol}_{len(requests)}"

                requests.append(BatchSentimentRequest(
                    custom_id=custom_id,
                    text=text,
                    text_type='news',
                    metadata={
                        'symbol': symbol,
                        'type': 'news',
                        **metadata
                    }
                ))

        # Process Reddit posts
        if reddit_posts:
            for symbol, title, content, metadata in reddit_posts:
                text = f"{title}. {content or ''}"
                custom_id = f"reddit_{symbol}_{len(requests)}"

                requests.append(BatchSentimentRequest(
                    custom_id=custom_id,
                    text=text,
                    text_type='reddit',
                    metadata={
                        'symbol': symbol,
                        'type': 'reddit',
                        **metadata
                    }
                ))

        logger.info(f"📦 Prepared {len(requests)} sentiment analysis requests for batch processing")
        return requests

    def create_anthropic_batch(self, requests: List[BatchSentimentRequest]) -> Optional[str]:
        """
        Create and submit batch to Anthropic's Message Batches API

        Args:
            requests: List of sentiment analysis requests

        Returns:
            Batch ID if successful, None if failed
        """
        if not self.client:
            logger.error("❌ Anthropic client not available")
            return None

        if len(requests) > 10000:
            logger.error(f"❌ Too many requests ({len(requests)}) - maximum is 10,000 per batch")
            return None

        try:
            # Convert requests to Anthropic batch format
            batch_messages = []

            for request in requests:
                prompt = self.create_sentiment_prompt(request.text, request.text_type)

                batch_messages.append({
                    "custom_id": request.custom_id,
                    "method": "POST",
                    "url": "/v1/messages",
                    "body": {
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 150,
                        "temperature": 0.1,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    }
                })

            # Submit batch
            logger.info(f"🚀 Submitting batch with {len(batch_messages)} requests to Anthropic...")
            batch_response = self.client.message_batches.create(requests=batch_messages)

            logger.info(f"✅ Batch submitted successfully! Batch ID: {batch_response.id}")
            logger.info(f"📊 Status: {batch_response.processing_status}")
            logger.info(f"⏱️  Expected completion: <1 hour (usually much faster)")

            return batch_response.id

        except Exception as e:
            logger.error(f"❌ Failed to create Anthropic batch: {str(e)}")
            return None

    def poll_batch_completion(self, batch_id: str, max_wait_minutes: int = 120) -> Optional[Dict]:
        """
        Poll batch status until completion

        Args:
            batch_id: Batch ID to monitor
            max_wait_minutes: Maximum time to wait in minutes

        Returns:
            Batch results or None if failed/timeout
        """
        if not self.client:
            logger.error("❌ Anthropic client not available")
            return None

        start_time = datetime.now()
        max_wait_time = timedelta(minutes=max_wait_minutes)

        logger.info(f"⏳ Polling batch {batch_id} for completion...")

        while datetime.now() - start_time < max_wait_time:
            try:
                batch_status = self.client.message_batches.get(batch_id)
                status = batch_status.processing_status

                logger.info(f"📊 Batch status: {status}")

                if status == "ended":
                    logger.info("✅ Batch completed successfully!")
                    return batch_status.results
                elif status in ["failed", "expired", "cancelled"]:
                    logger.error(f"❌ Batch failed with status: {status}")
                    return None
                elif status in ["validating", "processing"]:
                    # Still processing - wait and check again
                    time.sleep(30)  # Check every 30 seconds
                else:
                    logger.warning(f"⚠️  Unknown batch status: {status}")
                    time.sleep(30)

            except Exception as e:
                logger.error(f"❌ Error checking batch status: {str(e)}")
                time.sleep(60)  # Wait longer on error

        logger.error(f"❌ Batch timed out after {max_wait_minutes} minutes")
        return None

    def parse_batch_results(self, batch_results: Dict,
                          original_requests: List[BatchSentimentRequest]) -> List[BatchSentimentResult]:
        """
        Parse results from completed batch

        Args:
            batch_results: Raw results from Anthropic batch API
            original_requests: Original requests for metadata

        Returns:
            List of parsed sentiment results
        """
        results = []
        request_lookup = {req.custom_id: req for req in original_requests}

        logger.info(f"🔍 Parsing {len(batch_results)} batch results...")

        for result in batch_results:
            custom_id = result.get('custom_id')
            if not custom_id:
                continue

            original_request = request_lookup.get(custom_id)
            if not original_request:
                logger.warning(f"⚠️  No original request found for {custom_id}")
                continue

            try:
                # Extract response content
                response_body = result.get('response', {}).get('body', {})
                content = response_body.get('content', [])

                if not content:
                    results.append(BatchSentimentResult(
                        custom_id=custom_id,
                        sentiment_score=0.0,
                        confidence=0.1,
                        method='batch_error',
                        success=False,
                        error="No content in response"
                    ))
                    continue

                # Parse JSON response
                text_content = content[0].get('text', '')
                sentiment_data = self._parse_sentiment_json(text_content)

                if sentiment_data:
                    results.append(BatchSentimentResult(
                        custom_id=custom_id,
                        sentiment_score=sentiment_data['sentiment_score'],
                        confidence=sentiment_data['confidence'],
                        method='batch_claude',
                        success=True
                    ))
                else:
                    results.append(BatchSentimentResult(
                        custom_id=custom_id,
                        sentiment_score=0.0,
                        confidence=0.1,
                        method='batch_parse_error',
                        success=False,
                        error="Failed to parse sentiment JSON"
                    ))

            except Exception as e:
                logger.warning(f"⚠️  Error parsing result for {custom_id}: {str(e)}")
                results.append(BatchSentimentResult(
                    custom_id=custom_id,
                    sentiment_score=0.0,
                    confidence=0.1,
                    method='batch_error',
                    success=False,
                    error=str(e)
                ))

        success_count = sum(1 for r in results if r.success)
        logger.info(f"✅ Successfully parsed {success_count}/{len(results)} batch results")

        return results

    def _parse_sentiment_json(self, response_text: str) -> Optional[Dict]:
        """
        Parse sentiment JSON from Claude response (reuses logic from sentiment_analyzer.py)

        Args:
            response_text: Raw response text from Claude

        Returns:
            Parsed sentiment data or None
        """
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)

                sentiment_score = max(-1.0, min(1.0, float(data.get('sentiment_score', 0.0))))
                confidence = max(0.0, min(1.0, float(data.get('confidence', 0.5))))

                return {
                    'sentiment_score': sentiment_score,
                    'confidence': confidence
                }

            # Fallback: extract using regex
            import re
            sentiment_match = re.search(r'"sentiment_score":\s*([0-9.-]+)', response_text)
            confidence_match = re.search(r'"confidence":\s*([0-9.-]+)', response_text)

            if sentiment_match:
                sentiment_score = max(-1.0, min(1.0, float(sentiment_match.group(1))))
                confidence = max(0.0, min(1.0, float(confidence_match.group(1)))) if confidence_match else 0.5

                return {
                    'sentiment_score': sentiment_score,
                    'confidence': confidence
                }

        except Exception as e:
            logger.warning(f"⚠️  Failed to parse sentiment JSON: {str(e)}")

        return None

    def process_bulk_sentiment(self,
                             news_articles: List[Tuple[str, str, str, Any]] = None,
                             reddit_posts: List[Tuple[str, str, str, Any]] = None) -> Dict[str, List[BatchSentimentResult]]:
        """
        Complete end-to-end bulk sentiment processing

        Args:
            news_articles: List of (symbol, title, summary, metadata) tuples
            reddit_posts: List of (symbol, title, content, metadata) tuples

        Returns:
            Dictionary mapping symbols to their sentiment results
        """
        if not self.client:
            logger.error("❌ Bulk processing not available - falling back to individual processing")
            return {}

        # Prepare batch requests
        requests = self.prepare_batch_requests(news_articles, reddit_posts)
        if not requests:
            logger.warning("⚠️  No requests to process")
            return {}

        # Submit batch
        batch_id = self.create_anthropic_batch(requests)
        if not batch_id:
            logger.error("❌ Failed to create batch")
            return {}

        # Wait for completion
        batch_results = self.poll_batch_completion(batch_id)
        if not batch_results:
            logger.error("❌ Batch processing failed or timed out")
            return {}

        # Parse results
        parsed_results = self.parse_batch_results(batch_results, requests)

        # Group by symbol
        symbol_results = {}
        for result in parsed_results:
            # Extract symbol from custom_id (format: "news_SYMBOL_index" or "reddit_SYMBOL_index")
            parts = result.custom_id.split('_')
            if len(parts) >= 2:
                symbol = parts[1]
                if symbol not in symbol_results:
                    symbol_results[symbol] = []
                symbol_results[symbol].append(result)

        logger.info(f"🎉 Bulk sentiment processing completed for {len(symbol_results)} symbols")
        return symbol_results