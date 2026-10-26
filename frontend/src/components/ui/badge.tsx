import { cva, type VariantProps } from 'class-variance-authority';
import type { HTMLAttributes } from 'react';
import { cn } from '@/utils/cn';

const badgeVariants = cva(
  'inline-flex items-center rounded px-2 py-0.5 font-mono text-xs font-medium',
  {
    variants: {
      variant: {
        default: 'bg-accent/15 text-accent-muted',
        ok: 'bg-verify-ok/15 text-verify-ok',
        fail: 'bg-verify-fail/15 text-verify-fail',
        pending: 'bg-verify-pending/15 text-verify-pending',
        muted: 'bg-navy-700 text-slate-300',
      },
    },
    defaultVariants: { variant: 'default' },
  },
);

export function Badge({
  className,
  variant,
  ...props
}: HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
