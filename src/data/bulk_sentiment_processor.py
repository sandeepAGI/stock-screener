#!/usr/bin/env python3
"""
Bulk Sentiment Processing using Anthropic's Message Batches API

This module implements efficient bulk sentiment analysis for news articles and Reddit posts
using Anthropic's Message Batches API, which provides:
- 50% cost reduction compared to individual API calls
- Processing up to 100,000 requests per batch
- Completion within 1 hour for most batches

Performance comparison:
- Individual calls: 24,499 items = 24,499 calls = 6+ hours + full cost
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
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
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

    def __init__(self, anthropic_api_key: Optional[str] = None, api_key_manager=None):
        """
        Initialize bulk sentiment processor

        Args:
            anthropic_api_key: Anthropic API key (fallback for development)
            api_key_manager: APIKeyManager instance for user-provided credentials
        """
        self.api_key_manager = api_key_manager

        # Get API key from manager first, then fallback to parameter/env
        self.api_key = None
        if api_key_manager:
            from src.utils.api_key_manager import APIKeyManager
            if api_key_manager.has_claude_credentials():
                self.api_key = api_key_manager.get_api_key(APIKeyManager.CLAUDE_API_KEY)
                logger.info("Using Claude API key from API Key Manager for bulk processing")

        # Fallback to .env for development/testing
        if not self.api_key:
            self.api_key = anthropic_api_key or os.getenv('NEWS_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
            if self.api_key:
                logger.info("Using Claude API key from .env for bulk processing (development mode)")

        if not self.api_key:
            logger.error("❌ No Anthropic API key provided - bulk processing requires API key")
            raise ValueError("Claude API key must be configured in API Key Manager or environment variables")

        if not ANTHROPIC_AVAILABLE:
            logger.error("❌ Anthropic library not available - install anthropic package")
            raise ImportError("Anthropic library required: pip install anthropic")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info("✅ Anthropic client initialized for bulk processing")

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
                          metadata should contain 'record_id' for database ID
            reddit_posts: List of (symbol, title, content, metadata) tuples
                         metadata should contain 'record_id' for database ID

        Returns:
            List of BatchSentimentRequest objects
        """
        requests = []

        # Process news articles
        if news_articles:
            for symbol, title, summary, metadata in news_articles:
                text = f"{title}. {summary or ''}"

                # Use database ID if provided, otherwise fall back to index
                record_id = metadata.get('record_id') if metadata else None
                if record_id:
                    custom_id = f"news_id_{record_id}"
                else:
                    # Fallback for backward compatibility
                    custom_id = f"news_{symbol}_{len(requests)}"
                    logger.warning(f"No record_id provided for news article, using index-based ID: {custom_id}")

                requests.append(BatchSentimentRequest(
                    custom_id=custom_id,
                    text=text,
                    text_type='news',
                    metadata={
                        'symbol': symbol,
                        'type': 'news',
                        'table': 'news_articles',
                        'record_id': record_id,
                        **(metadata if metadata else {})
                    }
                ))

        # Process Reddit posts
        if reddit_posts:
            for symbol, title, content, metadata in reddit_posts:
                text = f"{title}. {content or ''}"

                # Use database ID if provided, otherwise fall back to index
                record_id = metadata.get('record_id') if metadata else None
                if record_id:
                    custom_id = f"reddit_id_{record_id}"
                else:
                    # Fallback for backward compatibility
                    custom_id = f"reddit_{symbol}_{len(requests)}"
                    logger.warning(f"No record_id provided for reddit post, using index-based ID: {custom_id}")

                requests.append(BatchSentimentRequest(
                    custom_id=custom_id,
                    text=text,
                    text_type='reddit',
                    metadata={
                        'symbol': symbol,
                        'type': 'reddit',
                        'table': 'reddit_posts',
                        'record_id': record_id,
                        **(metadata if metadata else {})
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
        if len(requests) > 100000:
            logger.error(f"❌ Too many requests ({len(requests)}) - maximum is 100,000 per batch")
            return None

        try:
            # Convert requests to Anthropic batch format
            batch_requests = []

            for request in requests:
                prompt = self.create_sentiment_prompt(request.text, request.text_type)

                batch_requests.append(Request(
                    custom_id=request.custom_id,
                    params=MessageCreateParamsNonStreaming(
                        model="claude-3-haiku-20240307",
                        max_tokens=150,
                        temperature=0.1,
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    )
                ))

            # Submit batch
            logger.info(f"🚀 Submitting batch with {len(batch_requests)} requests to Anthropic...")
            batch_response = self.client.messages.batches.create(requests=batch_requests)

            logger.info(f"✅ Batch submitted successfully! Batch ID: {batch_response.id}")
            logger.info(f"📊 Status: {batch_response.processing_status}")
            logger.info(f"⏱️  Expected completion: <1 hour")

            return batch_response.id

        except Exception as e:
            logger.error(f"❌ Failed to create Anthropic batch: {str(e)}")
            return None

    def poll_batch_completion(self, batch_id: str, max_wait_minutes: int = 120) -> Optional[List]:
        """
        Poll batch status until completion

        Args:
            batch_id: Batch ID to monitor
            max_wait_minutes: Maximum time to wait in minutes

        Returns:
            Batch results or None if failed/timeout
        """
        start_time = datetime.now()
        max_wait_time = timedelta(minutes=max_wait_minutes)

        logger.info(f"⏳ Polling batch {batch_id} for completion...")

        while datetime.now() - start_time < max_wait_time:
            try:
                batch_status = self.client.messages.batches.retrieve(batch_id)
                status = batch_status.processing_status

                logger.info(f"📊 Batch status: {status}")

                if status == "ended":
                    logger.info("✅ Batch completed successfully!")
                    # Retrieve results
                    results = list(self.client.messages.batches.results(batch_id))
                    return results
                elif status in ["failed", "expired", "cancelled"]:
                    logger.error(f"❌ Batch failed with status: {status}")
                    return None
                elif status == "in_progress":
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

    def parse_batch_results(self, batch_results: List,
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
            custom_id = result.custom_id
            if not custom_id:
                continue

            original_request = request_lookup.get(custom_id)
            if not original_request:
                logger.warning(f"⚠️  No original request found for {custom_id}")
                continue

            try:
                # Check if request succeeded
                if result.result.type == "succeeded":
                    # Extract response content
                    content = result.result.message.content[0].text

                    # Parse JSON response
                    sentiment_data = self._parse_sentiment_json(content)

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
                else:
                    # Request failed
                    error_msg = getattr(result.result, 'error', 'Unknown error')
                    results.append(BatchSentimentResult(
                        custom_id=custom_id,
                        sentiment_score=0.0,
                        confidence=0.1,
                        method='batch_error',
                        success=False,
                        error=str(error_msg)
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
        Parse sentiment JSON from Claude response

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

    def submit_batch_for_processing(self,
                                   news_articles: List[Tuple[str, str, str, Any]] = None,
                                   reddit_posts: List[Tuple[str, str, str, Any]] = None) -> Optional[Tuple[str, List[BatchSentimentRequest]]]:
        """
        Submit batch for asynchronous processing

        Args:
            news_articles: List of (symbol, title, summary, metadata) tuples
            reddit_posts: List of (symbol, title, content, metadata) tuples

        Returns:
            Tuple of (batch_id, requests) if successful, None if failed
        """
        # Prepare batch requests
        requests = self.prepare_batch_requests(news_articles, reddit_posts)
        if not requests:
            logger.warning("⚠️  No requests to process")
            return None

        # Submit batch
        batch_id = self.create_anthropic_batch(requests)
        if not batch_id:
            logger.error("❌ Failed to create batch")
            return None

        logger.info(f"✅ Batch {batch_id} submitted successfully")
        return batch_id, requests

    def check_batch_status(self, batch_id: str) -> Optional[str]:
        """
        Check the status of a submitted batch

        Args:
            batch_id: Batch ID to check

        Returns:
            Status string or None if error
        """
        try:
            batch_status = self.client.messages.batches.retrieve(batch_id)
            return batch_status.processing_status
        except Exception as e:
            logger.error(f"❌ Error checking batch status: {str(e)}")
            return None

    def retrieve_batch_results(self, batch_id: str) -> Optional[List]:
        """
        Retrieve results from a completed batch

        Args:
            batch_id: Batch ID to retrieve results for

        Returns:
            List of raw batch results or None if failed
        """
        try:
            # Check if batch is complete
            status = self.check_batch_status(batch_id)
            if status != "ended":
                logger.error(f"❌ Batch not ready. Status: {status}")
                return None

            # Retrieve results
            results = list(self.client.messages.batches.results(batch_id))
            logger.info(f"✅ Retrieved {len(results)} results from batch {batch_id}")
            return results
        except Exception as e:
            logger.error(f"❌ Error retrieving batch results: {str(e)}")
            return None

    def process_bulk_sentiment(self,
                             news_articles: List[Tuple[str, str, str, Any]] = None,
                             reddit_posts: List[Tuple[str, str, str, Any]] = None) -> Dict[str, List[BatchSentimentResult]]:
        """
        Complete end-to-end bulk sentiment processing (synchronous)

        This method is kept for backward compatibility but now uses the new async methods internally.

        Args:
            news_articles: List of (symbol, title, summary, metadata) tuples
            reddit_posts: List of (symbol, title, content, metadata) tuples

        Returns:
            Dictionary mapping symbols to their sentiment results
        """
        # Submit batch
        submission_result = self.submit_batch_for_processing(news_articles, reddit_posts)
        if not submission_result:
            return {}

        batch_id, requests = submission_result

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
            # Extract symbol from metadata or custom_id
            metadata = next((req.metadata for req in requests if req.custom_id == result.custom_id), {})
            symbol = metadata.get('symbol')

            if symbol:
                if symbol not in symbol_results:
                    symbol_results[symbol] = []
                symbol_results[symbol].append(result)

        logger.info(f"🎉 Bulk sentiment processing completed for {len(symbol_results)} symbols")
        return symbol_results