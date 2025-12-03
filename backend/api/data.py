"""
Data Management API endpoints
"""

import sys
import asyncio
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.database import get_database_connection
from backend.models.schemas import (
    DataRefreshRequest,
    DataRefreshResponse,
    DataStatusResponse,
    MetricsSummary,
    TableStats,
)

router = APIRouter(prefix="/api/data", tags=["data"])

# Global state for tracking data refresh operations
_refresh_status = {
    "is_collecting": False,
    "current_symbol": None,
    "progress": 0.0,
    "completed": 0,
    "total": 0,
    "errors": [],
    "last_collection": None,
    "job_id": None,
}


async def _run_data_refresh(symbols: List[str], data_types: List[str], job_id: str):
    """Background task to run data refresh"""
    global _refresh_status

    _refresh_status["is_collecting"] = True
    _refresh_status["job_id"] = job_id
    _refresh_status["total"] = len(symbols)
    _refresh_status["completed"] = 0
    _refresh_status["errors"] = []

    try:
        # Import the correct collector class
        from src.data.collectors import DataCollectionOrchestrator

        orchestrator = DataCollectionOrchestrator()

        for i, symbol in enumerate(symbols):
            _refresh_status["current_symbol"] = symbol
            _refresh_status["progress"] = (i / len(symbols)) * 100

            try:
                # Collect based on data types requested using orchestrator methods
                if "fundamentals" in data_types:
                    orchestrator.refresh_fundamentals_only([symbol])
                if "prices" in data_types:
                    orchestrator.refresh_prices_only([symbol])
                if "news" in data_types:
                    orchestrator.refresh_news_only([symbol])
                if "reddit" in data_types:
                    orchestrator.refresh_sentiment_only([symbol])

                _refresh_status["completed"] += 1

            except Exception as e:
                _refresh_status["errors"].append(f"{symbol}: {str(e)}")

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        _refresh_status["last_collection"] = datetime.now()

    except Exception as e:
        # Capture any initialization errors
        _refresh_status["errors"].append(f"Initialization error: {str(e)}")

    finally:
        _refresh_status["is_collecting"] = False
        _refresh_status["current_symbol"] = None
        _refresh_status["progress"] = 100.0


@router.post("/refresh", response_model=DataRefreshResponse)
async def refresh_data(
    request: DataRefreshRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger data refresh for specified symbols"""
    global _refresh_status

    if _refresh_status["is_collecting"]:
        return DataRefreshResponse(
            status="already_running",
            job_id=_refresh_status["job_id"],
            message="A data refresh is already in progress",
            symbols_count=_refresh_status["total"]
        )

    db = get_database_connection()
    try:
        # Get symbols to refresh
        if request.symbols:
            symbols = request.symbols
        else:
            symbols = db.get_all_stocks()

        job_id = str(uuid.uuid4())[:8]

        # Start background task
        background_tasks.add_task(
            _run_data_refresh,
            symbols,
            request.data_types,
            job_id
        )

        return DataRefreshResponse(
            status="started",
            job_id=job_id,
            message=f"Started data refresh for {len(symbols)} symbols",
            symbols_count=len(symbols)
        )

    finally:
        db.close()


@router.get("/status", response_model=DataStatusResponse)
async def get_data_status():
    """Get current data collection status"""
    return DataStatusResponse(
        is_collecting=_refresh_status["is_collecting"],
        current_symbol=_refresh_status["current_symbol"],
        progress=_refresh_status["progress"],
        completed=_refresh_status["completed"],
        total=_refresh_status["total"],
        errors=_refresh_status["errors"][-10:],  # Last 10 errors
        last_collection=_refresh_status["last_collection"]
    )


@router.get("/metrics/summary", response_model=MetricsSummary)
async def get_metrics_summary():
    """Get database statistics and metrics summary"""
    db = get_database_connection()
    try:
        stats = db.get_database_statistics()
        record_counts = db.get_table_record_counts()
        freshness = db.get_data_freshness_status()

        # Get stock counts
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM stocks")
        total_stocks = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM stocks WHERE is_active = 1")
        active_stocks = cursor.fetchone()[0]

        # Get last calculation date
        cursor.execute("SELECT MAX(calculation_date) FROM calculated_metrics")
        last_calc_row = cursor.fetchone()
        last_calc = last_calc_row[0] if last_calc_row else None

        cursor.close()

        # Build table stats
        tables = []
        for table_stat in stats.get("table_statistics", []):
            tables.append(TableStats(
                name=table_stat["table_name"],
                record_count=table_stat["row_count"],
                last_updated=table_stat.get("last_updated")
            ))

        return MetricsSummary(
            database_size_mb=stats.get("total_size_mb", 0),
            total_stocks=total_stocks,
            active_stocks=active_stocks,
            tables=tables,
            data_freshness=freshness,
            last_calculation=last_calc
        )

    finally:
        db.close()


@router.get("/freshness")
async def get_data_freshness():
    """Get detailed data freshness information"""
    db = get_database_connection()
    try:
        freshness = db.get_data_freshness_status()
        return freshness
    finally:
        db.close()


@router.post("/sync-sp500")
async def sync_sp500(background_tasks: BackgroundTasks):
    """Sync S&P 500 stock list"""
    try:
        from src.data.stock_universe import StockUniverseManager

        manager = StockUniverseManager()
        result = manager.sync_sp500()

        return {
            "status": "completed",
            "added": result.get("added", 0),
            "deactivated": result.get("deactivated", 0),
            "message": "S&P 500 list synced successfully"
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
