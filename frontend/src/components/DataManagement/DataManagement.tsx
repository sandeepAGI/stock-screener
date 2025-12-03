import { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw,
  Brain,
  Calculator,
  CheckCircle,
  AlertCircle,
  Loader2,
  Clock,
  AlertTriangle,
  Search,
} from 'lucide-react';
import { api } from '../../api/client';
import { Card, CardHeader, MetricCard } from '../common/Card';
import { Loading } from '../common/Loading';
import type { MetricsSummary, DataStatusResponse } from '../../types';

type OperationType = 'data' | 'sentiment' | 'calculate';

type DataType = 'fundamentals' | 'prices' | 'news' | 'reddit';

interface BatchInfo {
  batch_id: string;
  pending_count: number;
  completed_count: number;
  failed_count: number;
  created_at?: string;
}

// Freshness indicator component
function FreshnessIndicator({ lastUpdated, thresholds }: {
  lastUpdated: string | null;
  thresholds: { fresh: number; stale: number }; // days
}) {
  if (!lastUpdated) {
    return (
      <span className="inline-flex items-center gap-1 text-gray-400">
        <Clock className="w-4 h-4" />
        Never
      </span>
    );
  }

  const daysSince = Math.floor(
    (Date.now() - new Date(lastUpdated).getTime()) / (1000 * 60 * 60 * 24)
  );

  if (daysSince <= thresholds.fresh) {
    return (
      <span className="inline-flex items-center gap-1 text-green-600">
        <span className="w-2 h-2 rounded-full bg-green-500" />
        Fresh ({daysSince}d)
      </span>
    );
  }

  if (daysSince <= thresholds.stale) {
    return (
      <span className="inline-flex items-center gap-1 text-yellow-600">
        <span className="w-2 h-2 rounded-full bg-yellow-500" />
        Aging ({daysSince}d)
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 text-red-600">
      <span className="w-2 h-2 rounded-full bg-red-500" />
      Stale ({daysSince}d)
    </span>
  );
}

// Data source status card
function DataSourceCard({
  name,
  recordCount,
  lastUpdated,
  thresholds,
  icon,
}: {
  name: string;
  recordCount: number;
  lastUpdated: string | null;
  thresholds: { fresh: number; stale: number };
  icon: React.ReactNode;
}) {
  const daysSince = lastUpdated
    ? Math.floor((Date.now() - new Date(lastUpdated).getTime()) / (1000 * 60 * 60 * 24))
    : null;

  let statusColor = 'border-gray-200';
  if (daysSince !== null) {
    if (daysSince <= thresholds.fresh) statusColor = 'border-l-green-500';
    else if (daysSince <= thresholds.stale) statusColor = 'border-l-yellow-500';
    else statusColor = 'border-l-red-500';
  }

  return (
    <div className={`bg-white rounded-lg border-l-4 ${statusColor} border border-gray-200 p-4`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          {icon}
          <div>
            <h4 className="font-medium text-gray-900">{name}</h4>
            <p className="text-sm text-gray-500">{recordCount.toLocaleString()} records</p>
          </div>
        </div>
        <FreshnessIndicator lastUpdated={lastUpdated} thresholds={thresholds} />
      </div>
    </div>
  );
}

export function DataManagement() {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [dataStatus, setDataStatus] = useState<DataStatusResponse | null>(null);
  const [pendingSentiment, setPendingSentiment] = useState<{
    news_pending: number;
    reddit_pending: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [operation, setOperation] = useState<OperationType | null>(null);
  const [operationStatus, setOperationStatus] = useState<string>('');
  const [selectedDataTypes, setSelectedDataTypes] = useState<DataType[]>([
    'fundamentals',
    'prices',
    'news',
    'reddit',
  ]);
  const [activeBatches, setActiveBatches] = useState<BatchInfo[]>([]);
  const [pollingBatch, setPollingBatch] = useState<string | null>(null);
  const [pollResult, setPollResult] = useState<{
    success: boolean;
    message?: string;
    anthropic_status?: string;
    results_retrieved?: boolean;
  } | null>(null);

  const fetchBatches = useCallback(async () => {
    try {
      const response = await api.getSentimentBatches();
      setActiveBatches(response.batches || []);
    } catch (error) {
      console.error('Failed to fetch batches:', error);
    }
  }, []);

  const fetchStatus = async () => {
    try {
      const [metricsRes, statusRes, pendingRes] = await Promise.all([
        api.getMetricsSummary(),
        api.getDataStatus(),
        api.getPendingSentiment(),
      ]);
      setMetrics(metricsRes);
      setDataStatus(statusRes);
      setPendingSentiment(pendingRes);
    } catch (error) {
      console.error('Failed to fetch status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchBatches();
    const interval = setInterval(() => {
      fetchStatus();
      fetchBatches();
    }, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [fetchBatches]);

  const toggleDataType = (type: DataType) => {
    setSelectedDataTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const handleRefreshData = async () => {
    if (selectedDataTypes.length === 0) {
      setOperationStatus('Please select at least one data type to refresh');
      return;
    }
    setOperation('data');
    setOperationStatus(`Starting refresh for: ${selectedDataTypes.join(', ')}...`);
    try {
      const response = await api.refreshData({
        data_types: selectedDataTypes,
        force: false,
      });
      setOperationStatus(response.message);
    } catch (error) {
      setOperationStatus(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleProcessSentiment = async () => {
    setOperation('sentiment');
    setOperationStatus('Submitting sentiment batch...');
    try {
      const response = await api.submitSentiment();
      if (response.status === 'no_items' || response.total_items === 0) {
        setOperationStatus('All items already have sentiment scores - nothing to process');
      } else if (response.status === 'already_processing') {
        setOperationStatus(`Batch already in progress: ${response.total_items || 0} items`);
      } else {
        setOperationStatus(`Batch submitted: ${response.total_items || 0} items`);
      }
    } catch (error) {
      setOperationStatus(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setOperation(null);
    }
  };

  const handleRunCalculations = async () => {
    setOperation('calculate');
    setOperationStatus('Running calculations...');
    try {
      const response = await api.runCalculations();
      setOperationStatus(response.message);
    } catch (error) {
      setOperationStatus(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setOperation(null);
    }
  };

  const handleSyncSP500 = async () => {
    setOperationStatus('Syncing S&P 500 list...');
    try {
      const response = await api.syncSP500();
      setOperationStatus(response.message || 'S&P 500 sync completed');
    } catch (error) {
      setOperationStatus(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handlePollBatch = async (batchId: string) => {
    setPollingBatch(batchId);
    setPollResult(null);
    try {
      const response = await api.pollBatchStatus(batchId);
      setPollResult(response);
      if (response.results_retrieved) {
        // Refresh status after results are retrieved
        fetchStatus();
        fetchBatches();
        setOperationStatus(`Batch completed: ${response.successful_updates || 0} items processed`);
      }
    } catch (error) {
      setPollResult({
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setPollingBatch(null);
    }
  };

  // Helper to get table info
  const getTableInfo = (tableName: string) => {
    const table = metrics?.tables?.find((t) => t.name === tableName);
    return {
      count: table?.record_count || 0,
      lastUpdated: table?.last_updated || null,
    };
  };

  if (loading) {
    return <Loading message="Loading data status..." />;
  }

  const fundamentals = getTableInfo('fundamental_data');
  const prices = getTableInfo('price_data');
  const news = getTableInfo('news_articles');
  const reddit = getTableInfo('reddit_posts');
  const calculated = getTableInfo('calculated_metrics');

  // Check if any data source is stale
  const hasStaleData = metrics?.tables?.some((table) => {
    if (!table.last_updated) return true;
    const daysSince = Math.floor(
      (Date.now() - new Date(table.last_updated).getTime()) / (1000 * 60 * 60 * 24)
    );
    return daysSince > 7; // More than 7 days
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Data Management</h1>
          <p className="text-gray-500">
            Manage data collection, sentiment processing, and calculations
          </p>
        </div>
        {hasStaleData && (
          <div className="flex items-center gap-2 px-3 py-1 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700 text-sm">
            <AlertTriangle className="w-4 h-4" />
            Some data sources need refresh
          </div>
        )}
      </div>

      {/* Data Source Freshness */}
      <Card>
        <CardHeader
          title="Data Source Status"
          subtitle="Freshness indicators for each data type"
          action={
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-500" /> Fresh
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-yellow-500" /> Aging
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-red-500" /> Stale
              </span>
            </div>
          }
        />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <DataSourceCard
            name="Fundamentals"
            recordCount={fundamentals.count}
            lastUpdated={fundamentals.lastUpdated}
            thresholds={{ fresh: 1, stale: 7 }}
            icon={<div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600 text-lg font-bold">F</div>}
          />
          <DataSourceCard
            name="Price Data"
            recordCount={prices.count}
            lastUpdated={prices.lastUpdated}
            thresholds={{ fresh: 1, stale: 3 }}
            icon={<div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center text-green-600 text-lg font-bold">$</div>}
          />
          <DataSourceCard
            name="News Articles"
            recordCount={news.count}
            lastUpdated={news.lastUpdated}
            thresholds={{ fresh: 3, stale: 14 }}
            icon={<div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center text-purple-600 text-lg font-bold">N</div>}
          />
          <DataSourceCard
            name="Reddit Posts"
            recordCount={reddit.count}
            lastUpdated={reddit.lastUpdated}
            thresholds={{ fresh: 3, stale: 14 }}
            icon={<div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center text-orange-600 text-lg font-bold">R</div>}
          />
          <DataSourceCard
            name="Calculated Metrics"
            recordCount={calculated.count}
            lastUpdated={calculated.lastUpdated}
            thresholds={{ fresh: 1, stale: 7 }}
            icon={<div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center text-emerald-600 text-lg font-bold">C</div>}
          />
        </div>
      </Card>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Active Stocks"
          value={metrics?.active_stocks || 0}
          subvalue={`${metrics?.total_stocks || 0} total`}
        />
        <MetricCard
          label="Database Size"
          value={`${metrics?.database_size_mb?.toFixed(1) || 0} MB`}
        />
        <MetricCard
          label="Pending Sentiment"
          value={
            (pendingSentiment?.news_pending || 0) + (pendingSentiment?.reddit_pending || 0)
          }
          subvalue={`${pendingSentiment?.news_pending || 0} news, ${
            pendingSentiment?.reddit_pending || 0
          } reddit`}
        />
        <MetricCard
          label="Last Calculation"
          value={
            metrics?.last_calculation
              ? new Date(metrics.last_calculation).toLocaleDateString()
              : 'Never'
          }
        />
      </div>

      {/* Collection Status */}
      {dataStatus?.is_collecting && (
        <Card>
          <CardHeader title="Data Collection in Progress" />
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">
                Processing: {dataStatus.current_symbol || 'Starting...'}
              </span>
              <span className="text-sm font-medium">
                {dataStatus.completed} / {dataStatus.total}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${dataStatus.progress}%` }}
              />
            </div>
            {dataStatus.errors.length > 0 && (
              <div className="text-sm text-red-600">
                Errors: {dataStatus.errors.slice(-3).join(', ')}
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Data Refresh */}
        <Card>
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <RefreshCw className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Data Refresh</h3>
              <p className="text-sm text-gray-500">Update fundamentals, prices, news</p>
            </div>
          </div>

          {/* Data Type Selection */}
          <div className="mb-4">
            <p className="text-xs text-gray-500 mb-2">Select data types to refresh:</p>
            <div className="grid grid-cols-2 gap-2">
              {(['fundamentals', 'prices', 'news', 'reddit'] as DataType[]).map((type) => (
                <label
                  key={type}
                  className={`flex items-center gap-2 p-2 rounded border cursor-pointer transition-colors ${
                    selectedDataTypes.includes(type)
                      ? 'bg-blue-50 border-blue-300'
                      : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedDataTypes.includes(type)}
                    onChange={() => toggleDataType(type)}
                    className="rounded text-blue-600"
                  />
                  <span className="text-sm capitalize">{type}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <button
              onClick={handleRefreshData}
              disabled={dataStatus?.is_collecting || selectedDataTypes.length === 0}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {dataStatus?.is_collecting
                ? 'Refreshing...'
                : selectedDataTypes.length === 4
                ? 'Refresh All Data'
                : `Refresh Selected (${selectedDataTypes.length})`}
            </button>
            <button
              onClick={handleSyncSP500}
              className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Sync S&P 500 List
            </button>
          </div>
        </Card>

        {/* Sentiment Processing */}
        <Card>
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <Brain className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Sentiment Analysis</h3>
              <p className="text-sm text-gray-500">Process pending content</p>
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Use AI to analyze sentiment for{' '}
            {(pendingSentiment?.news_pending || 0) + (pendingSentiment?.reddit_pending || 0)}{' '}
            pending items.
          </p>
          <div className="space-y-2">
            <button
              onClick={handleProcessSentiment}
              disabled={operation === 'sentiment'}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {operation === 'sentiment' ? 'Processing...' : 'Submit New Batch'}
            </button>

            {/* Active Batches Section */}
            {activeBatches.length > 0 && (
              <div className="mt-4 pt-3 border-t border-gray-200">
                <p className="text-xs font-medium text-gray-500 mb-2">Active Batches</p>
                <div className="space-y-2">
                  {activeBatches.map((batch) => {
                    const total = batch.pending_count + batch.completed_count + batch.failed_count;
                    const progress = total > 0 ? ((batch.completed_count + batch.failed_count) / total) * 100 : 0;
                    return (
                      <div key={batch.batch_id} className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-mono text-gray-600">
                            {batch.batch_id.slice(0, 20)}...
                          </span>
                          <button
                            onClick={() => handlePollBatch(batch.batch_id)}
                            disabled={pollingBatch === batch.batch_id}
                            className="flex items-center gap-1 px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200 disabled:opacity-50"
                          >
                            {pollingBatch === batch.batch_id ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <Search className="w-3 h-3" />
                            )}
                            Check Status
                          </button>
                        </div>
                        <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                          <span>Pending: {batch.pending_count}</span>
                          <span>Done: {batch.completed_count}</span>
                          {batch.failed_count > 0 && (
                            <span className="text-red-500">Failed: {batch.failed_count}</span>
                          )}
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div
                            className="bg-purple-600 h-1.5 rounded-full transition-all"
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Poll Result Display */}
            {pollResult && (
              <div
                className={`mt-2 p-3 rounded-lg text-sm ${
                  pollResult.success
                    ? pollResult.results_retrieved
                      ? 'bg-green-50 text-green-700'
                      : 'bg-blue-50 text-blue-700'
                    : 'bg-red-50 text-red-700'
                }`}
              >
                {pollResult.results_retrieved ? (
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" />
                    <span>{pollResult.message}</span>
                  </div>
                ) : (
                  <div>
                    <div className="font-medium">
                      Anthropic Status: {pollResult.anthropic_status || 'Unknown'}
                    </div>
                    {pollResult.message && (
                      <div className="text-xs mt-1">{pollResult.message}</div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>

        {/* Calculations */}
        <Card>
          <div className="flex items-center gap-4 mb-4">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Calculator className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Run Calculations</h3>
              <p className="text-sm text-gray-500">Generate composite scores</p>
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Calculate fundamental, quality, growth, and sentiment scores for all stocks.
          </p>
          <button
            onClick={handleRunCalculations}
            disabled={operation === 'calculate'}
            className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {operation === 'calculate' ? 'Calculating...' : 'Run Calculations'}
          </button>
        </Card>
      </div>

      {/* Status Banner - shown below action buttons */}
      {operationStatus && (
        <div
          className={`p-4 rounded-lg flex items-center gap-3 ${
            operationStatus.includes('Error')
              ? 'bg-red-50 text-red-700'
              : 'bg-blue-50 text-blue-700'
          }`}
        >
          {operation ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : operationStatus.includes('Error') ? (
            <AlertCircle className="w-5 h-5" />
          ) : (
            <CheckCircle className="w-5 h-5" />
          )}
          <span>{operationStatus}</span>
        </div>
      )}

      {/* Tables Overview */}
      <Card>
        <CardHeader title="Database Tables" subtitle="Record counts and status" />
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Table
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Records
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Last Updated
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {metrics?.tables?.map((table) => (
                <tr key={table.name} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {table.name.replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-600">
                    {table.record_count.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-500 text-sm">
                    {table.last_updated
                      ? new Date(table.last_updated).toLocaleDateString()
                      : '-'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <FreshnessIndicator
                      lastUpdated={table.last_updated}
                      thresholds={{ fresh: 3, stale: 14 }}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
