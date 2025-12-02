import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Search,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  MessageSquare,
  Newspaper,
  Lightbulb,
  AlertTriangle,
} from 'lucide-react';
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
  BarChart,
  Bar,
  Cell,
} from 'recharts';
import { useStockExtended } from '../../hooks/useStocks';
import { useWeightsContext } from '../../context/WeightsContext';
import { Card, CardHeader, MetricCard } from '../common/Card';
import { Loading } from '../common/Loading';
import { OutlierBadge } from '../common/ScoreBadge';
import type { PeerStock } from '../../types';

// Helper to format trend
function TrendIndicator({ current, previous }: { current: number | null; previous: number | null }) {
  if (current === null || previous === null) return <Minus className="w-4 h-4 text-gray-400" />;

  const diff = current - previous;
  const pctChange = previous !== 0 ? (diff / Math.abs(previous)) * 100 : 0;

  if (Math.abs(pctChange) < 1) return <Minus className="w-4 h-4 text-gray-400" />;

  if (diff > 0) {
    return (
      <span className="flex items-center text-green-600 text-xs">
        <TrendingUp className="w-3 h-3 mr-0.5" />
        +{pctChange.toFixed(1)}%
      </span>
    );
  }
  return (
    <span className="flex items-center text-red-600 text-xs">
      <TrendingDown className="w-3 h-3 mr-0.5" />
      {pctChange.toFixed(1)}%
    </span>
  );
}

// Metric with comparison
function MetricWithTrend({
  label,
  value,
  prevValue,
  format = 'number',
}: {
  label: string;
  value: number | null;
  prevValue: number | null;
  format?: 'number' | 'percent' | 'currency';
}) {
  const formatValue = (v: number | null) => {
    if (v === null) return '-';
    if (format === 'percent') return `${(v * 100).toFixed(1)}%`;
    if (format === 'currency') return `$${v.toFixed(2)}`;
    return v.toFixed(2);
  };

  return (
    <div className="p-3 bg-gray-50 rounded-lg">
      <div className="flex justify-between items-start">
        <p className="text-xs text-gray-500">{label}</p>
        <TrendIndicator current={value} previous={prevValue} />
      </div>
      <p className="text-lg font-semibold mt-1">{formatValue(value)}</p>
      {prevValue !== null && (
        <p className="text-xs text-gray-400">Prev: {formatValue(prevValue)}</p>
      )}
    </div>
  );
}

// Expandable section
function ExpandableSection({
  title,
  icon: Icon,
  children,
  defaultOpen = false,
}: {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-gray-200 rounded-lg">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon className="w-5 h-5 text-gray-500" />
          <span className="font-medium text-gray-900">{title}</span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        )}
      </button>
      {isOpen && <div className="p-4 pt-0 border-t border-gray-200">{children}</div>}
    </div>
  );
}

