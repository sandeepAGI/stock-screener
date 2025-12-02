"""
Rankings API endpoints
"""

import sys
from pathlib import Path
from typing import Optional
from datetime import date
from fastapi import APIRouter, Query

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.database import get_database_connection
from backend.models.schemas import RankingEntry, RankingsResponse

router = APIRouter(prefix="/api/rankings", tags=["rankings"])


@router.get("", response_model=RankingsResponse)
async def get_rankings(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("composite_score", description="Sort field"),
    ascending: bool = Query(False, description="Sort direction"),
    outlier_category: Optional[str] = Query(None, description="Filter by outlier category"),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    max_score: Optional[float] = Query(None, ge=0, le=100),
):
    """Get composite rankings for all stocks"""
    db = get_database_connection()
    try:
        cursor = db.connection.cursor()

        # Build query
        where_clauses = ["cm.composite_score IS NOT NULL"]
        params = []

        if outlier_category:
            # Calculate outlier category from market percentile
            if outlier_category == "strong_undervalued":
                where_clauses.append("cm.sector_percentile <= 20")
            elif outlier_category == "undervalued":
                where_clauses.append("cm.sector_percentile > 20 AND cm.sector_percentile <= 35")
            elif outlier_category == "fairly_valued":
                where_clauses.append("cm.sector_percentile > 35 AND cm.sector_percentile <= 65")
            elif outlier_category == "overvalued":
                where_clauses.append("cm.sector_percentile > 65 AND cm.sector_percentile <= 80")
            elif outlier_category == "strong_overvalued":
                where_clauses.append("cm.sector_percentile > 80")

        if min_score is not None:
            where_clauses.append("cm.composite_score >= ?")
            params.append(min_score)

        if max_score is not None:
            where_clauses.append("cm.composite_score <= ?")
            params.append(max_score)

        where_sql = " WHERE " + " AND ".join(where_clauses)

        # Valid sort fields
        valid_sort_fields = {
            "composite_score": "cm.composite_score",
            "fundamental_score": "cm.fundamental_score",
            "quality_score": "cm.quality_score",
            "growth_score": "cm.growth_score",
            "sentiment_score": "cm.sentiment_score",
            "symbol": "s.symbol",
            "sector": "s.sector",
        }
        sort_field = valid_sort_fields.get(sort_by, "cm.composite_score")
        sort_dir = "ASC" if ascending else "DESC"

        # Get total count
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM calculated_metrics cm
            JOIN stocks s ON cm.symbol = s.symbol
            {where_sql}
        """, params)
        total = cursor.fetchone()[0]

        # Get latest calculation date
        cursor.execute("SELECT MAX(calculation_date) FROM calculated_metrics")
        calc_date_row = cursor.fetchone()
        calc_date = calc_date_row[0] if calc_date_row else date.today()

        # Get rankings
        cursor.execute(f"""
            SELECT
                s.symbol,
                s.company_name,
                s.sector,
                cm.composite_score,
                cm.fundamental_score,
                cm.quality_score,
                cm.growth_score,
                cm.sentiment_score,
                cm.sector_percentile,
                cm.data_quality_lower
            FROM calculated_metrics cm
            JOIN stocks s ON cm.symbol = s.symbol
            {where_sql}
            ORDER BY {sort_field} {sort_dir}
            LIMIT ? OFFSET ?
        """, params + [limit, offset])

        rankings = []
        for i, row in enumerate(cursor.fetchall()):
            # Determine outlier category from percentile
            pct = row[8] if row[8] else 50
            if pct <= 20:
                outlier_cat = "strong_undervalued"
            elif pct <= 35:
                outlier_cat = "undervalued"
            elif pct <= 65:
                outlier_cat = "fairly_valued"
            elif pct <= 80:
                outlier_cat = "overvalued"
            else:
                outlier_cat = "strong_overvalued"

            rankings.append(RankingEntry(
                rank=offset + i + 1,
                symbol=row[0],
                company_name=row[1],
                sector=row[2],
                composite_score=row[3],
                fundamental_score=row[4],
                quality_score=row[5],
                growth_score=row[6],
                sentiment_score=row[7],
                outlier_category=outlier_cat,
                data_quality=row[9]
            ))

        cursor.close()

        return RankingsResponse(
            rankings=rankings,
            total=total,
            sector=None,
            calculation_date=calc_date
        )

    finally:
        db.close()


@router.get("/sector/{sector}", response_model=RankingsResponse)
async def get_sector_rankings(
    sector: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get rankings for a specific sector"""
    db = get_database_connection()
    try:
        cursor = db.connection.cursor()

        # Get total count for sector
        cursor.execute("""
            SELECT COUNT(*)
            FROM calculated_metrics cm
            JOIN stocks s ON cm.symbol = s.symbol
            WHERE s.sector = ? AND cm.composite_score IS NOT NULL
        """, (sector,))
        total = cursor.fetchone()[0]

        # Get latest calculation date
        cursor.execute("SELECT MAX(calculation_date) FROM calculated_metrics")
        calc_date_row = cursor.fetchone()
        calc_date = calc_date_row[0] if calc_date_row else date.today()

        # Get sector rankings
        cursor.execute("""
            SELECT
                s.symbol,
                s.company_name,
                s.sector,
                cm.composite_score,
                cm.fundamental_score,
                cm.quality_score,
                cm.growth_score,
                cm.sentiment_score,
                cm.sector_percentile,
                cm.data_quality_lower
            FROM calculated_metrics cm
            JOIN stocks s ON cm.symbol = s.symbol
            WHERE s.sector = ? AND cm.composite_score IS NOT NULL
            ORDER BY cm.composite_score DESC
            LIMIT ? OFFSET ?
        """, (sector, limit, offset))

        rankings = []
        for i, row in enumerate(cursor.fetchall()):
            pct = row[8] if row[8] else 50
            if pct <= 20:
                outlier_cat = "strong_undervalued"
            elif pct <= 35:
                outlier_cat = "undervalued"
            elif pct <= 65:
                outlier_cat = "fairly_valued"
            elif pct <= 80:
                outlier_cat = "overvalued"
            else:
                outlier_cat = "strong_overvalued"

            rankings.append(RankingEntry(
                rank=offset + i + 1,
                symbol=row[0],
                company_name=row[1],
                sector=row[2],
                composite_score=row[3],
                fundamental_score=row[4],
                quality_score=row[5],
                growth_score=row[6],
                sentiment_score=row[7],
                outlier_category=outlier_cat,
                data_quality=row[9]
            ))

        cursor.close()

        return RankingsResponse(
            rankings=rankings,
            total=total,
            sector=sector,
            calculation_date=calc_date
        )

    finally:
        db.close()


