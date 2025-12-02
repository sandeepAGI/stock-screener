import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  useReactTable,
} from '@tanstack/react-table';
import type { SortingState } from '@tanstack/react-table';
import { ArrowUpDown, Search } from 'lucide-react';
import { useRankings } from '../../hooks/useRankings';
import { useSectors } from '../../hooks/useStocks';
import { Card } from '../common/Card';
import { Loading } from '../common/Loading';
import { ScoreBadge, OutlierBadge } from '../common/ScoreBadge';
import type { RankingEntry, OutlierCategory } from '../../types';

const columnHelper = createColumnHelper<RankingEntry>();

const columns = [
  columnHelper.accessor('rank', {
    header: '#',
    cell: (info) => <span className="text-gray-500">{info.getValue()}</span>,
    size: 50,
  }),
  columnHelper.accessor('symbol', {
    header: 'Symbol',
    cell: (info) => (
      <Link
        to={`/analysis?symbol=${info.getValue()}`}
        className="font-medium text-blue-600 hover:text-blue-800"
      >
        {info.getValue()}
      </Link>
    ),
  }),
  columnHelper.accessor('company_name', {
    header: 'Company',
    cell: (info) => (
      <span className="text-gray-700 truncate max-w-xs">
        {info.getValue() || '-'}
      </span>
    ),
  }),
  columnHelper.accessor('sector', {
    header: 'Sector',
    cell: (info) => (
      <span className="text-sm text-gray-600">{info.getValue() || '-'}</span>
    ),
  }),
  columnHelper.accessor('composite_score', {
    header: 'Composite',
    cell: (info) => <ScoreBadge score={info.getValue()} />,
  }),
  columnHelper.accessor('fundamental_score', {
    header: 'Fundamental',
    cell: (info) => (info.getValue() ? <ScoreBadge score={info.getValue()!} size="sm" /> : '-'),
  }),
  columnHelper.accessor('quality_score', {
    header: 'Quality',
    cell: (info) => (info.getValue() ? <ScoreBadge score={info.getValue()!} size="sm" /> : '-'),
  }),
  columnHelper.accessor('growth_score', {
    header: 'Growth',
    cell: (info) => (info.getValue() ? <ScoreBadge score={info.getValue()!} size="sm" /> : '-'),
  }),
  columnHelper.accessor('sentiment_score', {
    header: 'Sentiment',
    cell: (info) => (info.getValue() ? <ScoreBadge score={info.getValue()!} size="sm" /> : '-'),
  }),
  columnHelper.accessor('outlier_category', {
    header: 'Category',
    cell: (info) => {
      const category = info.getValue();
      return category ? <OutlierBadge category={category} size="sm" /> : '-';
    },
  }),
];

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

  const category = searchParams.get('category') as OutlierCategory | null;
  const sector = searchParams.get('sector');

  const { rankings, total, calculationDate, loading, error } = useRankings({
    sector: sector || undefined,
    outlierCategory: category || undefined,
    limit: 200,
  });

  const { sectors } = useSectors();

  const table = useReactTable({
    data: rankings,
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
        <div className="bg-red-50 text-red-700 p-4 rounded-lg">
          Error loading rankings: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Stock Rankings</h1>
        <p className="text-gray-500">
          Composite scores for {total.toLocaleString()} stocks
          {calculationDate && ` (calculated ${new Date(calculationDate).toLocaleDateString()})`}
        </p>
      </div>

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
