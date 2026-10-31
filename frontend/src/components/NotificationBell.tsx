import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, Check, ExternalLink, Receipt, CreditCard, AlertCircle, Info } from 'lucide-react';
import { useUnreadNotificationsCount, usePortalNotifications, useInvalidateQueries } from '../api/hooks';
import { portalApi } from '../api/endpoints';
import { InAppNotification } from '../api/types';
import { formatDate } from '../lib/dates';

export const NotificationBell: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const { data: countData } = useUnreadNotificationsCount();
  const { data: notifsData } = usePortalNotifications({ page: 1, per_page: 5 });
  const { invalidateNotifications } = useInvalidateQueries();

  const unreadCount = countData?.count ?? countData?.unread_count ?? 0;
  const recentNotifications = notifsData?.items ?? [];

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkAsRead = async (notif: InAppNotification, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      if (!notif.is_read) {
        await portalApi.markNotificationRead(notif.id);
        invalidateNotifications();
      }
      if (notif.link_url) {
        setIsOpen(false);
        // Translate /me/invoices/INV-xxx to /portal/invoices
        const destination = notif.link_url.startsWith('/me/invoices')
          ? '/portal/invoices'
          : notif.link_url.startsWith('/me/subscriptions')
          ? '/portal/subscriptions'
          : notif.link_url;
        navigate(destination);
      }
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

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'invoice':
        return <Receipt className="h-4 w-4 text-blue-500" />;
      case 'payment':
        return <CreditCard className="h-4 w-4 text-emerald-500" />;
      case 'reminder':
        return <AlertCircle className="h-4 w-4 text-amber-500" />;
      default:
        return <Info className="h-4 w-4 text-primary" />;
    }
  };

  return (
    <div className="relative inline-block" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        aria-label="In-App Notifications"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground animate-pulse">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-xl border border-border bg-card shadow-xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-2">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border px-4 py-3 bg-muted/30">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm text-foreground">Notifications</span>
              {unreadCount > 0 && (
                <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">
                  {unreadCount} unread
                </span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-primary hover:underline font-medium flex items-center gap-1"
              >
                <Check className="h-3.5 w-3.5" />
                Mark all read
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-80 overflow-y-auto divide-y divide-border">
            {recentNotifications.length === 0 ? (
              <div className="p-6 text-center text-xs text-muted-foreground">
                No notifications right now.
              </div>
            ) : (
              recentNotifications.map((n) => (
                <div
                  key={n.id}
                  onClick={() => handleMarkAsRead(n)}
                  className={`p-3.5 hover:bg-muted/40 transition-colors cursor-pointer flex items-start gap-3 ${
                    !n.is_read ? 'bg-primary/5' : ''
                  }`}
                >
                  <div className="mt-0.5 shrink-0 rounded-lg bg-background p-1.5 border border-border">
                    {getTypeIcon(n.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <p className={`text-xs ${!n.is_read ? 'font-semibold text-foreground' : 'font-medium text-foreground/80'} truncate`}>
                        {n.title}
                      </p>
                      <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                        {formatDate(n.created_at)}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                      {n.message}
                    </p>
                    {n.link_url && (
                      <span className="inline-flex items-center gap-1 text-[11px] text-primary font-medium mt-1">
                        View Details <ExternalLink className="h-3 w-3" />
                      </span>
                    )}
                  </div>
                  {!n.is_read && (
                    <span className="h-2 w-2 rounded-full bg-primary shrink-0 mt-1.5" />
                  )}
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-border px-4 py-2.5 bg-muted/20 text-center">
            <Link
              to="/portal/notifications"
              onClick={() => setIsOpen(false)}
              className="text-xs text-primary font-medium hover:underline inline-block"
            >
              View all notifications
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

