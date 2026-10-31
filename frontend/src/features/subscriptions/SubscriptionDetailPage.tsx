import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useSubscription, useInvoices } from '../../api/hooks';
import { subscriptionApi } from '../../api/endpoints';
import { useAuth } from '../../app/AuthContext';
import { PageHeader } from '../../components/PageHeader';
import { StatusBadge } from '../../components/StatusBadge';
import { MoneyText } from '../../components/MoneyText';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { ErrorState } from '../../components/ErrorState';
import { formatDate, formatDateTime } from '../../lib/dates';
import { getValidSubscriptionTransitions } from '../../lib/permissions';
import {
  Layers,
  Calendar,
  Receipt,
  User,
  History,
  CheckCircle,
  Play,
  Pause,
  RotateCcw,
  XCircle,
  AlertCircle,
  Tag,
} from 'lucide-react';

export const SubscriptionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { role } = useAuth();

  const { data: sub, isLoading, isError, refetch } = useSubscription(id || '');
  const { data: invoicesData } = useInvoices({ subscription_id: id, per_page: 20 });

  // Transition modal state
  const [pendingAction, setPendingAction] = useState<{
    action: 'confirm' | 'activate' | 'pause' | 'resume' | 'renew' | 'close';
    label: string;
    destructive?: boolean;
  } | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  if (isError || (!isLoading && !sub)) {
    return <ErrorState message="Could not find the requested subscription." onRetry={() => refetch()} />;
  }

  const validActions = sub
    ? getValidSubscriptionTransitions(sub.status, role || 'customer', sub.plan)
    : [];

  const handleTriggerAction = async (reason?: string) => {
    if (!pendingAction || !id) return;

    setIsSubmitting(true);
    setActionError(null);

    try {
      await subscriptionApi[pendingAction.action](id, reason);
      setPendingAction(null);
      refetch();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={sub?.subscription_number || 'Subscription Details'}
        description={`Contract for ${sub?.customer_name || 'Customer'}`}
        breadcrumbs={[
          { label: 'Subscriptions', href: '/subscriptions' },
          { label: sub?.subscription_number || 'Details' },
        ]}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {validActions.map((act) => (
              <button
                key={act.action}
                onClick={() => setPendingAction(act)}
                disabled={isSubmitting}
                className={`inline-flex items-center gap-1.5 rounded-md px-3.5 py-1.5 text-xs font-semibold shadow-sm transition-colors disabled:opacity-50 ${
                  act.destructive
                    ? 'bg-destructive text-white hover:bg-destructive/90'
                    : 'bg-primary text-primary-foreground hover:bg-primary/90'
                }`}
              >
                {act.action === 'confirm' && <CheckCircle className="h-3.5 w-3.5" />}
                {act.action === 'activate' && <Play className="h-3.5 w-3.5" />}
                {act.action === 'pause' && <Pause className="h-3.5 w-3.5" />}
                {act.action === 'resume' && <Play className="h-3.5 w-3.5" />}
                {act.action === 'renew' && <RotateCcw className="h-3.5 w-3.5" />}
                {act.action === 'close' && <XCircle className="h-3.5 w-3.5" />}
                <span>{act.label}</span>
              </button>
            ))}
          </div>
        }
      />

      {actionError && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Summary Header Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <span className="text-xs text-muted-foreground">Current Status</span>
          <div className="mt-2 flex items-center gap-2">
            <StatusBadge status={sub?.status || 'draft'} />
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <span className="text-xs text-muted-foreground">Plan & Billing Frequency</span>
          <p className="mt-1 text-sm font-semibold text-foreground">
            {sub?.plan_name} <span className="uppercase text-xs font-normal text-muted-foreground">({sub?.billing_period})</span>
          </p>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <span className="text-xs text-muted-foreground">Recurring Cycle Total</span>
          <div className="mt-1 flex items-baseline gap-1.5">
            <MoneyText paise={sub?.recurring_total_paise ?? 0} className="text-lg font-bold text-foreground" />
            <span className="text-[10px] text-muted-foreground uppercase font-medium">(Estimate)</span>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <span className="text-xs text-muted-foreground">Next Scheduled Billing</span>
          <p className="mt-1 text-sm font-semibold text-foreground">
            {formatDate(sub?.next_billing_date)}
          </p>
        </div>
      </div>

      {/* Order Lines Table */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
            <Layers className="h-4 w-4 text-primary" /> Subscription Order Lines
          </h3>
          <span className="text-xs text-muted-foreground font-medium">
            Pricing: Sales Price + Variant Extra
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-border bg-muted/40 text-muted-foreground font-medium uppercase">
              <tr>
                <th className="p-3">Product / Service</th>
                <th className="p-3">Variant</th>
                <th className="p-3 text-right">Quantity</th>
                <th className="p-3 text-right">Unit Price (Estimate)</th>
                <th className="p-3 text-right">Tax (%)</th>
                <th className="p-3 text-right">Line Total (Estimate)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {sub?.lines.map((line) => (
                <tr key={line.id} className="hover:bg-muted/30">
                  <td className="p-3 font-medium text-foreground">{line.product_name}</td>
                  <td className="p-3 text-muted-foreground">{line.variant_name || 'Standard Base'}</td>
                  <td className="p-3 text-right font-mono">{line.quantity}</td>
                  <td className="p-3 text-right font-mono">
                    <MoneyText paise={line.unit_price_paise} />
                  </td>
                  <td className="p-3 text-right font-mono">{line.tax_rate_percent}%</td>
                  <td className="p-3 text-right font-mono font-semibold">
                    <MoneyText paise={line.line_total_paise} />
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="border-t border-border bg-muted/20 font-semibold text-foreground">
              <tr>
                <td colSpan={5} className="p-3 text-right">Subtotal:</td>
                <td className="p-3 text-right font-mono">
                  <MoneyText paise={sub?.subtotal_paise ?? 0} />
                </td>
              </tr>
              {Boolean(sub?.discount_paise) && (
                <tr className="text-emerald-600">
                  <td colSpan={5} className="p-3 text-right">
                    Applied Discount ({sub?.applied_discount_name || 'Discount'}):
                  </td>
                  <td className="p-3 text-right font-mono">
                    -<MoneyText paise={sub?.discount_paise ?? 0} />
                  </td>
                </tr>
              )}
              <tr>
                <td colSpan={5} className="p-3 text-right">Total Tax:</td>
                <td className="p-3 text-right font-mono">
                  <MoneyText paise={sub?.tax_paise ?? 0} />
                </td>
              </tr>
              <tr className="border-t-2 border-border text-sm">
                <td colSpan={5} className="p-3 text-right font-bold">
                  Recurring Total Per Period (Estimate):
                </td>
                <td className="p-3 text-right font-mono font-bold text-primary">
                  <MoneyText paise={sub?.recurring_total_paise ?? 0} />
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Grid: Linked Invoices & Status Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Linked Invoices */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
          <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
            <Receipt className="h-4 w-4 text-primary" /> Generated Invoices
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-border bg-muted/40 text-muted-foreground font-medium uppercase">
                <tr>
                  <th className="p-2.5">Invoice #</th>
                  <th className="p-2.5">Date</th>
                  <th className="p-2.5">Total</th>
                  <th className="p-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {invoicesData?.items.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-4 text-center text-muted-foreground">
                      No invoices generated yet. Run billing cycle to generate recurring invoices.
                    </td>
                  </tr>
                ) : (
                  invoicesData?.items.map((inv) => (
                    <tr key={inv.id} className="hover:bg-muted/30">
                      <td className="p-2.5 font-mono font-medium">
                        <Link to={`/invoices/${inv.id}`} className="text-primary hover:underline">
                          {inv.invoice_number}
                        </Link>
                      </td>
                      <td className="p-2.5">{formatDate(inv.issue_date)}</td>
                      <td className="p-2.5">
                        <MoneyText paise={inv.total_paise} />
                      </td>
                      <td className="p-2.5">
                        <StatusBadge status={inv.status} />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Status Transition History Timeline */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
          <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
            <History className="h-4 w-4 text-primary" /> Status Lifecycle Timeline
          </h3>

          <div className="space-y-4 pt-2">
            {sub?.status_history && sub.status_history.length > 0 ? (
              sub.status_history.map((sh, idx) => (
                <div key={sh.id || idx} className="flex gap-3 text-xs">
                  <div className="flex flex-col items-center">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-primary font-bold">
                      •
                    </span>
                    {idx < sub.status_history!.length - 1 && (
                      <span className="w-0.5 grow bg-border my-1" />
                    )}
                  </div>
                  <div className="flex-1 pb-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-foreground uppercase tracking-wide">
                        Transition to {sh.to_status}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {formatDateTime(sh.created_at)}
                      </span>
                    </div>
                    <p className="text-muted-foreground mt-0.5">
                      By <span className="font-medium text-foreground">{sh.changed_by_name}</span>
                    </p>
                    {sh.reason && (
                      <p className="mt-1 rounded bg-muted/40 p-2 text-foreground text-[11px] italic">
                        "{sh.reason}"
                      </p>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-muted-foreground">No historical transitions recorded.</p>
            )}
          </div>
        </div>
      </div>

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(pendingAction)}
        title={pendingAction?.label || 'Confirm Action'}
        message={`Are you sure you want to perform "${pendingAction?.label}" on ${sub?.subscription_number}?`}
        confirmLabel={pendingAction?.label}
        isDestructive={pendingAction?.destructive}
        requireReason={pendingAction?.action === 'close'}
        reasonPlaceholder="Specify reason for subscription closure/cancellation..."
        isLoading={isSubmitting}
        onConfirm={handleTriggerAction}
        onCancel={() => setPendingAction(null)}
      />
    </div>
  );
};
