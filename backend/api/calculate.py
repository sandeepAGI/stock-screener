"""
Calculation API endpoints
"""

import sys
from pathlib import Path
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.database import get_database_connection
from src.calculations.composite import CompositeCalculator
from backend.models.schemas import CalculateRequest, CalculateResponse

router = APIRouter(prefix="/api/calculate", tags=["calculate"])

# Global state for calculation progress
_calculation_status = {
    "is_calculating": False,
    "current_symbol": None,
    "progress": 0.0,
    "completed": 0,
    "total": 0,
    "failed": 0,
    "errors": [],
}


def _run_calculations(symbols: List[str]):
    """Run calculations for specified symbols"""
    global _calculation_status

    _calculation_status["is_calculating"] = True
    _calculation_status["total"] = len(symbols)
    _calculation_status["completed"] = 0
    _calculation_status["failed"] = 0
    _calculation_status["errors"] = []

    db = get_database_connection()
    calculator = CompositeCalculator()

    try:
        composite_scores = {}

        for i, symbol in enumerate(symbols):
            _calculation_status["current_symbol"] = symbol
            _calculation_status["progress"] = (i / len(symbols)) * 100

            try:
                score = calculator.calculate_composite_score(symbol, db)
                if score:
                    composite_scores[symbol] = score
                    _calculation_status["completed"] += 1
                else:
                    _calculation_status["failed"] += 1
                    _calculation_status["errors"].append(f"{symbol}: Insufficient data")

            except Exception as e:
                _calculation_status["failed"] += 1
                _calculation_status["errors"].append(f"{symbol}: {str(e)}")

        # Calculate percentiles
        if composite_scores:
            composite_scores = calculator.calculate_percentiles(composite_scores)
            calculator.save_composite_scores(composite_scores, db)

    finally:
        db.close()
        _calculation_status["is_calculating"] = False
        _calculation_status["current_symbol"] = None
        _calculation_status["progress"] = 100.0


@router.post("", response_model=CalculateResponse)
async def run_calculations(
    request: CalculateRequest,
    background_tasks: BackgroundTasks,
):
    """Run composite score calculations"""
    global _calculation_status

    if _calculation_status["is_calculating"]:
        return CalculateResponse(
            status="already_running",
            symbols_calculated=_calculation_status["completed"],
            symbols_failed=_calculation_status["failed"],
            message="Calculations already in progress",
            calculation_date=date.today()
        )

    db = get_database_connection()
    try:
        # Get symbols to calculate
        if request.symbols:
            symbols = request.symbols
        else:
            symbols = db.get_all_stocks()

        # Run calculations (in background for large batches)
        if len(symbols) > 50:
            background_tasks.add_task(_run_calculations, symbols)
            return CalculateResponse(
                status="started",
                symbols_calculated=0,
                symbols_failed=0,
                message=f"Started calculations for {len(symbols)} symbols",
                calculation_date=date.today()
            )
        else:
            # Run synchronously for small batches
            _run_calculations(symbols)
            return CalculateResponse(
                status="completed",
                symbols_calculated=_calculation_status["completed"],
                symbols_failed=_calculation_status["failed"],
                message=f"Completed calculations for {_calculation_status['completed']} symbols",
                calculation_date=date.today()
            )

    finally:
        db.close()


@router.get("/status")
async def get_calculation_status():
    """Get current calculation status"""
    return {
        "is_calculating": _calculation_status["is_calculating"],
        "current_symbol": _calculation_status["current_symbol"],
        "progress": _calculation_status["progress"],
        "completed": _calculation_status["completed"],
        "total": _calculation_status["total"],
        "failed": _calculation_status["failed"],
        "errors": _calculation_status["errors"][-10:],  # Last 10 errors
    }


@router.get("/history")
async def get_calculation_history():
    """Get calculation history"""
    db = get_database_connection()
    try:
        cursor = db.connection.cursor()

        cursor.execute("""
            SELECT
                calculation_date,
                COUNT(*) as symbols_calculated,
                AVG(composite_score) as avg_score,
                MIN(composite_score) as min_score,
                MAX(composite_score) as max_score
            FROM calculated_metrics
            GROUP BY calculation_date
            ORDER BY calculation_date DESC
            LIMIT 30
        """)

        history = []
        for row in cursor.fetchall():
            history.append({
                "date": row[0],
                "symbols_calculated": row[1],
                "avg_score": round(row[2], 2) if row[2] else None,
                "min_score": round(row[3], 2) if row[3] else None,
                "max_score": round(row[4], 2) if row[4] else None,
            })

        cursor.close()
        return {"history": history}

    finally:
        db.close()


@router.post("/single/{symbol}")
async def calculate_single_stock(symbol: str):
    """Calculate composite score for a single stock"""
    db = get_database_connection()
    calculator = CompositeCalculator()

    try:
        score = calculator.calculate_composite_score(symbol.upper(), db)

        if not score:
            return {
                "status": "failed",
                "symbol": symbol.upper(),
                "message": "Insufficient data for calculation"
            }

        # Save the score
        calculator.save_composite_scores({symbol.upper(): score}, db)

        return {
            "status": "completed",
            "symbol": symbol.upper(),
            "composite_score": score.composite_score,
            "fundamental_score": score.fundamental_score,
            "quality_score": score.quality_score,
            "growth_score": score.growth_score,
            "sentiment_score": score.sentiment_score,
            "data_quality": score.overall_data_quality,
            "sector": score.sector,
        }

    finally:
        db.close()
