'use client';

import { Button } from '@/components/ui/button';
import { ShoppingCart, ChevronRight } from 'lucide-react';
import { useCartStore } from '@/lib/store';

interface CartFloatingButtonProps {
  itemCount: number;
  onClick: () => void;
}

export function CartFloatingButton({ itemCount, onClick }: CartFloatingButtonProps) {
  const getTotal = useCartStore((state) => state.getTotal);
  const total = getTotal();

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(Number(price));
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background p-4 pb-safe">
      <Button
        onClick={onClick}
        className="h-14 w-full gap-3 text-base font-semibold"
      >
        <div className="flex items-center gap-2">
          <ShoppingCart className="h-5 w-5" />
          <span className="flex h-6 min-w-[24px] items-center justify-center rounded-full bg-primary-foreground px-2 text-sm font-bold text-primary">
            {itemCount}
          </span>
        </div>
        <span className="flex-1">View Cart</span>
        <span>{formatPrice(total)}</span>
        <ChevronRight className="h-5 w-5" />
      </Button>
    </div>
  );
}
