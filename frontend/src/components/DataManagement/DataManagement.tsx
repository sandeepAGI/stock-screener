import { useState, useEffect } from 'react';
import {
  RefreshCw,
  Brain,
  Calculator,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { api } from '../../api/client';
import { Card, CardHeader, MetricCard } from '../common/Card';
import { Loading } from '../common/Loading';
import type { MetricsSummary, DataStatusResponse } from '../../types';

type OperationType = 'data' | 'sentiment' | 'calculate';

export function DataManagement() {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [dataStatus, setDataStatus] = useState<DataStatusResponse | null>(null);
  const [pendingSentiment, setPendingSentiment] = useState<{ news_pending: number; reddit_pending: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [operation, setOperation] = useState<OperationType | null>(null);
  const [operationStatus, setOperationStatus] = useState<string>('');

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
    const interval = setInterval(fetchStatus, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const handleRefreshData = async () => {
    setOperation('data');
    setOperationStatus('Starting data refresh...');
    try {
      const response = await api.refreshData({
        data_types: ['fundamentals', 'prices', 'news', 'reddit'],
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
      setOperationStatus(`Batch submitted: ${response.total_items || 0} items`);
    } catch (error) {
      setOperationStatus(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
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

  if (loading) {
    return <Loading message="Loading data status..." />;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Data Management</h1>
        <p className="text-gray-500">Manage data collection, sentiment processing, and calculations</p>
      </div>

      {/* Status Banner */}
      {operationStatus && (
        <div className={`p-4 rounded-lg flex items-center gap-3 ${
          operationStatus.includes('Error')
            ? 'bg-red-50 text-red-700'
            : 'bg-blue-50 text-blue-700'
        }`}>
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
          value={(pendingSentiment?.news_pending || 0) + (pendingSentiment?.reddit_pending || 0)}
          subvalue={`${pendingSentiment?.news_pending || 0} news, ${pendingSentiment?.reddit_pending || 0} reddit`}
        />
        <MetricCard
          label="Last Calculation"
          value={metrics?.last_calculation ? new Date(metrics.last_calculation).toLocaleDateString() : 'Never'}
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
          <p className="text-sm text-gray-600 mb-4">
            Collect latest data from Yahoo Finance, news sources, and Reddit for all active stocks.
          </p>
          <div className="space-y-2">
            <button
              onClick={handleRefreshData}
              disabled={dataStatus?.is_collecting}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {dataStatus?.is_collecting ? 'Refreshing...' : 'Refresh All Data'}
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
            Use AI to analyze sentiment for {(pendingSentiment?.news_pending || 0) + (pendingSentiment?.reddit_pending || 0)} pending items.
          </p>
          <button
            onClick={handleProcessSentiment}
            disabled={operation === 'sentiment'}
            className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {operation === 'sentiment' ? 'Processing...' : 'Process Sentiment'}
          </button>
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

      {/* Tables Overview */}
      <Card>
        <CardHeader title="Database Tables" subtitle="Record counts and status" />
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Table</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Records</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Last Updated</th>
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
