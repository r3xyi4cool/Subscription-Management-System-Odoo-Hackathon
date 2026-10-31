import React, { useState } from 'react';
import { useTaxes } from '../../api/hooks';
import { catalogueApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { FormField } from '../../components/FormField';
import { TaxRule } from '../../api/types';
import { Plus, Percent } from 'lucide-react';

export const TaxesListPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('rate_percent');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [ratePercent, setRatePercent] = useState('');
  const [description, setDescription] = useState('');

  const { data, isLoading, refetch } = useTaxes({
    page,
    per_page: perPage,
    q: search,
    sort,
    order,
  });

  const handleOpenAdd = () => {
    setName('');
    setCode('');
    setRatePercent('18');
    setDescription('');
    setFormError(null);
    setIsAddModalOpen(true);
  };

  const handleCreateTax = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !code || !ratePercent) {
      setFormError('Tax name, code, and rate percent are required');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      await catalogueApi.createTax({
        name,
        code: code.toUpperCase(),
        rate_percent: parseFloat(ratePercent),
        description: description || null,
      });
      setIsAddModalOpen(false);
      refetch();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to create tax rule');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns: Column<TaxRule>[] = [
    {
      key: 'name',
      header: 'Tax Rule Name',
      sortable: true,
      render: (row) => (
        <div>
          <p className="font-semibold text-foreground">{row.name}</p>
          <p className="font-mono text-xs text-muted-foreground">{row.code}</p>
        </div>
      ),
    },
    {
      key: 'rate_percent',
      header: 'Rate (%)',
      sortable: true,
      render: (row) => (
        <span className="font-mono font-bold text-sm text-foreground">
          {row.rate_percent}%
        </span>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      render: (row) => <span className="text-xs text-muted-foreground">{row.description || '—'}</span>,
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
        title="Tax Rules"
        description="Configure GST rules applied automatically to line items and invoices (staff cannot override)"
        actions={
          <button
            onClick={handleOpenAdd}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-2 text-xs font-semibold text-primary-foreground shadow hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" /> Add Tax Rule
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
        searchPlaceholder="Search taxes..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        exportFilename="tax_rules"
      />

      {/* Add Tax Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-xl">
            <h3 className="text-base font-semibold text-foreground mb-4">Add Tax Rule</h3>

            {formError && (
              <p className="mb-4 rounded bg-destructive/10 p-2 text-xs text-destructive">{formError}</p>
            )}

            <form onSubmit={handleCreateTax} className="space-y-4">
              <FormField label="Rule Name" required id="tname">
                <input
                  id="tname"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="GST 18%"
                  required
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </FormField>

              <div className="grid grid-cols-2 gap-3">
                <FormField label="Tax Code" required id="tcode">
                  <input
                    id="tcode"
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    placeholder="GST_18"
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>

                <FormField label="Rate Percent (%)" required id="trate">
                  <input
                    id="trate"
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    value={ratePercent}
                    onChange={(e) => setRatePercent(e.target.value)}
                    placeholder="18"
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>
              </div>

              <FormField label="Description" id="tdesc">
                <textarea
                  id="tdesc"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Applies to standard IT software licenses..."
                  rows={2}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </FormField>

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
                  {isSubmitting ? 'Saving...' : 'Create Tax Rule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
