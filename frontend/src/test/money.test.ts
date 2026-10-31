import { describe, it, expect } from 'vitest';
import { formatMoney, rupeesToPaise, paiseToRupees } from '../lib/money';

describe('Monetary Arithmetic and Formatting', () => {
  it('formats integer paise to INR currency standard', () => {
    // 250000 paise = ₹2,500.00
    const formatted = formatMoney(250000);
    expect(formatted).toContain('2,500.00');
    expect(formatted).toContain('₹');

    // 50 paise = ₹0.50
    const fiftyPaise = formatMoney(50);
    expect(fiftyPaise).toContain('0.50');

    // 0 paise = ₹0.00
    const zero = formatMoney(0);
    expect(zero).toContain('0.00');
  });

  it('converts decimal and string rupees to integer paise without floating point error', () => {
    expect(rupeesToPaise(100)).toBe(10000);
    expect(rupeesToPaise(10.5)).toBe(1050);
    expect(rupeesToPaise('1250.75')).toBe(125075);
    expect(rupeesToPaise(0.29)).toBe(29);
  });

  it('converts integer paise to decimal rupees for input editing', () => {
    expect(paiseToRupees(250000)).toBe(2500);
    expect(paiseToRupees(1050)).toBe(10.5);
    expect(paiseToRupees(0)).toBe(0);
  });
});
