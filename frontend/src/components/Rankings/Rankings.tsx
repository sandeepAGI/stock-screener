import { useState, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  useReactTable,
} from '@tanstack/react-table';
import type { SortingState, ColumnDef } from '@tanstack/react-table';
import {
  ArrowUpDown,
  Search,
  TrendingUp,
  TrendingDown,
  ArrowUp,
  ArrowDown,
  Minus,
} from 'lucide-react';
import { useRankings } from '../../hooks/useRankings';
import { useSectors } from '../../hooks/useStocks';
import { useWeightsContext } from '../../context/WeightsContext';
import { Card, CardHeader } from '../common/Card';
import { Loading } from '../common/Loading';
import { ScoreBadge, OutlierBadge } from '../common/ScoreBadge';
import type { RankingEntry, OutlierCategory } from '../../types';

// Stock card for Top 5
function StockCard({
  stock,
  rank,
  type,
}: {
  stock: RankingEntry;
  rank: number;
  type: 'undervalued' | 'overvalued';
}) {
  const bgColor = type === 'undervalued' ? 'bg-emerald-50' : 'bg-red-50';
  const borderColor = type === 'undervalued' ? 'border-emerald-200' : 'border-red-200';
  const textColor = type === 'undervalued' ? 'text-emerald-700' : 'text-red-700';

  return (
    <Link
      to={`/analysis?symbol=${stock.symbol}`}
      className={`block p-4 rounded-lg border ${bgColor} ${borderColor} hover:shadow-md transition-shadow`}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className={`text-lg font-bold ${textColor}`}>#{rank}</span>
            <span className="font-bold text-gray-900">{stock.symbol}</span>
          </div>
          <p className="text-sm text-gray-600 truncate max-w-[150px]">
            {stock.company_name}
          </p>
          <p className="text-xs text-gray-500">{stock.sector}</p>
        </div>
        <div className="text-right">
          <ScoreBadge score={stock.composite_score} />
        </div>
      </div>
    </Link>
  );
}

// Rank change indicator
function RankChange({ change }: { change: number }) {
  if (change === 0) return <Minus className="w-4 h-4 text-gray-400" />;

  if (change > 0) {
    return (
      <span className="flex items-center text-green-600 text-sm font-medium">
        <ArrowUp className="w-4 h-4" />
        {change}
      </span>
    );
  }

  return (
    <span className="flex items-center text-red-600 text-sm font-medium">
      <ArrowDown className="w-4 h-4" />
      {Math.abs(change)}
    </span>
  );
}

