'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import useSWR from 'swr';
import { useAuthStore } from '@/lib/store';
import { restaurantApi, orderApi } from '@/lib/api';
import type { MenuItem, MenuCategory } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingPage, LoadingSpinner } from '@/components/ui/loading-states';
import { ErrorState, EmptyState } from '@/components/ui/error-states';
import { UnauthorizedError } from '@/components/ui/error-states';
import {
  Minus,
  Plus,
  ShoppingCart,
  Trash2,
  AlertCircle,
  CheckCircle,
  Banknote,
  UtensilsCrossed,
} from 'lucide-react';

interface CartItem {
  item: MenuItem;
  quantity: number;
}

export default function StaffNewOrderPage() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const restaurantId = user?.restaurant_id;
  const canCollectCash = user?.can_collect_cash || false;

  const [cart, setCart] = useState<CartItem[]>([]);
  const [customerName, setCustomerName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{ orderNumber: string } | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const { data: menuData, error: menuError, isLoading } = useSWR(
    restaurantId ? `/menu/${restaurantId}` : null,
    () => restaurantApi.getMenu(restaurantId!)
  );

  const categories = menuData?.data || [];

  // Cart functions
  const addToCart = (item: MenuItem) => {
    setCart((prev) => {
      const existing = prev.find((c) => c.item.id === item.id);
      if (existing) {
        return prev.map((c) =>
          c.item.id === item.id ? { ...c, quantity: c.quantity + 1 } : c
        );
      }
      return [...prev, { item, quantity: 1 }];
    });
  };

  const updateQuantity = (itemId: string, delta: number) => {
    setCart((prev) => {
      return prev
        .map((c) => {
          if (c.item.id === itemId) {
            const newQty = c.quantity + delta;
            return newQty > 0 ? { ...c, quantity: newQty } : null;
          }
          return c;
        })
        .filter(Boolean) as CartItem[];
    });
  };

  const getCartTotal = () => {
    return cart.reduce((sum, c) => sum + c.item.price * c.quantity, 0);
  };

  const getCartItemCount = () => {
    return cart.reduce((sum, c) => sum + c.quantity, 0);
  };

  const clearCart = () => {
    setCart([]);
    setCustomerName('');
  };

  // Submit order
  const handleSubmit = async () => {
    if (!restaurantId || cart.length === 0) return;

    setError(null);
    setIsSubmitting(true);

    const response = await orderApi.createCashOrder(
      restaurantId,
      cart.map((c) => ({ menu_item_id: c.item.id, quantity: c.quantity })),
      customerName.trim() || 'Walk-in Customer'
    );

    if (!response.success || !response.data) {
      setError(response.error || 'Failed to create order');
      setIsSubmitting(false);
      return;
    }

    setSuccess({ orderNumber: response.data.order_number || response.data.daily_order_number });
    setIsSubmitting(false);
  };

  // Reset for new order
  const handleNewOrder = () => {
    clearCart();
    setSuccess(null);
    setError(null);
  };

  // Permission check - hide from non-authorized staff
  if (!canCollectCash) {
    return (
      <main className="min-h-screen">
        <header className="sticky top-0 z-40 border-b border-border bg-background">
          <div className="px-4 py-3">
            <h1 className="text-xl font-bold text-foreground">New Cash Order</h1>
          </div>
        </header>
        <div className="p-4">
          <UnauthorizedError />
          <p className="mt-4 text-center text-sm text-muted-foreground">
            You do not have permission to create cash orders.
          </p>
        </div>
      </main>
    );
  }

  if (!restaurantId) {
    return (
      <div className="p-4">
        <ErrorState title="No Restaurant" message="You are not assigned to a restaurant." />
      </div>
    );
  }

  if (isLoading) {
    return <LoadingPage message="Loading menu..." />;
  }

  if (menuError || !menuData?.success) {
    return (
      <div className="p-4">
        <ErrorState title="Failed to Load Menu" message="Unable to load the menu." />
      </div>
    );
  }

  // Success state
  if (success) {
    return (
      <main className="min-h-screen bg-background">
        <div className="flex min-h-screen flex-col items-center justify-center p-4">
          <div className="w-full max-w-md text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-success">
              <CheckCircle className="h-8 w-8 text-success-foreground" />
            </div>
            <h1 className="text-2xl font-bold text-foreground">Order Created!</h1>
            <Card className="mt-6 border-2 border-primary">
              <CardContent className="py-6">
                <p className="text-sm text-muted-foreground">Order Number</p>
                <p className="text-6xl font-black text-primary">{success.orderNumber}</p>
              </CardContent>
            </Card>
            <div className="mt-6 space-y-3">
              <Button onClick={handleNewOrder} className="h-12 w-full text-base font-semibold">
                Create Another Order
              </Button>
              <Button
                variant="outline"
                onClick={() => router.push('/staff/orders')}
                className="h-12 w-full text-base"
              >
                View All Orders
              </Button>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen pb-44">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-background">
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-xl font-bold text-foreground">New Cash Order</h1>
          {cart.length > 0 && (
            <Button variant="ghost" size="sm" onClick={clearCart} className="text-destructive">
              <Trash2 className="h-4 w-4 mr-1" />
              Clear
            </Button>
          )}
        </div>

        {/* Category Tabs */}
        <div className="flex gap-2 overflow-x-auto px-4 pb-3 scrollbar-hide">
          {categories.map((category) => (
            <Button
              key={category.id}
              variant={activeCategory === category.id ? 'default' : 'outline'}
              size="sm"
              onClick={() =>
                setActiveCategory(activeCategory === category.id ? null : category.id)
              }
              className="whitespace-nowrap"
            >
              {category.name}
            </Button>
          ))}
        </div>
      </header>

      {/* Menu Grid - POS Style */}
      <div className="p-4">
        {error && (
          <div className="mb-4 flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

        {categories.length === 0 ? (
          <EmptyState
            icon={<UtensilsCrossed className="h-8 w-8 text-muted-foreground" />}
            title="No Menu Items"
            message="The menu has no items available."
          />
        ) : (
          <div className="space-y-6">
            {categories
              .filter((cat) => !activeCategory || cat.id === activeCategory)
              .map((category) => {
                const availableItems = category.items.filter((item) => item.is_available);
                if (availableItems.length === 0) return null;

                return (
                  <div key={category.id}>
                    <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                      {category.name}
                    </h2>
                    <div className="grid grid-cols-2 gap-3">
                      {availableItems.map((item) => {
                        const cartItem = cart.find((c) => c.item.id === item.id);
                        const quantity = cartItem?.quantity || 0;

                        return (
                          <button
                            key={item.id}
                            type="button"
                            onClick={() => addToCart(item)}
                            className={`relative rounded-lg border p-3 text-left transition-all ${
                              quantity > 0
                                ? 'border-primary bg-primary/5'
                                : 'border-border bg-card hover:border-primary/50'
                            }`}
                          >
                            {quantity > 0 && (
                              <span className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                                {quantity}
                              </span>
                            )}
                            <p className="font-medium text-foreground line-clamp-2">{item.name}</p>
                            <p className="mt-1 text-sm font-semibold text-primary">
                              ${item.price.toFixed(2)}
                            </p>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
          </div>
        )}
      </div>

      {/* Cart Summary - Fixed Bottom */}
      {cart.length > 0 && (
        <div className="fixed bottom-20 left-0 right-0 z-40 border-t border-border bg-background p-4 shadow-lg">
          {/* Cart Items */}
          <div className="mb-4 max-h-40 space-y-2 overflow-y-auto">
            {cart.map((cartItem) => (
              <div key={cartItem.item.id} className="flex items-center justify-between">
                <span className="flex-1 text-sm font-medium text-foreground truncate">
                  {cartItem.item.name}
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => updateQuantity(cartItem.item.id, -1)}
                    className="h-8 w-8 p-0"
                  >
                    <Minus className="h-3 w-3" />
                  </Button>
                  <span className="w-6 text-center text-sm font-medium">{cartItem.quantity}</span>
                  <Button
                    size="sm"
                    onClick={() => updateQuantity(cartItem.item.id, 1)}
                    className="h-8 w-8 p-0"
                  >
                    <Plus className="h-3 w-3" />
                  </Button>
                  <span className="w-16 text-right text-sm font-medium">
                    ${(cartItem.item.price * cartItem.quantity).toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Customer Name */}
          <div className="mb-3">
            <Input
              placeholder="Customer name (optional)"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              className="h-10"
            />
          </div>

          {/* Submit Button */}
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || cart.length === 0}
            className="h-12 w-full text-base font-semibold"
          >
            {isSubmitting ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Creating Order...
              </>
            ) : (
              <>
                <Banknote className="mr-2 h-5 w-5" />
                Create Cash Order - ${getCartTotal().toFixed(2)}
              </>
            )}
          </Button>
        </div>
      )}
    </main>
  );
}
