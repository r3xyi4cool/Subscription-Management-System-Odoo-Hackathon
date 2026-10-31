import React, { useState, useEffect, useMemo } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Search,
  Download,
} from 'lucide-react';
import { exportToCSV } from '../lib/csv';
import { EmptyState } from './EmptyState';

export interface Column<T> {
  key: string;
  header: string;
  sortable?: boolean;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data?: T[];
  total?: number;
  page?: number;
  perPage?: number;
  pages?: number;
  isLoading?: boolean;
  searchPlaceholder?: string;
  onPageChange?: (page: number) => void;
  onPerPageChange?: (perPage: number) => void;
  onSearchChange?: (q: string) => void;
  onSortChange?: (sort: string, order: 'asc' | 'desc') => void;
  exportFilename?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyActionLabel?: string;
  onEmptyAction?: () => void;
  customFilterNode?: React.ReactNode;
}

export function DataTable<T extends object>({
  columns,
  data = [],
  total = 0,
  page = 1,
  perPage = 20,
  pages = 1,
  isLoading = false,
  searchPlaceholder = 'Search...',
  onPageChange,
  onPerPageChange,
  onSearchChange,
  onSortChange,
  exportFilename = 'export_data',
  emptyTitle = 'No records found',
  emptyDescription = 'Try adjusting your search or filters.',
  emptyActionLabel,
  onEmptyAction,
  customFilterNode,
}: DataTableProps<T>) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortKey, setSortKey] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearchChange?.(searchTerm);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm, onSearchChange]);

  const handleSort = (key: string) => {
    let newOrder: 'asc' | 'desc' = 'asc';
    if (sortKey === key) {
      newOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    }
    setSortKey(key);
    setSortOrder(newOrder);
    onSortChange?.(key, newOrder);
  };

  const handleExport = () => {
    const columnHeaders: Record<string, string> = {};
    columns.forEach((col) => {
      columnHeaders[col.key] = col.header;
    });
    exportToCSV(exportFilename, data as unknown as Record<string, unknown>[], columnHeaders);
  };

  const csvAvailable = useMemo(() => data.length > 0, [data]);

  return (
    <div className="space-y-4">
      {/* Top Filter and Actions Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 flex-wrap items-center gap-2">
          {onSearchChange && (
            <div className="relative min-w-[240px] max-w-sm flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={searchPlaceholder}
                className="w-full rounded-md border border-input bg-background pl-9 pr-4 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          )}
          {customFilterNode}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            disabled={!csvAvailable || isLoading}
            className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-2 text-sm font-medium hover:bg-muted transition-colors disabled:opacity-40"
            title="Export current view to CSV"
          >
            <Download className="h-4 w-4" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/50 text-xs font-medium uppercase text-muted-foreground">
              <tr>
                {columns.map((col) => {
                  const isSorted = sortKey === col.key;
                  return (
                    <th
                      key={col.key}
                      className={`px-4 py-3.5 whitespace-nowrap ${col.className || ''}`}
                    >
                      {col.sortable ? (
                        <button
                          onClick={() => handleSort(col.key)}
                          className="flex items-center gap-1.5 hover:text-foreground transition-colors group"
                        >
                          <span>{col.header}</span>
                          {isSorted ? (
                            sortOrder === 'asc' ? (
                              <ArrowUp className="h-3.5 w-3.5 text-primary" />
                            ) : (
                              <ArrowDown className="h-3.5 w-3.5 text-primary" />
                            )
                          ) : (
                            <ArrowUpDown className="h-3.5 w-3.5 opacity-40 group-hover:opacity-100" />
                          )}
                        </button>
                      ) : (
                        <span>{col.header}</span>
                      )}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading ? (
                // Skeleton loading rows
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    {columns.map((_, idx) => (
                      <td key={idx} className="px-4 py-4">
                        <div className="h-4 bg-muted rounded w-3/4"></div>
                      </td>
                    ))}
                  </tr>
                ))
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="p-8">
                    <EmptyState
                      title={emptyTitle}
                      description={emptyDescription}
                      actionLabel={emptyActionLabel}
                      onAction={onEmptyAction}
                    />
                  </td>
                </tr>
              ) : (
                data.map((row, rIdx) => {
                  const rowRecord = row as Record<string, unknown>;
                  return (
                    <tr
                      key={(rowRecord.id as string) || rIdx}
                      className="hover:bg-muted/40 transition-colors"
                    >
                      {columns.map((col) => (
                        <td
                          key={col.key}
                          className={`px-4 py-3.5 text-foreground whitespace-nowrap ${
                            col.className || ''
                          }`}
                        >
                          {col.render ? col.render(row) : (rowRecord[col.key] as React.ReactNode) ?? '—'}
                        </td>
                      ))}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-border px-4 py-3 text-xs text-muted-foreground bg-muted/20">
          <div className="flex items-center gap-2">
            <span>Rows per page:</span>
            <select
              value={perPage}
              onChange={(e) => onPerPageChange?.(Number(e.target.value))}
              disabled={isLoading}
              className="rounded border border-input bg-background px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
            <span>
              Showing {total > 0 ? (page - 1) * perPage + 1 : 0} to{' '}
              {Math.min(page * perPage, total)} of {total} results
            </span>
          </div>

          <div className="flex items-center space-x-1">
            <button
              onClick={() => onPageChange?.(1)}
              disabled={page <= 1 || isLoading}
              className="rounded p-1 hover:bg-muted disabled:opacity-40"
              title="First page"
            >
              <ChevronsLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => onPageChange?.(page - 1)}
              disabled={page <= 1 || isLoading}
              className="rounded p-1 hover:bg-muted disabled:opacity-40"
              title="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>

            <span className="px-2 font-medium text-foreground">
              Page {page} of {Math.max(pages, 1)}
            </span>

            <button
              onClick={() => onPageChange?.(page + 1)}
              disabled={page >= pages || isLoading}
              className="rounded p-1 hover:bg-muted disabled:opacity-40"
              title="Next page"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
            <button
              onClick={() => onPageChange?.(pages)}
              disabled={page >= pages || isLoading}
              className="rounded p-1 hover:bg-muted disabled:opacity-40"
              title="Last page"
            >
              <ChevronsRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
