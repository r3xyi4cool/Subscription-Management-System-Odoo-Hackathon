import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { invoiceApi } from '../../api/endpoints';
import { useInvalidateQueries } from '../../api/hooks';
import { PageHeader } from '../../components/PageHeader';
import { MoneyText } from '../../components/MoneyText';
import { BillingRunResult } from '../../api/types';
import { formatDateTime } from '../../lib/dates';
import {
  Zap,
  CheckCircle,
  AlertTriangle,
  RotateCcw,
  Receipt,
  Layers,
  ArrowRight,
  Info,
} from 'lucide-react';

export const BillingRunPage: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<BillingRunResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { invalidateInvoices, invalidateSubscriptions } = useInvalidateQueries();

  const handleExecuteBilling = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const res = await invoiceApi.runBilling();
      setResult(res);
      invalidateInvoices();
      invalidateSubscriptions();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Billing job failed');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Billing Run Cycle"
        description="Automated recurring billing processor for active subscriptions"
        breadcrumbs={[
          { label: 'Invoices', href: '/invoices' },
          { label: 'Billing Run' },
        ]}
      />

      {/* Trigger Card */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
              <Zap className="h-5 w-5 text-amber-500 fill-amber-500/20" />
              <span>Execute Recurring Invoicing Job</span>
            </h3>
            <p className="text-xs text-muted-foreground max-w-xl">
              Inspects all Active subscriptions with scheduled billing dates on or before today, generates draft invoices, applies eligible discounts, adds GST tax rules, and advances billing periods atomically.
            </p>
          </div>

          <button
            onClick={handleExecuteBilling}
            disabled={isRunning}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-md hover:bg-primary/90 transition-all disabled:opacity-50 shrink-0"
          >
            {isRunning ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                <span>Processing Billing Job...</span>
              </>
            ) : (
              <>
                <Zap className="h-4 w-4" />
                <span>Run Billing Now</span>
              </>
            )}
          </button>
        </div>

        <div className="mt-4 rounded-lg border border-border bg-muted/20 p-3 text-xs text-muted-foreground flex items-center gap-2">
          <Info className="h-4 w-4 text-primary shrink-0" />
          <span>
            <strong>Idempotency Guarantee:</strong> Multiple runs on the same date will safely skip already-invoiced cycles without creating duplicate invoices.
          </span>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-xs text-destructive flex items-center justify-between">
          <span>{error}</span>
          <button
            onClick={handleExecuteBilling}
            className="inline-flex items-center gap-1 font-semibold hover:underline"
          >
            <RotateCcw className="h-3.5 w-3.5" /> Retry Run
          </button>
        </div>
      )}

      {/* Execution Report */}
      {result && (
        <div className="space-y-6 animate-in fade-in">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-foreground">Billing Execution Report</h3>
            <span className="text-xs text-muted-foreground">
              Run Completed: {formatDateTime(result.run_at)}
            </span>
          </div>

          {/* Counts Overview */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-4">
              <span className="text-xs font-medium text-emerald-700 dark:text-emerald-300">
                Invoices Created
              </span>
              <p className="mt-1 text-2xl font-bold text-emerald-600">
                {result.created_count}
              </p>
              <p className="mt-0.5 text-[11px] text-muted-foreground">Successfully generated</p>
            </div>

            <div className="rounded-xl border border-blue-500/30 bg-blue-500/5 p-4">
              <span className="text-xs font-medium text-blue-700 dark:text-blue-300">
                Subscriptions Skipped
              </span>
              <p className="mt-1 text-2xl font-bold text-blue-600">
                {result.skipped_count}
              </p>
              <p className="mt-0.5 text-[11px] text-muted-foreground">Not due or duplicate period</p>
            </div>

            <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4">
              <span className="text-xs font-medium text-destructive">
                Failures Encountered
              </span>
              <p className="mt-1 text-2xl font-bold text-destructive">
                {result.failed_count}
              </p>
              <p className="mt-0.5 text-[11px] text-muted-foreground">Required investigation</p>
            </div>
          </div>

          {/* Created Invoices Section */}
          {result.created.length > 0 && (
            <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
              <h4 className="text-sm font-semibold text-emerald-600 flex items-center gap-1.5">
                <CheckCircle className="h-4 w-4" /> Generated Invoices ({result.created.length})
              </h4>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-border bg-muted/40 text-muted-foreground uppercase font-medium">
                    <tr>
                      <th className="p-2.5">Invoice #</th>
                      <th className="p-2.5">Subscription #</th>
                      <th className="p-2.5 text-right">Invoiced Amount</th>
                      <th className="p-2.5 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {result.created.map((c, idx) => (
                      <tr key={idx} className="hover:bg-muted/30">
                        <td className="p-2.5 font-mono font-semibold text-foreground">
                          {c.invoice_number}
                        </td>
                        <td className="p-2.5 font-mono text-muted-foreground">
                          {c.subscription_number}
                        </td>
                        <td className="p-2.5 text-right font-mono font-bold text-foreground">
                          <MoneyText paise={c.amount_paise} />
                        </td>
                        <td className="p-2.5 text-right">
                          <Link
                            to={`/invoices/${c.invoice_id}`}
                            className="inline-flex items-center gap-1 text-xs text-primary font-medium hover:underline"
                          >
                            View Invoice <ArrowRight className="h-3 w-3" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Skipped Invoices Section */}
          {result.skipped.length > 0 && (
            <div className="rounded-xl border border-border bg-card p-5 shadow-sm space-y-3">
              <h4 className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                <Info className="h-4 w-4 text-blue-500" /> Skipped Subscriptions ({result.skipped.length})
              </h4>

              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {result.skipped.map((s, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-xs p-2 rounded bg-muted/30 border border-border"
                  >
                    <span className="font-mono font-medium text-foreground">{s.subscription_number}</span>
                    <span className="text-muted-foreground">{s.reason}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Failures Section */}
          {result.failed.length > 0 && (
            <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-destructive flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4" /> Failures ({result.failed.length})
                </h4>
                <button
                  onClick={handleExecuteBilling}
                  className="inline-flex items-center gap-1 rounded bg-destructive/10 px-2 py-1 text-xs font-semibold text-destructive hover:bg-destructive/20"
                >
                  <RotateCcw className="h-3.5 w-3.5" /> Retry Failed
                </button>
              </div>

              <div className="space-y-1.5">
                {result.failed.map((f, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-xs p-2 rounded bg-destructive/10 text-destructive border border-destructive/20"
                  >
                    <span className="font-mono font-medium">{f.subscription_number}</span>
                    <span>{f.error}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
