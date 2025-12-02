import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import type { Stock, StockDetail, SectorInfo } from '../types';

export function useStocks(sector?: string) {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStocks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getStocks({ sector, limit: 500 });
      setStocks(response.stocks);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stocks');
    } finally {
      setLoading(false);
    }
  }, [sector]);

  useEffect(() => {
    fetchStocks();
  }, [fetchStocks]);

  return { stocks, total, loading, error, refetch: fetchStocks };
}

export function useStock(symbol: string | null) {
  const [stock, setStock] = useState<StockDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStock = useCallback(async () => {
    if (!symbol) {
      setStock(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.getStock(symbol);
      setStock(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stock');
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchStock();
  }, [fetchStock]);

  return { stock, loading, error, refetch: fetchStock };
}

export function useSectors() {
  const [sectors, setSectors] = useState<SectorInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSectors = async () => {
      try {
        const response = await api.getSectors();
        setSectors(response.sectors);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch sectors');
      } finally {
        setLoading(false);
      }
    };

    fetchSectors();
  }, []);

  return { sectors, loading, error };
}