// Biggest Mover card
function MoverCard({
  stock,
  originalRank,
  customRank,
  direction,
}: {
  stock: RankingEntry & { customScore: number };
  originalRank: number;
  customRank: number;
  direction: 'up' | 'down';
}) {
  const rankChange = originalRank - customRank;
  const bgColor = direction === 'up' ? 'bg-green-50' : 'bg-red-50';
  const borderColor = direction === 'up' ? 'border-green-200' : 'border-red-200';

  return (
    <Link
      to={`/analysis?symbol=${stock.symbol}`}
      className={`block p-3 rounded-lg border ${bgColor} ${borderColor} hover:shadow-md transition-shadow`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <RankChange change={rankChange} />
          <div>
            <span className="font-bold text-gray-900">{stock.symbol}</span>
            <p className="text-xs text-gray-500">{stock.company_name}</p>
          </div>
        </div>
        <div className="text-right text-xs">
          <p className="text-gray-500">
            {originalRank} → {customRank}
          </p>
          <p className="font-medium">
            {stock.composite_score.toFixed(1)} → {stock.customScore.toFixed(1)}
          </p>
        </div>
      </div>
    </Link>
  );
}

type RankingWithCustom = RankingEntry & { customScore?: number; customRank?: number };

const outlierCategories: { value: OutlierCategory | ''; label: string }[] = [
  { value: '', label: 'All Categories' },
  { value: 'strong_undervalued', label: 'Strong Undervalued' },
  { value: 'undervalued', label: 'Undervalued' },
  { value: 'fairly_valued', label: 'Fairly Valued' },
  { value: 'overvalued', label: 'Overvalued' },
  { value: 'strong_overvalued', label: 'Strong Overvalued' },
];

export function Rankings() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [sorting, setSorting] = useState<SortingState>([]);
  const [globalFilter, setGlobalFilter] = useState('');

  const { calculateCustomScore, isDefault, normalizedWeights } = useWeightsContext();

  const category = searchParams.get('category') as OutlierCategory | null;
  const sector = searchParams.get('sector');

  const { rankings, total, calculationDate, loading, error } = useRankings({
    sector: sector || undefined,
    outlierCategory: category || undefined,
    limit: 500,
  });

  const { sectors } = useSectors();

  // Calculate custom scores and ranks
  const rankingsWithCustom = useMemo(() => {
    if (isDefault) return rankings.map((r) => ({ ...r, customScore: r.composite_score, customRank: r.rank }));

    const withCustom = rankings.map((r) => ({
      ...r,
      customScore: calculateCustomScore({
        fundamental: r.fundamental_score,
        quality: r.quality_score,
        growth: r.growth_score,
        sentiment: r.sentiment_score,
      }),
    }));

    // Sort by custom score to get custom ranks
    const sorted = [...withCustom].sort((a, b) => b.customScore - a.customScore);
    const rankMap = new Map<string, number>();
    sorted.forEach((s, i) => rankMap.set(s.symbol, i + 1));

    return withCustom.map((r) => ({
      ...r,
      customRank: rankMap.get(r.symbol) || r.rank,
    }));
  }, [rankings, isDefault, calculateCustomScore]);

  // Get top 5 undervalued and overvalued
  const top5Undervalued = useMemo(() => {
    return rankings
      .filter((r) => r.outlier_category === 'strong_undervalued' || r.outlier_category === 'undervalued')
      .slice(0, 5);
  }, [rankings]);

  const top5Overvalued = useMemo(() => {
    return rankings
      .filter((r) => r.outlier_category === 'strong_overvalued' || r.outlier_category === 'overvalued')
      .sort((a, b) => a.composite_score - b.composite_score)
      .slice(0, 5);
  }, [rankings]);

  // Get biggest movers (rank changes with custom weights)
  const biggestMovers = useMemo(() => {
    if (isDefault) return { gainers: [], losers: [] };

    const withChanges = rankingsWithCustom
      .map((r) => ({
        ...r,
        rankChange: r.rank - (r.customRank || r.rank),
      }))
      .filter((r) => Math.abs(r.rankChange) >= 5); // Only significant changes

    const gainers = withChanges
      .filter((r) => r.rankChange > 0)
      .sort((a, b) => b.rankChange - a.rankChange)
      .slice(0, 5);

    const losers = withChanges
      .filter((r) => r.rankChange < 0)
      .sort((a, b) => a.rankChange - b.rankChange)
      .slice(0, 5);

    return { gainers, losers };
  }, [rankingsWithCustom, isDefault]);

  // Dynamic columns based on whether comparison mode is on
  const columns = useMemo((): ColumnDef<RankingWithCustom>[] => {
    const baseColumns: ColumnDef<RankingWithCustom>[] = [
      {
        accessorKey: 'rank',
        header: '#',
        cell: (info) => <span className="text-gray-500">{info.getValue() as number}</span>,
        size: 50,
      },
      {
        accessorKey: 'symbol',
        header: 'Symbol',
        cell: (info) => (
          <Link
            to={`/analysis?symbol=${info.getValue()}`}
            className="font-medium text-blue-600 hover:text-blue-800"
          >
            {info.getValue() as string}
          </Link>
        ),
      },
      {
        accessorKey: 'company_name',
        header: 'Company',
        cell: (info) => (
          <span className="text-gray-700 truncate max-w-xs">{(info.getValue() as string) || '-'}</span>
        ),
      },
      {
        accessorKey: 'sector',
        header: 'Sector',
        cell: (info) => <span className="text-sm text-gray-600">{(info.getValue() as string) || '-'}</span>,
      },
      {
        accessorKey: 'composite_score',
        header: 'Original',
        cell: (info) => <ScoreBadge score={info.getValue() as number} />,
      },
    ];

    if (!isDefault) {
      baseColumns.push(
        {
          accessorKey: 'customScore',
          header: 'Custom',
          cell: (info) => {
            const val = info.getValue() as number | undefined;
            return val !== undefined ? <ScoreBadge score={val} /> : '-';
          },
        },
        {
          accessorKey: 'customRank',
          header: 'Δ Rank',
          cell: (info) => {
            const original = info.row.original.rank;
            const custom = info.getValue() as number | undefined;
            if (custom === undefined) return '-';
            const change = original - custom;
            return <RankChange change={change} />;
          },
        }
      );
    }

    baseColumns.push(
      {
        accessorKey: 'fundamental_score',
        header: 'Fund.',
        cell: (info) => {
          const val = info.getValue() as number | null;
          return val ? <ScoreBadge score={val} size="sm" /> : '-';
        },
      },
      {
        accessorKey: 'quality_score',
        header: 'Qual.',
        cell: (info) => {
          const val = info.getValue() as number | null;
          return val ? <ScoreBadge score={val} size="sm" /> : '-';
        },
      },
      {
        accessorKey: 'growth_score',
        header: 'Growth',
        cell: (info) => {
          const val = info.getValue() as number | null;
          return val ? <ScoreBadge score={val} size="sm" /> : '-';
        },
      },
      {
        accessorKey: 'sentiment_score',
        header: 'Sent.',
        cell: (info) => {
          const val = info.getValue() as number | null;
          return val ? <ScoreBadge score={val} size="sm" /> : '-';
        },
      },
      {
        accessorKey: 'outlier_category',
        header: 'Category',
        cell: (info) => {
          const cat = info.getValue() as OutlierCategory | null;
          return cat ? <OutlierBadge category={cat} size="sm" /> : '-';
        },
      }
    );

    return baseColumns;
  }, [isDefault]);

  const table = useReactTable({
    data: rankingsWithCustom,
    columns,
    state: {
      sorting,
      globalFilter,
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const handleCategoryChange = (value: string) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set('category', value);
    } else {
      newParams.delete('category');
    }
    setSearchParams(newParams);
  };

  const handleSectorChange = (value: string) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set('sector', value);
    } else {
      newParams.delete('sector');
    }
    setSearchParams(newParams);
  };

  if (loading) {
    return <Loading message="Loading rankings..." />;
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 text-red-700 p-4 rounded-lg">Error loading rankings: {error}</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Stock Rankings</h1>
          <p className="text-gray-500">
            Composite scores for {total.toLocaleString()} stocks
            {calculationDate && ` (calculated ${new Date(calculationDate).toLocaleDateString()})`}
          </p>
        </div>
        {!isDefault && (
          <div className="text-right text-sm">
            <p className="text-gray-500">Custom Weights:</p>
            <p className="font-medium">
              F:{(normalizedWeights.fundamental * 100).toFixed(0)}% /
              Q:{(normalizedWeights.quality * 100).toFixed(0)}% /
              G:{(normalizedWeights.growth * 100).toFixed(0)}% /
              S:{(normalizedWeights.sentiment * 100).toFixed(0)}%
            </p>
          </div>
        )}
      </div>

      {/* Top 5 Summary Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top 5 Undervalued */}
        <Card>
          <CardHeader
            title="Top 5 Most Undervalued"
            subtitle="Highest potential stocks"
            action={<TrendingDown className="w-5 h-5 text-emerald-600" />}
          />
          {top5Undervalued.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-3">
              {top5Undervalued.map((stock, i) => (
                <StockCard key={stock.symbol} stock={stock} rank={i + 1} type="undervalued" />
              ))}
            </div>
          ) : (
            <p className="text-center py-4 text-gray-500">No undervalued stocks found</p>
          )}
        </Card>

        {/* Top 5 Overvalued */}
        <Card>
          <CardHeader
            title="Top 5 Most Overvalued"
            subtitle="Potentially overpriced stocks"
            action={<TrendingUp className="w-5 h-5 text-red-600" />}
          />
          {top5Overvalued.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-3">
              {top5Overvalued.map((stock, i) => (
                <StockCard key={stock.symbol} stock={stock} rank={i + 1} type="overvalued" />
              ))}
            </div>
          ) : (
            <p className="text-center py-4 text-gray-500">No overvalued stocks found</p>
          )}
        </Card>
      </div>

      {/* Biggest Movers (only show when custom weights) */}
      {!isDefault && (biggestMovers.gainers.length > 0 || biggestMovers.losers.length > 0) && (
        <Card>
          <CardHeader
            title="Biggest Movers"
            subtitle="Stocks with largest rank changes under custom weights"
          />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Gainers */}
            <div>
              <h4 className="text-sm font-medium text-green-700 mb-3 flex items-center gap-1">
                <ArrowUp className="w-4 h-4" /> Biggest Gainers
              </h4>
              {biggestMovers.gainers.length > 0 ? (
                <div className="space-y-2">
                  {biggestMovers.gainers.map((stock) => (
                    <MoverCard
                      key={stock.symbol}
                      stock={stock}
                      originalRank={stock.rank}
                      customRank={stock.customRank || stock.rank}
                      direction="up"
                    />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No significant gainers</p>
              )}
            </div>

            {/* Losers */}
            <div>
              <h4 className="text-sm font-medium text-red-700 mb-3 flex items-center gap-1">
                <ArrowDown className="w-4 h-4" /> Biggest Losers
              </h4>
              {biggestMovers.losers.length > 0 ? (
                <div className="space-y-2">
                  {biggestMovers.losers.map((stock) => (
                    <MoverCard
                      key={stock.symbol}
                      stock={stock}
                      originalRank={stock.rank}
                      customRank={stock.customRank || stock.rank}
                      direction="down"
                    />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No significant losers</p>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search symbols..."
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            className="pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          />
        </div>

        {/* Category Filter */}
        <select
          value={category || ''}
          onChange={(e) => handleCategoryChange(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        >
          {outlierCategories.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* Sector Filter */}
        <select
          value={sector || ''}
          onChange={(e) => handleSectorChange(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        >
          <option value="">All Sectors</option>
          {sectors.map((s) => (
            <option key={s.sector} value={s.sector}>
              {s.sector} ({s.count})
            </option>
          ))}
        </select>
      </div>

      {/* Table */}
      <Card padding="none">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <div className="flex items-center gap-1">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        <ArrowUpDown className="w-3 h-3" />
                      </div>
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y divide-gray-200">
              {table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="hover:bg-gray-50">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 whitespace-nowrap">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {rankings.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No rankings found matching your filters
          </div>
        )}
      </Card>
    </div>
  );
}
