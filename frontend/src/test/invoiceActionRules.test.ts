import { describe, it, expect } from 'vitest';
import {
  canConfirmInvoice,
  canSendInvoice,
  canPrintInvoice,
  canCancelInvoice,
} from '../lib/permissions';
import { Invoice } from '../api/types';

describe('Invoice Action-State Permission Rules', () => {
  const baseInvoice: Invoice = {
    id: 'inv_1',
    invoice_number: 'INV-2026-000001',
    customer_id: 'cust_1',
    status: 'draft',
    issue_date: '2026-10-31',
    due_date: '2026-11-15',
    lines_subtotal_paise: 500000,
    discount_paise: 0,
    taxable_amount_paise: 500000,
    tax_total_paise: 90000,
    total_paise: 590000,
    amount_paid_paise: 0,
    balance_due_paise: 590000,
    lines: [],
    created_at: '',
    updated_at: '',
  };

  it('allows Confirm ONLY on draft invoices and never for customer role', () => {
    expect(canConfirmInvoice({ ...baseInvoice, status: 'draft' }, 'staff')).toBe(true);
    expect(canConfirmInvoice({ ...baseInvoice, status: 'confirmed' }, 'staff')).toBe(false);
    expect(canConfirmInvoice({ ...baseInvoice, status: 'paid' }, 'staff')).toBe(false);
    expect(canConfirmInvoice({ ...baseInvoice, status: 'draft' }, 'customer')).toBe(false);
  });

  it('allows Send/Print ONLY on confirmed or paid invoices', () => {
    // Draft cannot be sent
    expect(canSendInvoice({ ...baseInvoice, status: 'draft' }, 'staff')).toBe(false);
    expect(canPrintInvoice({ ...baseInvoice, status: 'draft' })).toBe(false);

    // Confirmed can be sent & printed
    expect(canSendInvoice({ ...baseInvoice, status: 'confirmed' }, 'staff')).toBe(true);
    expect(canPrintInvoice({ ...baseInvoice, status: 'confirmed' })).toBe(true);

    // Paid can be sent & printed
    expect(canSendInvoice({ ...baseInvoice, status: 'paid' }, 'staff')).toBe(true);
    expect(canPrintInvoice({ ...baseInvoice, status: 'paid' })).toBe(true);
  });

  it('allows Cancel ONLY on draft or confirmed invoices with ZERO payments', () => {
    // Draft with 0 payments -> can cancel
    expect(canCancelInvoice({ ...baseInvoice, status: 'draft', amount_paid_paise: 0 }, 'staff')).toBe(true);

    // Confirmed with 0 payments -> can cancel
    expect(canCancelInvoice({ ...baseInvoice, status: 'confirmed', amount_paid_paise: 0 }, 'staff')).toBe(true);

    // Confirmed with partial payment (> 0) -> CANNOT cancel
    expect(canCancelInvoice({ ...baseInvoice, status: 'confirmed', amount_paid_paise: 100000 }, 'staff')).toBe(false);

    // Paid invoice -> CANNOT cancel
    expect(canCancelInvoice({ ...baseInvoice, status: 'paid', amount_paid_paise: 590000 }, 'staff')).toBe(false);
  });
});