// Sentiment badge
function SentimentBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-gray-400">-</span>;

  let bgColor = 'bg-gray-100 text-gray-800';
  let label = 'Neutral';

  if (score > 0.2) {
    bgColor = 'bg-green-100 text-green-800';
    label = 'Positive';
  } else if (score < -0.2) {
    bgColor = 'bg-red-100 text-red-800';
    label = 'Negative';
  }

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${bgColor}`}>
      {label} ({score.toFixed(2)})
    </span>
  );
}

// Peer comparison table
function PeerTable({ peers, title }: { peers: PeerStock[]; title: string }) {
  const navigate = useNavigate();

  if (peers.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500">
        No {title.toLowerCase()} available
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-2 px-2 font-medium text-gray-500">Symbol</th>
            <th className="text-left py-2 px-2 font-medium text-gray-500">Company</th>
            <th className="text-right py-2 px-2 font-medium text-gray-500">Composite</th>
            <th className="text-right py-2 px-2 font-medium text-gray-500">Fund.</th>
            <th className="text-right py-2 px-2 font-medium text-gray-500">Qual.</th>
            <th className="text-right py-2 px-2 font-medium text-gray-500">Growth</th>
            <th className="text-right py-2 px-2 font-medium text-gray-500">Sent.</th>
          </tr>
        </thead>
        <tbody>
          {peers.map((peer) => (
            <tr
              key={peer.symbol}
              className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
              onClick={() => navigate(`/analysis?symbol=${peer.symbol}`)}
            >
              <td className="py-2 px-2 font-medium text-blue-600">{peer.symbol}</td>
              <td className="py-2 px-2 text-gray-600 truncate max-w-[150px]">
                {peer.company_name}
              </td>
              <td className="py-2 px-2 text-right font-medium">
                {peer.composite_score?.toFixed(1) || '-'}
              </td>
              <td className="py-2 px-2 text-right text-gray-600">
                {peer.fundamental_score?.toFixed(0) || '-'}
              </td>
              <td className="py-2 px-2 text-right text-gray-600">
                {peer.quality_score?.toFixed(0) || '-'}
              </td>
              <td className="py-2 px-2 text-right text-gray-600">
                {peer.growth_score?.toFixed(0) || '-'}
              </td>
              <td className="py-2 px-2 text-right text-gray-600">
                {peer.sentiment_score?.toFixed(0) || '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function StockAnalysis() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchInput, setSearchInput] = useState(searchParams.get('symbol') || '');
  const { normalizedWeights, calculateCustomScore, isDefault } = useWeightsContext();

  const symbol = searchParams.get('symbol');
  const { stock, loading, error } = useStockExtended(symbol);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      setSearchParams({ symbol: searchInput.trim().toUpperCase() });
    }
  };

  // Calculate custom score if weights are modified
  const customScore = stock?.scores
    ? calculateCustomScore({
        fundamental: stock.scores.fundamental_score,
        quality: stock.scores.quality_score,
        growth: stock.scores.growth_score,
        sentiment: stock.scores.sentiment_score,
      })
    : null;

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

  // Prepare historical metrics chart data
  const historicalData =
    stock?.historical_metrics
      ?.slice()
      .reverse()
      .map((h) => ({
        date: new Date(h.date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
        pe: h.pe_ratio,
        peg: h.peg_ratio,
        composite: h.composite_score,
      })) || [];

  // Prepare sector comparison data
  const sectorComparisonData = stock?.sector_peers
    ? [
        { name: stock.stock.symbol, score: stock.scores?.composite_score || 0, isTarget: true },
        ...stock.sector_peers.slice(0, 5).map((p) => ({
          name: p.symbol,
          score: p.composite_score || 0,
          isTarget: false,
        })),
      ]
    : [];

  return (
    <div className="p-6 space-y-6">
      {/* Header with Search */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
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
        <div className="bg-red-50 text-red-700 p-4 rounded-lg">Error: {error}</div>
      )}

      {stock && (
        <>
          {/* Stock Header */}
          <Card>
            <div className="flex items-start justify-between flex-wrap gap-4">
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

              <div className="text-right">
                {stock.scores && stock.scores.composite_score !== null && (
                  <>
                    <p className="text-sm text-gray-500">
                      {isDefault ? 'Composite Score' : 'Custom Score'}
                    </p>
                    <p className="text-4xl font-bold text-gray-900">
                      {isDefault
                        ? stock.scores.composite_score?.toFixed(1)
                        : customScore?.toFixed(1)}
                    </p>
                    {!isDefault && stock.scores && (
                      <p className="text-xs text-gray-400">
                        Original: {stock.scores.composite_score?.toFixed(1)}
                      </p>
                    )}
                    <p className="text-sm text-gray-500 mt-1">
                      Sector Percentile: {stock.scores?.sector_percentile?.toFixed(0) || '-'}%
                    </p>
                  </>
                )}
              </div>
            </div>
          </Card>

          {/* Score Cards */}
          {stock.scores && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                label="Fundamental Score"
                value={stock.scores.fundamental_score?.toFixed(1) || '-'}
                subvalue={`${(normalizedWeights.fundamental * 100).toFixed(0)}% weight`}
              />
              <MetricCard
                label="Quality Score"
                value={stock.scores.quality_score?.toFixed(1) || '-'}
                subvalue={`${(normalizedWeights.quality * 100).toFixed(0)}% weight`}
              />
              <MetricCard
                label="Growth Score"
                value={stock.scores.growth_score?.toFixed(1) || '-'}
                subvalue={`${(normalizedWeights.growth * 100).toFixed(0)}% weight`}
              />
              <MetricCard
                label="Sentiment Score"
                value={stock.scores.sentiment_score?.toFixed(1) || '-'}
                subvalue={`${(normalizedWeights.sentiment * 100).toFixed(0)}% weight`}
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

          {/* Historical Trends */}
          {historicalData.length > 0 && (
            <Card>
              <CardHeader title="Historical Trends" subtitle="P/E, PEG, and Composite Score over time" />
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div className="h-48">
                  <p className="text-sm text-gray-500 mb-2 text-center">P/E Ratio</p>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={historicalData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                      <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Line type="monotone" dataKey="pe" stroke="#3b82f6" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="h-48">
                  <p className="text-sm text-gray-500 mb-2 text-center">PEG Ratio</p>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={historicalData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                      <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Line type="monotone" dataKey="peg" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="h-48">
                  <p className="text-sm text-gray-500 mb-2 text-center">Composite Score</p>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={historicalData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Line type="monotone" dataKey="composite" stroke="#10b981" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </Card>
          )}

          {/* Investment Insights */}
          {stock.insights && (stock.insights.strengths.length > 0 || stock.insights.weaknesses.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Strengths */}
              <Card className="border-l-4 border-l-green-500">
                <div className="flex items-center gap-2 mb-3">
                  <Lightbulb className="w-5 h-5 text-green-600" />
                  <h3 className="font-semibold text-gray-900">Strengths</h3>
                </div>
                {stock.insights.strengths.length > 0 ? (
                  <ul className="space-y-2">
                    {stock.insights.strengths.map((s, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <TrendingUp className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <span className="font-medium text-gray-900">{s.component}</span>
                          <span className="text-gray-500 ml-2">({s.score.toFixed(0)})</span>
                          <p className="text-sm text-gray-600">{s.description}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 text-sm">No significant strengths identified</p>
                )}
              </Card>

              {/* Weaknesses */}
              <Card className="border-l-4 border-l-amber-500">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-5 h-5 text-amber-600" />
                  <h3 className="font-semibold text-gray-900">Areas for Attention</h3>
                </div>
                {stock.insights.weaknesses.length > 0 ? (
                  <ul className="space-y-2">
                    {stock.insights.weaknesses.map((w, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <TrendingDown className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <span className="font-medium text-gray-900">{w.component}</span>
                          <span className="text-gray-500 ml-2">({w.score.toFixed(0)})</span>
                          <p className="text-sm text-gray-600">{w.description}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 text-sm">No significant concerns identified</p>
                )}
              </Card>
            </div>
          )}

          {/* Metrics with Comparison */}
          {stock.fundamentals && (
            <div className="space-y-4">
              <ExpandableSection title="Fundamental Metrics" icon={TrendingUp} defaultOpen>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                  <MetricWithTrend
                    label="P/E Ratio"
                    value={stock.fundamentals.pe_ratio}
                    prevValue={stock.fundamentals.pe_ratio_prev}
                  />
                  <MetricWithTrend
                    label="Forward P/E"
                    value={stock.fundamentals.forward_pe}
                    prevValue={stock.fundamentals.forward_pe_prev}
                  />
                  <MetricWithTrend
                    label="PEG Ratio"
                    value={stock.fundamentals.peg_ratio}
                    prevValue={stock.fundamentals.peg_ratio_prev}
                  />
                  <MetricWithTrend
                    label="P/B Ratio"
                    value={stock.fundamentals.price_to_book}
                    prevValue={stock.fundamentals.price_to_book_prev}
                  />
                </div>
              </ExpandableSection>

              <ExpandableSection title="Quality Metrics" icon={TrendingUp} defaultOpen>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                  <MetricWithTrend
                    label="ROE"
                    value={stock.fundamentals.return_on_equity}
                    prevValue={stock.fundamentals.return_on_equity_prev}
                    format="percent"
                  />
                  <MetricWithTrend
                    label="ROA"
                    value={stock.fundamentals.return_on_assets}
                    prevValue={stock.fundamentals.return_on_assets_prev}
                    format="percent"
                  />
                  <MetricWithTrend
                    label="Debt/Equity"
                    value={stock.fundamentals.debt_to_equity}
                    prevValue={stock.fundamentals.debt_to_equity_prev}
                  />
                  <MetricWithTrend
                    label="Current Ratio"
                    value={stock.fundamentals.current_ratio}
                    prevValue={stock.fundamentals.current_ratio_prev}
                  />
                </div>
              </ExpandableSection>

              <ExpandableSection title="Growth Metrics" icon={TrendingUp} defaultOpen>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                  <MetricWithTrend
                    label="Revenue Growth"
                    value={stock.fundamentals.revenue_growth}
                    prevValue={stock.fundamentals.revenue_growth_prev}
                    format="percent"
                  />
                  <MetricWithTrend
                    label="Earnings Growth"
                    value={stock.fundamentals.earnings_growth}
                    prevValue={stock.fundamentals.earnings_growth_prev}
                    format="percent"
                  />
                  <MetricWithTrend
                    label="EV/EBITDA"
                    value={stock.fundamentals.ev_to_ebitda}
                    prevValue={stock.fundamentals.ev_to_ebitda_prev}
                  />
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500">Dividend Yield</p>
                    <p className="text-lg font-semibold">
                      {stock.fundamentals.dividend_yield
                        ? `${(stock.fundamentals.dividend_yield * 100).toFixed(2)}%`
                        : '-'}
                    </p>
                  </div>
                </div>
              </ExpandableSection>
            </div>
          )}

          {/* Peer Comparison */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Industry Peers */}
            <Card>
              <CardHeader
                title="Industry Peers"
                subtitle={stock.stock.industry || 'Same industry'}
              />
              <PeerTable peers={stock.industry_peers} title="Industry peers" />
            </Card>

            {/* Sector Comparison Chart */}
            <Card>
              <CardHeader
                title="Sector Comparison"
                subtitle={`Top ${stock.stock.sector} performers`}
              />
              {sectorComparisonData.length > 0 ? (
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={sectorComparisonData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" domain={[0, 100]} />
                      <YAxis type="category" dataKey="name" width={60} tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                        {sectorComparisonData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={entry.isTarget ? '#3b82f6' : '#d1d5db'}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">No sector comparison data</div>
              )}
            </Card>
          </div>

          {/* News & Reddit */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* News Articles */}
            <Card>
              <CardHeader
                title="Recent News"
                subtitle={`${stock.news_articles.length} articles`}
                action={<Newspaper className="w-5 h-5 text-gray-400" />}
              />
              {stock.news_articles.length > 0 ? (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {stock.news_articles.slice(0, 10).map((article) => (
                    <div
                      key={article.id}
                      className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <a
                            href={article.url || '#'}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-gray-900 hover:text-blue-600 line-clamp-2"
                          >
                            {article.title}
                            {article.url && (
                              <ExternalLink className="inline w-3 h-3 ml-1 text-gray-400" />
                            )}
                          </a>
                          <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                            {article.summary}
                          </p>
                          <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                            <span>{article.publisher}</span>
                            {article.publish_date && (
                              <span>
                                {new Date(article.publish_date).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                        <SentimentBadge score={article.sentiment_score} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">No recent news articles</div>
              )}
            </Card>

            {/* Reddit Posts */}
            <Card>
              <CardHeader
                title="Reddit Discussions"
                subtitle={`${stock.reddit_posts.length} posts`}
                action={<MessageSquare className="w-5 h-5 text-gray-400" />}
              />
              {stock.reddit_posts.length > 0 ? (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {stock.reddit_posts.slice(0, 10).map((post) => (
                    <div
                      key={post.id}
                      className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <a
                            href={post.url || '#'}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-gray-900 hover:text-blue-600 line-clamp-2"
                          >
                            {post.title}
                            {post.url && (
                              <ExternalLink className="inline w-3 h-3 ml-1 text-gray-400" />
                            )}
                          </a>
                          <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                            <span className="text-orange-600">r/{post.subreddit}</span>
                            <span>⬆ {post.score}</span>
                            <span>💬 {post.num_comments}</span>
                            {post.created_utc && (
                              <span>
                                {new Date(post.created_utc).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                        <SentimentBadge score={post.sentiment_score} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">No recent Reddit posts</div>
              )}
            </Card>
          </div>

          {/* Sentiment Summary */}
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
