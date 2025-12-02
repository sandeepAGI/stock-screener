import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { TrendingDown, Activity } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { api } from '../../api/client';
import { Card, CardHeader, MetricCard } from '../common/Card';
import { Loading } from '../common/Loading';
import { ScoreBadge } from '../common/ScoreBadge';
import type { RankingEntry, MetricsSummary, SectorInfo } from '../../types';

export function Dashboard() {
  const [topOutliers, setTopOutliers] = useState<RankingEntry[]>([]);
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [sectors, setSectors] = useState<SectorInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [outliersRes, metricsRes, sectorsRes, healthRes] = await Promise.all([
          api.getOutliers('strong_undervalued', { limit: 10 }),
          api.getMetricsSummary(),
          api.getSectors(),
          api.getHealth(),
        ]);
        setTopOutliers(outliersRes.outliers);
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

  if (loading) {
    return <Loading message="Loading dashboard..." />;
  }

  // Prepare sector chart data
  const sectorChartData = sectors.slice(0, 8).map((s) => ({
    name: s.sector.length > 12 ? s.sector.slice(0, 12) + '...' : s.sector,
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
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Activity className={`w-4 h-4 ${health?.status === 'healthy' ? 'text-green-500' : 'text-red-500'}`} />
          <span>API {health?.status}</span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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
        <MetricCard
          label="Sectors"
          value={sectors.length}
          subvalue="Active sectors"
        />
        <MetricCard
          label="Last Calculation"
          value={metrics?.last_calculation ? new Date(metrics.last_calculation).toLocaleDateString() : 'Never'}
          subvalue="Composite scores"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sector Distribution */}
        <Card>
          <CardHeader title="Sector Distribution" subtitle="Stocks by sector" />
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sectorChartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Top Undervalued Stocks */}
        <Card>
          <CardHeader
            title="Top Undervalued Stocks"
            subtitle="Strong undervalued by composite score"
            action={
              <Link to="/rankings?category=strong_undervalued" className="text-sm text-blue-600 hover:text-blue-800">
                View all
              </Link>
            }
          />
          <div className="space-y-2">
            {topOutliers.slice(0, 5).map((stock) => (
              <Link
                key={stock.symbol}
                to={`/analysis?symbol=${stock.symbol}`}
                className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                    <TrendingDown className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{stock.symbol}</p>
                    <p className="text-sm text-gray-500">{stock.sector || 'Unknown'}</p>
                  </div>
                </div>
                <ScoreBadge score={stock.composite_score} />
              </Link>
            ))}
            {topOutliers.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">No outliers found</p>
            )}
          </div>
        </Card>
      </div>

      {/* Data Tables */}
      <Card>
        <CardHeader title="Data Tables" subtitle="Record counts by table" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metrics?.tables?.slice(0, 8).map((table) => (
            <div key={table.name} className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-600">
                {table.name.replace(/_/g, ' ')}
              </p>
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
