import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useInvoices } from '../../api/hooks';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { StatusBadge } from '../../components/StatusBadge';
import { MoneyText } from '../../components/MoneyText';
import { Invoice } from '../../api/types';
import { formatDate, isOverdue } from '../../lib/dates';
import { Plus, Receipt, Zap, Clock, AlertCircle } from 'lucide-react';

export const InvoicesListPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('created_at');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const queryParams: Record<string, string | number> = {
    page,
    per_page: perPage,
    sort,
    order,
  };
  if (search) queryParams.q = search;
  if (statusFilter) queryParams.status = statusFilter;

  const { data, isLoading } = useInvoices(queryParams);

  const columns: Column<Invoice>[] = [
    {
      key: 'invoice_number',
      header: 'Invoice #',
      sortable: true,
      render: (row) => (
        <div>
          <Link
            to={`/invoices/${row.id}`}
            className="font-mono font-semibold text-primary hover:underline"
          >
            {row.invoice_number}
          </Link>
          <p className="text-xs text-muted-foreground">{row.customer_name}</p>
        </div>
      ),
    },
    {
      key: 'subscription_number',
      header: 'Subscription',
      render: (row) =>
        row.subscription_id ? (
          <Link
            to={`/subscriptions/${row.subscription_id}`}
            className="font-mono text-xs text-primary hover:underline"
          >
            {row.subscription_number || 'View Sub'}
          </Link>
        ) : (
          <span className="text-xs text-muted-foreground">Ad-hoc Invoice</span>
        ),
    },
    {
      key: 'issue_date',
      header: 'Issue Date',
      sortable: true,
      render: (row) => <span>{formatDate(row.issue_date)}</span>,
    },
    {
      key: 'due_date',
      header: 'Due Date',
      sortable: true,
      render: (row) => {
        const overdue = isOverdue(row.due_date, row.balance_due_paise);
        return (
          <span className={overdue ? 'text-destructive font-semibold flex items-center gap-1' : ''}>
            {formatDate(row.due_date)}
            {overdue && <AlertCircle className="h-3 w-3 inline" />}
          </span>
        );
      },
    },
    {
      key: 'total_paise',
      header: 'Invoice Total',
      sortable: true,
      render: (row) => <MoneyText paise={row.total_paise} className="font-semibold" />,
    },
    {
      key: 'balance_due_paise',
      header: 'Balance Due',
      sortable: true,
      render: (row) => (
        <MoneyText
          paise={row.balance_due_paise}
          isOverdue={isOverdue(row.due_date, row.balance_due_paise)}
          className="font-bold"
        />
      ),
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Invoices"
        description="Billing statements, tax invoices, outstanding payment balances, and payment collection status"
        actions={
          <div className="flex items-center gap-2">
            <Link
              to="/invoices/outstanding"
              className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-1.5 text-xs font-semibold hover:bg-muted"
            >
              <Clock className="h-3.5 w-3.5 text-amber-500" />
              <span>Outstanding List</span>
            </Link>
            <Link
              to="/billing-run"
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-1.5 text-xs font-semibold text-primary-foreground shadow hover:bg-primary/90"
            >
              <Zap className="h-3.5 w-3.5" />
              <span>Billing Run</span>
            </Link>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items}
        total={data?.total}
        page={page}
        perPage={perPage}
        pages={data?.pages}
        isLoading={isLoading}
        searchPlaceholder="Search invoices by number, customer..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        onSortChange={(k, ord) => {
          setSort(k);
          setOrder(ord);
        }}
        exportFilename="invoices"
        customFilterNode={
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-md border border-input bg-background px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="confirmed">Confirmed</option>
            <option value="paid">Paid</option>
            <option value="cancelled">Cancelled</option>
          </select>
        }
      />
    </div>
  );
};
