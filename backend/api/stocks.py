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
    StockExtendedDetail,
    FundamentalsWithPrevious,
    NewsArticle,
    RedditPost,
    HistoricalMetric,
    PeerStock,
    InvestmentInsights,
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
                   methodology_version, created_at, market_percentile, outlier_category
            FROM calculated_metrics
            WHERE symbol = ?
            ORDER BY calculation_date DESC
            LIMIT 1
        """, (symbol.upper(),))

        scores_row = cursor.fetchone()
        scores = None
        last_updated = None

        if scores_row:
            # Use stored values from database
            market_pct = scores_row[10] if scores_row[10] else 50
            outlier_cat = scores_row[11] if scores_row[11] else "fairly_valued"

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


@router.get("/{symbol}/extended", response_model=StockExtendedDetail)
async def get_stock_extended(symbol: str):
    """Get extended stock information with news, Reddit, peers, and historical data"""
    db = get_database_connection()
    try:
        # Get basic stock info
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

        cursor = db.connection.cursor()

        # Get scores
        cursor.execute("""
            SELECT fundamental_score, quality_score, growth_score, sentiment_score,
                   composite_score, sector_percentile, market_percentile, created_at,
                   outlier_category
            FROM calculated_metrics
            WHERE symbol = ?
            ORDER BY calculation_date DESC
            LIMIT 1
        """, (symbol.upper(),))

        scores_row = cursor.fetchone()
        scores = None
        last_updated = None

        if scores_row:
            # Use stored values from database
            market_pct = scores_row[6] if scores_row[6] else 50
            outlier_cat = scores_row[8] if scores_row[8] else "fairly_valued"

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
            last_updated = scores_row[7]

        # Get fundamentals with previous values for comparison
        cursor.execute("""
            SELECT pe_ratio, forward_pe, peg_ratio, price_to_book, ev_to_ebitda,
                   return_on_equity, return_on_assets, debt_to_equity, current_ratio,
                   revenue_growth, earnings_growth, current_price, week_52_high,
                   week_52_low, dividend_yield, beta, reporting_date
            FROM fundamental_data
            WHERE symbol = ?
            ORDER BY reporting_date DESC
            LIMIT 2
        """, (symbol.upper(),))

        fund_rows = cursor.fetchall()
        fundamentals = None
        if fund_rows:
            curr = fund_rows[0]
            prev = fund_rows[1] if len(fund_rows) > 1 else None
            fundamentals = FundamentalsWithPrevious(
                pe_ratio=curr[0],
                pe_ratio_prev=prev[0] if prev else None,
                forward_pe=curr[1],
                forward_pe_prev=prev[1] if prev else None,
                peg_ratio=curr[2],
                peg_ratio_prev=prev[2] if prev else None,
                price_to_book=curr[3],
                price_to_book_prev=prev[3] if prev else None,
                ev_to_ebitda=curr[4],
                ev_to_ebitda_prev=prev[4] if prev else None,
                return_on_equity=curr[5],
                return_on_equity_prev=prev[5] if prev else None,
                return_on_assets=curr[6],
                return_on_assets_prev=prev[6] if prev else None,
                debt_to_equity=curr[7],
                debt_to_equity_prev=prev[7] if prev else None,
                current_ratio=curr[8],
                current_ratio_prev=prev[8] if prev else None,
                revenue_growth=curr[9],
                revenue_growth_prev=prev[9] if prev else None,
                earnings_growth=curr[10],
                earnings_growth_prev=prev[10] if prev else None,
                current_price=curr[11],
                week_52_high=curr[12],
                week_52_low=curr[13],
                dividend_yield=curr[14],
                beta=curr[15]
            )

        # Get sentiment summary
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

        # Get news articles
        news_data = db.get_recent_news(symbol.upper(), days=30)
        news_articles = []
        for article in news_data[:20]:  # Limit to 20 articles
            news_articles.append(NewsArticle(
                id=article.get("id", 0),
                title=article.get("title", ""),
                summary=article.get("summary"),
                publisher=article.get("publisher"),
                publish_date=article.get("publish_date"),
                url=article.get("url"),
                sentiment_score=article.get("sentiment_score")
            ))

        # Get Reddit posts
        reddit_data = db.get_recent_reddit_posts(symbol.upper(), days=30)
        reddit_posts = []
        for post in reddit_data[:20]:  # Limit to 20 posts
            reddit_posts.append(RedditPost(
                id=post.get("id", 0),
                post_id=post.get("post_id", ""),
                title=post.get("title", ""),
                content=post.get("content"),
                subreddit=post.get("subreddit"),
                author=post.get("author"),
                score=post.get("score", 0),
                upvote_ratio=post.get("upvote_ratio"),
                num_comments=post.get("num_comments", 0),
                created_utc=post.get("created_utc"),
                url=post.get("url"),
                sentiment_score=post.get("sentiment_score")
            ))

        # Get historical metrics (P/E, PEG, Composite over time)
        cursor.execute("""
            SELECT f.reporting_date, f.pe_ratio, f.peg_ratio, c.composite_score
            FROM fundamental_data f
            LEFT JOIN calculated_metrics c ON f.symbol = c.symbol
                AND f.reporting_date = c.calculation_date
            WHERE f.symbol = ?
            ORDER BY f.reporting_date DESC
            LIMIT 12
        """, (symbol.upper(),))

        historical_metrics = []
        for row in cursor.fetchall():
            if row[0]:  # Has date
                historical_metrics.append(HistoricalMetric(
                    date=row[0] if isinstance(row[0], str) else row[0],
                    pe_ratio=row[1],
                    peg_ratio=row[2],
                    composite_score=row[3]
                ))

        # Get industry peers (same industry) - using created_at subquery for latest record only
        cursor.execute("""
            SELECT s.symbol, s.company_name, s.sector, s.industry,
                   c.composite_score, c.fundamental_score, c.quality_score,
                   c.growth_score, c.sentiment_score
            FROM stocks s
            JOIN calculated_metrics c ON s.symbol = c.symbol
            WHERE s.industry = ? AND s.symbol != ? AND s.is_active = 1
            AND c.created_at = (
                SELECT MAX(created_at) FROM calculated_metrics c2 WHERE c2.symbol = s.symbol
            )
            ORDER BY c.composite_score DESC
            LIMIT 5
        """, (stock_info.get("industry"), symbol.upper()))

        industry_peers = []
        for row in cursor.fetchall():
            industry_peers.append(PeerStock(
                symbol=row[0],
                company_name=row[1],
                sector=row[2],
                industry=row[3],
                composite_score=row[4],
                fundamental_score=row[5],
                quality_score=row[6],
                growth_score=row[7],
                sentiment_score=row[8]
            ))

        # Get sector peers (same sector, top performers) - using created_at subquery for latest record only
        cursor.execute("""
            SELECT s.symbol, s.company_name, s.sector, s.industry,
                   c.composite_score, c.fundamental_score, c.quality_score,
                   c.growth_score, c.sentiment_score
            FROM stocks s
            JOIN calculated_metrics c ON s.symbol = c.symbol
            WHERE s.sector = ? AND s.symbol != ? AND s.is_active = 1
            AND c.created_at = (
                SELECT MAX(created_at) FROM calculated_metrics c2 WHERE c2.symbol = s.symbol
            )
            ORDER BY c.composite_score DESC
            LIMIT 10
        """, (stock_info.get("sector"), symbol.upper()))

        sector_peers = []
        for row in cursor.fetchall():
            sector_peers.append(PeerStock(
                symbol=row[0],
                company_name=row[1],
                sector=row[2],
                industry=row[3],
                composite_score=row[4],
                fundamental_score=row[5],
                quality_score=row[6],
                growth_score=row[7],
                sentiment_score=row[8]
            ))

        # Generate investment insights
        insights = InvestmentInsights(strengths=[], weaknesses=[])
        if scores:
            score_components = [
                ("Fundamental", scores.fundamental_score or 0),
                ("Quality", scores.quality_score or 0),
                ("Growth", scores.growth_score or 0),
                ("Sentiment", scores.sentiment_score or 0)
            ]
            sorted_scores = sorted(score_components, key=lambda x: x[1], reverse=True)

            # Top 2 are strengths
            for name, score in sorted_scores[:2]:
                if score > 50:
                    insights.strengths.append({
                        "component": name,
                        "score": score,
                        "description": f"Strong {name.lower()} metrics"
                    })

            # Bottom 2 are weaknesses (if below 50)
            for name, score in sorted_scores[2:]:
                if score < 50:
                    insights.weaknesses.append({
                        "component": name,
                        "score": score,
                        "description": f"{name} metrics need attention"
                    })

        cursor.close()

        return StockExtendedDetail(
            stock=stock,
            scores=scores,
            fundamentals=fundamentals,
            sentiment=sentiment,
            recent_prices=recent_prices,
            news_articles=news_articles,
            reddit_posts=reddit_posts,
            historical_metrics=historical_metrics,
            industry_peers=industry_peers,
            sector_peers=sector_peers,
            insights=insights,
            last_updated=last_updated
        )

    finally:
        db.close()
