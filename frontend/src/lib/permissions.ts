import { UserRole, Plan, SubscriptionStatus, Invoice } from '../api/types';
import { isDatePast } from './dates';

export interface PasswordValidationResult {
  minLength: boolean;
  hasUpper: boolean;
  hasLower: boolean;
  hasSpecial: boolean;
  isValid: boolean;
}

export function validatePassword(password: string): PasswordValidationResult {
  const minLength = password.length > 8; // > 8 characters as specified
  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasSpecial = /[^A-Za-z0-9]/.test(password);

  return {
    minLength,
    hasUpper,
    hasLower,
    hasSpecial,
    isValid: minLength && hasUpper && hasLower && hasSpecial,
  };
}

/**
 * Checks whether a user can perform subscription action based on role and plan toggles.
 */
export function canPauseSubscription(role: UserRole, plan?: Plan | null): boolean {
  if (role === 'admin' || role === 'staff') return true;
  // Customer can only pause if plan allows it
  return Boolean(plan?.allow_pause);
}

export function canCloseEarlySubscription(role: UserRole, plan?: Plan | null): boolean {
  if (role === 'admin' || role === 'staff') return true;
  // Customer can only close early if plan allows it
  return Boolean(plan?.allow_early_close);
}

export function canRenewSubscription(role: UserRole, plan?: Plan | null): boolean {
  if (role === 'admin' || role === 'staff') return true;
  // Customer can only renew if plan allows it
  return Boolean(plan?.allow_renewal);
}

/**
 * Valid transitions for subscriptions:
 * draft -> quotation -> confirmed -> active -> closed
 * pause/resume (from active to paused, paused to active)
 * renew (from active or closed to confirmed/active)
 */
export function getValidSubscriptionTransitions(
  currentStatus: SubscriptionStatus,
  role: UserRole,
  plan?: Plan | null
): Array<{ action: 'confirm' | 'activate' | 'pause' | 'resume' | 'renew' | 'close'; label: string; destructive?: boolean }> {
  const actions: Array<{ action: 'confirm' | 'activate' | 'pause' | 'resume' | 'renew' | 'close'; label: string; destructive?: boolean }> = [];

  switch (currentStatus) {
    case 'draft':
    case 'quotation':
      if (role !== 'customer') {
        actions.push({ action: 'confirm', label: 'Confirm Subscription' });
      }
      break;

    case 'confirmed':
      if (role !== 'customer') {
        actions.push({ action: 'activate', label: 'Activate' });
      }
      break;

    case 'active':
      if (canPauseSubscription(role, plan)) {
        actions.push({ action: 'pause', label: 'Pause' });
      }
      if (canCloseEarlySubscription(role, plan)) {
        actions.push({ action: 'close', label: 'Close Subscription', destructive: true });
      }
      if (canRenewSubscription(role, plan)) {
        actions.push({ action: 'renew', label: 'Renew' });
      }
      break;

    case 'paused':
      actions.push({ action: 'resume', label: 'Resume' });
      if (canCloseEarlySubscription(role, plan)) {
        actions.push({ action: 'close', label: 'Close Subscription', destructive: true });
      }
      break;

    case 'closed':
      if (canRenewSubscription(role, plan)) {
        actions.push({ action: 'renew', label: 'Renew Subscription' });
      }
      break;
  }

  return actions;
}

/**
 * Invoice action-state rules:
 * - Confirm only on draft
 * - Send / Print only on confirmed or paid
 * - Cancel only on draft/confirmed with no payments
 */
export function canConfirmInvoice(invoice: Invoice, role: UserRole): boolean {
  if (role === 'customer') return false;
  return invoice.status === 'draft';
}

export function canSendInvoice(invoice: Invoice, role: UserRole): boolean {
  if (role === 'customer') return false;
  return invoice.status === 'confirmed' || invoice.status === 'paid';
}

export function canPrintInvoice(invoice: Invoice): boolean {
  return invoice.status === 'confirmed' || invoice.status === 'paid';
}

export function canCancelInvoice(invoice: Invoice, role: UserRole): boolean {
  if (role === 'customer') return false;
  const isDraftOrConfirmed = invoice.status === 'draft' || invoice.status === 'confirmed';
  const hasNoPayments = (invoice.amount_paid_paise || 0) === 0;
  return isDraftOrConfirmed && hasNoPayments;
}

export function isQuotationExpired(validUntil: string): boolean {
  return isDatePast(validUntil);
}
