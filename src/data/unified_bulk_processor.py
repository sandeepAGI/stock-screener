#!/usr/bin/env python3
"""
Unified Bulk Sentiment Processor

This module implements unified bulk sentiment analysis using the temporary table approach.
Instead of creating hundreds of separate batch requests per symbol, this processor:
1. Populates temporary sentiment queue with all pending items
2. Processes items in optimized batches (up to 10,000 per batch)
3. Updates results back to original tables
4. Provides audit trail and resumability

Performance: Processes 24,499 items in 3 batches vs 24,499 individual calls (8,166x efficiency)
"""

import logging
import time
import os
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import json

from src.data.database import DatabaseManager
from src.data.bulk_sentiment_processor import BulkSentimentProcessor, BatchSentimentRequest

logger = logging.getLogger(__name__)

class UnifiedBulkProcessor:
    """
    Unified bulk sentiment processor using temporary table approach for efficient processing
    """

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """
        Initialize unified bulk processor

        Args:
            anthropic_api_key: Required Anthropic API key for Claude LLM processing
        """
        self.db = DatabaseManager()

        # Require API key - no fallback processing
        api_key = anthropic_api_key or os.getenv('NEWS_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            logger.error("❌ Anthropic API key is required for bulk sentiment processing")
            raise ValueError("NEWS_API_KEY or ANTHROPIC_API_KEY environment variable or parameter is required")

        self.bulk_processor = BulkSentimentProcessor(api_key)
        self.batch_size = 25000  # Process all items in single batch (within 100k limit)

    def get_processing_status(self) -> Dict:
        """
        Get current processing status and statistics

        Returns:
            Dictionary with processing status information
        """
        if not self.db.connect():
            return {"error": "Database connection failed"}

        try:
            stats = self.db.get_sentiment_queue_statistics()
            return {
                "queue_populated": stats['total_items'] > 0,
                "total_items": stats['total_items'],
                "pending_items": stats['pending_count'],
                "processing_items": stats.get('processing_count', 0),
                "completed_items": stats.get('completed_count', 0),
                "failed_items": stats.get('failed_count', 0),
                "estimated_batches": stats['estimated_batches_needed'],
                "within_single_batch": stats['within_single_batch_limit'],
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting processing status: {str(e)}")
            return {"error": str(e)}
        finally:
            self.db.close()

    def populate_sentiment_queue(self) -> Dict:
        """
        Populate temporary sentiment queue with all pending items

        Returns:
            Results of population operation
        """
        if not self.db.connect():
            return {"success": False, "error": "Database connection failed"}

        try:
            logger.info("🔄 Populating sentiment queue with existing data...")
            total_items = self.db.populate_sentiment_queue_from_existing_data()

            if total_items == 0:
                return {
                    "success": True,
                    "message": "No items found requiring sentiment analysis",
                    "total_items": 0
                }

            logger.info(f"✅ Populated sentiment queue with {total_items} items")
            return {
                "success": True,
                "message": f"Successfully populated queue with {total_items} items",
                "total_items": total_items
            }

        except Exception as e:
            logger.error(f"❌ Error populating sentiment queue: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            self.db.close()

    def process_next_batch(self) -> Dict:
        """
        Process the next batch of items from the sentiment queue

        Returns:
            Results of batch processing operation
        """
        if not self.db.connect():
            return {"success": False, "error": "Database connection failed"}

        try:
            # Get next batch of pending items
            logger.info(f"📦 Getting next batch of {self.batch_size} items...")
            batch_items = self.db.get_pending_sentiment_batch(self.batch_size)

            if not batch_items:
                return {
                    "success": True,
                    "message": "No pending items to process",
                    "processed_count": 0
                }

            batch_id = f"batch_{int(time.time())}"
            logger.info(f"🚀 Processing batch {batch_id} with {len(batch_items)} items...")

            # Mark items as processing - items are already dictionaries with custom_id
            self.db.mark_sentiment_batch_processing(batch_items, batch_id)

            # Process with Claude LLM bulk processing
            return self._process_batch_with_claude(batch_items, batch_id)

        except Exception as e:
            logger.error(f"❌ Error processing batch: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            self.db.close()

    def _process_batch_with_claude(self, batch_items: List, batch_id: str) -> Dict:
        """
        Process batch using Claude LLM bulk API

        Args:
            batch_items: List of database items to process
            batch_id: Unique batch identifier

        Returns:
            Processing results
        """
        try:
            # Prepare requests for Claude bulk processing
            news_articles = []
            reddit_posts = []

            for item in batch_items:
                symbol = item['symbol']
                content_type = item['content_type']
                text_content = item['text_content']
                queue_id = item['queue_id']
                content_id = item['content_id']

                # Split text_content into title and content (assuming format: "title. content")
                parts = text_content.split('. ', 1)
                title = parts[0] if parts else text_content
                content = parts[1] if len(parts) > 1 else ''

                if content_type == 'news':
                    news_articles.append((symbol, title, content, {
                        'queue_id': queue_id,
                        'record_id': content_id,  # This is the actual news_articles.id
                        'content_id': content_id
                    }))
                elif content_type == 'reddit':
                    reddit_posts.append((symbol, title, content, {
                        'queue_id': queue_id,
                        'record_id': content_id,  # This is the actual reddit_posts.id
                        'content_id': content_id
                    }))

            logger.info(f"🤖 Processing {len(news_articles)} news articles and {len(reddit_posts)} Reddit posts with Claude...")

            # Submit batch for processing (asynchronous)
            submission_result = self.bulk_processor.submit_batch_for_processing(
                news_articles=news_articles if news_articles else None,
                reddit_posts=reddit_posts if reddit_posts else None
            )

            if not submission_result:
                logger.error("❌ Failed to submit batch for processing")
                return {"success": False, "error": "Failed to submit batch for processing"}

            anthropic_batch_id, requests = submission_result

            # Store batch mapping for tracking
            self._store_batch_mapping(anthropic_batch_id, requests)

            logger.info(f"✅ Batch {anthropic_batch_id} submitted successfully")

            return {
                "success": True,
                "message": f"Batch submitted for processing with {len(batch_items)} items",
                "processed_count": len(batch_items),
                "batch_id": batch_id,
                "anthropic_batch_id": anthropic_batch_id,
                "status": "submitted",
                "method": "claude_bulk_async"
            }

        except Exception as e:
            logger.error(f"❌ Error in Claude bulk processing: {str(e)}")
            return {"success": False, "error": str(e)}

    def _store_batch_mapping(self, batch_id: str, requests: List) -> None:
        """
        Store batch mapping in database for tracking

        Args:
            batch_id: Anthropic batch ID
            requests: List of BatchSentimentRequest objects
        """
        try:
            # Ensure database connection
            if not self.db.connect():
                logger.error("❌ Failed to connect to database for storing batch mapping")
                return

            cursor = self.db.connection.cursor()

            for request in requests:
                # Extract table and record_id from custom_id
                custom_id = request.custom_id
                metadata = request.metadata

                if custom_id.startswith('news_id_'):
                    table_name = 'news_articles'
                    record_id = int(custom_id.replace('news_id_', ''))
                elif custom_id.startswith('reddit_id_'):
                    table_name = 'reddit_posts'
                    record_id = int(custom_id.replace('reddit_id_', ''))
                else:
                    # Fallback for old format
                    table_name = metadata.get('table', '')
                    record_id = metadata.get('record_id', 0)

                cursor.execute("""
                    INSERT INTO batch_mapping
                    (batch_id, custom_id, record_type, record_id, symbol, status)
                    VALUES (?, ?, ?, ?, ?, 'submitted')
                """, (
                    batch_id,
                    custom_id,
                    table_name,
                    record_id,
                    metadata.get('symbol', '')
                ))

            self.db.connection.commit()
            cursor.close()
            self.db.close()
            logger.info(f"📊 Stored {len(requests)} batch mappings for batch {batch_id}")

        except Exception as e:
            logger.error(f"❌ Error storing batch mapping: {str(e)}")
            if self.db.connection:
                self.db.close()

    def check_batch_status(self, batch_id: str) -> Dict:
        """
        Check the status of a submitted batch

        Args:
            batch_id: Anthropic batch ID

        Returns:
            Status information
        """
        try:
            status = self.bulk_processor.check_batch_status(batch_id)

            if not status:
                return {"success": False, "error": "Failed to check batch status"}

            # Get counts from batch_mapping
            if self.db.connect():
                cursor = self.db.connection.cursor()
                cursor.execute("""
                    SELECT status, COUNT(*)
                    FROM batch_mapping
                    WHERE batch_id = ?
                    GROUP BY status
                """, (batch_id,))
                status_counts = dict(cursor.fetchall())
                cursor.close()
                self.db.close()
            else:
                status_counts = {}

            return {
                "success": True,
                "batch_id": batch_id,
                "status": status,
                "submitted_count": status_counts.get('submitted', 0),
                "completed_count": status_counts.get('completed', 0),
                "failed_count": status_counts.get('failed', 0)
            }

        except Exception as e:
            logger.error(f"❌ Error checking batch status: {str(e)}")
            return {"success": False, "error": str(e)}

    def retrieve_and_process_batch_results(self, batch_id: str) -> Dict:
        """
        Retrieve and process results from a completed batch

        Args:
            batch_id: Anthropic batch ID

        Returns:
            Processing results
        """
        try:
            # Retrieve results from Anthropic
            batch_results = self.bulk_processor.retrieve_batch_results(batch_id)

            if not batch_results:
                return {"success": False, "error": "Failed to retrieve batch results"}

            if not self.db.connect():
                return {"success": False, "error": "Database connection failed"}

            # Process results
            successful_updates = 0
            failed_updates = 0
            cursor = self.db.connection.cursor()

            for result in batch_results:
                try:
                    custom_id = result.custom_id

                    if result.result.type == "succeeded":
                        # Parse sentiment from response
                        content = result.result.message.content[0].text
                        sentiment_data = self._parse_sentiment_json(content)

                        if sentiment_data:
                            # Update batch_mapping (only status and timestamp, no sentiment columns)
                            cursor.execute("""
                                UPDATE batch_mapping
                                SET status = 'completed',
                                    processed_at = CURRENT_TIMESTAMP
                                WHERE batch_id = ? AND custom_id = ?
                            """, (
                                batch_id,
                                custom_id
                            ))

                            # Apply to original table
                            if custom_id.startswith('news_id_'):
                                record_id = int(custom_id.replace('news_id_', ''))
                                cursor.execute("""
                                    UPDATE news_articles
                                    SET sentiment_score = ?, data_quality_score = ?
                                    WHERE id = ?
                                """, (sentiment_data['sentiment_score'], sentiment_data.get('confidence', 0.5), record_id))

                            elif custom_id.startswith('reddit_id_'):
                                record_id = int(custom_id.replace('reddit_id_', ''))
                                cursor.execute("""
                                    UPDATE reddit_posts
                                    SET sentiment_score = ?, data_quality_score = ?
                                    WHERE id = ?
                                """, (sentiment_data['sentiment_score'], sentiment_data.get('confidence', 0.5), record_id))

                            successful_updates += 1
                        else:
                            # Failed to parse - just update status
                            cursor.execute("""
                                UPDATE batch_mapping
                                SET status = 'failed',
                                    processed_at = CURRENT_TIMESTAMP
                                WHERE batch_id = ? AND custom_id = ?
                            """, (batch_id, custom_id))
                            failed_updates += 1
                    else:
                        # Request failed - just update status
                        cursor.execute("""
                            UPDATE batch_mapping
                            SET status = 'failed',
                                processed_at = CURRENT_TIMESTAMP
                            WHERE batch_id = ? AND custom_id = ?
                        """, (batch_id, custom_id))
                        failed_updates += 1

                except Exception as e:
                    logger.error(f"❌ Error processing result {custom_id}: {str(e)}")
                    failed_updates += 1

            self.db.connection.commit()
            cursor.close()
            self.db.close()

            logger.info(f"✅ Processed batch results: {successful_updates} successful, {failed_updates} failed")

            return {
                "success": True,
                "batch_id": batch_id,
                "successful_updates": successful_updates,
                "failed_updates": failed_updates,
                "total_processed": successful_updates + failed_updates
            }

        except Exception as e:
            logger.error(f"❌ Error retrieving batch results: {str(e)}")
            return {"success": False, "error": str(e)}

    def _parse_sentiment_json(self, response_text: str) -> Optional[Dict]:
        """Parse sentiment JSON from Claude response"""
        try:
            import json
            import re

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

    def finalize_processing(self) -> Dict:
        """
        Finalize processing by copying results back to original tables

        Returns:
            Results of finalization operation
        """
        logger.info("🚀 Starting finalize_processing method...")

        try:
            logger.info("🔗 Attempting database connection...")
            if not self.db.connect():
                logger.error("❌ Database connection failed in finalize_processing")
                return {"success": False, "error": "Database connection failed"}
            logger.info("✅ Database connected successfully")
        except Exception as e:
            logger.error(f"❌ Exception during database connection: {str(e)}")
            return {"success": False, "error": f"Database connection exception: {str(e)}"}

        try:
            logger.info("🔄 Finalizing processing - copying results to original tables...")

            # Get completed results from queue
            cursor = self.db.connection.cursor()

            logger.info("📊 Starting news articles update...")
            # Update news articles (only sentiment_score exists in original schema)
            cursor.execute("""
                UPDATE news_articles
                SET sentiment_score = tsq.sentiment_score
                FROM temp_sentiment_queue tsq
                WHERE news_articles.id = tsq.content_id
                AND tsq.content_type = 'news'
                AND tsq.processing_status = 'completed'
            """)
            news_updated = cursor.rowcount
            logger.info(f"📰 News articles query completed: {news_updated} rows updated")

            logger.info("📊 Starting Reddit posts update...")
            # Update Reddit posts (only sentiment_score exists in original schema)
            cursor.execute("""
                UPDATE reddit_posts
                SET sentiment_score = tsq.sentiment_score
                FROM temp_sentiment_queue tsq
                WHERE reddit_posts.id = tsq.content_id
                AND tsq.content_type = 'reddit'
                AND tsq.processing_status = 'completed'
            """)
            reddit_updated = cursor.rowcount
            logger.info(f"💭 Reddit posts query completed: {reddit_updated} rows updated")

            logger.info("📊 Committing changes...")
            self.db.connection.commit()

            logger.info(f"✅ Updated {news_updated} news articles and {reddit_updated} Reddit posts")

            return {
                "success": True,
                "message": f"Successfully updated {news_updated + reddit_updated} items in original tables",
                "news_updated": news_updated,
                "reddit_updated": reddit_updated
            }

        except Exception as e:
            logger.error(f"❌ Error finalizing processing: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            self.db.close()

    def cleanup_completed_queue(self) -> Dict:
        """
        Clean up completed items from sentiment queue

        Returns:
            Results of cleanup operation
        """
        if not self.db.connect():
            return {"success": False, "error": "Database connection failed"}

        try:
            cleaned_count = self.db.cleanup_old_sentiment_queue()

            return {
                "success": True,
                "message": f"Cleaned up {cleaned_count} completed items from queue",
                "cleaned_count": cleaned_count
            }

        except Exception as e:
            logger.error(f"❌ Error cleaning up queue: {str(e)}")
            return {"success": False, "error": str(e)}
        finally:
            self.db.close()

    def get_batch_progress(self) -> Dict:
        """
        Get detailed progress information for dashboard display

        Returns:
            Detailed progress statistics
        """
        if not self.db.connect():
            return {"error": "Database connection failed"}

        try:
            cursor = self.db.connection.cursor()

            # Get detailed status counts
            cursor.execute("""
                SELECT processing_status, COUNT(*) as count
                FROM temp_sentiment_queue
                GROUP BY processing_status
            """)
            status_counts = dict(cursor.fetchall())

            # Get recent batch information
            cursor.execute("""
                SELECT batch_id, COUNT(*) as items,
                       MIN(processed_at) as started,
                       MAX(processed_at) as last_update
                FROM temp_sentiment_queue
                WHERE batch_id IS NOT NULL
                GROUP BY batch_id
                ORDER BY started DESC
                LIMIT 5
            """)
            recent_batches = cursor.fetchall()

            total_items = sum(status_counts.values())
            progress_percentage = 0
            if total_items > 0:
                completed = status_counts.get('completed', 0) + status_counts.get('failed', 0)
                progress_percentage = (completed / total_items) * 100

            return {
                "total_items": total_items,
                "pending": status_counts.get('pending', 0),
                "processing": status_counts.get('processing', 0),
                "completed": status_counts.get('completed', 0),
                "failed": status_counts.get('failed', 0),
                "progress_percentage": round(progress_percentage, 1),
                "recent_batches": recent_batches,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting batch progress: {str(e)}")
            return {"error": str(e)}
        finally:
            self.db.close()