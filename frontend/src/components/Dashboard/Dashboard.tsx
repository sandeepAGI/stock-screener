import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { TrendingDown, TrendingUp, Activity, BarChart3 } from 'lucide-react';
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

// Stock card component for Top 5 lists
function TopStockCard({
  stock,
  rank,
  type,
  customScore,
}: {
  stock: RankingEntry;
  rank: number;
  type: 'undervalued' | 'overvalued';
  customScore?: number;
}) {
  const bgColor = type === 'undervalued' ? 'bg-emerald-50' : 'bg-red-50';
  const borderColor = type === 'undervalued' ? 'border-emerald-200' : 'border-red-200';
  const iconBgColor = type === 'undervalued' ? 'bg-emerald-100' : 'bg-red-100';
  const iconColor = type === 'undervalued' ? 'text-emerald-600' : 'text-red-600';
  const Icon = type === 'undervalued' ? TrendingDown : TrendingUp;

  return (
    <Link
      to={`/analysis?symbol=${stock.symbol}`}
      className={`flex items-center justify-between p-3 rounded-lg border ${bgColor} ${borderColor} hover:shadow-md transition-all`}
    >
      <div className="flex items-center gap-3">
        <div className={`w-8 h-8 ${iconBgColor} rounded-lg flex items-center justify-center`}>
          <span className={`text-sm font-bold ${iconColor}`}>#{rank}</span>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <p className="font-semibold text-gray-900">{stock.symbol}</p>
            <Icon className={`w-4 h-4 ${iconColor}`} />
          </div>
          <p className="text-xs text-gray-500 truncate max-w-[120px]">{stock.company_name}</p>
        </div>
      </div>
      <div className="text-right">
        <ScoreBadge score={customScore ?? stock.composite_score} size="sm" />
        {customScore !== undefined && customScore !== stock.composite_score && (
          <p className="text-xs text-gray-400 mt-0.5">
            Orig: {stock.composite_score.toFixed(1)}
          </p>
        )}
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
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null);

  const { calculateCustomScore, isDefault, normalizedWeights } = useWeightsContext();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [rankingsRes, metricsRes, sectorsRes, healthRes] = await Promise.all([
          api.getRankings({ limit: 500 }),
          api.getMetricsSummary(),
          api.getSectors(),
          api.getHealth(),
        ]);
        setRankings(rankingsRes.rankings);
        setMetrics(metricsRes);
        setSectors(sectorsRes.sectors);
        setHealth(healthRes);
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
    if (isDefault) {
      return rankings.map((r) => ({ ...r, customScore: r.composite_score }));
    }

    const withCustom = rankings.map((r) => ({
      ...r,
      customScore: calculateCustomScore({
        fundamental: r.fundamental_score,
        quality: r.quality_score,
        growth: r.growth_score,
        sentiment: r.sentiment_score,
      }),
    }));

    // Sort by custom score
    return [...withCustom].sort((a, b) => b.customScore - a.customScore);
  }, [rankings, isDefault, calculateCustomScore]);

  // Top 5 undervalued (highest scores)
  const top5Undervalued = useMemo(() => {
    return rankedStocks
      .filter(
        (r) =>
          r.outlier_category === 'strong_undervalued' || r.outlier_category === 'undervalued'
      )
      .slice(0, 5);
  }, [rankedStocks]);

  // Top 5 overvalued (lowest scores)
  const top5Overvalued = useMemo(() => {
    return rankedStocks
      .filter(
        (r) => r.outlier_category === 'strong_overvalued' || r.outlier_category === 'overvalued'
      )
      .sort((a, b) => a.customScore - b.customScore)
      .slice(0, 5);
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

  // Average score
  const avgScore = useMemo(() => {
    if (rankedStocks.length === 0) return 0;
    const sum = rankedStocks.reduce((acc, r) => acc + r.customScore, 0);
    return sum / rankedStocks.length;
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
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500">Overview of stock analysis data</p>
        </div>
        <div className="flex items-center gap-4">
          {!isDefault && (
            <div className="text-right text-xs">
              <p className="text-gray-500">Custom Weights Active</p>
              <p className="font-medium text-blue-600">
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

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          label="Active Stocks"
          value={metrics?.active_stocks || 0}
          subvalue={`of ${metrics?.total_stocks || 0} total`}
        />
        <MetricCard
          label="Database Size"
          value={`${metrics?.database_size_mb?.toFixed(1) || 0} MB`}
          subvalue={`${metrics?.tables?.length || 0} tables`}
        />
        <MetricCard label="Sectors" value={sectors.length} subvalue="Active sectors" />
        <MetricCard
          label="Avg Score"
          value={avgScore.toFixed(1)}
          subvalue={isDefault ? 'Original weights' : 'Custom weights'}
        />
        <MetricCard
          label="Last Calculation"
          value={
            metrics?.last_calculation
              ? new Date(metrics.last_calculation).toLocaleDateString()
              : 'Never'
          }
          subvalue="Composite scores"
        />
      </div>

      {/* Top 5 Undervalued & Overvalued */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top 5 Undervalued */}
        <Card>
          <CardHeader
            title="Top 5 Undervalued"
            subtitle={isDefault ? 'Highest potential stocks' : 'Based on custom weights'}
            action={
              <Link
                to="/rankings?category=strong_undervalued"
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                View all
              </Link>
            }
          />
          <div className="space-y-2">
            {top5Undervalued.length > 0 ? (
              top5Undervalued.map((stock, i) => (
                <TopStockCard
                  key={stock.symbol}
                  stock={stock}
                  rank={i + 1}
                  type="undervalued"
                  customScore={isDefault ? undefined : stock.customScore}
                />
              ))
            ) : (
              <p className="text-sm text-gray-500 text-center py-4">No undervalued stocks found</p>
            )}
          </div>
        </Card>

        {/* Top 5 Overvalued */}
        <Card>
          <CardHeader
            title="Top 5 Overvalued"
            subtitle={isDefault ? 'Potentially overpriced stocks' : 'Based on custom weights'}
            action={
              <Link
                to="/rankings?category=strong_overvalued"
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                View all
              </Link>
            }
          />
          <div className="space-y-2">
            {top5Overvalued.length > 0 ? (
              top5Overvalued.map((stock, i) => (
                <TopStockCard
                  key={stock.symbol}
                  stock={stock}
                  rank={i + 1}
                  type="overvalued"
                  customScore={isDefault ? undefined : stock.customScore}
                />
              ))
            ) : (
              <p className="text-sm text-gray-500 text-center py-4">No overvalued stocks found</p>
            )}
          </div>
        </Card>
      </div>

      {/* Distribution Charts */}
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
                  {histogramData.map((entry, index) => {
                    // Color based on score range
                    let color = '#6b7280'; // gray for middle
                    if (entry.max <= 35) color = '#ef4444'; // red for low
                    else if (entry.max <= 50) color = '#f97316'; // orange
                    else if (entry.min >= 65) color = '#10b981'; // green for high
                    else if (entry.min >= 50) color = '#3b82f6'; // blue
                    return <Cell key={`cell-${index}`} fill={color} />;
                  })}
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

      {/* Sector Distribution */}
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

      {/* Data Tables */}
      <Card>
        <CardHeader title="Data Tables" subtitle="Record counts by table" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metrics?.tables?.slice(0, 8).map((table) => (
            <div key={table.name} className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-600">{table.name.replace(/_/g, ' ')}</p>
              <p className="text-lg font-semibold text-gray-900">
                {table.record_count.toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
