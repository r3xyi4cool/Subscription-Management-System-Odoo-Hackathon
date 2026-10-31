import React, { useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { authApi } from '../../api/endpoints';
import { FormField } from '../../components/FormField';
import { PasswordChecklist } from '../../components/PasswordChecklist';
import { validatePassword } from '../../lib/permissions';
import { KeyRound, AlertCircle, CheckCircle2 } from 'lucide-react';

export const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  const pwdValidation = validatePassword(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setErrorMessage('Missing password reset token in URL.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    if (!pwdValidation.isValid) {
      setErrorMessage('Please ensure your password satisfies all security criteria.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      await authApi.resetPassword({ token, password });
      setIsSuccess(true);
      setTimeout(() => navigate('/login'), 2500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid or expired reset token.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-muted/20 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md px-4">
          <div className="rounded-xl border border-destructive/30 bg-card p-6 text-center shadow-sm">
            <AlertCircle className="h-10 w-10 text-destructive mx-auto mb-3" />
            <h3 className="text-base font-semibold text-foreground">Invalid Reset Link</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              No reset token was found in the URL. Please request a new password reset link.
            </p>
            <div className="mt-4">
              <Link
                to="/forgot-password"
                className="inline-flex rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Request New Link
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted/20 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="mx-auto h-12 w-12 rounded-xl bg-primary flex items-center justify-center text-primary-foreground font-black text-2xl shadow-md">
          B
        </div>
        <h2 className="mt-4 text-2xl font-bold tracking-tight text-foreground">
          Set New Password
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Enter and confirm your new secure password
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm sm:p-8">
          {isSuccess ? (
            <div className="space-y-3 text-center">
              <CheckCircle2 className="h-12 w-12 text-emerald-500 mx-auto" />
              <h3 className="text-base font-semibold text-foreground">Password Reset Successfully!</h3>
              <p className="text-sm text-muted-foreground">
                Redirecting you to the login screen...
              </p>
            </div>
          ) : (
            <>
              {errorMessage && (
                <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <FormField label="New Password" required id="password">
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter new password"
                    disabled={isLoading}
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>

                <FormField label="Confirm New Password" required id="confirm">
                  <input
                    id="confirm"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                    disabled={isLoading}
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>

                <PasswordChecklist password={password} />

                <button
                  type="submit"
                  disabled={isLoading || !pwdValidation.isValid || password !== confirmPassword}
                  className="w-full flex items-center justify-center gap-2 rounded-md bg-primary py-2 text-sm font-semibold text-primary-foreground shadow hover:bg-primary/90 transition-colors disabled:opacity-50"
                >
                  {isLoading ? (
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                  ) : (
                    <KeyRound className="h-4 w-4" />
                  )}
                  <span>Save New Password</span>
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
