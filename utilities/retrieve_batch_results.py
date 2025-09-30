#!/usr/bin/env python3
"""
Manual Batch Result Retrieval Script

This script retrieves results from a completed Anthropic batch and processes them
into the temp_sentiment_queue table.
"""

import sys
import os
import json
import logging
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import anthropic
    from src.data.database import DatabaseManager
    ANTHROPIC_AVAILABLE = True
except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    ANTHROPIC_AVAILABLE = False

def parse_sentiment_json(response_text: str) -> Dict:
    """Parse sentiment JSON from Claude response"""
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

def retrieve_batch_results(batch_id: str):
    """Retrieve and process batch results"""

    if not ANTHROPIC_AVAILABLE:
        logger.error("❌ Anthropic library not available")
        return False

    # Get API key
    api_key = os.getenv('NEWS_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("❌ No API key found (NEWS_API_KEY or ANTHROPIC_API_KEY)")
        return False

    try:
        # Initialize client
        client = anthropic.Anthropic(api_key=api_key)
        logger.info(f"🔍 Checking batch status: {batch_id}")

        # Check batch status
        batch_status = client.messages.batches.retrieve(batch_id)
        logger.info(f"📊 Batch status: {batch_status.processing_status}")

        if batch_status.processing_status != "ended":
            logger.error(f"❌ Batch not completed yet. Status: {batch_status.processing_status}")
            return False

        # Retrieve results
        logger.info("📥 Retrieving batch results...")
        batch_results = list(client.messages.batches.results(batch_id))
        logger.info(f"✅ Retrieved {len(batch_results)} results")

        # Connect to database
        db = DatabaseManager()
        if not db.connect():
            logger.error("❌ Database connection failed")
            return False

        logger.info("🔄 Processing results and updating database...")

        # Process results in batches for efficiency
        successful_updates = 0
        failed_updates = 0
        update_batch = []
        batch_size = 1000  # Process in batches of 1000

        logger.info(f"📊 Processing {len(batch_results)} results in batches of {batch_size}...")

        for i, result in enumerate(batch_results):
            try:
                custom_id = result.custom_id

                # Check if request succeeded
                if result.result.type == "succeeded":
                    # Extract response content
                    content = result.result.message.content[0].text

                    # Parse sentiment data
                    sentiment_data = parse_sentiment_json(content)

                    if sentiment_data:
                        # Add to batch
                        update_batch.append({
                            'custom_id': custom_id,
                            'sentiment_score': sentiment_data['sentiment_score'],
                            'confidence': sentiment_data['confidence'],
                            'method': 'batch_claude',
                            'success': True,
                            'error': None,
                            'raw_response': content
                        })
                        successful_updates += 1
                    else:
                        # Failed to parse JSON
                        update_batch.append({
                            'custom_id': custom_id,
                            'sentiment_score': 0.0,
                            'confidence': 0.1,
                            'method': 'batch_parse_error',
                            'success': False,
                            'error': 'Failed to parse sentiment JSON',
                            'raw_response': content
                        })
                        failed_updates += 1
                else:
                    # Request failed
                    error_msg = getattr(result.result, 'error', 'Unknown error')
                    update_batch.append({
                        'custom_id': custom_id,
                        'sentiment_score': 0.0,
                        'confidence': 0.1,
                        'method': 'batch_error',
                        'success': False,
                        'error': str(error_msg),
                        'raw_response': None
                    })
                    failed_updates += 1

                # Process batch when full or at end
                if len(update_batch) >= batch_size or i == len(batch_results) - 1:
                    if update_batch:
                        try:
                            db.update_sentiment_results(update_batch)
                            logger.info(f"📊 Updated batch of {len(update_batch)} results (processed {i+1}/{len(batch_results)} total)")
                            update_batch = []  # Clear batch
                        except Exception as e:
                            logger.error(f"❌ Batch database update failed: {str(e)}")
                            # Reset counters since batch failed
                            for item in update_batch:
                                if item['success']:
                                    successful_updates -= 1
                                    failed_updates += 1
                            update_batch = []

            except Exception as e:
                logger.warning(f"⚠️  Error processing result {result.custom_id}: {str(e)}")
                failed_updates += 1

        # Close database
        db.close()

        logger.info(f"✅ Batch processing completed!")
        logger.info(f"📊 Successful updates: {successful_updates}")
        logger.info(f"❌ Failed updates: {failed_updates}")
        logger.info(f"📈 Success rate: {(successful_updates / len(batch_results) * 100):.1f}%")

        return True

    except Exception as e:
        logger.error(f"❌ Error retrieving batch results: {str(e)}")
        return False

def main():
    """Main function"""
    batch_id = "msgbatch_012uVodeFEqfXSek6w2o8g3D"

    print("🚀 Manual Batch Result Retrieval")
    print("=" * 50)
    print(f"Batch ID: {batch_id}")
    print()

    success = retrieve_batch_results(batch_id)

    if success:
        print("\n✅ Batch results successfully retrieved and processed!")
        print("🔄 You can now go to the dashboard and run Step 3: Finalize")

        # Check final status
        db = DatabaseManager()
        if db.connect():
            cursor = db.connection.cursor()
            cursor.execute("SELECT processing_status, COUNT(*) FROM temp_sentiment_queue GROUP BY processing_status")
            status_counts = dict(cursor.fetchall())
            db.close()

            print("\n📊 Final Status Summary:")
            for status, count in status_counts.items():
                print(f"   {status}: {count:,} items")

    else:
        print("\n❌ Failed to retrieve batch results")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())