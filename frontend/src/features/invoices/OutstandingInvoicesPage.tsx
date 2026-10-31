import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useOutstandingInvoices } from '../../api/hooks';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { StatusBadge } from '../../components/StatusBadge';
import { MoneyText } from '../../components/MoneyText';
import { Invoice } from '../../api/types';
import { formatDate, isOverdue } from '../../lib/dates';
import { Clock, AlertTriangle, ArrowLeft } from 'lucide-react';

export const OutstandingInvoicesPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('due_date');
  const [order, setOrder] = useState<'asc' | 'desc'>('asc');

  const { data, isLoading } = useOutstandingInvoices({
    page,
    per_page: perPage,
    q: search,
    sort,
    order,
  });

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
      key: 'due_date',
      header: 'Due Date',
      sortable: true,
      render: (row) => {
        const overdue = isOverdue(row.due_date, row.balance_due_paise);
        return (
          <span className={overdue ? 'text-destructive font-semibold flex items-center gap-1' : ''}>
            {formatDate(row.due_date)}
            {overdue && <AlertTriangle className="h-3 w-3 inline text-destructive" />}
          </span>
        );
      },
    },
    {
      key: 'total_paise',
      header: 'Total Invoiced',
      render: (row) => <MoneyText paise={row.total_paise} />,
    },
    {
      key: 'amount_paid_paise',
      header: 'Amount Paid',
      render: (row) => <MoneyText paise={row.amount_paid_paise} className="text-emerald-600" />,
    },
    {
      key: 'balance_due_paise',
      header: 'Remaining Balance Due',
      sortable: true,
      render: (row) => (
        <MoneyText
          paise={row.balance_due_paise}
          isOverdue={isOverdue(row.due_date, row.balance_due_paise)}
          className="text-base font-bold"
        />
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Outstanding & Overdue Invoices"
        description="All confirmed invoices with positive unpaid balance requiring settlement"
        breadcrumbs={[
          { label: 'Invoices', href: '/invoices' },
          { label: 'Outstanding' },
        ]}
      />

      <DataTable
        columns={columns}
        data={data?.items}
        total={data?.total}
        page={page}
        perPage={perPage}
        pages={data?.pages}
        isLoading={isLoading}
        searchPlaceholder="Search outstanding invoices..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        exportFilename="outstanding_invoices"
      />
    </div>
  );
};
