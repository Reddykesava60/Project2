'use client';

import React from "react"

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useCartStore } from '@/lib/store';
import { publicService } from '@/lib/api-service';
import type { PaymentMethod } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { LoadingSpinner } from '@/components/ui/loading-states';
import { ChevronLeft, CreditCard, Banknote, AlertCircle, Minus, Plus, Trash2, ShoppingBag, Flame } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function CheckoutPage() {
  const params = useParams();
  const slug = params.slug as string;
  const router = useRouter();

  const {
    items,
    customerName,
    paymentMethod,
    restaurantId,
    setCustomerName,
    setPaymentMethod,
    updateQuantity,
    removeItem,
    getTotal,
    clearCart,
  } = useCartStore();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const total = getTotal();
  const tax = total * 0.08; // 8% tax
  const grandTotal = total + tax;

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const [privacyAccepted, setPrivacyAccepted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!customerName.trim()) {
      setError('Please enter your name');
      return;
    }

    if (items.length === 0) {
      setError('Your cart is empty');
      return;
    }

    if (!privacyAccepted) {
      setError('You must accept the privacy policy to place an order.');
      return;
    }

    if (!restaurantId) {
      setError('Restaurant not found');
      return;
    }

    setIsSubmitting(true);

    try {
      // Format items for backend (menu_item_id instead of menu_item object)
      const orderItems = items.map(item => ({
        menu_item_id: item.menu_item.id,
        quantity: item.quantity,
      }));

      // Use public service for customer orders
      const order = await publicService.createOrder(slug, {
        items: orderItems,
        customer_name: customerName.trim(),
        payment_method: paymentMethod.toUpperCase() as 'CASH' | 'ONLINE',
        privacy_accepted: true,
      });

      // Store order info and navigate to success
      clearCart();
      router.push(`/r/${slug}/order-success?orderId=${order.id}&orderNumber=${order.order_number}`);
    } catch (err: any) {
      setError(err.message || 'Failed to place order. Please try again.');
      setIsSubmitting(false);
    }
  };

  if (items.length === 0) {
    return (
      <main className="min-h-screen bg-background">
        <header className="sticky top-0 z-40 border-b border-border bg-background">
          <div className="mx-auto flex h-14 max-w-2xl items-center px-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push(`/r/${slug}`)}
              className="min-h-[44px] min-w-[44px] -ml-2"
            >
              <ChevronLeft className="h-5 w-5" />
            </Button>
            <h1 className="flex-1 text-center text-lg font-semibold">Checkout</h1>
            <div className="w-10" />
          </div>
        </header>
        <div className="flex flex-col items-center justify-center gap-4 p-8 pt-24 text-center">
          <p className="text-muted-foreground">Your cart is empty</p>
          <Button onClick={() => router.push(`/r/${slug}`)}>Browse Menu</Button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background pb-32">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-background">
        <div className="mx-auto flex h-14 max-w-2xl items-center px-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push(`/r/${slug}`)}
            className="min-h-[44px] min-w-[44px] -ml-2"
          >
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <h1 className="flex-1 text-center text-lg font-semibold">Checkout</h1>
          <div className="w-10" />
        </div>
      </header>

      <form onSubmit={handleSubmit} className="mx-auto max-w-2xl px-4 py-6 space-y-6">
        {/* Error Display */}
        {error && (
          <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Order Items */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Your Order</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {items.map((item) => (
              <div key={item.menu_item.id} className="flex items-center gap-3">
                <div className="flex-1">
                  <p className="font-medium text-foreground">{item.menu_item.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatPrice(item.menu_item.price)} each
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      if (item.quantity <= 1) {
                        removeItem(item.menu_item.id);
                      } else {
                        updateQuantity(item.menu_item.id, item.quantity - 1);
                      }
                    }}
                    className="h-9 w-9 p-0"
                  >
                    {item.quantity <= 1 ? (
                      <Trash2 className="h-4 w-4 text-destructive" />
                    ) : (
                      <Minus className="h-4 w-4" />
                    )}
                  </Button>
                  <span className="w-6 text-center font-medium">{item.quantity}</span>
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => updateQuantity(item.menu_item.id, item.quantity + 1)}
                    className="h-9 w-9 p-0"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <p className="w-20 text-right font-medium text-foreground">
                  {formatPrice(item.menu_item.price * item.quantity)}
                </p>
              </div>
            ))}

            {/* Totals */}
            <div className="border-t border-border pt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Subtotal</span>
                <span className="text-foreground">{formatPrice(total)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Tax (8%)</span>
                <span className="text-foreground">{formatPrice(tax)}</span>
              </div>
              <div className="flex justify-between text-lg font-semibold">
                <span>Total</span>
                <span>{formatPrice(grandTotal)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Order Options */}
        <div className="grid gap-4 sm:grid-cols-2">
          {/* Dining Option (Parcel) */}
          <Card
            className={cn(
              "cursor-pointer transition-all border-2",
              useCartStore.getState().isParcel ? "border-primary bg-primary/5" : "border-transparent"
            )}
            onClick={() => useCartStore.getState().setParcel(!useCartStore.getState().isParcel)}
          >
            <CardContent className="p-4 flex items-center gap-4">
              <div className={cn("p-2 rounded-full", useCartStore.getState().isParcel ? "bg-primary text-primary-foreground" : "bg-muted")}>
                <ShoppingBag className="h-5 w-5" />
              </div>
              <div>
                <p className="font-bold">Takeaway</p>
                <p className="text-xs text-muted-foreground">Pack as parcel</p>
              </div>
            </CardContent>
          </Card>

          {/* Spice Preference */}
          <div className="space-y-3">
            <Label className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Pick your heat level</Label>
            <div className="flex gap-2">
              {(['normal', 'medium', 'high'] as const).map((level) => {
                const colors = {
                  normal: "bg-zinc-100 text-zinc-600 border-zinc-200",
                  medium: "bg-orange-100 text-orange-700 border-orange-200",
                  high: "bg-red-100 text-red-700 border-red-200"
                };
                const activeColors = {
                  normal: "bg-zinc-800 text-white border-zinc-900 ring-2 ring-zinc-800",
                  medium: "bg-orange-500 text-white border-orange-600 ring-2 ring-orange-400",
                  high: "bg-red-600 text-white border-red-700 ring-2 ring-red-500"
                };

                const isSelected = useCartStore.getState().spicyLevel === level;

                return (
                  <button
                    key={level}
                    type="button"
                    onClick={() => useCartStore.getState().setSpicyLevel(level)}
                    className={cn(
                      "flex-1 h-14 rounded-2xl border-2 transition-all flex flex-col items-center justify-center gap-0.5",
                      isSelected ? activeColors[level] : "border-transparent bg-muted/60 hover:bg-muted"
                    )}
                  >
                    <Flame className={cn("w-5 h-5", isSelected ? "animate-bounce" : "text-muted-foreground/50")} />
                    <span className="text-[10px] font-black uppercase">{level === 'normal' ? 'No Heat' : level}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Customer Name */}
        <Card className="border-none shadow-none bg-muted/30">
          <CardHeader className="pb-2 text-center">
            <CardTitle className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Ordering For</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Input
                id="name"
                type="text"
                placeholder="Enter Your Name"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                required
                disabled={isSubmitting}
                className="h-16 text-center text-2xl font-black tracking-tight bg-transparent border-b-2 border-t-0 border-x-0 rounded-none focus-visible:ring-0 focus-visible:border-primary px-0"
              />
            </div>
          </CardContent>
        </Card>

        {/* Payment Method */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Payment Method</CardTitle>
          </CardHeader>
          <CardContent>
            <RadioGroup
              value={paymentMethod}
              onValueChange={(value) => setPaymentMethod(value as PaymentMethod)}
              disabled={isSubmitting}
              className="space-y-3"
            >
              <label
                htmlFor="online"
                className="flex cursor-pointer items-center gap-4 rounded-lg border border-border p-4 transition-colors hover:bg-muted/50 has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary/5"
              >
                <RadioGroupItem value="online" id="online" />
                <CreditCard className="h-5 w-5 text-muted-foreground" />
                <div className="flex-1">
                  <p className="font-medium text-foreground">Pay Online</p>
                  <p className="text-sm text-muted-foreground">
                    Pay now with card or digital wallet
                  </p>
                </div>
              </label>
              <label
                htmlFor="cash"
                className="flex cursor-pointer items-center gap-4 rounded-lg border border-border p-4 transition-colors hover:bg-muted/50 has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary/5"
              >
                <RadioGroupItem value="cash" id="cash" />
                <Banknote className="h-5 w-5 text-muted-foreground" />
                <div className="flex-1">
                  <p className="font-medium text-foreground">Pay at Counter</p>
                  <p className="text-sm text-muted-foreground">
                    Pay with cash when you pick up your order
                  </p>
                </div>
              </label>
            </RadioGroup>
          </CardContent>
        </Card>

        {/* Privacy Policy */}
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="privacy"
            checked={privacyAccepted}
            onChange={(e) => setPrivacyAccepted(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
          />
          <label
            htmlFor="privacy"
            className="text-sm text-muted-foreground leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            I accept the <span className="underline">Privacy Policy</span> and <span className="underline">Terms of Service</span>
          </label>
        </div>
      </form>

      {/* Submit Button */}
      <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background p-4 pb-safe">
        <div className="mx-auto max-w-2xl">
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || items.length === 0 || !customerName.trim() || !privacyAccepted}
            className="h-14 w-full text-base font-semibold"
          >
            {isSubmitting ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Placing Order...
              </>
            ) : (
              <>Place Order - {formatPrice(grandTotal)}</>
            )}
          </Button>
        </div>
      </div>
    </main>
  );
}
