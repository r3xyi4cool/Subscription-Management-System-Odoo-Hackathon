import React, { useState } from 'react';
import { usePlans } from '../../api/hooks';
import { catalogueApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { FormField } from '../../components/FormField';
import { Plan, BillingPeriod } from '../../api/types';
import { formatDate } from '../../lib/dates';
import { Plus, Check, X, ShoppingBag } from 'lucide-react';

export const PlansListPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('name');
  const [order, setOrder] = useState<'asc' | 'desc'>('asc');

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form states
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>('monthly');
  const [minQuantity, setMinQuantity] = useState(1);
  const [description, setDescription] = useState('');
  const [availableFrom, setAvailableFrom] = useState('');
  const [availableTo, setAvailableTo] = useState('');

  // 4 Plan Toggles
  const [autoClose, setAutoClose] = useState(false);
  const [allowEarlyClose, setAllowEarlyClose] = useState(true);
  const [allowPause, setAllowPause] = useState(true);
  const [allowRenewal, setAllowRenewal] = useState(true);

  const { data, isLoading, refetch } = usePlans({
    page,
    per_page: perPage,
    q: search,
    sort,
    order,
  });

  const handleOpenAdd = () => {
    setName('');
    setCode('');
    setBillingPeriod('monthly');
    setMinQuantity(1);
    setDescription('');
    setAvailableFrom('');
    setAvailableTo('');
    setAutoClose(false);
    setAllowEarlyClose(true);
    setAllowPause(true);
    setAllowRenewal(true);
    setFormError(null);
    setIsAddModalOpen(true);
  };

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !code) {
      setFormError('Plan name and code are required');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      await catalogueApi.createPlan({
        name,
        code: code.toUpperCase(),
        billing_period: billingPeriod,
        min_quantity: Number(minQuantity),
        description: description || null,
        available_from: availableFrom || null,
        available_to: availableTo || null,
        auto_close: autoClose,
        allow_early_close: allowEarlyClose,
        allow_pause: allowPause,
        allow_renewal: allowRenewal,
      });

      setIsAddModalOpen(false);
      refetch();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to create plan');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns: Column<Plan>[] = [
    {
      key: 'name',
      header: 'Plan Name / Code',
      sortable: true,
      render: (row) => (
        <div>
          <p className="font-semibold text-foreground">{row.name}</p>
          <p className="font-mono text-xs text-muted-foreground">{row.code}</p>
        </div>
      ),
    },
    {
      key: 'billing_period',
      header: 'Billing Period',
      sortable: true,
      render: (row) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider bg-primary/10 text-primary">
          {row.billing_period}
        </span>
      ),
    },
    {
      key: 'min_quantity',
      header: 'Min Qty',
      render: (row) => <span>{row.min_quantity} seat(s)</span>,
    },
    {
      key: 'toggles',
      header: 'Plan Feature Toggles',
      render: (row) => (
        <div className="flex flex-wrap gap-1.5 text-[10px]">
          <span
            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border font-medium ${
              row.allow_pause
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300'
                : 'bg-muted text-muted-foreground border-border'
            }`}
          >
            {row.allow_pause ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
            Pause
          </span>

          <span
            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border font-medium ${
              row.allow_early_close
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300'
                : 'bg-muted text-muted-foreground border-border'
            }`}
          >
            {row.allow_early_close ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
            Early Close
          </span>

          <span
            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border font-medium ${
              row.allow_renewal
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300'
                : 'bg-muted text-muted-foreground border-border'
            }`}
          >
            {row.allow_renewal ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
            Renewal
          </span>

          <span
            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border font-medium ${
              row.auto_close
                ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300'
                : 'bg-muted text-muted-foreground border-border'
            }`}
          >
            {row.auto_close ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
            Auto-Close
          </span>
        </div>
      ),
    },
    {
      key: 'availability',
      header: 'Availability Window',
      render: (row) => (
        <span className="text-xs text-muted-foreground">
          {row.available_from ? formatDate(row.available_from) : 'Immediate'} →{' '}
          {row.available_to ? formatDate(row.available_to) : 'Evergreen'}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Subscription Plans"
        description="Configure recurring billing frequencies, seat minimums, and customer self-service permissions"
        actions={
          <button
            onClick={handleOpenAdd}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-2 text-xs font-semibold text-primary-foreground shadow hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" /> Create Plan
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
        searchPlaceholder="Search plans by name, code..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        onSortChange={(k, ord) => {
          setSort(k);
          setOrder(ord);
        }}
        exportFilename="subscription_plans"
      />

      {/* Add Plan Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-semibold text-foreground mb-4">Create Subscription Plan</h3>

            {formError && (
              <p className="mb-4 rounded bg-destructive/10 p-2 text-xs text-destructive">{formError}</p>
            )}

            <form onSubmit={handleCreatePlan} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <FormField label="Plan Name" required id="plname">
                  <input
                    id="plname"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Professional Monthly"
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>

                <FormField label="Plan Code" required id="plcode">
                  <input
                    id="plcode"
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    placeholder="PRO_MONTHLY"
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <FormField label="Billing Period" required id="plperiod">
                  <select
                    id="plperiod"
                    value={billingPeriod}
                    onChange={(e) => setBillingPeriod(e.target.value as BillingPeriod)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </FormField>

                <FormField label="Minimum Quantity" required id="plminqty">
                  <input
                    id="plminqty"
                    type="number"
                    min="1"
                    value={minQuantity}
                    onChange={(e) => setMinQuantity(parseInt(e.target.value, 10) || 1)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <FormField label="Available From (Optional)" id="plfrom">
                  <input
                    id="plfrom"
                    type="date"
                    value={availableFrom}
                    onChange={(e) => setAvailableFrom(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>

                <FormField label="Available To (Optional)" id="plto">
                  <input
                    id="plto"
                    type="date"
                    value={availableTo}
                    onChange={(e) => setAvailableTo(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>
              </div>

              {/* 4 Plan Toggles Checklist */}
              <div className="border-t border-border pt-4 space-y-3">
                <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider">
                  Plan Rules & Customer Permissions (4 Spec Toggles)
                </h4>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <label className="flex items-center gap-2 p-2.5 rounded border border-border bg-muted/20 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={allowPause}
                      onChange={(e) => setAllowPause(e.target.checked)}
                      className="rounded border-input text-primary focus:ring-primary h-4 w-4"
                    />
                    <div>
                      <p className="font-semibold text-foreground">Allow Pause</p>
                      <p className="text-[10px] text-muted-foreground">Customers can pause subscription</p>
                    </div>
                  </label>

                  <label className="flex items-center gap-2 p-2.5 rounded border border-border bg-muted/20 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={allowEarlyClose}
                      onChange={(e) => setAllowEarlyClose(e.target.checked)}
                      className="rounded border-input text-primary focus:ring-primary h-4 w-4"
                    />
                    <div>
                      <p className="font-semibold text-foreground">Allow Early Close</p>
                      <p className="text-[10px] text-muted-foreground">Early cancellation permitted</p>
                    </div>
                  </label>

                  <label className="flex items-center gap-2 p-2.5 rounded border border-border bg-muted/20 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={allowRenewal}
                      onChange={(e) => setAllowRenewal(e.target.checked)}
                      className="rounded border-input text-primary focus:ring-primary h-4 w-4"
                    />
                    <div>
                      <p className="font-semibold text-foreground">Allow Renewal</p>
                      <p className="text-[10px] text-muted-foreground">Self-service renewal enabled</p>
                    </div>
                  </label>

                  <label className="flex items-center gap-2 p-2.5 rounded border border-border bg-muted/20 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autoClose}
                      onChange={(e) => setAutoClose(e.target.checked)}
                      className="rounded border-input text-primary focus:ring-primary h-4 w-4"
                    />
                    <div>
                      <p className="font-semibold text-foreground">Auto-Close</p>
                      <p className="text-[10px] text-muted-foreground">Closes on period completion</p>
                    </div>
                  </label>
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
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
                  {isSubmitting ? 'Saving...' : 'Create Plan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
