import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../app/AuthContext';
import { FormField } from '../../components/FormField';
import { ShieldCheck, LogIn, AlertCircle } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, sessionExpiredMessage, clearSessionExpiredMessage } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setErrorMessage('Please enter both email and password.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    clearSessionExpiredMessage();

    try {
      await login({ email, password });
      if (from) {
        navigate(from, { replace: true });
      } else {
        // Redirect will happen automatically through RequireAnonymous or root
        navigate('/', { replace: true });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid login credentials.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickFill = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('Demo@1234');
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-muted/20 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="mx-auto h-12 w-12 rounded-xl bg-primary flex items-center justify-center text-primary-foreground font-black text-2xl shadow-md">
          B
        </div>
        <h2 className="mt-4 text-2xl font-bold tracking-tight text-foreground">
          Sign in to Brightloop SMS
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Subscription Management and Billing Operations
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm sm:p-8">
          {sessionExpiredMessage && (
            <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-300 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{sessionExpiredMessage}</span>
            </div>
          )}

          {errorMessage && (
            <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <FormField label="Email address" required id="email">
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                disabled={isLoading}
                required
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </FormField>

            <FormField label="Password" required id="password">
              <div className="flex items-center justify-between">
                <span />
                <Link
                  to="/forgot-password"
                  className="text-xs text-primary hover:underline font-medium"
                >
                  Forgot password?
                </Link>
              </div>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                disabled={isLoading}
                required
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </FormField>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 rounded-md bg-primary py-2 text-sm font-semibold text-primary-foreground shadow hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
              ) : (
                <LogIn className="h-4 w-4" />
              )}
              <span>Sign in</span>
            </button>
          </form>

          {/* Demo Logins Quick-Fill (Mock Mode) */}
          <div className="mt-6 border-t border-border pt-4">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              <ShieldCheck className="h-3.5 w-3.5 text-primary" />
              <span>Demo Quick-Fill Credentials</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <button
                type="button"
                onClick={() => handleQuickFill('admin@brightloop.test')}
                className="rounded border border-input bg-muted/40 p-2 text-center hover:bg-muted font-medium transition-colors"
              >
                Admin
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('staff@brightloop.test')}
                className="rounded border border-input bg-muted/40 p-2 text-center hover:bg-muted font-medium transition-colors"
              >
                Staff
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('customer@brightloop.test')}
                className="rounded border border-input bg-muted/40 p-2 text-center hover:bg-muted font-medium transition-colors"
              >
                Customer
              </button>
            </div>
          </div>

          <div className="mt-6 text-center text-xs text-muted-foreground">
            Don't have a customer account?{' '}
            <Link to="/signup" className="font-semibold text-primary hover:underline">
              Sign up here
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
