import React, { useState } from 'react';
import { usePortalInvoices } from '../../api/hooks';
import { invoiceApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { StatusBadge } from '../../components/StatusBadge';
import { MoneyText } from '../../components/MoneyText';
import { Invoice } from '../../api/types';
import { formatDate, isOverdue } from '../../lib/dates';
import { FileDown } from 'lucide-react';

export const CustomerInvoicesPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');

  const { data, isLoading } = usePortalInvoices({
    page,
    per_page: perPage,
    q: search,
  });

  const handleDownloadPdf = async (inv: Invoice) => {
    try {
      const blob = await invoiceApi.getPdf(inv.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${inv.invoice_number}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to download PDF');
    }
  };

  const columns: Column<Invoice>[] = [
    {
      key: 'invoice_number',
      header: 'Invoice #',
      sortable: true,
      render: (row) => <span className="font-mono font-semibold text-foreground">{row.invoice_number}</span>,
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
          <span className={overdue ? 'text-destructive font-semibold' : ''}>
            {formatDate(row.due_date)}
          </span>
        );
      },
    },
    {
      key: 'total_paise',
      header: 'Total Amount',
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
    {
      key: 'actions',
      header: 'Invoice PDF',
      render: (row) => (
        <button
          onClick={() => handleDownloadPdf(row)}
          className="inline-flex items-center gap-1 rounded border border-input bg-background px-2.5 py-1 text-xs font-medium hover:bg-muted"
        >
          <FileDown className="h-3.5 w-3.5 text-primary" />
          <span>PDF</span>
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Invoices"
        description="Review billing statements, outstanding balances, and download tax invoice receipts"
      />

      <DataTable
        columns={columns}
        data={data?.items}
        total={data?.total}
        page={page}
        perPage={perPage}
        pages={data?.pages}
        isLoading={isLoading}
        searchPlaceholder="Search invoices..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        exportFilename="my_invoices"
      />
    </div>
  );
};
