import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useSubscriptions, usePlans, useCustomers, useProducts } from '../../api/hooks';
import { subscriptionApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { StatusBadge } from '../../components/StatusBadge';
import { MoneyText } from '../../components/MoneyText';
import { FormField } from '../../components/FormField';
import { Subscription, SubscriptionStatus } from '../../api/types';
import { formatDate } from '../../lib/dates';
import { Plus, Layers, Filter } from 'lucide-react';

export const SubscriptionsListPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('created_at');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Create Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [customerId, setCustomerId] = useState('');
  const [planId, setPlanId] = useState('');
  const [productId, setProductId] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const queryParams: Record<string, string | number> = {
    page,
    per_page: perPage,
    sort,
    order,
  };
  if (search) queryParams.q = search;
  if (statusFilter) queryParams.status = statusFilter;

  const { data, isLoading, refetch } = useSubscriptions(queryParams);
  const { data: customersData } = useCustomers({ per_page: 100 });
  const { data: plansData } = usePlans({ per_page: 50 });
  const { data: productsData } = useProducts({ per_page: 50 });

  const handleOpenCreate = () => {
    setCustomerId(customersData?.items[0]?.id || '');
    setPlanId(plansData?.items[0]?.id || '');
    setProductId(productsData?.items[0]?.id || '');
    setQuantity(1);
    setErrorMsg(null);
    setIsCreateOpen(true);
  };

  const handleCreateSubscription = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerId || !planId || !productId) {
      setErrorMsg('Please select customer, plan, and product');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const prod = productsData?.items.find((p) => p.id === productId);
      const unitPrice = prod?.sales_price_paise || 250000;

      await subscriptionApi.create({
        customer_id: customerId,
        plan_id: planId,
        lines: [
          {
            id: `line_${Date.now()}`,
            subscription_id: '',
            product_id: productId,
            product_name: prod?.name,
            quantity,
            unit_price_paise: unitPrice,
            tax_rate_percent: 18,
            line_subtotal_paise: unitPrice * quantity,
            line_tax_paise: Math.round((unitPrice * quantity * 18) / 100),
            line_total_paise: unitPrice * quantity + Math.round((unitPrice * quantity * 18) / 100),
          },
        ],
      });

      setIsCreateOpen(false);
      refetch();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to create subscription');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns: Column<Subscription>[] = [
    {
      key: 'subscription_number',
      header: 'Subscription #',
      sortable: true,
      render: (row) => (
        <div>
          <Link
            to={`/subscriptions/${row.id}`}
            className="font-mono font-semibold text-primary hover:underline"
          >
            {row.subscription_number}
          </Link>
          <p className="text-xs text-muted-foreground">{row.customer_name}</p>
        </div>
      ),
    },
    {
      key: 'plan_name',
      header: 'Plan',
      render: (row) => <span>{row.plan_name}</span>,
    },
    {
      key: 'billing_period',
      header: 'Billing Frequency',
      render: (row) => (
        <span className="uppercase text-xs font-semibold text-muted-foreground">
          {row.billing_period}
        </span>
      ),
    },
    {
      key: 'recurring_total_paise',
      header: 'Cycle Amount (Est.)',
      sortable: true,
      render: (row) => <MoneyText paise={row.recurring_total_paise} className="font-semibold" />,
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: 'next_billing_date',
      header: 'Next Billing',
      sortable: true,
      render: (row) => <span>{formatDate(row.next_billing_date)}</span>,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Subscriptions"
        description="Monitor active contracts, recurring cycles, scheduled renewals, and status transitions"
        actions={
          <button
            onClick={handleOpenCreate}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-2 text-xs font-semibold text-primary-foreground shadow hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> New Subscription
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
        searchPlaceholder="Search subscriptions by number, customer..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        onSortChange={(k, ord) => {
          setSort(k);
          setOrder(ord);
        }}
        exportFilename="subscriptions"
        customFilterNode={
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-md border border-input bg-background px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="quotation">Quotation</option>
            <option value="confirmed">Confirmed</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="closed">Closed</option>
          </select>
        }
      />

      {/* Create Subscription Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-semibold text-foreground mb-4">Create New Subscription</h3>

            {errorMsg && (
              <p className="mb-4 rounded bg-destructive/10 p-2 text-xs text-destructive">{errorMsg}</p>
            )}

            <form onSubmit={handleCreateSubscription} className="space-y-4">
              <FormField label="Customer" required id="scust">
                <select
                  id="scust"
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                >
                  {customersData?.items.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.company_name ? `${c.company_name} (${c.name})` : c.name}
                    </option>
                  ))}
                </select>
              </FormField>

              <FormField label="Subscription Plan" required id="splan">
                <select
                  id="splan"
                  value={planId}
                  onChange={(e) => setPlanId(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                >
                  {plansData?.items.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.billing_period})
                    </option>
                  ))}
                </select>
              </FormField>

              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <FormField label="Base Product" required id="sprod">
                    <select
                      id="sprod"
                      value={productId}
                      onChange={(e) => setProductId(e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      required
                    >
                      {productsData?.items.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </FormField>
                </div>

                <FormField label="Quantity / Seats" required id="sqty">
                  <input
                    id="sqty"
                    type="number"
                    min="1"
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value, 10) || 1)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    required
                  />
                </FormField>
              </div>

              <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
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
                  {isSubmitting ? 'Creating...' : 'Create Subscription'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
