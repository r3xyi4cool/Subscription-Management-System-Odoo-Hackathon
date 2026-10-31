import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { usePayments, useInvoices, useInvalidateQueries } from '../../api/hooks';
import { paymentApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { MoneyText } from '../../components/MoneyText';
import { FormField } from '../../components/FormField';
import { Payment, PaymentMethod } from '../../api/types';
import { formatDate } from '../../lib/dates';
import { formatMoney, rupeesToPaise } from '../../lib/money';
import { Plus, CreditCard, Receipt, AlertCircle } from 'lucide-react';

export const PaymentsListPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('created_at');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');

  // Record Payment Modal
  const [isRecordOpen, setIsRecordOpen] = useState(false);
  const [invoiceId, setInvoiceId] = useState('');
  const [amountRupees, setAmountRupees] = useState('');
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('bank_transfer');
  const [reference, setReference] = useState('');
  const [paymentDate, setPaymentDate] = useState('');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading, refetch } = usePayments({
    page,
    per_page: perPage,
    q: search,
    sort,
    order,
  });

  const { data: outstandingInvoicesData } = useInvoices({ status: 'confirmed', per_page: 100 });
  const { invalidateInvoices, invalidatePayments } = useInvalidateQueries();

  const selectedInvoice = outstandingInvoicesData?.items.find((i) => i.id === invoiceId);

  const handleOpenRecord = () => {
    const firstInv = outstandingInvoicesData?.items[0];
    setInvoiceId(firstInv?.id || '');
    if (firstInv) {
      setAmountRupees((firstInv.balance_due_paise / 100).toFixed(2));
    } else {
      setAmountRupees('');
    }
    setPaymentMethod('bank_transfer');
    setReference('');
    setPaymentDate(new Date().toISOString().split('T')[0]);
    setNotes('');
    setFormError(null);
    setIsRecordOpen(true);
  };

  const handleInvoiceChange = (id: string) => {
    setInvoiceId(id);
    const inv = outstandingInvoicesData?.items.find((i) => i.id === id);
    if (inv) {
      setAmountRupees((inv.balance_due_paise / 100).toFixed(2));
    }
  };

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!invoiceId || !amountRupees) {
      setFormError('Please select an invoice and enter amount');
      return;
    }

    const amountPaise = rupeesToPaise(amountRupees);

    // Client-side rule: Block overpayment
    if (selectedInvoice && amountPaise > selectedInvoice.balance_due_paise) {
      setFormError(
        `Overpayment blocked! Payment amount cannot exceed remaining balance due of ${formatMoney(
          selectedInvoice.balance_due_paise
        )}.`
      );
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      await paymentApi.create({
        invoice_id: invoiceId,
        amount_paise: amountPaise,
        payment_method: paymentMethod,
        payment_date: paymentDate || undefined,
        reference: reference || null,
        notes: notes || null,
      });

      setIsRecordOpen(false);
      refetch();
      invalidateInvoices();
      invalidatePayments();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to record payment');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns: Column<Payment>[] = [
    {
      key: 'payment_number',
      header: 'Payment #',
      sortable: true,
      render: (row) => (
        <div>
          <span className="font-mono font-semibold text-primary">{row.payment_number}</span>
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
      key: 'payment_date',
      header: 'Payment Date',
      sortable: true,
      render: (row) => <span>{formatDate(row.payment_date)}</span>,
    },
    {
      key: 'payment_method',
      header: 'Method',
      sortable: true,
      render: (row) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wider bg-muted text-foreground border border-border">
          {row.payment_method.replace('_', ' ')}
        </span>
      ),
    },
    {
      key: 'reference',
      header: 'Reference / Transaction ID',
      render: (row) => (
        <span className="font-mono text-xs text-muted-foreground">{row.reference || '—'}</span>
      ),
    },
    {
      key: 'amount_paise',
      header: 'Amount Paid',
      sortable: true,
      render: (row) => (
        <MoneyText paise={row.amount_paise} className="font-bold text-emerald-600 text-sm" />
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Payments"
        description="Recorded settlements, transaction ledger, and invoice balance collections"
        actions={
          <button
            onClick={handleOpenRecord}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-2 text-xs font-semibold text-primary-foreground shadow hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> Record Payment
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
        searchPlaceholder="Search payments by number, reference..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        onSortChange={(k, ord) => {
          setSort(k);
          setOrder(ord);
        }}
        exportFilename="payments_ledger"
      />

      {/* Record Payment Modal */}
      {isRecordOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-semibold text-foreground mb-4">Record Inward Payment</h3>

            {formError && (
              <div className="mb-4 rounded bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleRecordPayment} className="space-y-4">
              <FormField label="Target Invoice" required id="pinv">
                <select
                  id="pinv"
                  value={invoiceId}
                  onChange={(e) => handleInvoiceChange(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                >
                  {outstandingInvoicesData?.items.length === 0 ? (
                    <option value="">No confirmed invoices with outstanding balance</option>
                  ) : (
                    outstandingInvoicesData?.items.map((inv) => (
                      <option key={inv.id} value={inv.id}>
                        {inv.invoice_number} - {inv.customer_name} (Balance: {formatMoney(inv.balance_due_paise)})
                      </option>
                    ))
                  )}
                </select>
              </FormField>

              {selectedInvoice && (
                <div className="rounded-lg border border-border bg-muted/30 p-3 text-xs flex justify-between">
                  <div>
                    <span className="text-muted-foreground">Invoice Total:</span>
                    <p className="font-semibold text-foreground">{formatMoney(selectedInvoice.total_paise)}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Already Paid:</span>
                    <p className="font-semibold text-emerald-600">{formatMoney(selectedInvoice.amount_paid_paise)}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Max Amount (Balance Due):</span>
                    <p className="font-bold text-primary">{formatMoney(selectedInvoice.balance_due_paise)}</p>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <FormField label="Payment Amount (₹)" required id="pamt">
                  <input
                    id="pamt"
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

                <FormField label="Payment Method" required id="pmeth">
                  <select
                    id="pmeth"
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="bank_transfer">Bank Transfer (NEFT/RTGS)</option>
                    <option value="credit_card">Credit Card</option>
                    <option value="upi">UPI / Instant</option>
                    <option value="cheque">Cheque</option>
                    <option value="cash">Cash</option>
                    <option value="other">Other</option>
                  </select>
                </FormField>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <FormField label="Payment Date" required id="pdate">
                  <input
                    id="pdate"
                    type="date"
                    value={paymentDate}
                    onChange={(e) => setPaymentDate(e.target.value)}
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>

                <FormField label="Transaction / Reference ID" id="pref">
                  <input
                    id="pref"
                    type="text"
                    value={reference}
                    onChange={(e) => setReference(e.target.value)}
                    placeholder="UTR / Ref #123456"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary font-mono"
                  />
                </FormField>
              </div>

              <FormField label="Notes" id="pnotes">
                <textarea
                  id="pnotes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Payment notes or remittance reference..."
                  rows={2}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </FormField>

              <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setIsRecordOpen(false)}
                  disabled={isSubmitting}
                  className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !selectedInvoice}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                >
                  {isSubmitting ? 'Recording...' : 'Record Payment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
