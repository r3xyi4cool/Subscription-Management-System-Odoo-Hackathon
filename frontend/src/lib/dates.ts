/**
 * Date and time utilities for Brightloop SMS.
 * Dates are ISO 8601 (YYYY-MM-DD or UTC timestamps).
 */

export function formatDate(dateString?: string | null): string {
  if (!dateString) return '—';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return new Intl.DateTimeFormat('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    }).format(d);
  } catch {
    return dateString;
  }
}

export function formatDateTime(dateTimeString?: string | null): string {
  if (!dateTimeString) return '—';
  try {
    const d = new Date(dateTimeString);
    if (isNaN(d.getTime())) return dateTimeString;
    return new Intl.DateTimeFormat('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    }).format(d);
  } catch {
    return dateTimeString;
  }
}

export function isDatePast(dateString?: string | null): boolean {
  if (!dateString) return false;
  const target = new Date(dateString);
  const now = new Date();
  // Strip time for pure date comparisons
  target.setHours(0, 0, 0, 0);
  now.setHours(0, 0, 0, 0);
  return target.getTime() < now.getTime();
}

export function isOverdue(dueDateString?: string | null, balanceDuePaise = 0): boolean {
  if (!dueDateString || balanceDuePaise <= 0) return false;
  return isDatePast(dueDateString);
}

export function todayISO(): string {
  return new Date().toISOString().split('T')[0];
}

export function addDaysISO(baseDateStr: string, days: number): string {
  const d = new Date(baseDateStr);
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}
