/**
 * API Client for StockAnalyzer Pro Backend
 */

import type {
  StockListResponse,
  StockDetail,
  RankingsResponse,
  SectorInfo,
  DataRefreshRequest,
  DataRefreshResponse,
  DataStatusResponse,
  MetricsSummary,
  HealthResponse,
} from '../types';

// Base URL - in Electron, get from preload; in browser, use proxy
const getBaseUrl = (): string => {
  // Check if running in Electron
  if (typeof window !== 'undefined' && (window as any).electronAPI) {
    return 'http://127.0.0.1:8000';
  }
  // In development with Vite proxy
  return '';
};

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = getBaseUrl();
  }

  private async fetch<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Health
  async getHealth(): Promise<HealthResponse> {
    return this.fetch('/api/health');
  }

  // Stocks
  async getStocks(params?: {
    sector?: string;
    active_only?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<StockListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.sector) searchParams.set('sector', params.sector);
    if (params?.active_only !== undefined) searchParams.set('active_only', String(params.active_only));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));

    const query = searchParams.toString();
    return this.fetch(`/api/stocks${query ? `?${query}` : ''}`);
  }

  async getStock(symbol: string): Promise<StockDetail> {
    return this.fetch(`/api/stocks/${symbol.toUpperCase()}`);
  }

  async getSectors(): Promise<{ sectors: SectorInfo[] }> {
    return this.fetch('/api/stocks/sectors');
  }

  // Rankings
  async getRankings(params?: {
    limit?: number;
    offset?: number;
    sort_by?: string;
    ascending?: boolean;
    outlier_category?: string;
    min_score?: number;
    max_score?: number;
  }): Promise<RankingsResponse> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));
    if (params?.sort_by) searchParams.set('sort_by', params.sort_by);
    if (params?.ascending !== undefined) searchParams.set('ascending', String(params.ascending));
    if (params?.outlier_category) searchParams.set('outlier_category', params.outlier_category);
    if (params?.min_score !== undefined) searchParams.set('min_score', String(params.min_score));
    if (params?.max_score !== undefined) searchParams.set('max_score', String(params.max_score));

    const query = searchParams.toString();
    return this.fetch(`/api/rankings${query ? `?${query}` : ''}`);
  }

  async getSectorRankings(sector: string, params?: {
    limit?: number;
    offset?: number;
  }): Promise<RankingsResponse> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));

    const query = searchParams.toString();
    return this.fetch(`/api/rankings/sector/${encodeURIComponent(sector)}${query ? `?${query}` : ''}`);
  }

  async getOutliers(category: string, params?: {
    limit?: number;
    min_data_quality?: number;
  }): Promise<{ category: string; outliers: any[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.min_data_quality !== undefined) searchParams.set('min_data_quality', String(params.min_data_quality));

    const query = searchParams.toString();
    return this.fetch(`/api/rankings/outliers/${category}${query ? `?${query}` : ''}`);
  }

  // Data Management
  async refreshData(request: DataRefreshRequest): Promise<DataRefreshResponse> {
    return this.fetch('/api/data/refresh', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getDataStatus(): Promise<DataStatusResponse> {
    return this.fetch('/api/data/status');
  }

  async getMetricsSummary(): Promise<MetricsSummary> {
    return this.fetch('/api/data/metrics/summary');
  }

  async syncSP500(): Promise<{ status: string; added?: number; deactivated?: number; message?: string }> {
    return this.fetch('/api/data/sync-sp500', { method: 'POST' });
  }

  // Sentiment
  async submitSentiment(symbols?: string[]): Promise<any> {
    return this.fetch('/api/sentiment/submit', {
      method: 'POST',
      body: JSON.stringify({ symbols }),
    });
  }

  async getSentimentStatus(batchId?: string): Promise<any> {
    if (batchId) {
      return this.fetch(`/api/sentiment/status/${batchId}`);
    }
    return this.fetch('/api/sentiment/status');
  }

  async getPendingSentiment(): Promise<any> {
    return this.fetch('/api/sentiment/pending');
  }

  // Calculations
  async runCalculations(symbols?: string[]): Promise<any> {
    return this.fetch('/api/calculate', {
      method: 'POST',
      body: JSON.stringify({ symbols }),
    });
  }

  async getCalculationStatus(): Promise<any> {
    return this.fetch('/api/calculate/status');
  }

  async calculateSingleStock(symbol: string): Promise<any> {
    return this.fetch(`/api/calculate/single/${symbol.toUpperCase()}`, {
      method: 'POST',
    });
  }
}

// Export singleton instance
export const api = new ApiClient();