@router.get("/outliers/{category}")
async def get_outliers(
    category: str,
    limit: int = Query(20, ge=1, le=100),
    min_data_quality: float = Query(0.5, ge=0, le=1),
):
    """Get stocks in a specific outlier category"""
    db = get_database_connection()
    try:
        cursor = db.connection.cursor()

        # Map category to percentile ranges
        category_ranges = {
            "strong_undervalued": (0, 20),
            "undervalued": (20, 35),
            "fairly_valued": (35, 65),
            "overvalued": (65, 80),
            "strong_overvalued": (80, 100),
        }

        if category not in category_ranges:
            return {"error": f"Invalid category. Valid options: {list(category_ranges.keys())}"}

        min_pct, max_pct = category_ranges[category]

        cursor.execute("""
            SELECT
                s.symbol,
                s.company_name,
                s.sector,
                cm.composite_score,
                cm.fundamental_score,
                cm.quality_score,
                cm.growth_score,
                cm.sentiment_score,
                cm.sector_percentile,
                cm.data_quality_lower
            FROM calculated_metrics cm
            JOIN stocks s ON cm.symbol = s.symbol
            WHERE cm.sector_percentile > ? AND cm.sector_percentile <= ?
            AND cm.data_quality_lower >= ?
            ORDER BY cm.composite_score ASC
            LIMIT ?
        """, (min_pct, max_pct, min_data_quality, limit))

        outliers = []
        for i, row in enumerate(cursor.fetchall()):
            outliers.append({
                "rank": i + 1,
                "symbol": row[0],
                "company_name": row[1],
                "sector": row[2],
                "composite_score": row[3],
                "fundamental_score": row[4],
                "quality_score": row[5],
                "growth_score": row[6],
                "sentiment_score": row[7],
                "sector_percentile": row[8],
                "data_quality": row[9],
                "outlier_category": category
            })

        cursor.close()

        return {
            "category": category,
            "outliers": outliers,
            "total": len(outliers)
        }

    finally:
        db.close()
