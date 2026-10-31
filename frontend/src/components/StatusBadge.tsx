import React from 'react';
import { SubscriptionStatus, InvoiceStatus, RefundStatus } from '../api/types';

interface StatusBadgeProps {
  status: SubscriptionStatus | InvoiceStatus | RefundStatus | string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const norm = String(status).toLowerCase();

  let styles = 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-700';

  // Active / Paid / Processed (Success)
  if (['active', 'paid', 'approved', 'processed'].includes(norm)) {
    styles = 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800';
  }
  // Confirmed / Sent (Primary / Info)
  else if (['confirmed', 'sent', 'converted'].includes(norm)) {
    styles = 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800';
  }
  // Paused / Quotation / Requested (Warning)
  else if (['paused', 'quotation', 'requested'].includes(norm)) {
    styles = 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800';
  }
  // Closed / Cancelled / Rejected / Expired (Destructive / Muted)
  else if (['closed', 'cancelled', 'rejected', 'expired'].includes(norm)) {
    styles = 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800';
  }
  // Draft (Neutral)
  else if (['draft'].includes(norm)) {
    styles = 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border uppercase tracking-wider ${styles} ${className}`}
    >
      <span className="w-1.5 h-1.5 mr-1.5 rounded-full bg-current opacity-70"></span>
      {norm}
    </span>
  );
};
