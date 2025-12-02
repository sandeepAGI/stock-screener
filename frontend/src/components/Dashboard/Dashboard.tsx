import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { TrendingDown, TrendingUp, Activity, BarChart3, Factory } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
} from 'recharts';
import { api } from '../../api/client';
import { useWeightsContext } from '../../context/WeightsContext';
import { Card, CardHeader, MetricCard } from '../common/Card';
import { Loading } from '../common/Loading';
import { ScoreBadge } from '../common/ScoreBadge';
import type { RankingEntry, MetricsSummary, SectorInfo } from '../../types';

// Sector performance data type
interface SectorPerformance {
  sector: string;
  stock_count: number;
  avg_composite: number | null;
  avg_fundamental: number | null;
  avg_quality: number | null;
  avg_growth: number | null;
  avg_sentiment: number | null;
}

// Stock card component for Top 5 lists - matching Streamlit's show_top_performers
function TopStockCard({
  stock,
  rank,
  type,
  customScore,
}: {
  stock: RankingEntry;
  rank: number;
  type: 'undervalued' | 'overvalued';
  customScore: number;
}) {
  const borderColor = type === 'undervalued' ? 'border-l-green-500' : 'border-l-red-500';
  const bgColor = type === 'undervalued' ? 'bg-green-50' : 'bg-red-50';

  return (
    <Link
      to={`/analysis?symbol=${stock.symbol}`}
      className={`block p-3 rounded-lg border-l-4 ${borderColor} ${bgColor} hover:shadow-md transition-all mb-2`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-bold text-gray-900">{stock.symbol}</span>
            {type === 'undervalued' ? (
              <TrendingDown className="w-4 h-4 text-green-600" />
            ) : (
              <TrendingUp className="w-4 h-4 text-red-600" />
            )}
          </div>
          <p className="text-xs text-gray-500 truncate">{stock.company_name}</p>
        </div>
        <div className="text-center px-3">
          <p className="text-xs text-gray-500">Sector</p>
          <p className="text-xs font-medium text-gray-700 truncate max-w-[80px]">{stock.sector}</p>
        </div>
        <div className="text-center px-3">
          <p className="text-xs text-gray-500">Score</p>
          <ScoreBadge score={customScore} size="sm" />
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">Rank</p>
          <p className="text-sm font-bold text-gray-900">#{rank}</p>
        </div>
      </div>
    </Link>
  );
}

// Category distribution colors
const CATEGORY_COLORS: Record<string, string> = {
  strong_undervalued: '#10b981',
  undervalued: '#34d399',
  fairly_valued: '#6b7280',
  overvalued: '#f87171',
  strong_overvalued: '#ef4444',
};

const CATEGORY_LABELS: Record<string, string> = {
  strong_undervalued: 'Strong Undervalued',
  undervalued: 'Undervalued',
  fairly_valued: 'Fairly Valued',
  overvalued: 'Overvalued',
  strong_overvalued: 'Strong Overvalued',
};

export function Dashboard() {
  const [rankings, setRankings] = useState<RankingEntry[]>([]);
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [sectors, setSectors] = useState<SectorInfo[]>([]);
  const [sectorPerformance, setSectorPerformance] = useState<SectorPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null);

  const { calculateCustomScore, isDefault, normalizedWeights } = useWeightsContext();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [rankingsRes, metricsRes, sectorsRes, healthRes, sectorPerfRes] = await Promise.all([
          api.getRankings({ limit: 500 }),
          api.getMetricsSummary(),
          api.getSectors(),
          api.getHealth(),
          api.getSectorPerformance(),
        ]);
        setRankings(rankingsRes.rankings);
        setMetrics(metricsRes);
        setSectors(sectorsRes.sectors);
        setHealth(healthRes);
        setSectorPerformance(sectorPerfRes.sectors);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Calculate custom scores and re-rank if weights changed
  const rankedStocks = useMemo(() => {
    const withCustom = rankings.map((r, originalIndex) => ({
      ...r,
      customScore: isDefault
        ? r.composite_score
        : calculateCustomScore({
            fundamental: r.fundamental_score,
            quality: r.quality_score,
            growth: r.growth_score,
            sentiment: r.sentiment_score,
          }),
      originalRank: originalIndex + 1,
    }));

    // Sort by custom score (descending - highest score first)
    return [...withCustom].sort((a, b) => b.customScore - a.customScore);
  }, [rankings, isDefault, calculateCustomScore]);

  // Top 5 Undervalued = Top 5 highest scores (best stocks)
  const top5Undervalued = useMemo(() => {
    return rankedStocks.slice(0, 5);
  }, [rankedStocks]);

  // Top 5 Overvalued = Bottom 5 lowest scores (worst stocks)
  const top5Overvalued = useMemo(() => {
    return [...rankedStocks].sort((a, b) => a.customScore - b.customScore).slice(0, 5);
  }, [rankedStocks]);

  // Score distribution histogram data
  const histogramData = useMemo(() => {
    if (rankedStocks.length === 0) return [];

    const scores = rankedStocks.map((r) => r.customScore);
    const min = Math.floor(Math.min(...scores) / 5) * 5;
    const max = Math.ceil(Math.max(...scores) / 5) * 5;
    const binSize = 5;
    const bins: { range: string; count: number; min: number; max: number }[] = [];

    for (let i = min; i < max; i += binSize) {
      const binMin = i;
      const binMax = i + binSize;
      const count = scores.filter((s) => s >= binMin && s < binMax).length;
      bins.push({
        range: `${binMin}-${binMax}`,
        count,
        min: binMin,
        max: binMax,
      });
    }

    return bins;
  }, [rankedStocks]);

  // Category distribution data
  const categoryDistribution = useMemo(() => {
    const counts: Record<string, number> = {};
    rankedStocks.forEach((r) => {
      const cat = r.outlier_category || 'fairly_valued';
      counts[cat] = (counts[cat] || 0) + 1;
    });

    return Object.entries(counts).map(([category, count]) => ({
      name: CATEGORY_LABELS[category] || category,
      value: count,
      color: CATEGORY_COLORS[category] || '#6b7280',
    }));
  }, [rankedStocks]);

  // Statistical summary calculations
  const stats = useMemo(() => {
    if (rankedStocks.length === 0) {
      return { mean: 0, median: 0, std: 0, q25: 0, q75: 0, iqr: 0 };
    }

    const scores = rankedStocks.map((r) => r.customScore).sort((a, b) => a - b);
    const n = scores.length;

    // Mean
    const mean = scores.reduce((a, b) => a + b, 0) / n;

    // Median
    const median = n % 2 === 0 ? (scores[n / 2 - 1] + scores[n / 2]) / 2 : scores[Math.floor(n / 2)];

    // Standard deviation
    const variance = scores.reduce((acc, s) => acc + Math.pow(s - mean, 2), 0) / n;
    const std = Math.sqrt(variance);

    // Quartiles
    const q25 = scores[Math.floor(n * 0.25)];
    const q75 = scores[Math.floor(n * 0.75)];
    const iqr = q75 - q25;

    return { mean, median, std, q25, q75, iqr };
  }, [rankedStocks]);

  if (loading) {
    return <Loading message="Loading dashboard..." />;
  }

  // Prepare sector chart data
  const sectorChartData = sectors.slice(0, 8).map((s) => ({
    name: s.sector.length > 15 ? s.sector.slice(0, 12) + '...' : s.sector,
    count: s.count,
  }));

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analysis Summary</h1>
          <p className="text-gray-500">S&amp;P 500 Stock Analysis Dashboard</p>
        </div>
        <div className="flex items-center gap-4">
          {!isDefault && (
            <div className="text-right text-xs bg-blue-50 px-3 py-2 rounded-lg border border-blue-200">
              <p className="text-blue-600 font-medium">Custom Weights Active</p>
              <p className="text-blue-800">
                F:{(normalizedWeights.fundamental * 100).toFixed(0)}% /
                Q:{(normalizedWeights.quality * 100).toFixed(0)}% /
                G:{(normalizedWeights.growth * 100).toFixed(0)}% /
                S:{(normalizedWeights.sentiment * 100).toFixed(0)}%
              </p>
            </div>
          )}
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Activity
              className={`w-4 h-4 ${health?.status === 'healthy' ? 'text-green-500' : 'text-red-500'}`}
            />
            <span>API {health?.status}</span>
          </div>
        </div>
      </div>

      {/* Summary Metrics - matching Streamlit */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Stocks Analyzed"
          value={`${metrics?.active_stocks || 0}/${metrics?.total_stocks || 0}`}
          subvalue={`${metrics?.active_stocks && metrics?.total_stocks ? ((metrics.active_stocks / metrics.total_stocks) * 100).toFixed(1) : 0}%`}
        />
        <MetricCard
          label="Data Quality"
          value="Enhanced"
          subvalue="v1.1 fallbacks"
        />
        <MetricCard
          label="Last Updated"
          value={
            metrics?.last_calculation
              ? new Date(metrics.last_calculation).toLocaleDateString()
              : 'Never'
          }
          subvalue="Auto-refresh"
        />
        <MetricCard
          label="Avg Score"
          value={stats.mean.toFixed(1)}
          subvalue="Market baseline"
        />
      </div>

      {/* Performance Leaders - matching Streamlit show_top_performers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Most Undervalued (Top 5) */}
        <Card>
          <CardHeader
            title="Most Undervalued (Top 5)"
            subtitle={isDefault ? 'Highest scoring stocks' : 'Based on custom weights'}
            action={
              <Link
                to="/rankings"
                className="text-sm text-green-600 hover:text-green-800"
              >
                View all
              </Link>
            }
          />
          <div>
            {top5Undervalued.length > 0 ? (
              top5Undervalued.map((stock, i) => (
                <TopStockCard
                  key={stock.symbol}
                  stock={stock}
                  rank={i + 1}
                  type="undervalued"
                  customScore={stock.customScore}
                />
              ))
            ) : (
              <p className="text-sm text-gray-500 text-center py-4">No data available</p>
            )}
          </div>
        </Card>

        {/* Most Overvalued (Bottom 5) */}
        <Card>
          <CardHeader
            title="Most Overvalued (Bottom 5)"
            subtitle={isDefault ? 'Lowest scoring stocks' : 'Based on custom weights'}
            action={
              <Link
                to="/rankings?ascending=true"
                className="text-sm text-red-600 hover:text-red-800"
              >
                View all
              </Link>
            }
          />
          <div>
            {top5Overvalued.length > 0 ? (
              top5Overvalued.map((stock, i) => (
                <TopStockCard
                  key={stock.symbol}
                  stock={stock}
                  rank={rankedStocks.length - i}
                  type="overvalued"
                  customScore={stock.customScore}
                />
              ))
            ) : (
              <p className="text-sm text-gray-500 text-center py-4">No data available</p>
            )}
          </div>
        </Card>
      </div>

      {/* Distribution Analysis - matching Streamlit */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Score Distribution Histogram */}
        <Card>
          <CardHeader
            title="Score Distribution"
            subtitle={isDefault ? 'Composite score histogram' : 'Custom score histogram'}
            action={<BarChart3 className="w-5 h-5 text-gray-400" />}
          />
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={histogramData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={60} />
                <YAxis />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-2 border border-gray-200 rounded shadow-sm">
                          <p className="font-medium">Score: {data.range}</p>
                          <p className="text-sm text-gray-600">{data.count} stocks</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {histogramData.map((_, index) => (
                    // Color based on score range - matching Streamlit blue theme
                    <Cell key={`cell-${index}`} fill="#636EFA" />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Category Distribution Pie Chart */}
        <Card>
          <CardHeader
            title="Category Distribution"
            subtitle="Stocks by valuation category"
          />
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ value }) => `${value}`}
                  labelLine={false}
                >
                  {categoryDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-2 border border-gray-200 rounded shadow-sm">
                          <p className="font-medium">{data.name}</p>
                          <p className="text-sm text-gray-600">{data.value} stocks</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend
                  layout="horizontal"
                  verticalAlign="bottom"
                  align="center"
                  wrapperStyle={{ fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Statistical Summary - matching Streamlit */}
      <Card>
        <CardHeader title="Statistical Summary" subtitle="Score distribution statistics" />
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="p-3 bg-gray-50 rounded-lg text-center">
            <p className="text-sm text-gray-500">Mean Score</p>
            <p className="text-xl font-bold text-gray-900">{stats.mean.toFixed(1)}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg text-center">
            <p className="text-sm text-gray-500">Std Deviation</p>
            <p className="text-xl font-bold text-gray-900">{stats.std.toFixed(1)}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg text-center">
            <p className="text-sm text-gray-500">Median Score</p>
            <p className="text-xl font-bold text-gray-900">{stats.median.toFixed(1)}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg text-center">
            <p className="text-sm text-gray-500">IQR</p>
            <p className="text-xl font-bold text-gray-900">{stats.iqr.toFixed(1)}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg text-center">
            <p className="text-sm text-gray-500">75th Percentile</p>
            <p className="text-xl font-bold text-gray-900">{stats.q75.toFixed(1)}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg text-center">
            <p className="text-sm text-gray-500">25th Percentile</p>
            <p className="text-xl font-bold text-gray-900">{stats.q25.toFixed(1)}</p>
          </div>
        </div>
      </Card>

      {/* Sector Performance - matching Streamlit */}
      <Card>
        <CardHeader
          title="Sector Performance"
          subtitle="Average scores by sector"
          action={<Factory className="w-5 h-5 text-gray-400" />}
        />
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sector
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Composite
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Stock Count
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Fund
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Quality
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Growth
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Sentiment
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sectorPerformance.map((sector) => (
                <tr key={sector.sector} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                    {sector.sector}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-right">
                    <ScoreBadge score={sector.avg_composite ?? 0} size="sm" />
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 text-right">
                    {sector.stock_count}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 text-right">
                    {sector.avg_fundamental?.toFixed(1) ?? '-'}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 text-right">
                    {sector.avg_quality?.toFixed(1) ?? '-'}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 text-right">
                    {sector.avg_growth?.toFixed(1) ?? '-'}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 text-right">
                    {sector.avg_sentiment?.toFixed(1) ?? '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Sector Distribution Bar Chart */}
      <Card>
        <CardHeader title="Sector Distribution" subtitle="Stocks by sector" />
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sectorChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Footer */}
      <div className="text-center text-sm text-gray-500 border-t pt-4">
        <p>
          <strong>Methodology:</strong> 4-component weighted analysis (Fundamental 40%, Quality 25%, Growth 20%, Sentiment 15%)
        </p>
        <p>
          <strong>Data Sources:</strong> Yahoo Finance, Reddit API
        </p>
        <p className="mt-2 text-amber-600">
          Disclaimer: For educational purposes only. Not investment advice.
        </p>
      </div>
    </div>
  );
}
