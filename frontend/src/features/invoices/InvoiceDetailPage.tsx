import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useInvoice, usePayments } from '../../api/hooks';
import { invoiceApi } from '../../api/endpoints';
import { useAuth } from '../../app/AuthContext';
import { PageHeader } from '../../components/PageHeader';
import { StatusBadge } from '../../components/StatusBadge';
import { MoneyText } from '../../components/MoneyText';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { ErrorState } from '../../components/ErrorState';
import { formatDate, isOverdue } from '../../lib/dates';
import {
  canConfirmInvoice,
  canSendInvoice,
  canPrintInvoice,
  canCancelInvoice,
} from '../../lib/permissions';
import {
  CheckCircle,
  Send,
  Printer,
  XCircle,
  Receipt,
  CreditCard,
  Building,
  AlertCircle,
  FileDown,
} from 'lucide-react';

export const InvoiceDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { role } = useAuth();

  const { data: invoice, isLoading, isError, refetch } = useInvoice(id || '');
  const { data: paymentsData } = usePayments({ invoice_id: id, per_page: 20 });

  const [isCancelDialogOpen, setIsCancelDialogOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (isError || (!isLoading && !invoice)) {
    return <ErrorState message="Could not find the requested invoice." onRetry={() => refetch()} />;
  }

  const userRole = role || 'customer';
  const overdue = isOverdue(invoice?.due_date, invoice?.balance_due_paise);

  const canConfirm = invoice ? canConfirmInvoice(invoice, userRole) : false;
  const canSend = invoice ? canSendInvoice(invoice, userRole) : false;
  const canPrint = invoice ? canPrintInvoice(invoice) : false;
  const canCancel = invoice ? canCancelInvoice(invoice, userRole) : false;

  const handleConfirm = async () => {
    if (!id) return;
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await invoiceApi.confirm(id);
      setActionFeedback('Invoice confirmed and amounts locked.');
      refetch();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to confirm invoice');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSend = async () => {
    if (!id) return;
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const res = await invoiceApi.send(id);
      setActionFeedback(res.message);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to send invoice');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!id || !invoice) return;
    try {
      const blob = await invoiceApi.getPdf(id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${invoice.invoice_number}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to download PDF');
    }
  };

  const handleCancelInvoice = async (reason?: string) => {
    if (!id) return;
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await invoiceApi.cancel(id, reason);
      setIsCancelDialogOpen(false);
      setActionFeedback('Invoice has been cancelled.');
      refetch();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to cancel invoice');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={invoice?.invoice_number || 'Invoice Statement'}
        description={`Issued to ${invoice?.customer_name || 'Customer'}`}
        breadcrumbs={[
          { label: 'Invoices', href: '/invoices' },
          { label: invoice?.invoice_number || 'Details' },
        ]}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {canConfirm && (
              <button
                onClick={handleConfirm}
                disabled={isSubmitting}
                className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-1.5 text-xs font-semibold text-primary-foreground shadow hover:bg-primary/90 disabled:opacity-50"
              >
                <CheckCircle className="h-3.5 w-3.5" /> Confirm Invoice
              </button>
            )}

            {canSend && (
              <button
                onClick={handleSend}
                disabled={isSubmitting}
                className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3.5 py-1.5 text-xs font-semibold hover:bg-muted disabled:opacity-50"
              >
                <Send className="h-3.5 w-3.5 text-primary" /> Send Statement
              </button>
            )}

            {canPrint && (
              <button
                onClick={handleDownloadPdf}
                className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3.5 py-1.5 text-xs font-semibold hover:bg-muted"
                title="Download official PDF copy"
              >
                <FileDown className="h-3.5 w-3.5 text-primary" /> Download PDF
              </button>
            )}

            {canCancel && (
              <button
                onClick={() => setIsCancelDialogOpen(true)}
                disabled={isSubmitting}
                className="inline-flex items-center gap-1.5 rounded-md bg-destructive/10 text-destructive border border-destructive/20 px-3.5 py-1.5 text-xs font-semibold hover:bg-destructive/20 disabled:opacity-50"
              >
                <XCircle className="h-3.5 w-3.5" /> Cancel Invoice
              </button>
            )}
          </div>
        }
      />

      {actionFeedback && (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-800 dark:text-emerald-200 flex items-center justify-between">
          <span>{actionFeedback}</span>
          <button onClick={() => setActionFeedback(null)} className="font-bold opacity-60">Dismiss</button>
        </div>
      )}

      {errorMessage && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Invoice Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <span className="text-xs text-muted-foreground">Invoice Status</span>
          <div className="mt-2 flex items-center gap-2">
            <StatusBadge status={invoice?.status || 'draft'} />
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <span className="text-xs text-muted-foreground">Issue & Due Date</span>
          <p className="mt-1 text-xs text-foreground font-medium">
            Issued: {formatDate(invoice?.issue_date)}
          </p>
          <p className={`text-xs mt-0.5 font-medium ${overdue ? 'text-destructive font-bold' : 'text-muted-foreground'}`}>
            Due: {formatDate(invoice?.due_date)} {overdue && '(OVERDUE)'}
          </p>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <span className="text-xs text-muted-foreground">Total Invoiced</span>
          <div className="mt-1">
            <MoneyText paise={invoice?.total_paise ?? 0} className="text-xl font-bold text-foreground" />
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <span className="text-xs text-muted-foreground">Balance Due</span>
          <div className="mt-1">
            <MoneyText
              paise={invoice?.balance_due_paise ?? 0}
              isOverdue={overdue}
              className="text-xl font-bold"
            />
          </div>
        </div>
      </div>

      {/* Invoice Line Items & Strict Calculation Breakdown */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
        <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
          <Receipt className="h-4 w-4 text-primary" /> Invoice Breakdown
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-border bg-muted/40 text-muted-foreground font-medium uppercase">
              <tr>
                <th className="p-3">Line Item Description</th>
                <th className="p-3 text-right">Quantity</th>
                <th className="p-3 text-right">Unit Price</th>
                <th className="p-3 text-right">Tax (%)</th>
                <th className="p-3 text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {invoice?.lines.map((line) => (
                <tr key={line.id} className="hover:bg-muted/30">
                  <td className="p-3">
                    <p className="font-semibold text-foreground">{line.product_name}</p>
                    {line.variant_name && (
                      <p className="text-[11px] text-muted-foreground">Variant: {line.variant_name}</p>
                    )}
                  </td>
                  <td className="p-3 text-right font-mono">{line.quantity}</td>
                  <td className="p-3 text-right font-mono">
                    <MoneyText paise={line.unit_price_paise} />
                  </td>
                  <td className="p-3 text-right font-mono">{line.tax_rate_percent}%</td>
                  <td className="p-3 text-right font-mono font-medium">
                    <MoneyText paise={line.line_subtotal_paise} />
                  </td>
                </tr>
              ))}
            </tbody>

            {/* Strict Calculation Order: Line Amount -> Discount -> Tax -> Total */}
            <tfoot className="border-t border-border bg-muted/20 font-medium text-foreground">
              <tr>
                <td colSpan={4} className="p-3 text-right">1. Lines Subtotal:</td>
                <td className="p-3 text-right font-mono font-semibold">
                  <MoneyText paise={invoice?.lines_subtotal_paise ?? 0} />
                </td>
              </tr>

              {/* Discount as its own line */}
              {Boolean(invoice?.discount_paise) && (
                <tr className="text-emerald-600 dark:text-emerald-400">
                  <td colSpan={4} className="p-3 text-right">
                    2. Discount ({invoice?.discount_name || 'Promotional concession'}):
                  </td>
                  <td className="p-3 text-right font-mono font-semibold">
                    -<MoneyText paise={invoice?.discount_paise ?? 0} />
                  </td>
                </tr>
              )}

              <tr>
                <td colSpan={4} className="p-3 text-right text-muted-foreground">
                  Net Taxable Amount:
                </td>
                <td className="p-3 text-right font-mono text-muted-foreground">
                  <MoneyText paise={invoice?.taxable_amount_paise ?? 0} />
                </td>
              </tr>

              <tr>
                <td colSpan={4} className="p-3 text-right">3. Total Taxes (GST):</td>
                <td className="p-3 text-right font-mono font-semibold">
                  <MoneyText paise={invoice?.tax_total_paise ?? 0} />
                </td>
              </tr>

              <tr className="border-t-2 border-border text-sm font-bold">
                <td colSpan={4} className="p-3 text-right">4. Final Invoice Total:</td>
                <td className="p-3 text-right font-mono text-primary font-bold">
                  <MoneyText paise={invoice?.total_paise ?? 0} />
                </td>
              </tr>

              <tr className="text-xs text-muted-foreground">
                <td colSpan={4} className="p-3 text-right">Amount Settled / Paid:</td>
                <td className="p-3 text-right font-mono text-emerald-600 font-semibold">
                  <MoneyText paise={invoice?.amount_paid_paise ?? 0} />
                </td>
              </tr>

              <tr className="border-t border-border text-sm font-bold bg-muted/40">
                <td colSpan={4} className="p-3 text-right">Remaining Balance Due:</td>
                <td className="p-3 text-right font-mono font-bold">
                  <MoneyText
                    paise={invoice?.balance_due_paise ?? 0}
                    isOverdue={overdue}
                  />
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Linked Payments Table */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
            <CreditCard className="h-4 w-4 text-primary" /> Recorded Payments
          </h3>
          {invoice?.status === 'confirmed' && invoice.balance_due_paise > 0 && userRole !== 'customer' && (
            <Link
              to="/payments"
              className="inline-flex items-center gap-1 text-xs text-primary font-medium hover:underline"
            >
              Record Payment
            </Link>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-border bg-muted/40 text-muted-foreground font-medium uppercase">
              <tr>
                <th className="p-2.5">Payment #</th>
                <th className="p-2.5">Date</th>
                <th className="p-2.5">Method</th>
                <th className="p-2.5">Reference</th>
                <th className="p-2.5 text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {paymentsData?.items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-4 text-center text-muted-foreground">
                    No payments recorded for this invoice yet.
                  </td>
                </tr>
              ) : (
                paymentsData?.items.map((pay) => (
                  <tr key={pay.id} className="hover:bg-muted/30">
                    <td className="p-2.5 font-mono font-medium">{pay.payment_number}</td>
                    <td className="p-2.5">{formatDate(pay.payment_date)}</td>
                    <td className="p-2.5 uppercase font-medium">{pay.payment_method}</td>
                    <td className="p-2.5 font-mono text-[11px] text-muted-foreground">
                      {pay.reference || '—'}
                    </td>
                    <td className="p-2.5 text-right font-mono font-bold text-emerald-600">
                      <MoneyText paise={pay.amount_paise} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cancel Confirm Dialog */}
      <ConfirmDialog
        isOpen={isCancelDialogOpen}
        title="Cancel Invoice"
        message={`Are you sure you want to cancel invoice ${invoice?.invoice_number}? This will nullify the balance and freeze further payment processing.`}
        confirmLabel="Cancel Invoice"
        isDestructive={true}
        requireReason={true}
        reasonPlaceholder="Specify reason for cancelling this invoice..."
        isLoading={isSubmitting}
        onConfirm={handleCancelInvoice}
        onCancel={() => setIsCancelDialogOpen(false)}
      />
    </div>
  );
};
