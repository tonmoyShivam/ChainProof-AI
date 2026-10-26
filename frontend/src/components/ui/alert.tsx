import type { HTMLAttributes } from 'react';
import { cn } from '@/utils/cn';

export function Alert({
  className,
  variant = 'info',
  ...props
}: HTMLAttributes<HTMLDivElement> & {
  variant?: 'info' | 'success' | 'error' | 'pending';
}) {
  const styles = {
    info: 'border-accent/40 bg-accent/10 text-slate-200',
    success: 'border-verify-ok/40 bg-verify-ok/10 text-verify-ok',
    error: 'border-verify-fail/40 bg-verify-fail/10 text-verify-fail',
    pending: 'border-verify-pending/40 bg-verify-pending/10 text-verify-pending',
  } as const;

  return (
    <div
      role="alert"
      className={cn('rounded-md border px-3 py-2 text-sm', styles[variant], className)}
      {...props}
    />
  );
}
