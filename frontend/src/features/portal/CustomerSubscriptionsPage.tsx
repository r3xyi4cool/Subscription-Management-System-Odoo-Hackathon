import React, { useState } from 'react';
import { usePortalSubscriptions, useInvalidateQueries } from '../../api/hooks';
import { subscriptionApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { StatusBadge } from '../../components/StatusBadge';
import { MoneyText } from '../../components/MoneyText';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { Subscription } from '../../api/types';
import { formatDate } from '../../lib/dates';
import {
  canPauseSubscription,
  canCloseEarlySubscription,
  canRenewSubscription,
} from '../../lib/permissions';
import { Pause, Play, RotateCcw, XCircle, AlertCircle, Check } from 'lucide-react';

export const CustomerSubscriptionsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');

  const [pendingAction, setPendingAction] = useState<{
    sub: Subscription;
    action: 'pause' | 'resume' | 'renew' | 'close';
    label: string;
    destructive?: boolean;
  } | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { data, isLoading, refetch } = usePortalSubscriptions({
    page,
    per_page: perPage,
    q: search,
  });

  const { invalidateSubscriptions } = useInvalidateQueries();

  const handleAction = async (reason?: string) => {
    if (!pendingAction) return;
    setIsSubmitting(true);
    setFeedbackMsg(null);

    try {
      await subscriptionApi[pendingAction.action](pendingAction.sub.id, reason);
      setFeedbackMsg({
        type: 'success',
        text: `Subscription ${pendingAction.sub.subscription_number} ${pendingAction.label.toLowerCase()} successfully!`,
      });
      setPendingAction(null);
      refetch();
      invalidateSubscriptions();
    } catch (err: unknown) {
      // Handles 403 gracefully
      setFeedbackMsg({
        type: 'error',
        text: err instanceof Error ? err.message : 'Action not permitted by plan policy (403)',
      });
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
          <span className="font-mono font-bold text-foreground">{row.subscription_number}</span>
          <p className="text-xs text-muted-foreground">{row.plan_name}</p>
        </div>
      ),
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
      header: 'Cycle Estimate',
      render: (row) => <MoneyText paise={row.recurring_total_paise} className="font-semibold" />,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: 'next_billing_date',
      header: 'Next Billing',
      render: (row) => <span>{formatDate(row.next_billing_date)}</span>,
    },
    {
      key: 'actions',
      header: 'Self-Service Actions',
      render: (row) => {
        // Enforce Plan flags strictly
        const allowPause = canPauseSubscription('customer', row.plan);
        const allowEarlyClose = canCloseEarlySubscription('customer', row.plan);
        const allowRenewal = canRenewSubscription('customer', row.plan);

        return (
          <div className="flex flex-wrap items-center gap-1.5">
            {/* Pause Action: only if active and allowed by plan */}
            {row.status === 'active' && allowPause && (
              <button
                onClick={() =>
                  setPendingAction({
                    sub: row,
                    action: 'pause',
                    label: 'Pause Plan',
                  })
                }
                className="inline-flex items-center gap-1 rounded border border-input bg-background px-2 py-1 text-xs font-medium hover:bg-muted"
                title="Pause subscription"
              >
                <Pause className="h-3 w-3 text-amber-600" />
                <span>Pause</span>
              </button>
            )}

            {/* Resume Action: only if paused */}
            {row.status === 'paused' && (
              <button
                onClick={() =>
                  setPendingAction({
                    sub: row,
                    action: 'resume',
                    label: 'Resume Plan',
                  })
                }
                className="inline-flex items-center gap-1 rounded border border-input bg-background px-2 py-1 text-xs font-medium hover:bg-muted"
                title="Resume subscription"
              >
                <Play className="h-3 w-3 text-emerald-600" />
                <span>Resume</span>
              </button>
            )}

            {/* Renew Action: only if allowed by plan and active/closed */}
            {(row.status === 'active' || row.status === 'closed') && allowRenewal && (
              <button
                onClick={() =>
                  setPendingAction({
                    sub: row,
                    action: 'renew',
                    label: 'Renew Contract',
                  })
                }
                className="inline-flex items-center gap-1 rounded border border-input bg-background px-2 py-1 text-xs font-medium hover:bg-muted"
                title="Renew subscription"
              >
                <RotateCcw className="h-3 w-3 text-primary" />
                <span>Renew</span>
              </button>
            )}

            {/* Close Early Action: only if allowed by plan and active/paused */}
            {(row.status === 'active' || row.status === 'paused') && allowEarlyClose && (
              <button
                onClick={() =>
                  setPendingAction({
                    sub: row,
                    action: 'close',
                    label: 'Terminate Plan',
                    destructive: true,
                  })
                }
                className="inline-flex items-center gap-1 rounded border border-destructive/20 bg-destructive/10 text-destructive px-2 py-1 text-xs font-medium hover:bg-destructive/20"
                title="Terminate subscription early"
              >
                <XCircle className="h-3 w-3" />
                <span>Close Early</span>
              </button>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Subscriptions"
        description="Self-service management of your active software subscriptions and recurring agreements"
      />

      {feedbackMsg && (
        <div
          className={`rounded-lg border p-3 text-xs flex items-center justify-between ${
            feedbackMsg.type === 'success'
              ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-800 dark:text-emerald-200'
              : 'border-destructive/30 bg-destructive/10 text-destructive'
          }`}
        >
          <div className="flex items-center gap-2">
            {feedbackMsg.type === 'success' ? (
              <Check className="h-4 w-4" />
            ) : (
              <AlertCircle className="h-4 w-4" />
            )}
            <span>{feedbackMsg.text}</span>
          </div>
          <button onClick={() => setFeedbackMsg(null)} className="font-bold opacity-60">
            Dismiss
          </button>
        </div>
      )}

      <DataTable
        columns={columns}
        data={data?.items}
        total={data?.total}
        page={page}
        perPage={perPage}
        pages={data?.pages}
        isLoading={isLoading}
        searchPlaceholder="Search your subscriptions..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        exportFilename="my_subscriptions"
      />

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(pendingAction)}
        title={pendingAction?.label || 'Confirm Action'}
        message={`Are you sure you want to perform "${pendingAction?.label}" on ${pendingAction?.sub.subscription_number}?`}
        confirmLabel={pendingAction?.label}
        isDestructive={pendingAction?.destructive}
        requireReason={pendingAction?.action === 'close'}
        reasonPlaceholder="Optional feedback for closing subscription..."
        isLoading={isSubmitting}
        onConfirm={handleAction}
        onCancel={() => setPendingAction(null)}
      />
    </div>
  );
};
