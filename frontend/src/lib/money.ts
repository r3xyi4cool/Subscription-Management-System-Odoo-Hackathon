/**
 * Money utilities for Brightloop SMS.
 * SQLite and API representation: integer in paise (1 INR = 100 paise).
 * Never use floats for monetary arithmetic.
 */

const inrFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/**
 * Format paise into Indian Rupee currency string (e.g. ₹1,250.00)
 */
export function formatMoney(paise: number): string {
  if (isNaN(paise) || !isFinite(paise)) return '₹0.00';
  return inrFormatter.format(paise / 100);
}

/**
 * Convert user-entered rupees (decimal or integer) to integer paise.
 * Rounds to nearest integer paise to prevent floating-point inaccuracies.
 */
export function rupeesToPaise(rupees: number | string): number {
  const val = typeof rupees === 'string' ? parseFloat(rupees) : rupees;
  if (isNaN(val) || !isFinite(val)) return 0;
  return Math.round(val * 100);
}

/**
 * Convert integer paise to decimal rupees for input fields.
 */
export function paiseToRupees(paise: number): number {
  if (isNaN(paise) || !isFinite(paise)) return 0;
  return paise / 100;
}
