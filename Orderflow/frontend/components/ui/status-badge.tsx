'use client';

import { cn } from '@/lib/utils';
import type { OrderStatus, PaymentStatus, PaymentMethod } from '@/lib/types';

interface StatusBadgeProps {
  status: string;
  variant?: 'order' | 'payment' | 'method' | 'custom';
  className?: string;
}

const orderStatusConfig: Record<OrderStatus, { label: string; className: string }> = {
  pending: {
    label: 'Pending',
    className: 'bg-warning text-warning-foreground',
  },
  preparing: {
    label: 'Preparing',
    className: 'bg-info text-info-foreground',
  },
  completed: {
    label: 'Completed',
    className: 'bg-muted text-muted-foreground',
  },
};

const paymentStatusConfig: Record<PaymentStatus, { label: string; className: string }> = {
  pending: {
    label: 'Unpaid',
    className: 'bg-warning text-warning-foreground',
  },
  // Backend uses "success" for successful payments; display it as "Paid"
  success: {
    label: 'Paid',
    className: 'bg-success text-success-foreground',
  },
};

const paymentMethodConfig: Record<PaymentMethod, { label: string; className: string }> = {
  upi: {
    label: 'UPI',
    className: 'bg-info text-info-foreground',
  },
  cash: {
    label: 'Cash',
    className: 'bg-secondary text-secondary-foreground border border-border',
  },
};

export function StatusBadge({ status, variant = 'custom', className }: StatusBadgeProps) {
  let config: { label: string; className: string } | undefined;

  switch (variant) {
    case 'order':
      config = orderStatusConfig[status as OrderStatus];
      break;
    case 'payment':
      config = paymentStatusConfig[status as PaymentStatus];
      break;
    case 'method':
      config = paymentMethodConfig[status as PaymentMethod];
      break;
    default:
      config = { label: status, className: 'bg-muted text-muted-foreground' };
  }

  if (!config) {
    config = { label: status, className: 'bg-muted text-muted-foreground' };
  }

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold',
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  );
}

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  return <StatusBadge status={status} variant="order" />;
}

export function PaymentStatusBadge({ status }: { status: PaymentStatus }) {
  return <StatusBadge status={status} variant="payment" />;
}

export function PaymentMethodBadge({ method }: { method: PaymentMethod }) {
  return <StatusBadge status={method} variant="method" />;
}
