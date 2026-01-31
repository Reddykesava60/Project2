'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { useAuthStore } from '@/lib/store';
import { qrApi, restaurantApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { LoadingSpinner, LoadingCard } from '@/components/ui/loading-states';
import { ErrorState } from '@/components/ui/error-states';
import { QrCode, Download, RefreshCw, AlertTriangle, ExternalLink } from 'lucide-react';

export default function OwnerQRPage() {
  const user = useAuthStore((state) => state.user);
  const restaurantId = user?.restaurant_id;

  const [showRegenerate, setShowRegenerate] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Get restaurant info for the menu URL
  const { data: restaurantData } = useSWR(
    restaurantId ? `/restaurant/${restaurantId}` : null,
    () => restaurantApi.getBySlug(user?.restaurant_id || '')
  );

  const {
    data: qrData,
    error,
    isLoading,
    mutate,
  } = useSWR(
    restaurantId ? `/qr/${restaurantId}` : null,
    () => qrApi.getRestaurantQr(restaurantId!)
  );

  const qrCodeUrl = qrData?.data?.qr_code_url;
  const restaurant = restaurantData?.data;
  const menuUrl = restaurant ? `${window.location.origin}/r/${restaurant.slug}` : '';

  const handleDownload = () => {
    if (!qrCodeUrl) return;
    
    const link = document.createElement('a');
    link.href = qrCodeUrl;
    link.download = `${restaurant?.name || 'restaurant'}-qr-code.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleRegenerate = async () => {
    if (!restaurantId) return;
    setIsRegenerating(true);

    const response = await qrApi.regenerateQr(restaurantId);

    setIsRegenerating(false);
    setShowRegenerate(false);

    if (!response.success) {
      alert(response.error || 'Failed to regenerate QR code');
      return;
    }

    mutate();
  };

  if (!restaurantId) {
    return (
      <div className="p-4 lg:p-6">
        <ErrorState title="No Restaurant" message="You are not assigned to a restaurant." />
      </div>
    );
  }

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-background">
        <div className="px-4 py-4 lg:px-6">
          <h1 className="text-2xl font-bold text-foreground">QR Code</h1>
          <p className="text-sm text-muted-foreground">
            Customers can scan this to view your menu
          </p>
        </div>
      </header>

      <div className="p-4 lg:p-6 max-w-2xl mx-auto">
        {isLoading ? (
          <LoadingCard />
        ) : error || !qrData?.success ? (
          <ErrorState
            title="Failed to Load QR Code"
            message="Unable to fetch your restaurant QR code."
            onRetry={() => mutate()}
          />
        ) : (
          <div className="space-y-6">
            {/* QR Code Display */}
            <Card>
              <CardHeader className="text-center">
                <CardTitle>Your Restaurant QR Code</CardTitle>
                <CardDescription>
                  Print this and display it at tables for customers to scan
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col items-center">
                {qrCodeUrl ? (
                  <div className="rounded-lg border-4 border-foreground bg-white p-4">
                    <img
                      src={qrCodeUrl || "/placeholder.svg"}
                      alt="Restaurant QR Code"
                      className="h-64 w-64"
                    />
                  </div>
                ) : (
                  <div className="flex h-64 w-64 items-center justify-center rounded-lg border-2 border-dashed border-border bg-muted">
                    <QrCode className="h-16 w-16 text-muted-foreground" />
                  </div>
                )}

                {/* Menu URL */}
                {menuUrl && (
                  <div className="mt-4 text-center">
                    <p className="text-sm text-muted-foreground">Direct link to your menu:</p>
                    <a
                      href={menuUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-1 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                    >
                      {menuUrl}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                )}

                {/* Actions */}
                <div className="mt-6 flex flex-col gap-3 w-full max-w-xs">
                  <Button
                    onClick={handleDownload}
                    disabled={!qrCodeUrl}
                    className="h-12 w-full text-base"
                  >
                    <Download className="h-5 w-5 mr-2" />
                    Download QR Code
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Regenerate Section */}
            <Card className="border-destructive/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-destructive">
                  <AlertTriangle className="h-5 w-5" />
                  Danger Zone
                </CardTitle>
                <CardDescription>
                  Regenerating will invalidate all existing printed QR codes
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  variant="destructive"
                  onClick={() => setShowRegenerate(true)}
                  className="h-12"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Regenerate QR Code
                </Button>
              </CardContent>
            </Card>

            {/* Instructions */}
            <Card>
              <CardHeader>
                <CardTitle>How to Use</CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="space-y-3 text-sm text-muted-foreground list-decimal list-inside">
                  <li>Download the QR code image above</li>
                  <li>Print it on table tents, menus, or signs</li>
                  <li>Customers scan with their phone camera</li>
                  <li>They can browse your menu and place orders instantly</li>
                </ol>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* Regenerate Confirmation */}
      <AlertDialog open={showRegenerate} onOpenChange={setShowRegenerate}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Regenerate QR Code?
            </AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. All existing printed QR codes will stop
              working. You will need to print and distribute new QR codes.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isRegenerating} className="min-h-[44px]">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRegenerate}
              disabled={isRegenerating}
              className="min-h-[44px] bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isRegenerating ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Regenerating...
                </>
              ) : (
                'Yes, Regenerate'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </main>
  );
}
