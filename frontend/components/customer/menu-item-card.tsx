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

  const cartItem = items.find((i) => i.menu_item.id === item.id);
  const quantity = cartItem?.quantity || 0;

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(Number(price));
  };

  const handleAdd = () => {
    addItem(item, 1);
    setShowAdded(true);
    setTimeout(() => setShowAdded(false), 1500);
  };

  const handleIncrement = () => {
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
    <Card className="overflow-hidden border-border">
      <div className="flex">
        {/* Image or Placeholder */}
        {item.image_url ? (
          <div className="relative h-28 w-28 flex-shrink-0">
            <img
              src={item.image_url || "/placeholder.svg"}
              alt={item.name}
              className="h-full w-full object-cover"
            />
          </div>
        ) : (
          <div className="flex h-28 w-28 flex-shrink-0 items-center justify-center bg-muted">
            <span className="text-2xl font-bold text-muted-foreground">
              {item.name.charAt(0)}
            </span>
          </div>
        )}

        {/* Content */}
        <div className="flex flex-1 flex-col justify-between p-3">
          <div>
            <h3 className="font-semibold text-foreground">{item.name}</h3>
            {item.description && (
              <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                {item.description}
              </p>
            )}
          </div>
          <div className="flex items-center justify-between">
            <span className="font-semibold text-foreground">{formatPrice(item.price)}</span>

            {quantity === 0 ? (
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
              <div className="flex items-center gap-2">
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
                  className="h-10 w-10 p-0"
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
