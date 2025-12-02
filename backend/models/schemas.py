"""
Pydantic models for StockAnalyzer Pro API
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Health Check
class HealthResponse(BaseModel):
    status: str = "healthy"
    database_connected: bool = True
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.now)


# Stock Models
class StockBase(BaseModel):
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[int] = None
    is_active: bool = True


class StockScores(BaseModel):
    fundamental_score: Optional[float] = None
    quality_score: Optional[float] = None
    growth_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    composite_score: Optional[float] = None
    sector_percentile: Optional[float] = None
    market_percentile: Optional[float] = None
    outlier_category: Optional[str] = None


class StockFundamentals(BaseModel):
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    current_price: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None


class StockSentiment(BaseModel):
    news_sentiment: Optional[float] = None
    news_count: int = 0
    reddit_sentiment: Optional[float] = None
    reddit_count: int = 0
    combined_sentiment: Optional[float] = None


class PriceData(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None


class StockDetail(BaseModel):
    stock: StockBase
    scores: Optional[StockScores] = None
    fundamentals: Optional[StockFundamentals] = None
    sentiment: Optional[StockSentiment] = None
    recent_prices: Optional[List[PriceData]] = None
    last_updated: Optional[datetime] = None


class StockList(BaseModel):
    stocks: List[StockBase]
    total: int
    active_count: int


# Ranking Models
class RankingEntry(BaseModel):
    rank: int
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    composite_score: float
    fundamental_score: Optional[float] = None
    quality_score: Optional[float] = None
    growth_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    outlier_category: Optional[str] = None
    data_quality: Optional[float] = None


class RankingsResponse(BaseModel):
    rankings: List[RankingEntry]
    total: int
    sector: Optional[str] = None
    calculation_date: Optional[date] = None


# Data Management Models
class DataRefreshRequest(BaseModel):
    symbols: Optional[List[str]] = None  # None = all symbols
    data_types: List[str] = Field(
        default=["fundamentals", "prices", "news", "reddit"],
        description="Types: fundamentals, prices, news, reddit"
    )
    force: bool = False


class DataRefreshResponse(BaseModel):
    status: str  # "started", "completed", "failed"
    job_id: Optional[str] = None
    message: str
    symbols_count: int = 0


class DataStatusResponse(BaseModel):
    is_collecting: bool = False
    current_symbol: Optional[str] = None
    progress: float = 0.0  # 0-100
    completed: int = 0
    total: int = 0
    errors: List[str] = []
    last_collection: Optional[datetime] = None


# Sentiment Models
class SentimentSubmitRequest(BaseModel):
    symbols: Optional[List[str]] = None  # None = all with pending sentiment
    force_reprocess: bool = False


class SentimentStatusResponse(BaseModel):
    batch_id: Optional[str] = None
    status: str  # "pending", "processing", "completed", "failed"
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# Calculation Models
class CalculateRequest(BaseModel):
    symbols: Optional[List[str]] = None  # None = all symbols
    recalculate: bool = False


class CalculateResponse(BaseModel):
    status: str  # "completed", "failed"
    symbols_calculated: int = 0
    symbols_failed: int = 0
    message: str
    calculation_date: date = Field(default_factory=date.today)


# Metrics Summary
class TableStats(BaseModel):
    name: str
    record_count: int
    last_updated: Optional[datetime] = None


class MetricsSummary(BaseModel):
    database_size_mb: float
    total_stocks: int
    active_stocks: int
    tables: List[TableStats]
    data_freshness: Dict[str, Any]
    last_calculation: Optional[datetime] = None


# WebSocket Progress
class ProgressUpdate(BaseModel):
    type: str  # "data_refresh", "sentiment", "calculation"
    status: str  # "started", "progress", "completed", "error"
    current: int = 0
    total: int = 0
    progress: float = 0.0
    message: str = ""
    symbol: Optional[str] = None
    error: Optional[str] = None
