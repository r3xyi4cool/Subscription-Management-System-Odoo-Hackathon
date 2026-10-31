import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useDashboardSummary, usePlans, useCustomers } from '../../api/hooks';
import { PageHeader } from '../../components/PageHeader';
import { MoneyText } from '../../components/MoneyText';
import { ErrorState } from '../../components/ErrorState';
import { formatMoney } from '../../lib/money';
import {
  TrendingUp,
  CreditCard,
  AlertTriangle,
  Users,
  Repeat,
  DollarSign,
  Activity,
  ArrowRight,
  Filter,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
} from 'recharts';

export const DashboardPage: React.FC = () => {
  const [selectedPlanId, setSelectedPlanId] = useState<string>('');
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>('');

  const { data: plansData } = usePlans({ per_page: 100 });
  const { data: customersData } = useCustomers({ per_page: 100 });

  const queryParams: Record<string, string> = {};
  if (selectedPlanId) queryParams.plan_id = selectedPlanId;
  if (selectedCustomerId) queryParams.customer_id = selectedCustomerId;

  const {
    data: summary,
    isLoading,
    isError,
    refetch,
  } = useDashboardSummary(queryParams);

  if (isError) {
    return <ErrorState onRetry={() => refetch()} />;
  }

  const kpis = [
    {
      title: 'Monthly Recurring Revenue (MRR)',
      paise: summary?.mrr_paise ?? 0,
      icon: TrendingUp,
      accent: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-950/40',
      sub: `ARR: ${formatMoney(summary?.arr_paise ?? 0)}`,
    },
    {
      title: 'Net Revenue Collected',
      paise: summary?.revenue_collected_paise ?? 0,
      icon: DollarSign,
      accent: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-50 dark:bg-blue-950/40',
      sub: `${summary?.payments_received_count ?? 0} payments settled`,
    },
    {
      title: 'Outstanding Balance Owed',
      paise: summary?.amount_owed_paise ?? 0,
      icon: CreditCard,
      accent: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-50 dark:bg-amber-950/40',
      sub: `Collection Rate: ${summary?.collection_rate_percent ?? 0}%`,
    },
    {
      title: 'Overdue Invoices',
      paise: summary?.overdue_amount_paise ?? 0,
      icon: AlertTriangle,
      accent: 'text-rose-600 dark:text-rose-400',
      bg: 'bg-rose-50 dark:bg-rose-950/40',
      sub: `${summary?.overdue_invoices_count ?? 0} overdue invoices`,
      isOverdue: true,
      link: '/invoices/outstanding',
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Operational Dashboard"
        description="Real-time subscriptions, revenue telemetry, and billing health"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5 rounded-lg border border-input bg-card px-3 py-1.5 text-xs text-muted-foreground">
              <Filter className="h-3.5 w-3.5" />
              <span>Filters:</span>
              <select
                value={selectedPlanId}
                onChange={(e) => setSelectedPlanId(e.target.value)}
                className="bg-transparent font-medium text-foreground focus:outline-none"
              >
                <option value="">All Plans</option>
                {plansData?.items.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
              <select
                value={selectedCustomerId}
                onChange={(e) => setSelectedCustomerId(e.target.value)}
                className="bg-transparent font-medium text-foreground focus:outline-none ml-2"
              >
                <option value="">All Customers</option>
                {customersData?.items.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.company_name || c.name}
                  </option>
                ))}
              </select>
            </div>
            <Link
              to="/billing-run"
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground shadow hover:bg-primary/90 transition-colors"
            >
              Trigger Billing Run
            </Link>
          </div>
        }
      />

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => (
          <div
            key={idx}
            className="rounded-xl border border-border bg-card p-5 shadow-sm hover:shadow transition-shadow relative overflow-hidden"
          >
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-muted-foreground">{kpi.title}</p>
              <div className={`p-2 rounded-lg ${kpi.bg}`}>
                <kpi.icon className={`h-4 w-4 ${kpi.accent}`} />
              </div>
            </div>

            <div className="mt-3">
              {isLoading ? (
                <div className="h-7 w-28 bg-muted animate-pulse rounded" />
              ) : (
                <MoneyText
                  paise={kpi.paise}
                  isOverdue={kpi.isOverdue}
                  className="text-2xl font-bold tracking-tight"
                />
              )}
            </div>

            <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
              <span>{kpi.sub}</span>
              {kpi.link && (
                <Link
                  to={kpi.link}
                  className="inline-flex items-center gap-1 text-primary hover:underline font-medium"
                >
                  View <ArrowRight className="h-3 w-3" />
                </Link>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Secondary Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 rounded-xl border border-border bg-card p-4 shadow-sm text-center">
        <div>
          <p className="text-xs text-muted-foreground">Active Subscriptions</p>
          <p className="text-xl font-bold text-foreground mt-1">
            {isLoading ? '...' : summary?.active_subscriptions ?? 0}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Annual Run Rate (ARR)</p>
          <p className="text-xl font-bold text-foreground mt-1 font-mono">
            {isLoading ? '...' : formatMoney(summary?.arr_paise ?? 0)}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Collection Rate</p>
          <p className="text-xl font-bold text-foreground mt-1">
            {isLoading ? '...' : `${summary?.collection_rate_percent ?? 0}%`}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Churn Rate</p>
          <p className="text-xl font-bold text-foreground mt-1">
            {isLoading ? '...' : `${summary?.churn_rate_percent ?? 0}%`}
          </p>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Trend Area Chart */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-foreground">Revenue & Invoicing Trend</h3>
              <p className="text-xs text-muted-foreground">Past 6 months collected vs invoiced</p>
            </div>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={summary?.revenue_trend || []}>
                <defs>
                  <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="invoicedGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis
                  tickFormatter={(val) => `₹${val / 100000}k`}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip
                  formatter={(val: number) => [formatMoney(val), '']}
                  labelFormatter={(lbl) => `Period: ${lbl}`}
                  contentStyle={{ backgroundColor: 'var(--card)', borderRadius: '8px', border: '1px solid var(--border)' }}
                />
                <Area
                  type="monotone"
                  dataKey="invoiced_paise"
                  name="Invoiced"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#invoicedGrad)"
                />
                <Area
                  type="monotone"
                  dataKey="revenue_paise"
                  name="Collected"
                  stroke="#10b981"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#revenueGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Subscription Distribution Bar Chart */}
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-foreground">Subscriptions by Status</h3>
              <p className="text-xs text-muted-foreground">Current distribution across lifecycle states</p>
            </div>
            <Repeat className="h-4 w-4 text-muted-foreground" />
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={summary?.subscription_distribution || []}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(val: number) => [`${val} subscriptions`, 'Count']}
                  contentStyle={{ backgroundColor: 'var(--card)', borderRadius: '8px', border: '1px solid var(--border)' }}
                />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
