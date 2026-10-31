import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, FileQuestion, Clock, ArrowLeft } from 'lucide-react';

export const ForbiddenPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-muted/20 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10 text-destructive mb-4">
        <ShieldAlert className="h-8 w-8" />
      </div>
      <h1 className="text-3xl font-extrabold text-foreground tracking-tight">403 - Access Forbidden</h1>
      <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">
        You do not possess the necessary role authorization or administrative permissions to access this screen.
      </p>
      <div className="mt-6">
        <Link
          to="/"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow hover:bg-primary/90"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Return to Dashboard</span>
        </Link>
      </div>
    </div>
  );
};

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-muted/20 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-muted text-muted-foreground mb-4">
        <FileQuestion className="h-8 w-8" />
      </div>
      <h1 className="text-3xl font-extrabold text-foreground tracking-tight">404 - Page Not Found</h1>
      <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">
        The requested URL could not be found or has been moved.
      </p>
      <div className="mt-6">
        <Link
          to="/"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow hover:bg-primary/90"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Return Home</span>
        </Link>
      </div>
    </div>
  );
};

export const SessionExpiredPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-muted/20 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-amber-500/10 text-amber-600 mb-4">
        <Clock className="h-8 w-8" />
      </div>
      <h1 className="text-3xl font-extrabold text-foreground tracking-tight">Session Expired</h1>
      <p className="mt-2 text-sm text-muted-foreground max-w-md mx-auto">
        Your authentication session has timed out due to inactivity or token revocation. Please log in again to continue.
      </p>
      <div className="mt-6">
        <Link
          to="/login"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow hover:bg-primary/90"
        >
          <span>Sign In</span>
        </Link>
      </div>
    </div>
  );
};
