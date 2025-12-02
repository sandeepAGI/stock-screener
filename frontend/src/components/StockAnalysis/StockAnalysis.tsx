import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { useStock } from '../../hooks/useStocks';
import { Card, CardHeader, MetricCard } from '../common/Card';
import { Loading } from '../common/Loading';
import { OutlierBadge } from '../common/ScoreBadge';

export function StockAnalysis() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchInput, setSearchInput] = useState(searchParams.get('symbol') || '');

  const symbol = searchParams.get('symbol');
  const { stock, loading, error } = useStock(symbol);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setSearchParams({ symbol: searchInput.trim().toUpperCase() });
    }
  };

  // Prepare radar chart data
  const radarData = stock?.scores
    ? [
        { subject: 'Fundamental', value: stock.scores.fundamental_score || 0, fullMark: 100 },
        { subject: 'Quality', value: stock.scores.quality_score || 0, fullMark: 100 },
        { subject: 'Growth', value: stock.scores.growth_score || 0, fullMark: 100 },
        { subject: 'Sentiment', value: stock.scores.sentiment_score || 0, fullMark: 100 },
      ]
    : [];

  // Prepare price chart data
  const priceData =
    stock?.recent_prices
      ?.slice()
      .reverse()
      .map((p) => ({
        date: new Date(p.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        price: p.close,
      })) || [];

  return (
    <div className="p-6 space-y-6">
      {/* Header with Search */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Stock Analysis</h1>
          <p className="text-gray-500">Detailed analysis and scoring breakdown</p>
        </div>

        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Enter symbol (e.g., AAPL)"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value.toUpperCase())}
              className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none w-48"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Analyze
          </button>
        </form>
      </div>

      {!symbol && (
        <Card className="text-center py-12">
          <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Enter a stock symbol</h3>
          <p className="text-gray-500">Search for a stock to see detailed analysis</p>
        </Card>
      )}

      {loading && <Loading message={`Loading ${symbol}...`} />}

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg">
          Error: {error}
        </div>
      )}

      {stock && (
        <>
          {/* Stock Header */}
          <Card>
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="text-2xl font-bold text-gray-900">{stock.stock.symbol}</h2>
                  {stock.scores?.outlier_category && (
                    <OutlierBadge category={stock.scores.outlier_category} />
                  )}
                </div>
                <p className="text-lg text-gray-600">{stock.stock.company_name}</p>
                <p className="text-sm text-gray-500">
                  {stock.stock.sector} • {stock.stock.industry}
                </p>
              </div>

              {stock.scores?.composite_score && (
                <div className="text-right">
                  <p className="text-sm text-gray-500">Composite Score</p>
                  <p className="text-4xl font-bold text-gray-900">
                    {stock.scores.composite_score.toFixed(1)}
                  </p>
                  <p className="text-sm text-gray-500">
                    Sector Percentile: {stock.scores.sector_percentile?.toFixed(0) || '-'}%
                  </p>
                </div>
              )}
            </div>
          </Card>

          {/* Score Cards */}
          {stock.scores && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                label="Fundamental Score"
                value={stock.scores.fundamental_score?.toFixed(1) || '-'}
                subvalue="40% weight"
              />
              <MetricCard
                label="Quality Score"
                value={stock.scores.quality_score?.toFixed(1) || '-'}
                subvalue="25% weight"
              />
              <MetricCard
                label="Growth Score"
                value={stock.scores.growth_score?.toFixed(1) || '-'}
                subvalue="20% weight"
              />
              <MetricCard
                label="Sentiment Score"
                value={stock.scores.sentiment_score?.toFixed(1) || '-'}
                subvalue="15% weight"
              />
            </div>
          )}

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Score Radar */}
            <Card>
              <CardHeader title="Score Breakdown" subtitle="Component score comparison" />
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} />
                    <Radar
                      name="Score"
                      dataKey="value"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.5}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Price Chart */}
            <Card>
              <CardHeader
                title="Price History"
                subtitle="Last 30 days"
                action={
                  stock.fundamentals?.current_price && (
                    <span className="text-lg font-semibold">
                      ${stock.fundamentals.current_price.toFixed(2)}
                    </span>
                  )
                }
              />
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={priceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis domain={['auto', 'auto']} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="price"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          {/* Fundamentals */}
          {stock.fundamentals && (
            <Card>
              <CardHeader title="Key Fundamentals" subtitle="Financial metrics" />
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">P/E Ratio</p>
                  <p className="text-lg font-semibold">{stock.fundamentals.pe_ratio?.toFixed(1) || '-'}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Forward P/E</p>
                  <p className="text-lg font-semibold">{stock.fundamentals.forward_pe?.toFixed(1) || '-'}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">PEG Ratio</p>
                  <p className="text-lg font-semibold">{stock.fundamentals.peg_ratio?.toFixed(2) || '-'}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">P/B Ratio</p>
                  <p className="text-lg font-semibold">{stock.fundamentals.price_to_book?.toFixed(2) || '-'}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">ROE</p>
                  <p className="text-lg font-semibold">
                    {stock.fundamentals.return_on_equity
                      ? `${(stock.fundamentals.return_on_equity * 100).toFixed(1)}%`
                      : '-'}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Debt/Equity</p>
                  <p className="text-lg font-semibold">{stock.fundamentals.debt_to_equity?.toFixed(2) || '-'}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Revenue Growth</p>
                  <p className="text-lg font-semibold">
                    {stock.fundamentals.revenue_growth
                      ? `${(stock.fundamentals.revenue_growth * 100).toFixed(1)}%`
                      : '-'}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Earnings Growth</p>
                  <p className="text-lg font-semibold">
                    {stock.fundamentals.earnings_growth
                      ? `${(stock.fundamentals.earnings_growth * 100).toFixed(1)}%`
                      : '-'}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Dividend Yield</p>
                  <p className="text-lg font-semibold">
                    {stock.fundamentals.dividend_yield
                      ? `${(stock.fundamentals.dividend_yield * 100).toFixed(2)}%`
                      : '-'}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Beta</p>
                  <p className="text-lg font-semibold">{stock.fundamentals.beta?.toFixed(2) || '-'}</p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">52W High</p>
                  <p className="text-lg font-semibold">
                    {stock.fundamentals.week_52_high ? `$${stock.fundamentals.week_52_high.toFixed(2)}` : '-'}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">52W Low</p>
                  <p className="text-lg font-semibold">
                    {stock.fundamentals.week_52_low ? `$${stock.fundamentals.week_52_low.toFixed(2)}` : '-'}
                  </p>
                </div>
              </div>
            </Card>
          )}

          {/* Sentiment */}
          {stock.sentiment && (
            <Card>
              <CardHeader title="Sentiment Analysis" subtitle="News and social media sentiment" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">News Sentiment</p>
                  <p className="text-2xl font-semibold">
                    {stock.sentiment.news_sentiment?.toFixed(2) || '-'}
                  </p>
                  <p className="text-xs text-gray-400">{stock.sentiment.news_count} articles</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-500">Reddit Sentiment</p>
                  <p className="text-2xl font-semibold">
                    {stock.sentiment.reddit_sentiment?.toFixed(2) || '-'}
                  </p>
                  <p className="text-xs text-gray-400">{stock.sentiment.reddit_count} posts</p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg col-span-2">
                  <p className="text-sm text-gray-500">Combined Sentiment</p>
                  <p className="text-2xl font-semibold">
                    {stock.sentiment.combined_sentiment?.toFixed(2) || '-'}
                  </p>
                  <p className="text-xs text-gray-400">Weighted average</p>
                </div>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
