'use client';

import { useState } from 'react';
import type { Order } from '@/lib/types';
import { orderApi } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { OrderStatusBadge, PaymentStatusBadge, PaymentMethodBadge } from '@/components/ui/status-badge';
import { LoadingSpinner } from '@/components/ui/loading-states';
import { Clock, CheckCircle, Banknote, AlertCircle, ShoppingBag, Flame, Maximize2, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface OrderCardProps {
  order: Order;
  onComplete: () => void;
  canCollectCash: boolean;
}

export function OrderCard({ order, onComplete, canCollectCash }: OrderCardProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [isCompleting, setIsCompleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewImage, setPreviewImage] = useState<string | null>(null);

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const getElapsedTime = (dateString: string) => {
    const created = new Date(dateString).getTime();
    const now = Date.now();
    const diffMinutes = Math.floor((now - created) / 60000);

    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes === 1) return '1 min ago';
    if (diffMinutes < 60) return `${diffMinutes} mins ago`;

    const hours = Math.floor(diffMinutes / 60);
    return `${hours}h ${diffMinutes % 60}m ago`;
  };

  const handleComplete = async () => {
    setError(null);
    setIsCompleting(true);

    // For cash orders with pending payment, collect cash first
    const needsCash = order.payment_method === 'cash' && order.payment_status === 'pending';
    if (needsCash) {
      const cashResponse = await orderApi.collectCash(order.id);
      if (!cashResponse.success) {
        setError(cashResponse.error || 'Failed to collect cash');
        setIsCompleting(false);
        return;
      }
    }

    const response = await orderApi.markCompleted(order.id);

    if (!response.success) {
      setError(response.error || 'Failed to complete order');
      setIsCompleting(false);
      return;
    }

    setIsCompleting(false);
    setShowConfirm(false);
    onComplete();
  };

  const needsCashCollection = order.payment_method === 'cash' && order.payment_status === 'pending';
  const canComplete = !needsCashCollection || canCollectCash;

  // Card urgency styling based on status (only pending/preparing/completed exist)
  const cardClassName = cn(
    'border-l-4 transition-all',
    order.status === 'preparing' && 'border-l-info',
    order.status === 'pending' && 'border-l-warning',
    order.status === 'completed' && 'border-l-success bg-success/5'
  );

  return (
    <>
      <Card className={cardClassName}>
        <CardContent className="p-4">
          {/* Header Row */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-4">
              <div>
                {/* Order Number - VERY PROMINENT */}
                <div className="flex items-center gap-2">
                  <p className="text-3xl font-black text-primary">{order.daily_order_number}</p>
                  {order.is_parcel && (
                    <div className="bg-primary/10 p-1.5 rounded-lg" title="Parcel / Takeaway">
                      <ShoppingBag className="h-5 w-5 text-primary" />
                    </div>
                  )}
                  {order.spicy_level && order.spicy_level !== 'normal' && (
                    <div className={cn(
                      "flex items-center gap-1 px-2 py-1 rounded-lg border shadow-sm animate-in zoom-in duration-300",
                      order.spicy_level === 'medium' && "bg-orange-50 border-orange-200 text-orange-700",
                      order.spicy_level === 'high' && "bg-red-50 border-red-200 text-red-700"
                    )}>
                      <Flame className={cn(
                        "h-4 w-4",
                        order.spicy_level === 'medium' && "text-orange-500",
                        order.spicy_level === 'high' && "text-red-500"
                      )} />
                      <span className="text-[10px] font-black uppercase tracking-tighter">{order.spicy_level === 'high' ? 'Extra Hot' : 'Medium'}</span>
                    </div>
                  )}
                </div>
                <p className="text-sm font-medium text-foreground">{order.customer_name}</p>
              </div>
            </div>
            <div className="flex flex-col items-end gap-1">
              <OrderStatusBadge status={order.status} />
              <PaymentStatusBadge status={order.payment_status} />
            </div>
          </div>

          {/* Order Items */}
          <div className="mt-6 space-y-3">
            {order.items.map((item) => (
              <div key={item.id} className="flex items-center justify-between group">
                <div className="flex items-center gap-3">
                  {/* Item Image Thumbnail */}
                  {item.menu_item_image_url && (
                    <div
                      className="relative h-12 w-12 flex-shrink-0 cursor-zoom-in overflow-hidden rounded-lg border border-border shadow-sm transition-all hover:scale-110 active:scale-95"
                      onClick={() => setPreviewImage(item.menu_item_image_url || null)}
                    >
                      <img
                        src={item.menu_item_image_url}
                        alt={item.menu_item_name}
                        className="h-full w-full object-cover"
                      />
                      <div className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/20 transition-colors">
                        <Maximize2 className="h-4 w-4 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                  )}
                  <span className="font-bold text-lg text-foreground">
                    {item.quantity}x {item.menu_item_name}
                  </span>
                </div>
              </div>
            ))}
            {order.notes && (
              <p className="mt-2 text-sm italic text-muted-foreground bg-muted/30 p-2 rounded">
                Note: {order.notes}
              </p>
            )}
          </div>

          {/* Footer Row */}
          <div className="mt-6 flex items-center justify-between pt-4 border-t border-dashed border-border">
            <div className="flex items-center gap-3">
              <PaymentMethodBadge method={order.payment_method} />
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>{getElapsedTime(order.created_at)}</span>
              </div>
            </div>
            <p className="font-black text-xl text-foreground">${Number(order.total).toFixed(2)}</p>
          </div>

          {/* Cash Warning */}
          {needsCashCollection && !canCollectCash && (
            <div className="mt-3 flex items-center gap-2 rounded-lg bg-warning/10 p-3 text-sm text-warning-foreground font-medium">
              <Banknote className="h-5 w-5" />
              <span>Cash collection required - contact authorized staff</span>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mt-3 flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive font-medium">
              <AlertCircle className="h-5 w-5" />
              <span>{error}</span>
            </div>
          )}

          {/* Complete Button */}
          {order.status !== 'completed' && canComplete && (
            <Button
              onClick={() => setShowConfirm(true)}
              className="mt-6 h-14 w-full text-lg font-black shadow-lg shadow-primary/20"
              disabled={isCompleting}
            >
              {isCompleting ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Processing...
                </>
              ) : (
                <>
                  <CheckCircle className="mr-2 h-6 w-6" />
                  Complete Order
                  {needsCashCollection && ` - Collect $${Number(order.total).toFixed(2)}`}
                </>
              )}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Image Preview Modal */}
      <Dialog open={!!previewImage} onOpenChange={(open) => !open && setPreviewImage(null)}>
        <DialogContent className="max-w-3xl p-0 overflow-hidden bg-transparent border-none shadow-none">
          <div className="relative group">
            <img
              src={previewImage || ''}
              alt="Item Preview"
              className="w-full h-auto max-h-[80vh] rounded-2xl object-cover shadow-2xl ring-1 ring-white/20"
            />
            <Button
              variant="secondary"
              size="icon"
              className="absolute top-4 right-4 rounded-full bg-black/50 hover:bg-black/80 text-white backdrop-blur-md transition-all"
              onClick={() => setPreviewImage(null)}
            >
              <X className="h-6 w-6" />
            </Button>
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-black/60 backdrop-blur-lg px-6 py-3 rounded-full text-white font-bold shadow-xl">
              Quick Identification
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Confirmation Dialog */}
      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Complete Order {order.daily_order_number}?</AlertDialogTitle>
            <AlertDialogDescription>
              {needsCashCollection ? (
                <>
                  Confirm that you have collected <strong>${Number(order.total).toFixed(2)}</strong> in cash
                  from the customer before completing this order.
                </>
              ) : (
                'This will mark the order as completed and remove it from the active orders list.'
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isCompleting} className="min-h-[44px]">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleComplete}
              disabled={isCompleting}
              className="min-h-[44px]"
            >
              {isCompleting ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Processing...
                </>
              ) : (
                'Complete Order'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
