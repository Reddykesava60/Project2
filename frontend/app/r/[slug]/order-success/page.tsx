'use client';

import { useSearchParams, useParams } from 'next/navigation';
import { Suspense } from 'react';
import useSWR from 'swr';
import { orderApi, restaurantApi } from '@/lib/api';
import { LoadingPage } from '@/components/ui/loading-states';
import { ErrorState } from '@/components/ui/error-states';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Clock, Banknote, CreditCard, QrCode, Home } from 'lucide-react';
import { PaymentMethodBadge, PaymentStatusBadge } from '@/components/ui/status-badge';
import Link from 'next/link';

function OrderSuccessContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const orderId = searchParams.get('orderId');
  const orderNumber = searchParams.get('orderNumber');

  // Get restaurant for context
  const { data: restaurantData } = useSWR(
    slug ? `/restaurant/${slug}` : null,
    () => restaurantApi.getBySlug(slug),
    { revalidateOnFocus: false }
  );

  // Poll for order status updates using public endpoint
  const { data: orderData, error, isLoading } = useSWR(
    orderId && slug ? `/public/order/${slug}/${orderId}` : null,
    async () => {
      const { publicService } = await import('@/lib/api-service');
      try {
        return await publicService.getOrderStatus(slug, orderId!);
      } catch (err) {
        // If getOrderStatus fails, try getOrderDetail
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/api/public/r/${slug}/order/${orderId}/`
        );
        if (!response.ok) throw new Error('Order not found');
        return response.json();
      }
    },
    { refreshInterval: 5000 } // Poll every 5 seconds
  );

  const restaurant = restaurantData?.data;
  const order = orderData;

  if (isLoading) {
    return <LoadingPage message="Loading order details..." />;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <ErrorState
          title="Order Not Found"
          message="We couldn't find your order. Please check with the staff."
        />
      </div>
    );
  }

  // Even without full order data, show success with order number
  const displayOrderNumber = order?.order_number || order?.daily_order_number || orderNumber || 'N/A';
  const isCashPayment = order?.payment_method === 'cash' || searchParams.get('paymentMethod') === 'cash';
  const hasQrCode = order?.qr_code_url && !isCashPayment;

  return (
    <main className="flex min-h-screen flex-col bg-background">
      {/* Success Header */}
      <div className="bg-success/10 px-4 py-8 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-success">
          <CheckCircle2 className="h-8 w-8 text-success-foreground" />
        </div>
        <h1 className="text-2xl font-bold text-foreground">Order Placed!</h1>
        <p className="mt-2 text-muted-foreground">
          {restaurant?.name || 'The restaurant'} is preparing your order
        </p>
      </div>

      {/* Order Number - VERY PROMINENT */}
      <div className="mx-auto -mt-4 w-full max-w-md px-4">
        <Card className="border-2 border-primary bg-card shadow-lg">
          <CardContent className="p-6 text-center">
            <p className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
              Order Number
            </p>
            <p className="mt-2 text-6xl font-black tracking-tight text-primary">
              {displayOrderNumber}
            </p>
            <p className="mt-3 text-sm text-muted-foreground">
              Show this to staff when collecting your order
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Order Details */}
      <div className="mx-auto w-full max-w-md px-4 py-6 space-y-4">
        {/* QR Code (if applicable) */}
        {hasQrCode && (
          <Card>
            <CardContent className="p-6 text-center">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                <QrCode className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="font-medium text-foreground">Quick Pickup QR</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Staff can scan this for faster service
              </p>
              <div className="mt-4 flex justify-center">
                <img
                  src={order.qr_code_url || '/placeholder.svg'}
                  alt="Order QR Code"
                  className="h-40 w-40 rounded-lg border border-border"
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Payment Info */}
        <Card>
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {isCashPayment ? (
                  <Banknote className="h-5 w-5 text-muted-foreground" />
                ) : (
                  <CreditCard className="h-5 w-5 text-muted-foreground" />
                )}
                <span className="text-sm text-muted-foreground">Payment</span>
              </div>
              <div className="flex items-center gap-2">
                <PaymentMethodBadge method={order?.payment_method || (isCashPayment ? 'cash' : 'upi')} />
                {order?.payment_status && (
                  <PaymentStatusBadge status={order.payment_status} />
                )}
              </div>
            </div>
            
            {isCashPayment && (
              <div className="rounded-lg bg-warning/10 p-3">
                <p className="text-sm font-medium text-warning-foreground">
                  Please pay {order?.total || order?.total_amount ? `$${(order.total || order.total_amount).toFixed(2)}` : ''} at the counter
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Status */}
        {order?.status && (
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-info/10">
                  <Clock className="h-5 w-5 text-info" />
                </div>
                <div>
                  <p className="font-medium text-foreground">
                    {order.status === 'pending' && 'Order Received'}
                    {order.status === 'preparing' && 'Being Prepared'}
                    {order.status === 'completed' && 'Order Complete'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {order.status === 'pending' && 'The kitchen has received your order'}
                    {order.status === 'preparing' && 'Your food is being prepared'}
                    {order.status === 'completed' && 'Thank you for your order!'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Order Items Summary */}
        {order?.items && order.items.length > 0 && (
          <Card>
            <CardContent className="p-4">
              <p className="mb-3 text-sm font-medium text-muted-foreground">Order Summary</p>
              <div className="space-y-2">
                {order.items.map((item) => (
                  <div key={item.id} className="flex justify-between text-sm">
                    <span className="text-foreground">
                      {item.quantity}x {item.menu_item_name}
                    </span>
                    <span className="text-muted-foreground">
                      ${((item.total_price || item.subtotal || 0)).toFixed(2)}
                    </span>
                  </div>
                ))}
                <div className="border-t border-border pt-2 mt-2">
                  <div className="flex justify-between font-medium">
                    <span>Total</span>
                    <span>${(order.total || order.total_amount || 0).toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Back to Menu */}
        <Button
          asChild
          variant="outline"
          className="h-12 w-full bg-transparent"
        >
          <Link href={`/r/${slug}`}>
            <Home className="mr-2 h-4 w-4" />
            Back to Menu
          </Link>
        </Button>
      </div>
    </main>
  );
}

export default function OrderSuccessPage() {
  return (
    <Suspense fallback={<LoadingPage message="Loading..." />}>
      <OrderSuccessContent />
    </Suspense>
  );
}
