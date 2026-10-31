import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useRefunds, usePayments, useInvalidateQueries } from '../../api/hooks';
import { refundApi } from '../../api/endpoints';
import { useAuth } from '../../app/AuthContext';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { StatusBadge } from '../../components/StatusBadge';
import { MoneyText } from '../../components/MoneyText';
import { FormField } from '../../components/FormField';
import { Refund } from '../../api/types';
import { formatDate } from '../../lib/dates';
import { formatMoney, rupeesToPaise } from '../../lib/money';
import { Plus, RotateCcw, AlertCircle, CheckCircle, ShieldAlert, X } from 'lucide-react';

export const RefundsListPage: React.FC = () => {
  const { role } = useAuth();
  const isAdmin = role === 'admin';

  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('created_at');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');

  // Request Refund Modal
  const [isRequestOpen, setIsRequestOpen] = useState(false);
  const [paymentId, setPaymentId] = useState('');
  const [amountRupees, setAmountRupees] = useState('');
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Review / Process Modal
  const [reviewingRefund, setReviewingRefund] = useState<Refund | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');

  const { data, isLoading, refetch } = useRefunds({
    page,
    per_page: perPage,
    q: search,
    sort,
    order,
  });

  const { data: paymentsData } = usePayments({ per_page: 50 });
  const { invalidateRefunds, invalidatePayments } = useInvalidateQueries();

  const selectedPayment = paymentsData?.items.find((p) => p.id === paymentId);

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
      setFormError('Please select a payment, enter amount, and specify a reason');
      return;
    }

    const amountPaise = rupeesToPaise(amountRupees);
    if (selectedPayment && amountPaise > selectedPayment.amount_paise) {
      setFormError(`Refund amount cannot exceed payment amount of ${formatMoney(selectedPayment.amount_paise)}.`);
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      await refundApi.create({
        payment_id: paymentId,
        amount_paise: amountPaise,
        reason,
      });

      setIsRequestOpen(false);
      refetch();
      invalidateRefunds();
      invalidatePayments();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to request refund');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateStatus = async (status: Refund['status']) => {
    if (!reviewingRefund) return;
    setIsSubmitting(true);
    setFormError(null);

    try {
      await refundApi.update(reviewingRefund.id, {
        status,
        rejection_reason: status === 'rejected' ? rejectionReason : undefined,
      });

      setReviewingRefund(null);
      refetch();
      invalidateRefunds();
      invalidatePayments();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns: Column<Refund>[] = [
    {
      key: 'refund_number',
      header: 'Refund #',
      sortable: true,
      render: (row) => (
        <div>
          <span className="font-mono font-semibold text-primary">{row.refund_number}</span>
          <p className="text-xs text-muted-foreground">{row.customer_name}</p>
        </div>
      ),
    },
    {
      key: 'invoice_number',
      header: 'Linked Invoice',
      render: (row) => (
        <Link
          to={`/invoices/${row.invoice_id}`}
          className="font-mono text-xs text-primary hover:underline"
        >
          {row.invoice_number}
        </Link>
      ),
    },
    {
      key: 'amount_paise',
      header: 'Refund Amount',
      sortable: true,
      render: (row) => (
        <MoneyText paise={row.amount_paise} className="font-bold text-rose-600 text-sm" />
      ),
    },
    {
      key: 'reason',
      header: 'Reason',
      render: (row) => (
        <span className="text-xs text-muted-foreground line-clamp-1 max-w-xs">{row.reason}</span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: 'created_at',
      header: 'Requested Date',
      sortable: true,
      render: (row) => <span>{formatDate(row.created_at)}</span>,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => {
        if (row.status === 'processed' || row.status === 'rejected') {
          return <span className="text-xs text-muted-foreground">Completed</span>;
        }

        return (
          <button
            onClick={() => {
              setReviewingRefund(row);
              setRejectionReason('');
              setFormError(null);
            }}
            className="inline-flex items-center gap-1 rounded border border-input bg-background px-2.5 py-1 text-xs font-medium hover:bg-muted"
          >
            Review / Process
          </button>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Refunds"
        description="Process customer credit reversals, overcharge corrections, and manage approval thresholds"
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
        searchPlaceholder="Search refunds..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        onSortChange={(k, ord) => {
          setSort(k);
          setOrder(ord);
        }}
        exportFilename="refunds_ledger"
      />

      {/* Request Refund Modal */}
      {isRequestOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-semibold text-foreground mb-4">Request Customer Refund</h3>

            {formError && (
              <div className="mb-4 rounded bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleRequestRefund} className="space-y-4">
              <FormField label="Target Paid Settlement" required id="rpay">
                <select
                  id="rpay"
                  value={paymentId}
                  onChange={(e) => {
                    setPaymentId(e.target.value);
                    const p = paymentsData?.items.find((item) => item.id === e.target.value);
                    if (p) setAmountRupees((p.amount_paise / 100).toFixed(2));
                  }}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                >
                  {paymentsData?.items.map((pay) => (
                    <option key={pay.id} value={pay.id}>
                      {pay.payment_number} ({pay.customer_name}) - Paid: {formatMoney(pay.amount_paise)}
                    </option>
                  ))}
                </select>
              </FormField>

              {selectedPayment && (
                <div className="rounded-lg border border-border bg-muted/30 p-3 text-xs flex justify-between">
                  <div>
                    <span className="text-muted-foreground">Invoice #</span>
                    <p className="font-semibold text-foreground">{selectedPayment.invoice_number}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Original Payment:</span>
                    <p className="font-semibold text-emerald-600">{formatMoney(selectedPayment.amount_paise)}</p>
                  </div>
                </div>
              )}

              <FormField label="Refund Amount (₹)" required id="ramt">
                <input
                  id="ramt"
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

              <FormField label="Justification / Refund Reason" required id="rreason">
                <textarea
                  id="rreason"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Billing error, service credit, duplicate payment..."
                  rows={3}
                  required
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
                  {isSubmitting ? 'Submitting...' : 'Submit Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Review / Process Modal */}
      {reviewingRefund && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-xl">
            <h3 className="text-base font-semibold text-foreground mb-4">
              Review Refund: {reviewingRefund.refund_number}
            </h3>

            {formError && (
              <div className="mb-4 rounded bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <div className="space-y-3 text-xs mb-4">
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">Customer:</span>
                <span className="font-semibold text-foreground">{reviewingRefund.customer_name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">Refund Amount:</span>
                <span className="font-mono font-bold text-rose-600 text-sm">
                  {formatMoney(reviewingRefund.amount_paise)}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">Current Status:</span>
                <StatusBadge status={reviewingRefund.status} />
              </div>
              <div>
                <span className="text-muted-foreground block mb-1">Reason:</span>
                <p className="bg-muted/40 p-2.5 rounded border border-border text-foreground italic">
                  "{reviewingRefund.reason}"
                </p>
              </div>

              {/* Staff threshold limit warning */}
              {reviewingRefund.amount_paise > 500000 && !isAdmin && (
                <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-2.5 text-xs text-amber-700 dark:text-amber-300 flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 shrink-0" />
                  <span>
                    Refunds above ₹5,000.00 require Admin approval. You may request admin review.
                  </span>
                </div>
              )}

              <FormField label="Rejection Note (if rejecting)" id="rejnote">
                <input
                  id="rejnote"
                  type="text"
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="Specify reason for refusal..."
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </FormField>
            </div>

            <div className="mt-6 flex flex-wrap justify-end gap-2 pt-4 border-t border-border">
              <button
                type="button"
                onClick={() => setReviewingRefund(null)}
                disabled={isSubmitting}
                className="rounded-md border border-input px-3 py-1.5 text-xs font-medium hover:bg-muted"
              >
                Close
              </button>

              <button
                type="button"
                onClick={() => handleUpdateStatus('rejected')}
                disabled={isSubmitting}
                className="rounded-md bg-destructive/10 text-destructive border border-destructive/30 px-3 py-1.5 text-xs font-semibold hover:bg-destructive/20"
              >
                Reject Refund
              </button>

              {reviewingRefund.status === 'requested' && (
                <button
                  type="button"
                  onClick={() => handleUpdateStatus('approved')}
                  disabled={isSubmitting || (reviewingRefund.amount_paise > 500000 && !isAdmin)}
                  className="rounded-md bg-blue-600 text-white px-3 py-1.5 text-xs font-semibold hover:bg-blue-700 disabled:opacity-50"
                >
                  Approve Refund
                </button>
              )}

              <button
                type="button"
                onClick={() => handleUpdateStatus('processed')}
                disabled={isSubmitting || (reviewingRefund.amount_paise > 500000 && !isAdmin)}
                className="rounded-md bg-emerald-600 text-white px-3 py-1.5 text-xs font-semibold hover:bg-emerald-700 disabled:opacity-50"
              >
                Process & Disburse
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
