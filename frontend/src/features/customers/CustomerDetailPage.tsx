import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useCustomer, useSubscriptions, useInvoices, usePayments } from '../../api/hooks';
import { customerApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { StatusBadge } from '../../components/StatusBadge';
import { MoneyText } from '../../components/MoneyText';
import { ErrorState } from '../../components/ErrorState';
import { formatDate } from '../../lib/dates';
import {
  Mail,
  Phone,
  Building,
  MapPin,
  FileText,
  CreditCard,
  Layers,
  Receipt,
  Check,
  ExternalLink,
} from 'lucide-react';

export const CustomerDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [resetFeedback, setResetFeedback] = useState<string | null>(null);
  const [isSendingReset, setIsSendingReset] = useState(false);

  const { data: customer, isLoading, isError, refetch } = useCustomer(id || '');
  const { data: subsData } = useSubscriptions({ customer_id: id, per_page: 10 });
  const { data: invsData } = useInvoices({ customer_id: id, per_page: 10 });
  const { data: paysData } = usePayments({ customer_id: id, per_page: 10 });

  if (isError || (!isLoading && !customer)) {
    return <ErrorState message="Could not find the requested customer profile." onRetry={() => refetch()} />;
  }

  const handleSendResetLink = async () => {
    if (!id) return;
    setIsSendingReset(true);
    setResetFeedback(null);
    try {
      const res = await customerApi.sendResetLink(id);
      setResetFeedback(`Password reset link dispatched to ${customer?.email}`);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to send reset link');
    } finally {
      setIsSendingReset(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={customer?.name || 'Customer Details'}
        description={customer?.company_name || 'Customer Account Profile'}
        breadcrumbs={[
          { label: 'Customers', href: '/customers' },
          { label: customer?.name || 'Customer' },
        ]}
        actions={
          <button
            onClick={handleSendResetLink}
            disabled={isSendingReset || isLoading}
            className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3.5 py-2 text-xs font-semibold hover:bg-muted transition-colors disabled:opacity-50"
          >
            <Mail className="h-3.5 w-3.5 text-primary" />
            <span>{isSendingReset ? 'Sending Link...' : 'Send Password Reset Link'}</span>
          </button>
        }
      />

      {resetFeedback && (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-800 dark:text-emerald-200 flex items-center gap-2">
          <Check className="h-4 w-4 shrink-0" />
          <span>{resetFeedback}</span>
        </div>
      )}

      {/* Top Profile & Aggregations Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Customer Information Card */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-4">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Building className="h-4 w-4 text-primary" /> Company Profile
          </h3>

          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between py-1 border-b border-border">
              <span className="text-muted-foreground">Account Status:</span>
              <span
                className={`font-medium ${
                  customer?.is_active ? 'text-emerald-600' : 'text-rose-600'
                }`}
              >
                {customer?.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1 border-b border-border">
              <span className="text-muted-foreground">Contact Email:</span>
              <span className="font-mono text-foreground">{customer?.email}</span>
            </div>

            <div className="flex items-center justify-between py-1 border-b border-border">
              <span className="text-muted-foreground">Phone:</span>
              <span className="text-foreground">{customer?.phone || '—'}</span>
            </div>

            <div className="flex items-center justify-between py-1 border-b border-border">
              <span className="text-muted-foreground">GSTIN:</span>
              <span className="font-mono text-foreground">{customer?.gstin || '—'}</span>
            </div>

            <div className="pt-2">
              <span className="text-muted-foreground block mb-1">Billing Address:</span>
              <p className="text-foreground bg-muted/30 p-2 rounded border border-border text-[11px]">
                {customer?.billing_address || 'No billing address specified.'}
              </p>
            </div>
          </div>
        </div>

        {/* Aggregations KPI Cards */}
        <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Active Subscriptions</span>
              <div className="p-2 rounded-lg bg-primary/10 text-primary">
                <Layers className="h-4 w-4" />
              </div>
            </div>
            <p className="mt-3 text-2xl font-bold text-foreground">
              {customer?.active_subscriptions_count ?? 0}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">Currently active plans</p>
          </div>

          <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Total Invoiced</span>
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-600">
                <Receipt className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <MoneyText
                paise={customer?.total_invoiced_paise ?? 0}
                className="text-2xl font-bold text-foreground"
              />
            </div>
            <p className="mt-1 text-xs text-muted-foreground">Lifetime invoiced value</p>
          </div>

          <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">Outstanding Balance</span>
              <div className="p-2 rounded-lg bg-amber-500/10 text-amber-600">
                <CreditCard className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3">
              <MoneyText
                paise={customer?.outstanding_balance_paise ?? 0}
                isOverdue={(customer?.outstanding_balance_paise ?? 0) > 0}
                className="text-2xl font-bold"
              />
            </div>
            <p className="mt-1 text-xs text-muted-foreground">Pending confirmation or payment</p>
          </div>
        </div>
      </div>

      {/* Linked Subscriptions Table */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
        <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
          <Layers className="h-4 w-4 text-primary" /> Linked Subscriptions
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-border bg-muted/40 text-muted-foreground font-medium uppercase">
              <tr>
                <th className="p-2.5">Subscription #</th>
                <th className="p-2.5">Plan</th>
                <th className="p-2.5">Billing Period</th>
                <th className="p-2.5">Recurring Estimate</th>
                <th className="p-2.5">Status</th>
                <th className="p-2.5">Next Billing</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {subsData?.items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-4 text-center text-muted-foreground">
                    No subscriptions found for this customer.
                  </td>
                </tr>
              ) : (
                subsData?.items.map((sub) => (
                  <tr key={sub.id} className="hover:bg-muted/30">
                    <td className="p-2.5 font-mono font-medium">
                      <Link to={`/subscriptions/${sub.id}`} className="text-primary hover:underline">
                        {sub.subscription_number}
                      </Link>
                    </td>
                    <td className="p-2.5">{sub.plan_name}</td>
                    <td className="p-2.5 uppercase font-medium">{sub.billing_period}</td>
                    <td className="p-2.5">
                      <MoneyText paise={sub.recurring_total_paise} />
                    </td>
                    <td className="p-2.5">
                      <StatusBadge status={sub.status} />
                    </td>
                    <td className="p-2.5">{formatDate(sub.next_billing_date)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Linked Invoices Table */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
        <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
          <Receipt className="h-4 w-4 text-primary" /> Linked Invoices
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-border bg-muted/40 text-muted-foreground font-medium uppercase">
              <tr>
                <th className="p-2.5">Invoice #</th>
                <th className="p-2.5">Issue Date</th>
                <th className="p-2.5">Due Date</th>
                <th className="p-2.5">Total</th>
                <th className="p-2.5">Balance Due</th>
                <th className="p-2.5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {invsData?.items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-4 text-center text-muted-foreground">
                    No invoices recorded for this customer.
                  </td>
                </tr>
              ) : (
                invsData?.items.map((inv) => (
                  <tr key={inv.id} className="hover:bg-muted/30">
                    <td className="p-2.5 font-mono font-medium">
                      <Link to={`/invoices/${inv.id}`} className="text-primary hover:underline">
                        {inv.invoice_number}
                      </Link>
                    </td>
                    <td className="p-2.5">{formatDate(inv.issue_date)}</td>
                    <td className="p-2.5">{formatDate(inv.due_date)}</td>
                    <td className="p-2.5">
                      <MoneyText paise={inv.total_paise} />
                    </td>
                    <td className="p-2.5">
                      <MoneyText paise={inv.balance_due_paise} isOverdue={inv.balance_due_paise > 0} />
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
    </div>
  );
};
