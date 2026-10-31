import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { UserRole } from '../api/types';

export const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          <p className="text-sm text-muted-foreground">Authenticating session...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!user.is_active) {
    return (
      <div className="flex h-screen w-full items-center justify-center p-4">
        <div className="max-w-md rounded-lg border border-destructive/30 bg-destructive/10 p-6 text-center">
          <h2 className="text-lg font-semibold text-destructive">Account Inactive</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Your account has been deactivated. Please contact your organization administrator for assistance.
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export const RequireRole: React.FC<{
  roles: UserRole[];
  children: React.ReactNode;
}> = ({ roles, children }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (!user || !roles.includes(user.role)) {
    return <Navigate to="/403" replace />;
  }

  return <>{children}</>;
};

export const RequireAnonymous: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (user) {
    if (user.role === 'customer') {
      return <Navigate to="/portal/dashboard" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};
