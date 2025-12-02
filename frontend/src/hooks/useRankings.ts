import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import type { RankingEntry, OutlierCategory } from '../types';

interface UseRankingsParams {
  sector?: string;
  outlierCategory?: OutlierCategory;
  sortBy?: string;
  ascending?: boolean;
  limit?: number;
}

export function useRankings(params: UseRankingsParams = {}) {
  const [rankings, setRankings] = useState<RankingEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [calculationDate, setCalculationDate] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { sector, outlierCategory, sortBy, ascending, limit = 100 } = params;

  const fetchRankings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let response;
      if (sector) {
        response = await api.getSectorRankings(sector, { limit });
      } else {
        response = await api.getRankings({
          limit,
          sort_by: sortBy,
          ascending,
          outlier_category: outlierCategory,
        });
      }
      setRankings(response.rankings);
      setTotal(response.total);
      setCalculationDate(response.calculation_date);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch rankings');
    } finally {
      setLoading(false);
    }
  }, [sector, outlierCategory, sortBy, ascending, limit]);

  useEffect(() => {
    fetchRankings();
  }, [fetchRankings]);

  return { rankings, total, calculationDate, loading, error, refetch: fetchRankings };
}

export function useOutliers(category: OutlierCategory, limit: number = 20) {
  const [outliers, setOutliers] = useState<RankingEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOutliers = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.getOutliers(category, { limit });
        setOutliers(response.outliers);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch outliers');
      } finally {
        setLoading(false);
      }
    };

    fetchOutliers();
  }, [category, limit]);

  return { outliers, loading, error };
}
