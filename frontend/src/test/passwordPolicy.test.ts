import { describe, it, expect } from 'vitest';
import { validatePassword } from '../lib/permissions';

describe('Password Policy Validator', () => {
  it('rejects passwords with 8 or fewer characters', () => {
    // Exact rule: "more than 8 characters"
    expect(validatePassword('Pass@12').minLength).toBe(false);
    expect(validatePassword('Passw@12').minLength).toBe(false); // 8 chars -> false
    expect(validatePassword('Passwo@12').minLength).toBe(true);  // 9 chars -> true
  });

  it('verifies uppercase character requirement', () => {
    expect(validatePassword('demopassword@1').hasUpper).toBe(false);
    expect(validatePassword('DemoPassword@1').hasUpper).toBe(true);
  });

  it('verifies lowercase character requirement', () => {
    expect(validatePassword('DEMOPASSWORD@1').hasLower).toBe(false);
    expect(validatePassword('DEMOPassword@1').hasLower).toBe(true);
  });

  it('verifies special character requirement', () => {
    expect(validatePassword('DemoPassword123').hasSpecial).toBe(false);
    expect(validatePassword('DemoPassword@123').hasSpecial).toBe(true);
  });

  it('approves compliant strong passwords', () => {
    const valid = validatePassword('Demo@1234');
    expect(valid.minLength).toBe(true); // 9 characters
    expect(valid.hasUpper).toBe(true);
    expect(valid.hasLower).toBe(true);
    expect(valid.hasSpecial).toBe(true);
    expect(valid.isValid).toBe(true);
  });
});
