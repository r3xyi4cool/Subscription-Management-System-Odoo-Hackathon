import React, { useState } from 'react';
import { useAuth } from '../../app/AuthContext';
import { authApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { FormField } from '../../components/FormField';
import { User, Check, AlertCircle } from 'lucide-react';

export const CustomerAccountPage: React.FC = () => {
  const { user, refreshUser } = useAuth();

  const [name, setName] = useState(user?.name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [companyName, setCompanyName] = useState(user?.company_name || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

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

  return (
    <div className="space-y-6 max-w-2xl">
      <PageHeader
        title="Account Profile"
        description="Update your contact information and primary company credentials"
      />

      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
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
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
