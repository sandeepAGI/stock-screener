"""
Stock API endpoints
"""

import sys
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.database import get_database_connection
from backend.models.schemas import (
    StockBase,
    StockDetail,
    StockList,
    StockScores,
    StockFundamentals,
    StockSentiment,
    PriceData,
)

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("", response_model=StockList)
async def list_stocks(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    active_only: bool = Query(True, description="Only show active stocks"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """List all stocks with optional filtering"""
    db = get_database_connection()
    try:
        cursor = db.connection.cursor()

        # Build query
        where_clauses = []
        params = []

        if active_only:
            where_clauses.append("is_active = 1")

        if sector:
            where_clauses.append("sector = ?")
            params.append(sector)

        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM stocks{where_sql}", params)
        total = cursor.fetchone()[0]

        # Get active count
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE is_active = 1")
        active_count = cursor.fetchone()[0]

        # Get stocks
        cursor.execute(f"""
            SELECT symbol, company_name, sector, industry, market_cap, is_active
            FROM stocks
            {where_sql}
            ORDER BY symbol
            LIMIT ? OFFSET ?
        """, params + [limit, offset])

        stocks = []
        for row in cursor.fetchall():
            stocks.append(StockBase(
                symbol=row[0],
                company_name=row[1],
                sector=row[2],
                industry=row[3],
                market_cap=row[4],
                is_active=bool(row[5])
            ))

        cursor.close()
        return StockList(stocks=stocks, total=total, active_count=active_count)

    finally:
        db.close()


@router.get("/sectors")
async def list_sectors():
    """Get list of all sectors"""
    db = get_database_connection()
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT DISTINCT sector, COUNT(*) as count
            FROM stocks
            WHERE sector IS NOT NULL AND is_active = 1
            GROUP BY sector
            ORDER BY count DESC
        """)

        sectors = [{"sector": row[0], "count": row[1]} for row in cursor.fetchall()]
        cursor.close()
        return {"sectors": sectors}

    finally:
        db.close()


@router.get("/{symbol}", response_model=StockDetail)
async def get_stock(symbol: str):
    """Get detailed stock information with scores"""
    db = get_database_connection()
    try:
        # Get stock info
        stock_info = db.get_stock_info(symbol.upper())
        if not stock_info:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

        stock = StockBase(
            symbol=stock_info["symbol"],
            company_name=stock_info.get("company_name"),
            sector=stock_info.get("sector"),
            industry=stock_info.get("industry"),
            market_cap=stock_info.get("market_cap"),
            is_active=bool(stock_info.get("is_active", True))
        )

        # Get scores from calculated_metrics
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT fundamental_score, quality_score, growth_score, sentiment_score,
                   composite_score, sector_percentile, data_quality_lower, data_quality_upper,
                   methodology_version, created_at
            FROM calculated_metrics
            WHERE symbol = ?
            ORDER BY calculation_date DESC
            LIMIT 1
        """, (symbol.upper(),))

        scores_row = cursor.fetchone()
        scores = None
        last_updated = None

        if scores_row:
            # Get outlier category based on market percentile
            cursor.execute("""
                SELECT market_percentile FROM calculated_metrics
                WHERE symbol = ? ORDER BY calculation_date DESC LIMIT 1
            """, (symbol.upper(),))
            pct_row = cursor.fetchone()
            market_pct = pct_row[0] if pct_row and pct_row[0] else 50

            if market_pct <= 20:
                outlier_cat = "strong_undervalued"
            elif market_pct <= 35:
                outlier_cat = "undervalued"
            elif market_pct <= 65:
                outlier_cat = "fairly_valued"
            elif market_pct <= 80:
                outlier_cat = "overvalued"
            else:
                outlier_cat = "strong_overvalued"

            scores = StockScores(
                fundamental_score=scores_row[0],
                quality_score=scores_row[1],
                growth_score=scores_row[2],
                sentiment_score=scores_row[3],
                composite_score=scores_row[4],
                sector_percentile=scores_row[5],
                market_percentile=market_pct,
                outlier_category=outlier_cat
            )
            last_updated = scores_row[9]

        # Get fundamentals
        fundamentals_data = db.get_latest_fundamentals(symbol.upper())
        fundamentals = None
        if fundamentals_data:
            fundamentals = StockFundamentals(
                pe_ratio=fundamentals_data.get("pe_ratio"),
                forward_pe=fundamentals_data.get("forward_pe"),
                peg_ratio=fundamentals_data.get("peg_ratio"),
                price_to_book=fundamentals_data.get("price_to_book"),
                ev_to_ebitda=fundamentals_data.get("ev_to_ebitda"),
                return_on_equity=fundamentals_data.get("return_on_equity"),
                return_on_assets=fundamentals_data.get("return_on_assets"),
                debt_to_equity=fundamentals_data.get("debt_to_equity"),
                current_ratio=fundamentals_data.get("current_ratio"),
                revenue_growth=fundamentals_data.get("revenue_growth"),
                earnings_growth=fundamentals_data.get("earnings_growth"),
                current_price=fundamentals_data.get("current_price"),
                week_52_high=fundamentals_data.get("week_52_high"),
                week_52_low=fundamentals_data.get("week_52_low"),
                dividend_yield=fundamentals_data.get("dividend_yield"),
                beta=fundamentals_data.get("beta")
            )

        # Get sentiment
        sentiment_data = db.get_daily_sentiment(symbol.upper(), days=7)
        sentiment = None
        if sentiment_data:
            latest = sentiment_data[0]
            sentiment = StockSentiment(
                news_sentiment=latest.get("news_sentiment"),
                news_count=latest.get("news_count", 0),
                reddit_sentiment=latest.get("reddit_sentiment"),
                reddit_count=latest.get("reddit_count", 0),
                combined_sentiment=latest.get("combined_sentiment")
            )

        # Get recent prices
        cursor.execute("""
            SELECT date, open, high, low, close, volume, adjusted_close
            FROM price_data
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT 30
        """, (symbol.upper(),))

        recent_prices = []
        for row in cursor.fetchall():
            recent_prices.append(PriceData(
                date=row[0],
                open=row[1],
                high=row[2],
                low=row[3],
                close=row[4],
                volume=row[5],
                adjusted_close=row[6]
            ))

        cursor.close()

        return StockDetail(
            stock=stock,
            scores=scores,
            fundamentals=fundamentals,
            sentiment=sentiment,
            recent_prices=recent_prices,
            last_updated=last_updated
        )

    finally:
        db.close()
