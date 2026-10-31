import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePortalNotifications, useInvalidateQueries } from '../../api/hooks';
import { portalApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { InAppNotification } from '../../api/types';
import { formatDate } from '../../lib/dates';
import {
  Bell,
  Check,
  CheckCheck,
  ExternalLink,
  Receipt,
  CreditCard,
  AlertCircle,
  Info,
  Filter,
} from 'lucide-react';

export const CustomerNotificationsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [filterUnreadOnly, setFilterUnreadOnly] = useState<boolean | undefined>(undefined);

  const navigate = useNavigate();
  const { invalidateNotifications } = useInvalidateQueries();

  const { data, isLoading } = usePortalNotifications({
    page,
    per_page: perPage,
    is_read: filterUnreadOnly,
  });

  const handleMarkAsRead = async (notif: InAppNotification) => {
    if (notif.is_read) return;
    try {
      await portalApi.markNotificationRead(notif.id);
      invalidateNotifications();
    } catch {
      // ignore
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await portalApi.markAllNotificationsRead();
      invalidateNotifications();
    } catch {
      // ignore
    }
  };

  const handleNavigate = (url?: string | null) => {
    if (!url) return;
    const dest = url.startsWith('/me/invoices')
      ? '/portal/invoices'
      : url.startsWith('/me/subscriptions')
      ? '/portal/subscriptions'
      : url;
    navigate(dest);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'invoice':
        return <Receipt className="h-5 w-5 text-blue-500" />;
      case 'payment':
        return <CreditCard className="h-5 w-5 text-emerald-500" />;
      case 'reminder':
        return <AlertCircle className="h-5 w-5 text-amber-500" />;
      default:
        return <Info className="h-5 w-5 text-primary" />;
    }
  };

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notifications & Messages"
        description="Stay updated with your billing cycles, payment confirmations, and account notices"
        actions={
          <button
            onClick={handleMarkAllRead}
            className="inline-flex items-center gap-1.5 rounded-lg border border-input bg-background px-3.5 py-2 text-xs font-semibold text-foreground hover:bg-muted shadow-sm transition-colors"
          >
            <CheckCheck className="h-4 w-4 text-primary" />
            <span>Mark All as Read</span>
          </button>
        }
      />

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-3">
        <button
          onClick={() => { setFilterUnreadOnly(undefined); setPage(1); }}
          className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
            filterUnreadOnly === undefined
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:bg-muted hover:text-foreground'
          }`}
        >
          All Notifications ({total})
        </button>
        <button
          onClick={() => { setFilterUnreadOnly(false); setPage(1); }}
          className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
            filterUnreadOnly === false
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:bg-muted hover:text-foreground'
          }`}
        >
          Unread Only
        </button>
      </div>

      {/* Notifications List */}
      <div className="rounded-xl border border-border bg-card shadow-sm divide-y divide-border overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-sm text-muted-foreground">
            Loading notifications...
          </div>
        ) : items.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <Bell className="h-8 w-8 text-muted-foreground mx-auto" />
            <p className="text-sm font-medium text-foreground">No notifications found</p>
            <p className="text-xs text-muted-foreground">You are all caught up!</p>
          </div>
        ) : (
          items.map((notif) => (
            <div
              key={notif.id}
              className={`p-5 flex flex-col sm:flex-row items-start justify-between gap-4 transition-colors ${
                !notif.is_read ? 'bg-primary/5 hover:bg-primary/10' : 'hover:bg-muted/30'
              }`}
            >
              <div className="flex items-start gap-4">
                <div className="p-2.5 rounded-xl bg-background border border-border shrink-0 shadow-sm">
                  {getTypeIcon(notif.type)}
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className={`text-sm ${!notif.is_read ? 'font-bold text-foreground' : 'font-semibold text-foreground/80'}`}>
                      {notif.title}
                    </h4>
                    {!notif.is_read && (
                      <span className="inline-flex items-center rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-bold text-primary">
                        NEW
                      </span>
                    )}
                    <span className="text-xs text-muted-foreground">
                      • {formatDate(notif.created_at)}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed max-w-2xl">
                    {notif.message}
                  </p>
                  {notif.link_url && (
                    <button
                      onClick={() => handleNavigate(notif.link_url)}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline pt-1"
                    >
                      <span>View document</span>
                      <ExternalLink className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                {!notif.is_read && (
                  <button
                    onClick={() => handleMarkAsRead(notif)}
                    className="inline-flex items-center gap-1 rounded-md border border-input bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
                    title="Mark as read"
                  >
                    <Check className="h-3.5 w-3.5" />
                    <span>Mark read</span>
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-muted-foreground pt-2">
          <span>Page {page} of {totalPages}</span>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="rounded border border-input bg-background px-3 py-1 font-medium hover:bg-muted disabled:opacity-50"
            >
              Previous
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="rounded border border-input bg-background px-3 py-1 font-medium hover:bg-muted disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
