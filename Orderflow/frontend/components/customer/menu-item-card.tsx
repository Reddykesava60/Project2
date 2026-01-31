'use client';

import { useState } from 'react';
import type { MenuItem } from '@/lib/types';
import { useCartStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Plus, Minus, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MenuItemCardProps {
  item: MenuItem;
}

export function MenuItemCard({ item }: MenuItemCardProps) {
  const { items, addItem, updateQuantity, removeItem } = useCartStore();
  const [showAdded, setShowAdded] = useState(false);
  const [errorShake, setErrorShake] = useState(false);

  const cartItem = items.find((i) => i.menu_item.id === item.id);
  const quantity = cartItem?.quantity || 0;

  const isOutOfStock = item.stock_quantity === 0;
  // Null is unlimited
  const stockLimit = item.stock_quantity ?? Infinity;
  const isLowStock = stockLimit < 10 && stockLimit > 0;

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(Number(price));
  };

  const shakeError = () => {
    setErrorShake(true);
    setTimeout(() => setErrorShake(false), 400);
  }

  const handleAdd = () => {
    if (isOutOfStock) return;
    if (quantity >= stockLimit) {
      shakeError();
      return;
    }
    addItem(item, 1);
    setShowAdded(true);
    setTimeout(() => setShowAdded(false), 1500);
  };

  const handleIncrement = () => {
    if (quantity >= stockLimit) {
      shakeError();
      return;
    }
    updateQuantity(item.id, quantity + 1);
  };

  const handleDecrement = () => {
    if (quantity <= 1) {
      removeItem(item.id);
    } else {
      updateQuantity(item.id, quantity - 1);
    }
  };

  return (
    <Card className={cn(
      "overflow-hidden border-border transition-all",
      isOutOfStock && "opacity-60 grayscale bg-muted/20"
    )}>
      <div className="flex">
        {/* Image or Placeholder */}
        <div className="relative h-28 w-28 flex-shrink-0">
          {item.image_url ? (
            <img
              src={item.image_url || "/placeholder.svg"}
              alt={item.name}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center bg-muted">
              <span className="text-2xl font-bold text-muted-foreground">
                {item.name.charAt(0)}
              </span>
            </div>
          )}

          {/* Out of Stock Overlay */}
          {isOutOfStock && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-[1px]">
              <span className="rounded-md bg-destructive/90 px-2 py-1 text-xs font-bold text-destructive-foreground shadow-sm">
                SOLD OUT
              </span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex flex-1 flex-col justify-between p-3">
          <div>
            <div className="flex items-center gap-2">
              {/* Veg/Non-veg indicator */}
              <span
                className={cn(
                  'inline-flex h-4 w-4 items-center justify-center rounded-sm border-2',
                  item.is_vegetarian
                    ? 'border-green-600'
                    : 'border-red-600'
                )}
              >
                <span
                  className={cn(
                    'h-2 w-2 rounded-full',
                    item.is_vegetarian ? 'bg-green-600' : 'bg-red-600'
                  )}
                />
              </span>
              <h3 className="font-semibold text-foreground">{item.name}</h3>
            </div>
            {item.description && (
              <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                {item.description}
              </p>
            )}

            {/* Low stock warning */}
            {!isOutOfStock && isLowStock && (
              <p className="mt-1 text-xs font-medium text-amber-600 animate-pulse">
                Only {stockLimit} left!
              </p>
            )}

            {/* Max limit warning */}
            {errorShake && (
              <p className="mt-1 text-xs font-bold text-destructive">
                Max quantity reached!
              </p>
            )}
          </div>
          <div className="flex items-center justify-between">
            <span className="font-semibold text-foreground">{formatPrice(item.price)}</span>

            {isOutOfStock ? (
              <Button size="sm" disabled variant="ghost" className="text-muted-foreground text-xs font-medium bg-muted/50">
                Unavailable
              </Button>
            ) : quantity === 0 ? (
              <Button
                size="sm"
                onClick={handleAdd}
                className={cn(
                  'min-h-[40px] min-w-[40px] transition-all',
                  showAdded && 'bg-success text-success-foreground'
                )}
              >
                {showAdded ? <Check className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
              </Button>
            ) : (
              <div className={cn(
                "flex items-center gap-2",
                errorShake && "animate-shake text-destructive"
              )}>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleDecrement}
                  className="h-10 w-10 p-0 bg-transparent"
                >
                  <Minus className="h-4 w-4" />
                </Button>
                <span className="w-8 text-center font-semibold text-foreground">{quantity}</span>
                <Button
                  size="sm"
                  onClick={handleIncrement}
                  className={cn("h-10 w-10 p-0", errorShake && "border-destructive text-destructive")}
                  disabled={quantity >= stockLimit}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
