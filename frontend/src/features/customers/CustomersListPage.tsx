import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useCustomers, useInvalidateQueries } from '../../api/hooks';
import { customerApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { Customer } from '../../api/types';
import { formatDate } from '../../lib/dates';
import { Mail, Plus, ExternalLink, Check, AlertCircle } from 'lucide-react';

export const CustomersListPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('created_at');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');

  const [resetFeedback, setResetFeedback] = useState<{ message: string; link?: string } | null>(null);
  const [isSendingReset, setIsSendingReset] = useState<string | null>(null);

  const { data, isLoading, refetch } = useCustomers({
    page,
    per_page: perPage,
    q: search,
    sort,
    order,
  });

  const handleSendResetLink = async (customerId: string, email: string) => {
    setIsSendingReset(customerId);
    setResetFeedback(null);
    try {
      const res = await customerApi.sendResetLink(customerId);
      setResetFeedback({
        message: `Password reset link dispatched for ${email}`,
        link: res.reset_link,
      });
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to send reset link');
    } finally {
      setIsSendingReset(null);
    }
  };

  const columns: Column<Customer>[] = [
    {
      key: 'name',
      header: 'Customer / Company',
      sortable: true,
      render: (row) => (
        <div>
          <Link
            to={`/customers/${row.id}`}
            className="font-semibold text-primary hover:underline flex items-center gap-1"
          >
            {row.name}
            <ExternalLink className="h-3 w-3 opacity-60" />
          </Link>
          {row.company_name && (
            <p className="text-xs text-muted-foreground">{row.company_name}</p>
          )}
        </div>
      ),
    },
    {
      key: 'email',
      header: 'Email',
      sortable: true,
      render: (row) => <span className="font-mono text-xs">{row.email}</span>,
    },
    {
      key: 'phone',
      header: 'Phone',
      render: (row) => <span>{row.phone || '—'}</span>,
    },
    {
      key: 'gstin',
      header: 'GSTIN',
      render: (row) => <span className="font-mono text-xs">{row.gstin || '—'}</span>,
    },
    {
      key: 'is_active',
      header: 'Status',
      sortable: true,
      render: (row) => (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
            row.is_active
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300'
              : 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300'
          }`}
        >
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Customer Since',
      sortable: true,
      render: (row) => <span>{formatDate(row.created_at)}</span>,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <button
          onClick={() => handleSendResetLink(row.id, row.email)}
          disabled={isSendingReset === row.id}
          className="inline-flex items-center gap-1 text-xs text-primary hover:underline font-medium disabled:opacity-50"
          title="Send password reset link"
        >
          <Mail className="h-3.5 w-3.5" />
          <span>{isSendingReset === row.id ? 'Sending...' : 'Send Reset Link'}</span>
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Customers"
        description="View enterprise accounts, contact details, and send authentication recovery links"
      />

      {resetFeedback && (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-4 text-xs text-emerald-800 dark:text-emerald-200 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-1.5 font-semibold">
              <Check className="h-4 w-4" />
              <span>{resetFeedback.message}</span>
            </div>
            {resetFeedback.link && (
              <p className="mt-1 font-mono text-[11px] text-muted-foreground break-all">
                Token link: <a href={resetFeedback.link} className="underline text-primary" target="_blank" rel="noreferrer">{resetFeedback.link}</a>
              </p>
            )}
          </div>
          <button
            onClick={() => setResetFeedback(null)}
            className="text-xs font-bold opacity-60 hover:opacity-100"
          >
            Dismiss
          </button>
        </div>
      )}

      <DataTable
        columns={columns}
        data={data?.items}
        total={data?.total}
        page={page}
        perPage={perPage}
        pages={data?.pages}
        isLoading={isLoading}
        searchPlaceholder="Search customers by name, company, email..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        onSortChange={(k, ord) => {
          setSort(k);
          setOrder(ord);
        }}
        exportFilename="customers"
      />
    </div>
  );
};
