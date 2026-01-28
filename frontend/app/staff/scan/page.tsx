'use client';

import React from "react"

import { useState, useRef, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { orderApi } from '@/lib/api';
import type { Order } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/loading-states';
import { ErrorState } from '@/components/ui/error-states';
import { QrCode, Camera, Hash, AlertCircle, CheckCircle, X } from 'lucide-react';

export default function StaffScanPage() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const restaurantId = user?.restaurant_id;

  const [mode, setMode] = useState<'camera' | 'manual'>('camera');
  const [orderNumber, setOrderNumber] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [foundOrder, setFoundOrder] = useState<Order | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Initialize camera
  const startCamera = useCallback(async () => {
    setCameraError(null);
    setIsScanning(true);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      });
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      // Start QR scanning with zxing
      const { BrowserMultiFormatReader } = await import('@zxing/library');
      const codeReader = new BrowserMultiFormatReader();

      const scan = async () => {
        if (!videoRef.current || !streamRef.current) return;

        try {
          const result = await codeReader.decodeOnceFromVideoDevice(
            undefined,
            videoRef.current
          );
          if (result) {
            handleQrResult(result.getText());
          }
        } catch {
          // Continue scanning
          if (streamRef.current) {
            requestAnimationFrame(scan);
          }
        }
      };

      scan();
    } catch (err) {
      setCameraError('Unable to access camera. Please use manual entry.');
      setMode('manual');
    }
  }, []);

  // Stop camera
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsScanning(false);
  }, []);

  // Handle scanned QR result
  const handleQrResult = async (qrData: string) => {
    stopCamera();
    setIsSearching(true);
    setError(null);

    const response = await orderApi.getByQrCode(qrData);

    if (!response.success || !response.data) {
      setError('Order not found. Try manual entry.');
      setIsSearching(false);
      return;
    }

    setFoundOrder(response.data);
    setIsSearching(false);
  };

  // Manual order number search
  const handleManualSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orderNumber.trim() || !restaurantId) return;

    setIsSearching(true);
    setError(null);
    setFoundOrder(null);

    const response = await orderApi.getByNumber(restaurantId, orderNumber.trim().toUpperCase());

    if (!response.success || !response.data) {
      setError('Order not found. Check the number and try again.');
      setIsSearching(false);
      return;
    }

    setFoundOrder(response.data);
    setIsSearching(false);
  };

  // Cleanup camera on unmount
  useEffect(() => {
    return () => stopCamera();
  }, [stopCamera]);

  // Start camera when in camera mode
  useEffect(() => {
    if (mode === 'camera' && !foundOrder) {
      startCamera();
    } else {
      stopCamera();
    }
  }, [mode, foundOrder, startCamera, stopCamera]);

  const resetSearch = () => {
    setFoundOrder(null);
    setError(null);
    setOrderNumber('');
    if (mode === 'camera') {
      startCamera();
    }
  };

  if (!restaurantId) {
    return (
      <div className="p-4">
        <ErrorState
          title="No Restaurant"
          message="You are not assigned to a restaurant."
        />
      </div>
    );
  }

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-background">
        <div className="px-4 py-3">
          <h1 className="text-xl font-bold text-foreground">Find Order</h1>
        </div>

        {/* Mode Toggle */}
        <div className="flex border-b border-border">
          <button
            type="button"
            onClick={() => setMode('camera')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              mode === 'camera'
                ? 'border-b-2 border-primary text-primary'
                : 'text-muted-foreground'
            }`}
          >
            <Camera className="mx-auto mb-1 h-5 w-5" />
            Scan QR
          </button>
          <button
            type="button"
            onClick={() => setMode('manual')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              mode === 'manual'
                ? 'border-b-2 border-primary text-primary'
                : 'text-muted-foreground'
            }`}
          >
            <Hash className="mx-auto mb-1 h-5 w-5" />
            Order Number
          </button>
        </div>
      </header>

      <div className="p-4">
        {/* Found Order Display */}
        {foundOrder ? (
          <Card className="border-2 border-success">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-success">
                  <CheckCircle className="h-5 w-5" />
                  <span className="font-medium">Order Found</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetSearch}
                  className="min-h-[44px] min-w-[44px]"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <p className="text-5xl font-black text-primary">
                  {foundOrder.daily_order_number || foundOrder.order_number}
                </p>
                <p className="mt-1 text-lg font-medium text-foreground">
                  {foundOrder.customer_name}
                </p>
              </div>

              <div className="space-y-2 rounded-lg bg-muted p-3">
                {foundOrder.items.map((item) => (
                  <div key={item.id} className="flex justify-between text-sm">
                    <span>
                      {item.quantity}x {item.menu_item_name}
                    </span>
                    <span>${item.total_price.toFixed(2)}</span>
                  </div>
                ))}
                <div className="border-t border-border pt-2 mt-2 flex justify-between font-semibold">
                  <span>Total</span>
                  <span>${foundOrder.total.toFixed(2)}</span>
                </div>
              </div>

              <Button
                onClick={() => router.push('/staff/orders')}
                className="h-12 w-full text-base font-semibold"
              >
                View in Orders
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Error Display */}
            {error && (
              <div className="mb-4 flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>{error}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetSearch}
                  className="ml-auto"
                >
                  Try Again
                </Button>
              </div>
            )}

            {/* Camera Mode */}
            {mode === 'camera' && (
              <div className="space-y-4">
                {cameraError ? (
                  <Card>
                    <CardContent className="py-8 text-center">
                      <QrCode className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                      <p className="text-muted-foreground">{cameraError}</p>
                      <Button
                        onClick={() => setMode('manual')}
                        variant="outline"
                        className="mt-4"
                      >
                        Use Manual Entry
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <>
                    <div className="relative aspect-square overflow-hidden rounded-lg bg-muted">
                      <video
                        ref={videoRef}
                        className="h-full w-full object-cover"
                        playsInline
                        muted
                      />
                      {isSearching && (
                        <div className="absolute inset-0 flex items-center justify-center bg-background/80">
                          <LoadingSpinner size="lg" />
                        </div>
                      )}
                      {/* Scanning overlay */}
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="h-48 w-48 rounded-lg border-2 border-primary/50" />
                      </div>
                    </div>
                    <p className="text-center text-sm text-muted-foreground">
                      Point the camera at the order QR code
                    </p>
                  </>
                )}
              </div>
            )}

            {/* Manual Mode */}
            {mode === 'manual' && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Enter Order Number</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleManualSearch} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="orderNumber">Order Number</Label>
                      <Input
                        id="orderNumber"
                        placeholder="e.g. A23"
                        value={orderNumber}
                        onChange={(e) => setOrderNumber(e.target.value.toUpperCase())}
                        className="h-14 text-2xl font-bold text-center uppercase"
                        disabled={isSearching}
                        autoFocus
                      />
                    </div>
                    <Button
                      type="submit"
                      className="h-12 w-full text-base font-semibold"
                      disabled={isSearching || !orderNumber.trim()}
                    >
                      {isSearching ? (
                        <>
                          <LoadingSpinner size="sm" className="mr-2" />
                          Searching...
                        </>
                      ) : (
                        'Find Order'
                      )}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </main>
  );
}
