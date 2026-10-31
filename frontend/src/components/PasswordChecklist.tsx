import React from 'react';
import { Check, X } from 'lucide-react';
import { validatePassword } from '../lib/permissions';

interface PasswordChecklistProps {
  password?: string;
}

export const PasswordChecklist: React.FC<PasswordChecklistProps> = ({ password = '' }) => {
  const result = validatePassword(password);

  const criteria = [
    { label: 'More than 8 characters', met: result.minLength },
    { label: 'At least one uppercase letter (A-Z)', met: result.hasUpper },
    { label: 'At least one lowercase letter (a-z)', met: result.hasLower },
    { label: 'At least one special character (!@#$%^&*...)', met: result.hasSpecial },
  ];

  return (
    <div className="rounded-lg border border-border bg-muted/30 p-3 space-y-1.5 text-xs">
      <p className="font-medium text-foreground">Password requirements:</p>
      <div className="space-y-1">
        {criteria.map((item, idx) => (
          <div key={idx} className="flex items-center gap-2">
            {item.met ? (
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                <Check className="h-2.5 w-2.5 stroke-[3]" />
              </span>
            ) : (
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-muted text-muted-foreground">
                <X className="h-2.5 w-2.5" />
              </span>
            )}
            <span className={item.met ? 'text-emerald-700 dark:text-emerald-400 font-medium' : 'text-muted-foreground'}>
              {item.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
