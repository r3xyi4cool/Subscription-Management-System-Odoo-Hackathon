import React, { useState } from 'react';
import { useProducts, useTaxes } from '../../api/hooks';
import { catalogueApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { FormField } from '../../components/FormField';
import { MoneyText } from '../../components/MoneyText';
import { Product, ProductVariant } from '../../api/types';
import { formatMoney, rupeesToPaise, paiseToRupees } from '../../lib/money';
import { Plus, Package, Layers, Trash2 } from 'lucide-react';

export const ProductsListPage: React.FC = () => {
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
  const [sku, setSku] = useState('');
  const [type, setType] = useState<'software' | 'service' | 'add_on'>('software');
  const [salesPriceRupees, setSalesPriceRupees] = useState('');
  const [taxRuleId, setTaxRuleId] = useState('tax_18');
  const [description, setDescription] = useState('');

  // Variants list in form
  const [variants, setVariants] = useState<Array<{ name: string; sku: string; extraPriceRupees: string }>>([]);

  const { data, isLoading, refetch } = useProducts({
    page,
    per_page: perPage,
    q: search,
    sort,
    order,
  });

  const { data: taxesData } = useTaxes({ per_page: 50 });

  const handleOpenAdd = () => {
    setName('');
    setSku('');
    setType('software');
    setSalesPriceRupees('');
    setTaxRuleId('tax_18');
    setDescription('');
    setVariants([]);
    setFormError(null);
    setIsAddModalOpen(true);
  };

  const handleAddVariantRow = () => {
    setVariants([...variants, { name: '', sku: '', extraPriceRupees: '0' }]);
  };

  const handleRemoveVariantRow = (index: number) => {
    setVariants(variants.filter((_, i) => i !== index));
  };

  const handleVariantChange = (index: number, field: string, value: string) => {
    const updated = [...variants];
    updated[index] = { ...updated[index], [field]: value };
    setVariants(updated);
  };

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !sku || !salesPriceRupees) {
      setFormError('Name, SKU, and base price are required');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      const basePricePaise = rupeesToPaise(salesPriceRupees);
      const parsedVariants: ProductVariant[] = variants.map((v, idx) => ({
        id: `var_${Date.now()}_${idx}`,
        product_id: '',
        name: v.name || `Variant ${idx + 1}`,
        sku: v.sku || `${sku}-V${idx + 1}`,
        extra_price_paise: rupeesToPaise(v.extraPriceRupees || '0'),
        is_active: true,
        created_at: new Date().toISOString(),
      }));

      await catalogueApi.createProduct({
        name,
        sku: sku.toUpperCase(),
        type,
        sales_price_paise: basePricePaise,
        tax_rule_id: taxRuleId,
        description: description || null,
        variants: parsedVariants,
      });

      setIsAddModalOpen(false);
      refetch();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to create product');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns: Column<Product>[] = [
    {
      key: 'name',
      header: 'Product Name',
      sortable: true,
      render: (row) => (
        <div>
          <p className="font-semibold text-foreground">{row.name}</p>
          <p className="font-mono text-[11px] text-muted-foreground">{row.sku}</p>
        </div>
      ),
    },
    {
      key: 'type',
      header: 'Category',
      sortable: true,
      render: (row) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium uppercase tracking-wider bg-muted text-foreground border border-border">
          {row.type}
        </span>
      ),
    },
    {
      key: 'sales_price_paise',
      header: 'Base Sales Price',
      sortable: true,
      render: (row) => <MoneyText paise={row.sales_price_paise} className="font-semibold" />,
    },
    {
      key: 'variants',
      header: 'Variants & Extra Pricing',
      render: (row) => (
        <div className="space-y-1">
          {row.variants && row.variants.length > 0 ? (
            row.variants.map((v) => (
              <div key={v.id} className="text-xs flex items-center gap-1.5">
                <span className="font-medium text-foreground">{v.name}:</span>
                <span className="font-mono text-muted-foreground">
                  +{formatMoney(v.extra_price_paise)}
                </span>
                <span className="text-[11px] text-primary">
                  (= {formatMoney(row.sales_price_paise + v.extra_price_paise)})
                </span>
              </div>
            ))
          ) : (
            <span className="text-muted-foreground text-xs">No variants (Standard base only)</span>
          )}
        </div>
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
        title="Products & Variants"
        description="Catalogue of service products, software licenses, add-ons, and pricing tier variants"
        actions={
          <button
            onClick={handleOpenAdd}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-2 text-xs font-semibold text-primary-foreground shadow hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" /> Add Product
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
        searchPlaceholder="Search products by title, sku..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        onSortChange={(k, ord) => {
          setSort(k);
          setOrder(ord);
        }}
        exportFilename="products_catalogue"
      />

      {/* Add Product Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-semibold text-foreground mb-4">Add Catalogue Product</h3>

            {formError && (
              <p className="mb-4 rounded bg-destructive/10 p-2 text-xs text-destructive">{formError}</p>
            )}

            <form onSubmit={handleCreateProduct} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <FormField label="Product Name" required id="pname">
                  <input
                    id="pname"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Cloud Core Platform"
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>

                <FormField label="SKU Code" required id="psku">
                  <input
                    id="psku"
                    type="text"
                    value={sku}
                    onChange={(e) => setSku(e.target.value)}
                    placeholder="PRD-CORE-001"
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <FormField label="Type" required id="ptype">
                  <select
                    id="ptype"
                    value={type}
                    onChange={(e) => setType(e.target.value as 'software' | 'service' | 'add_on')}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="software">Software</option>
                    <option value="service">Service</option>
                    <option value="add_on">Add-on</option>
                  </select>
                </FormField>

                <FormField label="Base Price (₹)" required id="pprice">
                  <input
                    id="pprice"
                    type="number"
                    step="0.01"
                    min="0"
                    value={salesPriceRupees}
                    onChange={(e) => setSalesPriceRupees(e.target.value)}
                    placeholder="2500.00"
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>

                <FormField label="Tax Rule" required id="ptax">
                  <select
                    id="ptax"
                    value={taxRuleId}
                    onChange={(e) => setTaxRuleId(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    {taxesData?.items.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name} ({t.rate_percent}%)
                      </option>
                    ))}
                  </select>
                </FormField>
              </div>

              <FormField label="Description" id="pdesc">
                <textarea
                  id="pdesc"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Product description and billing notes..."
                  rows={2}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </FormField>

              {/* Product Variants Section */}
              <div className="border-t border-border pt-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider">
                      Product Variants & Extra Price
                    </h4>
                    <p className="text-[11px] text-muted-foreground">
                      Final unit price = Sales Price + Variant Extra Price
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleAddVariantRow}
                    className="inline-flex items-center gap-1 rounded border border-input bg-background px-2.5 py-1 text-xs font-medium hover:bg-muted"
                  >
                    <Plus className="h-3 w-3" /> Add Variant
                  </button>
                </div>

                {variants.map((v, idx) => (
                  <div key={idx} className="flex items-center gap-2 bg-muted/20 p-2 rounded-lg border border-border">
                    <input
                      type="text"
                      placeholder="Variant Name (e.g. Odoo ERP)"
                      value={v.name}
                      onChange={(e) => handleVariantChange(idx, 'name', e.target.value)}
                      className="flex-1 rounded border border-input bg-background px-2 py-1 text-xs"
                      required
                    />
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="Extra (₹)"
                      value={v.extraPriceRupees}
                      onChange={(e) => handleVariantChange(idx, 'extraPriceRupees', e.target.value)}
                      className="w-24 rounded border border-input bg-background px-2 py-1 text-xs"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveVariantRow(idx)}
                      className="p-1 text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
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
                  {isSubmitting ? 'Saving...' : 'Create Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
