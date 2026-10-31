import React from 'react';
import { formatMoney } from '../lib/money';

interface MoneyTextProps {
  paise: number;
  className?: string;
  isOverdue?: boolean;
}

export const MoneyText: React.FC<MoneyTextProps> = ({
  paise,
  className = '',
  isOverdue = false,
}) => {
  const formatted = formatMoney(paise);

  return (
    <span
      className={`font-mono ${
        isOverdue
          ? 'text-rose-600 dark:text-rose-400 font-semibold'
          : 'text-foreground'
      } ${className}`}
    >
      {formatted}
    </span>
  );
};
