import React, { useState } from 'react';
import { useDiscounts } from '../../api/hooks';
import { catalogueApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { FormField } from '../../components/FormField';
import { DiscountRule, DiscountType, DiscountScope } from '../../api/types';
import { formatMoney, rupeesToPaise } from '../../lib/money';
import { formatDate } from '../../lib/dates';
import { Plus, Percent, Tag } from 'lucide-react';

export const DiscountsListPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('code');
  const [order, setOrder] = useState<'asc' | 'desc'>('asc');

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [discountType, setDiscountType] = useState<DiscountType>('percent');
  const [discountValue, setDiscountValue] = useState('');
  const [scope, setScope] = useState<DiscountScope>('subscription');
  const [minQuantity, setMinQuantity] = useState('');
  const [minAmountRupees, setMinAmountRupees] = useState('');
  const [validFrom, setValidFrom] = useState('');
  const [validTo, setValidTo] = useState('');
  const [usageLimit, setUsageLimit] = useState('');

  const { data, isLoading, refetch } = useDiscounts({
    page,
    per_page: perPage,
    q: search,
    sort,
    order,
  });

  const handleOpenAdd = () => {
    setCode('');
    setName('');
    setDiscountType('percent');
    setDiscountValue('10');
    setScope('subscription');
    setMinQuantity('');
    setMinAmountRupees('');
    setValidFrom('');
    setValidTo('');
    setUsageLimit('');
    setFormError(null);
    setIsAddModalOpen(true);
  };

  const handleCreateDiscount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code || !name || !discountValue) {
      setFormError('Code, name, and value are required');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      const valNum =
        discountType === 'percent'
          ? parseFloat(discountValue)
          : rupeesToPaise(discountValue);

      await catalogueApi.createDiscount({
        code: code.toUpperCase(),
        name,
        discount_type: discountType,
        discount_value: valNum,
        scope,
        min_quantity: minQuantity ? parseInt(minQuantity, 10) : undefined,
        min_amount_paise: minAmountRupees ? rupeesToPaise(minAmountRupees) : undefined,
        valid_from: validFrom || null,
        valid_to: validTo || null,
        usage_limit: usageLimit ? parseInt(usageLimit, 10) : null,
      });

      setIsAddModalOpen(false);
      refetch();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to create discount rule');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns: Column<DiscountRule>[] = [
    {
      key: 'code',
      header: 'Discount Code',
      sortable: true,
      render: (row) => (
        <div>
          <span className="font-mono font-bold text-xs uppercase px-2 py-0.5 rounded bg-muted border border-border">
            {row.code}
          </span>
          <p className="text-xs text-foreground font-medium mt-1">{row.name}</p>
        </div>
      ),
    },
    {
      key: 'discount_value',
      header: 'Value / Benefit',
      render: (row) => (
        <span className="font-semibold text-emerald-600 font-mono text-sm">
          {row.discount_type === 'percent'
            ? `${row.discount_value}% off`
            : `${formatMoney(row.discount_value)} off`}
        </span>
      ),
    },
    {
      key: 'scope',
      header: 'Scope',
      render: (row) => <span className="uppercase text-xs font-medium text-muted-foreground">{row.scope}</span>,
    },
    {
      key: 'times_used',
      header: 'Usage / Cap',
      render: (row) => (
        <span className="text-xs font-mono">
          {row.times_used} / {row.usage_limit ? row.usage_limit : '∞'}
        </span>
      ),
    },
    {
      key: 'validity',
      header: 'Validity Period',
      render: (row) => (
        <span className="text-xs text-muted-foreground">
          {row.valid_from ? formatDate(row.valid_from) : 'Immediate'} →{' '}
          {row.valid_to ? formatDate(row.valid_to) : 'Permanent'}
        </span>
      ),
    },
    {
      key: 'is_active',
      header: 'Status',
      render: (row) => (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
            row.is_active
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300'
              : 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300'
          }`}
        >
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Discount Rules"
        description="Manage promotional codes, seat-volume discounts, and contract concessions with usage limits"
        actions={
          <button
            onClick={handleOpenAdd}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-2 text-xs font-semibold text-primary-foreground shadow hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" /> Add Discount Rule
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
        searchPlaceholder="Search discount rules..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        exportFilename="discount_rules"
      />

      {/* Add Discount Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-semibold text-foreground mb-4">Create Discount Rule</h3>

            {formError && (
              <p className="mb-4 rounded bg-destructive/10 p-2 text-xs text-destructive">{formError}</p>
            )}

            <form onSubmit={handleCreateDiscount} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <FormField label="Discount Code" required id="dcode">
                  <input
                    id="dcode"
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    placeholder="VOLUME10"
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary font-mono uppercase"
                  />
                </FormField>

                <FormField label="Rule Name" required id="dname">
                  <input
                    id="dname"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="10% Volume Discount"
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <FormField label="Discount Type" required id="dtype">
                  <select
                    id="dtype"
                    value={discountType}
                    onChange={(e) => setDiscountType(e.target.value as DiscountType)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="percent">Percentage (%)</option>
                    <option value="fixed">Fixed (₹)</option>
                  </select>
                </FormField>

                <FormField label={discountType === 'percent' ? 'Percent (%)' : 'Amount (₹)'} required id="dval">
                  <input
                    id="dval"
                    type="number"
                    step={discountType === 'percent' ? '0.1' : '1'}
                    min="0"
                    value={discountValue}
                    onChange={(e) => setDiscountValue(e.target.value)}
                    placeholder={discountType === 'percent' ? '10' : '500'}
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>

                <FormField label="Scope" required id="dscope">
                  <select
                    id="dscope"
                    value={scope}
                    onChange={(e) => setScope(e.target.value as DiscountScope)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="subscription">Subscription</option>
                    <option value="line">Line Item</option>
                    <option value="product">Product</option>
                  </select>
                </FormField>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <FormField label="Min Order Amount (₹)" id="dminamt">
                  <input
                    id="dminamt"
                    type="number"
                    min="0"
                    value={minAmountRupees}
                    onChange={(e) => setMinAmountRupees(e.target.value)}
                    placeholder="e.g. 5000"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>

                <FormField label="Min Quantity" id="dminqty">
                  <input
                    id="dminqty"
                    type="number"
                    min="1"
                    value={minQuantity}
                    onChange={(e) => setMinQuantity(e.target.value)}
                    placeholder="e.g. 10"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <FormField label="Valid From" id="dfrom">
                  <input
                    id="dfrom"
                    type="date"
                    value={validFrom}
                    onChange={(e) => setValidFrom(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>

                <FormField label="Valid To" id="dto">
                  <input
                    id="dto"
                    type="date"
                    value={validTo}
                    onChange={(e) => setValidTo(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>

                <FormField label="Usage Cap" id="dlimit">
                  <input
                    id="dlimit"
                    type="number"
                    min="1"
                    value={usageLimit}
                    onChange={(e) => setUsageLimit(e.target.value)}
                    placeholder="∞"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>
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
                  {isSubmitting ? 'Saving...' : 'Create Discount Rule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
