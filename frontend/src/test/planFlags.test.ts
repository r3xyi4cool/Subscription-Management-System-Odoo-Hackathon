import { describe, it, expect } from 'vitest';
import {
  canPauseSubscription,
  canCloseEarlySubscription,
  canRenewSubscription,
  getValidSubscriptionTransitions,
} from '../lib/permissions';
import { Plan } from '../api/types';

describe('Plan Flags & Button Visibility Rules', () => {
  const strictPlan: Plan = {
    id: 'strict',
    name: 'Strict Plan',
    code: 'STRICT',
    billing_period: 'monthly',
    min_quantity: 1,
    auto_close: false,
    allow_early_close: false,
    allow_pause: false,
    allow_renewal: false,
    is_active: true,
    created_at: '',
    updated_at: '',
  };

  const flexiblePlan: Plan = {
    id: 'flex',
    name: 'Flexible Plan',
    code: 'FLEX',
    billing_period: 'monthly',
    min_quantity: 1,
    auto_close: false,
    allow_early_close: true,
    allow_pause: true,
    allow_renewal: true,
    is_active: true,
    created_at: '',
    updated_at: '',
  };

  it('hides pause, close early, and renew from customers when plan toggles are false', () => {
    expect(canPauseSubscription('customer', strictPlan)).toBe(false);
    expect(canCloseEarlySubscription('customer', strictPlan)).toBe(false);
    expect(canRenewSubscription('customer', strictPlan)).toBe(false);
  });

  it('shows pause, close early, and renew to customers when plan toggles are true', () => {
    expect(canPauseSubscription('customer', flexiblePlan)).toBe(true);
    expect(canCloseEarlySubscription('customer', flexiblePlan)).toBe(true);
    expect(canRenewSubscription('customer', flexiblePlan)).toBe(true);
  });

  it('always allows staff and admin to pause, close, or renew regardless of plan flags', () => {
    expect(canPauseSubscription('admin', strictPlan)).toBe(true);
    expect(canCloseEarlySubscription('admin', strictPlan)).toBe(true);
    expect(canRenewSubscription('admin', strictPlan)).toBe(true);

    expect(canPauseSubscription('staff', strictPlan)).toBe(true);
    expect(canCloseEarlySubscription('staff', strictPlan)).toBe(true);
    expect(canRenewSubscription('staff', strictPlan)).toBe(true);
  });

  it('generates only valid state transitions for active subscription', () => {
    // Customer with strict plan on active sub -> no actions allowed
    const customerStrictActions = getValidSubscriptionTransitions('active', 'customer', strictPlan);
    expect(customerStrictActions.map((a) => a.action)).toEqual([]);

    // Customer with flex plan on active sub -> pause, close, renew allowed
    const customerFlexActions = getValidSubscriptionTransitions('active', 'customer', flexiblePlan);
    expect(customerFlexActions.map((a) => a.action)).toEqual(['pause', 'close', 'renew']);

    // Staff on confirmed sub -> activate allowed
    const staffConfirmedActions = getValidSubscriptionTransitions('confirmed', 'staff', strictPlan);
    expect(staffConfirmedActions.map((a) => a.action)).toEqual(['activate']);
  });
});
