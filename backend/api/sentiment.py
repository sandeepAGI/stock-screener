"""
Sentiment Processing API endpoints
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, BackgroundTasks

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.database import get_database_connection
from backend.models.schemas import (
    SentimentSubmitRequest,
    SentimentStatusResponse,
)

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])

# Global state for tracking sentiment processing
_sentiment_status = {
    "batch_id": None,
    "status": "idle",
    "total_items": 0,
    "completed_items": 0,
    "failed_items": 0,
    "progress": 0.0,
    "started_at": None,
    "completed_at": None,
}


@router.post("/submit", response_model=SentimentStatusResponse)
async def submit_sentiment_batch(
    request: SentimentSubmitRequest,
    background_tasks: BackgroundTasks,
):
    """Submit content for sentiment analysis"""
    global _sentiment_status

    if _sentiment_status["status"] == "processing":
        return SentimentStatusResponse(
            batch_id=_sentiment_status["batch_id"],
            status="already_processing",
            total_items=_sentiment_status["total_items"],
            completed_items=_sentiment_status["completed_items"],
            failed_items=_sentiment_status["failed_items"],
            progress=_sentiment_status["progress"],
            started_at=_sentiment_status["started_at"]
        )

    db = get_database_connection()
    try:
        # Get unprocessed items count
        cursor = db.connection.cursor()

        if request.symbols:
            placeholders = ",".join(["?" for _ in request.symbols])
            cursor.execute(f"""
                SELECT COUNT(*) FROM news_articles
                WHERE symbol IN ({placeholders}) AND sentiment_score IS NULL
            """, request.symbols)
            news_count = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT COUNT(*) FROM reddit_posts
                WHERE symbol IN ({placeholders}) AND sentiment_score IS NULL
            """, request.symbols)
            reddit_count = cursor.fetchone()[0]
        else:
            cursor.execute("SELECT COUNT(*) FROM news_articles WHERE sentiment_score IS NULL")
            news_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM reddit_posts WHERE sentiment_score IS NULL")
            reddit_count = cursor.fetchone()[0]

        total_items = news_count + reddit_count
        cursor.close()

        if total_items == 0:
            return SentimentStatusResponse(
                batch_id=None,
                status="no_items",
                total_items=0,
                message="No items need sentiment processing"
            )

        # Start background processing
        from src.data.unified_bulk_processor import UnifiedBulkProcessor

        processor = UnifiedBulkProcessor()
        batch_id = processor.submit_batch(symbols=request.symbols)

        _sentiment_status.update({
            "batch_id": batch_id,
            "status": "processing",
            "total_items": total_items,
            "completed_items": 0,
            "failed_items": 0,
            "progress": 0.0,
            "started_at": datetime.now(),
            "completed_at": None,
        })

        return SentimentStatusResponse(
            batch_id=batch_id,
            status="submitted",
            total_items=total_items,
            completed_items=0,
            failed_items=0,
            progress=0.0,
            started_at=_sentiment_status["started_at"]
        )

    except Exception as e:
        return SentimentStatusResponse(
            status="failed",
            total_items=0,
            message=str(e)
        )

    finally:
        db.close()


