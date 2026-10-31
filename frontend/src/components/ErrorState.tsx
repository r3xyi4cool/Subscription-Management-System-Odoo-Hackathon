import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message = 'We could not load the requested data. Please try again.',
  onRetry,
}) => {
  return (
    <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 my-4 text-center">
      <div className="flex justify-center mb-3">
        <AlertCircle className="h-8 w-8 text-destructive" />
      </div>
      <h3 className="text-base font-semibold text-destructive">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground max-w-md mx-auto">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-2 rounded-md bg-destructive/10 px-3.5 py-1.5 text-sm font-medium text-destructive hover:bg-destructive/20 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Retry
        </button>
      )}
    </div>
  );
};
