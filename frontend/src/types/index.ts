// Stock types
export interface Stock {
  symbol: string;
  company_name: string | null;
  sector: string | null;
  industry: string | null;
  market_cap: number | null;
  is_active: boolean;
}

export interface StockScores {
  fundamental_score: number | null;
  quality_score: number | null;
  growth_score: number | null;
  sentiment_score: number | null;
  composite_score: number | null;
  sector_percentile: number | null;
  market_percentile: number | null;
  outlier_category: OutlierCategory | null;
}

export interface StockFundamentals {
  pe_ratio: number | null;
  forward_pe: number | null;
  peg_ratio: number | null;
  price_to_book: number | null;
  ev_to_ebitda: number | null;
  return_on_equity: number | null;
  return_on_assets: number | null;
  debt_to_equity: number | null;
  current_ratio: number | null;
  revenue_growth: number | null;
  earnings_growth: number | null;
  current_price: number | null;
  week_52_high: number | null;
  week_52_low: number | null;
  dividend_yield: number | null;
  beta: number | null;
}

export interface StockSentiment {
  news_sentiment: number | null;
  news_count: number;
  reddit_sentiment: number | null;
  reddit_count: number;
  combined_sentiment: number | null;
}

export interface PriceData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adjusted_close: number | null;
}

export interface StockDetail {
  stock: Stock;
  scores: StockScores | null;
  fundamentals: StockFundamentals | null;
  sentiment: StockSentiment | null;
  recent_prices: PriceData[] | null;
  last_updated: string | null;
}

// Extended types for Stock Analysis
export interface NewsArticle {
  id: number;
  title: string;
  summary: string | null;
  publisher: string | null;
  publish_date: string | null;
  url: string | null;
  sentiment_score: number | null;
}

export interface RedditPost {
  id: number;
  post_id: string;
  title: string;
  content: string | null;
  subreddit: string | null;
  author: string | null;
  score: number;
  upvote_ratio: number | null;
  num_comments: number;
  created_utc: string | null;
  url: string | null;
  sentiment_score: number | null;
}

export interface FundamentalsWithPrevious extends StockFundamentals {
  pe_ratio_prev: number | null;
  forward_pe_prev: number | null;
  peg_ratio_prev: number | null;
  price_to_book_prev: number | null;
  ev_to_ebitda_prev: number | null;
  return_on_equity_prev: number | null;
  return_on_assets_prev: number | null;
  debt_to_equity_prev: number | null;
  current_ratio_prev: number | null;
  revenue_growth_prev: number | null;
  earnings_growth_prev: number | null;
}

export interface HistoricalMetric {
  date: string;
  pe_ratio: number | null;
  peg_ratio: number | null;
  composite_score: number | null;
}

export interface PeerStock {
  symbol: string;
  company_name: string | null;
  sector: string | null;
  industry: string | null;
  composite_score: number | null;
  fundamental_score: number | null;
  quality_score: number | null;
  growth_score: number | null;
  sentiment_score: number | null;
}

export interface InvestmentInsight {
  component: string;
  score: number;
  description: string;
}

export interface InvestmentInsights {
  strengths: InvestmentInsight[];
  weaknesses: InvestmentInsight[];
}

export interface StockExtendedDetail {
  stock: Stock;
  scores: StockScores | null;
  fundamentals: FundamentalsWithPrevious | null;
  sentiment: StockSentiment | null;
  recent_prices: PriceData[] | null;
  news_articles: NewsArticle[];
  reddit_posts: RedditPost[];
  historical_metrics: HistoricalMetric[];
  industry_peers: PeerStock[];
  sector_peers: PeerStock[];
  insights: InvestmentInsights | null;
  last_updated: string | null;
}

export interface StockListResponse {
  stocks: Stock[];
  total: number;
  active_count: number;
}

// Ranking types
export type OutlierCategory =
  | 'strong_undervalued'
  | 'undervalued'
  | 'fairly_valued'
  | 'overvalued'
  | 'strong_overvalued';

export interface RankingEntry {
  rank: number;
  symbol: string;
  company_name: string | null;
  sector: string | null;
  composite_score: number;
  fundamental_score: number | null;
  quality_score: number | null;
  growth_score: number | null;
  sentiment_score: number | null;
  outlier_category: OutlierCategory | null;
  data_quality: number | null;
}

export interface RankingsResponse {
  rankings: RankingEntry[];
  total: number;
  sector: string | null;
  calculation_date: string | null;
}

// Sector type
export interface SectorInfo {
  sector: string;
  count: number;
}

// Data management types
export interface DataRefreshRequest {
  symbols?: string[];
  data_types: string[];
  force: boolean;
}

export interface DataRefreshResponse {
  status: string;
  job_id: string | null;
  message: string;
  symbols_count: number;
}

export interface DataStatusResponse {
  is_collecting: boolean;
  current_symbol: string | null;
  progress: number;
  completed: number;
  total: number;
  errors: string[];
  last_collection: string | null;
}

// Metrics types
export interface TableStats {
  name: string;
  record_count: number;
  last_updated: string | null;
}

export interface MetricsSummary {
  database_size_mb: number;
  total_stocks: number;
  active_stocks: number;
  tables: TableStats[];
  data_freshness: Record<string, unknown>;
  last_calculation: string | null;
}

// Health check
export interface HealthResponse {
  status: string;
  database_connected: boolean;
  version: string;
  timestamp: string;
}

// WebSocket progress
export interface ProgressUpdate {
  type: 'data_refresh' | 'sentiment' | 'calculation';
  status: 'started' | 'progress' | 'completed' | 'error';
  current: number;
  total: number;
  progress: number;
  message: string;
  symbol?: string;
  error?: string;
}
