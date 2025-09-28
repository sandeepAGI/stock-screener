#!/usr/bin/env python3
"""
Fix Reddit sentiment scores in the database by recalculating them using the new LLM-enhanced analyzer
"""

import sqlite3
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.sentiment_analyzer import SentimentAnalyzer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_reddit_sentiment(use_llm: bool = True, max_posts: int = None):
    """
    Recalculate sentiment scores for Reddit posts in the database

    Args:
        use_llm: Whether to use Claude LLM (requires ANTHROPIC_API_KEY)
        max_posts: Maximum number of posts to process (None for all)
    """
    db_path = "data/stock_data.db"

    if not os.path.exists(db_path):
        logger.error(f"Database not found at {db_path}")
        return

    # Initialize sentiment analyzer
    try:
        analyzer = SentimentAnalyzer(use_llm=use_llm)
        method = "auto" if use_llm else "combined"

        if use_llm and analyzer.claude_client:
            logger.info("Using Claude LLM for sentiment analysis")
        else:
            logger.info("Using traditional sentiment analysis (TextBlob + VADER)")

    except Exception as e:
        logger.error(f"Failed to initialize sentiment analyzer: {e}")
        return

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get Reddit posts with zero sentiment scores
        query = """
            SELECT id, symbol, title, content, score, num_comments
            FROM reddit_posts
            WHERE sentiment_score = 0.0
        """

        if max_posts:
            query += f" LIMIT {max_posts}"

        cursor.execute(query)
        posts = cursor.fetchall()

        if not posts:
            logger.info("No Reddit posts found with zero sentiment scores")
            return

        logger.info(f"Found {len(posts)} Reddit posts to process")

        updated_count = 0
        error_count = 0

        for post_id, symbol, title, content, score, num_comments in posts:
            try:
                # Combine title and content for sentiment analysis
                post_text = f"{title or ''} {content or ''}".strip()

                if not post_text:
                    logger.warning(f"Empty text for post {post_id}, skipping")
                    continue

                # Calculate sentiment using new analyzer
                sentiment_result = analyzer.analyze_text(post_text, method=method)

                # Calculate data quality based on engagement and sentiment confidence
                base_quality = 0.7
                engagement_score = max(1, (score or 0) + (num_comments or 0))
                engagement_quality = min(1.0, engagement_score / 50)

                # If using LLM, incorporate its confidence score
                if hasattr(sentiment_result, 'confidence') and sentiment_result.confidence:
                    final_quality = (base_quality * 0.5 +
                                   engagement_quality * 0.3 +
                                   sentiment_result.confidence * 0.2)
                else:
                    final_quality = base_quality * 0.7 + engagement_quality * 0.3

                # Update the database
                cursor.execute("""
                    UPDATE reddit_posts
                    SET sentiment_score = ?, data_quality_score = ?
                    WHERE id = ?
                """, (sentiment_result.sentiment_score, final_quality, post_id))

                updated_count += 1

                # Log progress and details
                if updated_count % 50 == 0:
                    logger.info(f"Updated {updated_count} posts...")

                if updated_count <= 5:  # Log first few for verification
                    logger.info(f"Post {post_id} ({symbol}): {sentiment_result.sentiment_score:.3f} ({sentiment_result.method})")
                    if hasattr(sentiment_result, 'reasoning') and sentiment_result.reasoning:
                        logger.debug(f"  Reasoning: {sentiment_result.reasoning}")

            except Exception as e:
                logger.error(f"Error processing post {post_id}: {str(e)}")
                error_count += 1
                continue

        # Commit all changes
        conn.commit()
        logger.info(f"Successfully updated sentiment scores for {updated_count} Reddit posts")

        if error_count > 0:
            logger.warning(f"Encountered errors processing {error_count} posts")

        # Verify the results
        cursor.execute("SELECT COUNT(*) FROM reddit_posts WHERE sentiment_score != 0.0")
        calculated_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reddit_posts")
        total_count = cursor.fetchone()[0]

        logger.info(f"Final status: {calculated_count}/{total_count} posts now have calculated sentiment scores")

        # Show sentiment distribution
        cursor.execute("""
            SELECT
                CASE
                    WHEN sentiment_score > 0.1 THEN 'Positive'
                    WHEN sentiment_score < -0.1 THEN 'Negative'
                    ELSE 'Neutral'
                END as sentiment_category,
                COUNT(*) as count,
                AVG(sentiment_score) as avg_score
            FROM reddit_posts
            WHERE sentiment_score != 0.0
            GROUP BY sentiment_category
        """)

        results = cursor.fetchall()
        logger.info("Sentiment distribution:")
        for category, count, avg_score in results:
            logger.info(f"  {category}: {count} posts (avg: {avg_score:.3f})")

    except Exception as e:
        logger.error(f"Error during sentiment calculation: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fix Reddit sentiment scores using enhanced analyzer")
    parser.add_argument("--no-llm", action="store_true", help="Use traditional analysis instead of Claude LLM")
    parser.add_argument("--max-posts", type=int, help="Maximum number of posts to process")
    parser.add_argument("--test", action="store_true", help="Process only 10 posts for testing")

    args = parser.parse_args()

    if args.test:
        args.max_posts = 10
        logger.info("Running in test mode (10 posts only)")

    use_llm = not args.no_llm
    fix_reddit_sentiment(use_llm=use_llm, max_posts=args.max_posts)