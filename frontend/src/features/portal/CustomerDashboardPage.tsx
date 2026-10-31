import React from 'react';
import { Link } from 'react-router-dom';
import { usePortalDashboard } from '../../api/hooks';
import { PageHeader } from '../../components/PageHeader';
import { MoneyText } from '../../components/MoneyText';
import { StatusBadge } from '../../components/StatusBadge';
import { ErrorState } from '../../components/ErrorState';
import { formatDate } from '../../lib/dates';
import {
  Layers,
  Receipt,
  Calendar,
  CreditCard,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';

export const CustomerDashboardPage: React.FC = () => {
  const { data, isLoading, isError, refetch } = usePortalDashboard();

  if (isError) {
    return <ErrorState onRetry={() => refetch()} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Customer Workspace"
        description="Manage your active software licenses, upcoming renewal dates, and billing invoices"
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Active Subscriptions</span>
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Layers className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-3 text-2xl font-bold text-foreground">
            {isLoading ? '...' : data?.active_subscriptions_count ?? 0}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">Active subscription contracts</p>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Next Renewal Date</span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-600">
              <Calendar className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-3 text-lg font-bold text-foreground">
            {isLoading ? '...' : formatDate(data?.next_renewal_date)}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">Upcoming scheduled renewal</p>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Total Lifetime Spent</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600">
              <CreditCard className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <MoneyText paise={data?.total_spent_paise ?? 0} className="text-2xl font-bold text-foreground" />
          </div>
          <p className="mt-1 text-xs text-muted-foreground">Settled invoices and renewals</p>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Balance Due</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-600">
              <Receipt className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <MoneyText
              paise={data?.balance_due_paise ?? 0}
              isOverdue={(data?.balance_due_paise ?? 0) > 0}
              className="text-2xl font-bold"
            />
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {data?.pending_invoices_count ?? 0} pending payment
          </p>
        </div>
      </div>

      {/* Grid: Recent Subscriptions and Invoices */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Subscriptions */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
              <Layers className="h-4 w-4 text-primary" /> Active Plans
            </h3>
            <Link to="/portal/subscriptions" className="text-xs text-primary font-medium hover:underline">
              View All
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-border bg-muted/40 text-muted-foreground font-medium uppercase">
                <tr>
                  <th className="p-2.5">Subscription #</th>
                  <th className="p-2.5">Plan</th>
                  <th className="p-2.5">Status</th>
                  <th className="p-2.5">Next Renewal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data?.recent_subscriptions.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-4 text-center text-muted-foreground">
                      No subscriptions active.
                    </td>
                  </tr>
                ) : (
                  data?.recent_subscriptions.map((s) => (
                    <tr key={s.id} className="hover:bg-muted/30">
                      <td className="p-2.5 font-mono font-medium">
                        <Link to={`/portal/subscriptions`} className="text-primary hover:underline">
                          {s.subscription_number}
                        </Link>
                      </td>
                      <td className="p-2.5">{s.plan_name}</td>
                      <td className="p-2.5">
                        <StatusBadge status={s.status} />
                      </td>
                      <td className="p-2.5">{formatDate(s.next_billing_date)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Invoices */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
              <Receipt className="h-4 w-4 text-primary" /> Recent Invoices
            </h3>
            <Link to="/portal/invoices" className="text-xs text-primary font-medium hover:underline">
              View All
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-border bg-muted/40 text-muted-foreground font-medium uppercase">
                <tr>
                  <th className="p-2.5">Invoice #</th>
                  <th className="p-2.5">Due Date</th>
                  <th className="p-2.5">Amount</th>
                  <th className="p-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data?.recent_invoices.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-4 text-center text-muted-foreground">
                      No invoices found.
                    </td>
                  </tr>
                ) : (
                  data?.recent_invoices.map((inv) => (
                    <tr key={inv.id} className="hover:bg-muted/30">
                      <td className="p-2.5 font-mono font-medium">{inv.invoice_number}</td>
                      <td className="p-2.5">{formatDate(inv.due_date)}</td>
                      <td className="p-2.5 font-mono">
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
      </div>
    </div>
  );
};