@router.get("/status/{batch_id}", response_model=SentimentStatusResponse)
async def get_sentiment_status(batch_id: str):
    """Get status of a sentiment processing batch"""
    db = get_database_connection()
    try:
        # Check batch_mapping table for status
        cursor = db.connection.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                MIN(created_at) as started_at,
                MAX(processed_at) as last_processed
            FROM batch_mapping
            WHERE batch_id = ?
        """, (batch_id,))

        row = cursor.fetchone()
        cursor.close()

        if not row or row[0] == 0:
            return SentimentStatusResponse(
                batch_id=batch_id,
                status="not_found",
                total_items=0
            )

        total = row[0]
        completed = row[1] or 0
        failed = row[2] or 0
        started_at = row[3]
        last_processed = row[4]

        # Determine status
        if completed + failed >= total:
            status = "completed"
        elif completed + failed > 0:
            status = "processing"
        else:
            status = "pending"

        progress = ((completed + failed) / total * 100) if total > 0 else 0

        return SentimentStatusResponse(
            batch_id=batch_id,
            status=status,
            total_items=total,
            completed_items=completed,
            failed_items=failed,
            progress=progress,
            started_at=started_at,
            completed_at=last_processed if status == "completed" else None
        )

    finally:
        db.close()


@router.get("/status")
async def get_current_sentiment_status():
    """Get current sentiment processing status"""
    return _sentiment_status


@router.get("/pending")
async def get_pending_sentiment():
    """Get count of items pending sentiment analysis"""
    db = get_database_connection()
    try:
        cursor = db.connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM news_articles WHERE sentiment_score IS NULL")
        news_pending = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reddit_posts WHERE sentiment_score IS NULL")
        reddit_pending = cursor.fetchone()[0]

        cursor.execute("""
            SELECT symbol, COUNT(*) as count
            FROM news_articles
            WHERE sentiment_score IS NULL
            GROUP BY symbol
            ORDER BY count DESC
            LIMIT 10
        """)
        top_news_symbols = [{"symbol": row[0], "count": row[1]} for row in cursor.fetchall()]

        cursor.execute("""
            SELECT symbol, COUNT(*) as count
            FROM reddit_posts
            WHERE sentiment_score IS NULL
            GROUP BY symbol
            ORDER BY count DESC
            LIMIT 10
        """)
        top_reddit_symbols = [{"symbol": row[0], "count": row[1]} for row in cursor.fetchall()]

        cursor.close()

        return {
            "news_pending": news_pending,
            "reddit_pending": reddit_pending,
            "total_pending": news_pending + reddit_pending,
            "top_news_symbols": top_news_symbols,
            "top_reddit_symbols": top_reddit_symbols,
        }

    finally:
        db.close()


@router.get("/batches")
async def list_batches():
    """List all sentiment processing batches"""
    db = get_database_connection()
    try:
        batch_ids = db.get_active_batch_ids()

        batches = []
        for batch_id in batch_ids:
            status = db.get_batch_status_summary(batch_id)
            batches.append(status)

        return {"batches": batches}

    finally:
        db.close()


@router.post("/poll/{batch_id}")
async def poll_batch_status(batch_id: str):
    """
    Poll Anthropic API for batch status and auto-retrieve results if complete.
    This is similar to the batch_monitor.py functionality but exposed via API.
    """
    global _sentiment_status

    try:
        from src.data.unified_bulk_processor import UnifiedBulkProcessor

        processor = UnifiedBulkProcessor()

        # Check status from Anthropic API
        status_result = processor.check_batch_status(batch_id)

        if not status_result or not status_result.get('success'):
            return {
                "success": False,
                "error": status_result.get('error', 'Failed to check batch status'),
                "batch_id": batch_id,
                "anthropic_status": None,
            }

        anthropic_status = status_result.get('status')
        submitted_count = status_result.get('submitted_count', 0)
        completed_count = status_result.get('completed_count', 0)
        failed_count = status_result.get('failed_count', 0)

        response = {
            "success": True,
            "batch_id": batch_id,
            "anthropic_status": anthropic_status,
            "submitted_count": submitted_count,
            "completed_count": completed_count,
            "failed_count": failed_count,
            "results_retrieved": False,
        }

        # If batch is complete (ended), auto-retrieve results
        if anthropic_status == 'ended':
            retrieve_result = processor.retrieve_and_process_batch_results(batch_id)

            if retrieve_result and retrieve_result.get('success'):
                response["results_retrieved"] = True
                response["successful_updates"] = retrieve_result.get('successful_updates', 0)
                response["failed_updates"] = retrieve_result.get('failed_updates', 0)
                response["message"] = f"Results retrieved: {retrieve_result.get('successful_updates', 0)} successful, {retrieve_result.get('failed_updates', 0)} failed"

                # Update global status
                _sentiment_status.update({
                    "batch_id": batch_id,
                    "status": "completed",
                    "completed_items": retrieve_result.get('successful_updates', 0),
                    "failed_items": retrieve_result.get('failed_updates', 0),
                    "progress": 100.0,
                    "completed_at": datetime.now(),
                })
            else:
                response["results_retrieved"] = False
                response["error"] = retrieve_result.get('error', 'Failed to retrieve results') if retrieve_result else 'No result returned'

        elif anthropic_status == 'in_progress':
            response["message"] = f"Batch still processing ({completed_count}/{submitted_count})"

        elif anthropic_status == 'processing':
            response["message"] = "Batch is being processed by Anthropic"

        else:
            response["message"] = f"Batch status: {anthropic_status}"

        return response

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "batch_id": batch_id,
        }
