import React, { useState } from 'react';
import { useRefunds, usePayments, useInvalidateQueries } from '../../api/hooks';
import { refundApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { StatusBadge } from '../../components/StatusBadge';
import { MoneyText } from '../../components/MoneyText';
import { FormField } from '../../components/FormField';
import { Refund } from '../../api/types';
import { formatDate } from '../../lib/dates';
import { formatMoney, rupeesToPaise } from '../../lib/money';
import { Plus, RotateCcw, AlertCircle } from 'lucide-react';

export const CustomerRefundsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');

  const [isRequestOpen, setIsRequestOpen] = useState(false);
  const [paymentId, setPaymentId] = useState('');
  const [amountRupees, setAmountRupees] = useState('');
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading, refetch } = useRefunds({
    page,
    per_page: perPage,
    q: search,
  });

  const { data: paymentsData } = usePayments({ per_page: 50 });
  const { invalidateRefunds } = useInvalidateQueries();

  const handleOpenRequest = () => {
    const firstPay = paymentsData?.items[0];
    setPaymentId(firstPay?.id || '');
    setAmountRupees(firstPay ? (firstPay.amount_paise / 100).toFixed(2) : '');
    setReason('');
    setFormError(null);
    setIsRequestOpen(true);
  };

  const handleRequestRefund = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!paymentId || !amountRupees || !reason) {
      setFormError('Please select a payment, enter amount, and explain the reason');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      await refundApi.create({
        payment_id: paymentId,
        amount_paise: rupeesToPaise(amountRupees),
        reason,
      });

      setIsRequestOpen(false);
      refetch();
      invalidateRefunds();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to submit refund request');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns: Column<Refund>[] = [
    {
      key: 'refund_number',
      header: 'Refund #',
      sortable: true,
      render: (row) => <span className="font-mono font-semibold text-primary">{row.refund_number}</span>,
    },
    {
      key: 'invoice_number',
      header: 'Invoice #',
      render: (row) => <span className="font-mono text-xs">{row.invoice_number}</span>,
    },
    {
      key: 'amount_paise',
      header: 'Amount',
      render: (row) => <MoneyText paise={row.amount_paise} className="font-bold text-rose-600" />,
    },
    {
      key: 'reason',
      header: 'Reason',
      render: (row) => <span className="text-xs text-muted-foreground">{row.reason}</span>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: 'created_at',
      header: 'Requested Date',
      render: (row) => <span>{formatDate(row.created_at)}</span>,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Refund Requests"
        description="Track credit refund reviews and submit claims for billing discrepancies"
        actions={
          <button
            onClick={handleOpenRequest}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-2 text-xs font-semibold text-primary-foreground shadow hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> Request Refund
          </button>
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
        searchPlaceholder="Search refund requests..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        exportFilename="my_refund_requests"
      />

      {/* Modal */}
      {isRequestOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-xl">
            <h3 className="text-base font-semibold text-foreground mb-4">Submit Refund Claim</h3>

            {formError && (
              <p className="mb-4 rounded bg-destructive/10 p-2 text-xs text-destructive">{formError}</p>
            )}

            <form onSubmit={handleRequestRefund} className="space-y-4">
              <FormField label="Select Paid Settlement" required id="cp">
                <select
                  id="cp"
                  value={paymentId}
                  onChange={(e) => setPaymentId(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                >
                  {paymentsData?.items.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.payment_number} (Invoice: {p.invoice_number}) - Paid: {formatMoney(p.amount_paise)}
                    </option>
                  ))}
                </select>
              </FormField>

              <FormField label="Claim Amount (₹)" required id="ca">
                <input
                  id="ca"
                  type="number"
                  step="0.01"
                  min="1"
                  value={amountRupees}
                  onChange={(e) => setAmountRupees(e.target.value)}
                  placeholder="0.00"
                  required
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </FormField>

              <FormField label="Explanation / Reason" required id="cr">
                <textarea
                  id="cr"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={3}
                  required
                  placeholder="Explain why you are requesting a refund..."
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </FormField>

              <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setIsRequestOpen(false)}
                  disabled={isSubmitting}
                  className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Claim'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
