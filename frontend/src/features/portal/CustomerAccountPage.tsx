import React, { useState } from 'react';
import { useAuth } from '../../app/AuthContext';
import { authApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { FormField } from '../../components/FormField';
import { PasswordChecklist } from '../../components/PasswordChecklist';
import { validatePassword } from '../../lib/permissions';
import { Check, AlertCircle, Key, UserCheck } from 'lucide-react';

export const CustomerAccountPage: React.FC = () => {
  const { user, refreshUser } = useAuth();

  const [name, setName] = useState(user?.name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [companyName, setCompanyName] = useState(user?.company_name || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isPasswordSubmitting, setIsPasswordSubmitting] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSuccessMsg(false);
    setErrorMsg(null);

    try {
      await authApi.updateProfile({
        name,
        phone,
        company_name: companyName,
      });
      await refreshUser();
      setSuccessMsg(true);
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordSuccess(false);
    setPasswordError(null);

    if (newPassword !== confirmPassword) {
      setPasswordError('New password and confirmation do not match.');
      return;
    }

    const { isValid } = validatePassword(newPassword);
    if (!isValid) {
      setPasswordError('New password does not meet the complexity requirements.');
      return;
    }

    setIsPasswordSubmitting(true);
    try {
      await authApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: unknown) {
      setPasswordError(err instanceof Error ? err.message : 'Failed to change password');
    } finally {
      setIsPasswordSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <PageHeader
        title="Account Profile & Settings"
        description="Update your contact information, credentials, and account password"
      />

      {/* Profile Details Card */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4 pb-2 border-b border-border">
          <UserCheck className="h-5 w-5 text-primary" />
          <h2 className="text-base font-semibold text-foreground">Contact & Organization</h2>
        </div>

        {successMsg && (
          <div className="mb-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-800 dark:text-emerald-200 flex items-center gap-2">
            <Check className="h-4 w-4" />
            <span>Profile successfully updated!</span>
          </div>
        )}

        {errorMsg && (
          <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <FormField label="Registered Email (Read-only)" id="cemail">
            <input
              id="cemail"
              type="email"
              value={user?.email || ''}
              disabled
              className="w-full rounded-md border border-input bg-muted/50 px-3 py-2 text-sm text-muted-foreground font-mono cursor-not-allowed"
            />
          </FormField>

          <FormField label="Full Name" required id="cname">
            <input
              id="cname"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </FormField>

          <div className="grid grid-cols-2 gap-3">
            <FormField label="Company Name" id="ccomp">
              <input
                id="ccomp"
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </FormField>

            <FormField label="Phone Number" id="cphone">
              <input
                id="cphone"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </FormField>
          </div>

          <div className="pt-4 border-t border-border flex justify-end">
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow hover:bg-primary/90 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        </form>
      </div>

      {/* Change Password Card */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4 pb-2 border-b border-border">
          <Key className="h-5 w-5 text-primary" />
          <h2 className="text-base font-semibold text-foreground">Change Password</h2>
        </div>

        {passwordSuccess && (
          <div className="mb-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-800 dark:text-emerald-200 flex items-center gap-2">
            <Check className="h-4 w-4" />
            <span>Password successfully changed!</span>
          </div>
        )}

        {passwordError && (
          <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
            <AlertCircle className="h-4 w-4" />
            <span>{passwordError}</span>
          </div>
        )}

        <form onSubmit={handlePasswordChange} className="space-y-4">
          <FormField label="Current Password" required id="currpass">
            <input
              id="currpass"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </FormField>

          <FormField label="New Password" required id="newpass">
            <input
              id="newpass"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </FormField>

          <PasswordChecklist password={newPassword} />

          <FormField label="Confirm New Password" required id="confpass">
            <input
              id="confpass"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </FormField>

          <div className="pt-4 border-t border-border flex justify-end">
            <button
              type="submit"
              disabled={isPasswordSubmitting}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow hover:bg-primary/90 disabled:opacity-50"
            >
              {isPasswordSubmitting ? 'Updating...' : 'Update Password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
