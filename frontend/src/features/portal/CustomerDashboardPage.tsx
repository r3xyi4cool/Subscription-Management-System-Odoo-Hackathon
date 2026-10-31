import React from 'react';
import { Link } from 'react-router-dom';
import { usePortalDashboard, useInvalidateQueries } from '../../api/hooks';
import { portalApi } from '../../api/endpoints';
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
  AlertTriangle,
  Bell,
  CheckCheck,
  ExternalLink,
  Info,
} from 'lucide-react';

export const CustomerDashboardPage: React.FC = () => {
  const { data, isLoading, isError, refetch } = usePortalDashboard();
  const { invalidateNotifications } = useInvalidateQueries();

  if (isError) {
    return <ErrorState onRetry={() => refetch()} />;
  }

  const hasPendingPayment = (data?.balance_due_paise ?? 0) > 0;
  const pendingCount = data?.pending_invoices_count ?? 0;
  const notifications = data?.recent_notifications ?? [];
  const unreadNotifCount = data?.unread_notifications_count ?? 0;

  const handleMarkAllRead = async () => {
    try {
      await portalApi.markAllNotificationsRead();
      invalidateNotifications();
      refetch();
    } catch {
      // ignore
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Customer Workspace"
        description="Manage your active software licenses, upcoming renewal dates, and billing invoices"
      />

      {/* Pending Payment Alert Banner */}
      {hasPendingPayment && (
        <div className="rounded-xl border border-amber-300 bg-amber-500/10 p-4 text-amber-900 dark:text-amber-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/20 text-amber-600 dark:text-amber-400 shrink-0">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <p className="font-bold text-sm">
                Outstanding Balance Due
              </p>
              <p className="text-xs text-amber-800/80 dark:text-amber-300/80 mt-0.5">
                You have <MoneyText paise={data?.balance_due_paise ?? 0} className="font-bold inline" /> pending across {pendingCount} invoice{pendingCount === 1 ? '' : 's'}.
              </p>
            </div>
          </div>
          <Link
            to="/portal/invoices"
            className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 px-4 py-2 text-xs font-semibold text-white shadow-sm transition-colors shrink-0"
          >
            <span>Review & Pay Now</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground font-medium">Active Subscriptions</span>
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <Layers className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-3 text-2xl font-bold text-foreground">
            {isLoading ? '...' : data?.active_subscriptions_count ?? 0}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">Active recurring subscriptions</p>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground font-medium">Next Renewal Date</span>
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
            <span className="text-xs text-muted-foreground font-medium">Total Lifetime Spent</span>
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
            <span className="text-xs text-muted-foreground font-medium">Balance Due</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-600">
              <Receipt className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <MoneyText
              paise={data?.balance_due_paise ?? 0}
              isOverdue={hasPendingPayment}
              className="text-2xl font-bold"
            />
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {pendingCount} invoice{pendingCount === 1 ? '' : 's'} pending payment
          </p>
        </div>
      </div>

      {/* Messages / Notifications Section */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
              <Bell className="h-4 w-4" />
            </div>
            <h3 className="text-base font-semibold text-foreground">Messages & Notifications</h3>
            {unreadNotifCount > 0 && (
              <span className="rounded-full bg-primary/15 px-2 py-0.5 text-xs font-bold text-primary">
                {unreadNotifCount} new
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {unreadNotifCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-primary font-medium hover:underline flex items-center gap-1"
              >
                <CheckCheck className="h-3.5 w-3.5" />
                <span>Mark all as read</span>
              </button>
            )}
            <Link to="/portal/notifications" className="text-xs text-primary font-semibold hover:underline">
              View All
            </Link>
          </div>
        </div>

        {notifications.length === 0 ? (
          <div className="py-6 text-center text-xs text-muted-foreground">
            No recent messages or notifications.
          </div>
        ) : (
          <div className="divide-y divide-border">
            {notifications.map((n) => (
              <div
                key={n.id}
                className={`py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${
                  !n.is_read ? 'bg-primary/5 px-3 rounded-lg -mx-3' : ''
                }`}
              >
                <div className="flex items-start gap-2.5 min-w-0">
                  <div className="mt-0.5 shrink-0">
                    <Info className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className={`text-xs ${!n.is_read ? 'font-bold text-foreground' : 'font-medium text-foreground/80'}`}>
                        {n.title}
                      </p>
                      <span className="text-[10px] text-muted-foreground">• {formatDate(n.created_at)}</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">{n.message}</p>
                  </div>
                </div>

                {n.link_url && (
                  <Link
                    to={n.link_url.startsWith('/me/invoices') ? '/portal/invoices' : n.link_url.startsWith('/me/subscriptions') ? '/portal/subscriptions' : n.link_url}
                    className="inline-flex items-center gap-1 text-xs text-primary font-medium hover:underline shrink-0 sm:self-center"
                  >
                    <span>View</span>
                    <ExternalLink className="h-3 w-3" />
                  </Link>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Grid: Recent Subscriptions and Invoices */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Subscriptions */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
              <Layers className="h-4 w-4 text-primary" /> Active Plans
            </h3>
            <Link to="/portal/subscriptions" className="text-xs text-primary font-semibold hover:underline">
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
            <Link to="/portal/invoices" className="text-xs text-primary font-semibold hover:underline">
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
