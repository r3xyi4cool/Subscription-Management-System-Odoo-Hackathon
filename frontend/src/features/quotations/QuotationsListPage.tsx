import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuotations, useCustomers, usePlans, useProducts } from '../../api/hooks';
import { quotationApi, subscriptionApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { FormField } from '../../components/FormField';
import { MoneyText } from '../../components/MoneyText';
import { Quotation } from '../../api/types';
import { formatDate, isDatePast } from '../../lib/dates';
import { Plus, FileText, CheckCircle2, Clock, AlertTriangle, ArrowRight } from 'lucide-react';

export const QuotationsListPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('created_at');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Form states
  const [customerId, setCustomerId] = useState('');
  const [planId, setPlanId] = useState('');
  const [validityDays, setValidityDays] = useState(15);
  const [notes, setNotes] = useState('');
  const [productId, setProductId] = useState('');
  const [quantity, setQuantity] = useState(1);

  const { data, isLoading, refetch } = useQuotations({
    page,
    per_page: perPage,
    q: search,
    sort,
    order,
  });

  const { data: customersData } = useCustomers({ per_page: 100 });
  const { data: plansData } = usePlans({ per_page: 50 });
  const { data: productsData } = useProducts({ per_page: 50 });

  const handleOpenCreate = () => {
    setCustomerId(customersData?.items[0]?.id || '');
    setPlanId(plansData?.items[0]?.id || '');
    setProductId(productsData?.items[0]?.id || '');
    setValidityDays(15);
    setQuantity(1);
    setNotes('');
    setFormError(null);
    setIsCreateModalOpen(true);
  };

  const handleCreateQuotation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerId || !planId || !productId) {
      setFormError('Please select customer, plan, and product');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      const prod = productsData?.items.find((p) => p.id === productId);
      const unitPrice = prod?.sales_price_paise || 250000;
      const subtotal = unitPrice * quantity;
      const tax = Math.round((subtotal * 18) / 100);
      const total = subtotal + tax;

      await quotationApi.create({
        customer_id: customerId,
        plan_id: planId,
        validity_days: Number(validityDays),
        subtotal_paise: subtotal,
        discount_total_paise: 0,
        tax_total_paise: tax,
        total_paise: total,
        items: [
          {
            id: `qline_${Date.now()}`,
            product_id: productId,
            product_name: prod?.name,
            quantity,
            unit_price_paise: unitPrice,
            discount_paise: 0,
            tax_rate_percent: 18,
            line_subtotal_paise: subtotal,
            line_tax_paise: tax,
            line_total_paise: total,
          },
        ],
        notes: notes || null,
      });

      setIsCreateModalOpen(false);
      refetch();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to create quotation');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConvertToSubscription = async (quotation: Quotation) => {
    if (isDatePast(quotation.valid_until)) {
      alert('Cannot confirm or convert an expired quotation (409 conflict).');
      return;
    }

    try {
      await subscriptionApi.create({
        customer_id: quotation.customer_id,
        plan_id: quotation.plan_id,
        quotation_id: quotation.id,
        lines: quotation.items.map((it) => ({
          id: `line_${Date.now()}`,
          subscription_id: '',
          product_id: it.product_id,
          product_name: it.product_name,
          quantity: it.quantity,
          unit_price_paise: it.unit_price_paise,
          tax_rate_percent: it.tax_rate_percent,
          line_subtotal_paise: it.line_subtotal_paise,
          line_tax_paise: it.line_tax_paise,
          line_total_paise: it.line_total_paise,
        })),
        notes: `Converted from quotation ${quotation.quotation_number}`,
      });
      alert('Successfully converted quotation to new Subscription!');
      refetch();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to convert quotation');
    }
  };

  const columns: Column<Quotation>[] = [
    {
      key: 'quotation_number',
      header: 'Quotation #',
      sortable: true,
      render: (row) => (
        <div>
          <span className="font-mono font-semibold text-primary">{row.quotation_number}</span>
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
      key: 'valid_until',
      header: 'Validity Date',
      sortable: true,
      render: (row) => {
        const expired = isDatePast(row.valid_until);
        return (
          <div className="flex items-center gap-1.5">
            <span className={expired ? 'text-destructive font-medium' : 'text-foreground'}>
              {formatDate(row.valid_until)}
            </span>
            {expired && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-destructive/10 text-destructive border border-destructive/20">
                EXPIRED
              </span>
            )}
          </div>
        );
      },
    },
    {
      key: 'total_paise',
      header: 'Estimated Total',
      sortable: true,
      render: (row) => <MoneyText paise={row.total_paise} className="font-semibold" />,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => {
        const expired = isDatePast(row.valid_until) && row.status !== 'converted';
        return (
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
              expired
                ? 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300'
                : row.status === 'converted'
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300'
                : 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300'
            }`}
          >
            {expired ? 'expired' : row.status}
          </span>
        );
      },
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => {
        const expired = isDatePast(row.valid_until);
        const canConvert = row.status !== 'converted' && !expired;

        return (
          <button
            onClick={() => handleConvertToSubscription(row)}
            disabled={!canConvert}
            className="inline-flex items-center gap-1 rounded border border-input bg-background px-2.5 py-1 text-xs font-medium hover:bg-muted transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            title={expired ? 'Expired quotations cannot be converted (409)' : 'Convert to Subscription'}
          >
            <CheckCircle2 className="h-3 w-3 text-emerald-600" />
            <span>Convert to Sub</span>
          </button>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Quotations"
        description="Issue sales proposals with configurable validity periods and convert accepted quotes to live subscriptions"
        actions={
          <div className="flex items-center gap-2">
            <Link
              to="/quotation-templates"
              className="inline-flex items-center gap-1.5 rounded-md border border-input bg-background px-3 py-2 text-xs font-medium hover:bg-muted"
            >
              Templates
            </Link>
            <button
              onClick={handleOpenCreate}
              className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-2 text-xs font-semibold text-primary-foreground shadow hover:bg-primary/90"
            >
              <Plus className="h-4 w-4" /> Create Quotation
            </button>
          </div>
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
        searchPlaceholder="Search quotations..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        exportFilename="quotations"
      />

      {/* Create Quotation Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-semibold text-foreground mb-4">Create Sales Quotation</h3>

            {formError && (
              <p className="mb-4 rounded bg-destructive/10 p-2 text-xs text-destructive">{formError}</p>
            )}

            <form onSubmit={handleCreateQuotation} className="space-y-4">
              <FormField label="Customer" required id="qcust">
                <select
                  id="qcust"
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

              <div className="grid grid-cols-2 gap-3">
                <FormField label="Subscription Plan" required id="qplan">
                  <select
                    id="qplan"
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

                <FormField label="Validity (Days)" required id="qdays">
                  <input
                    id="qdays"
                    type="number"
                    min="1"
                    max="90"
                    value={validityDays}
                    onChange={(e) => setValidityDays(parseInt(e.target.value, 10) || 15)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    required
                  />
                </FormField>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <FormField label="Product Line Item" required id="qprod">
                    <select
                      id="qprod"
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

                <FormField label="Quantity" required id="qqty">
                  <input
                    id="qqty"
                    type="number"
                    min="1"
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value, 10) || 1)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    required
                  />
                </FormField>
              </div>

              <FormField label="Notes / Commercial Terms" id="qnotes">
                <textarea
                  id="qnotes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Payment within 15 days of invoice generation..."
                  rows={2}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </FormField>

              <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
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
                  {isSubmitting ? 'Creating...' : 'Create Quotation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
