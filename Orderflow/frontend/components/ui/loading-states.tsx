'use client';

import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ size = 'md', className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-10 w-10',
  };

  return (
    <Loader2 className={cn('animate-spin text-primary', sizeClasses[size], className)} />
  );
}

interface PageLoaderProps {
  message?: string;
}

export function PageLoader({ message = 'Loading...' }: PageLoaderProps) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background">
      <LoadingSpinner size="lg" />
      <p className="text-lg font-medium text-muted-foreground">{message}</p>
    </div>
  );
}

export function LoadingCard() {
  return (
    <div className="flex h-48 items-center justify-center rounded-lg border border-border bg-card">
      <LoadingSpinner />
    </div>
  );
}

export function LoadingOverlay({ message }: { message?: string }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-4">
        <LoadingSpinner size="lg" />
        {message && <p className="text-lg font-medium text-foreground">{message}</p>}
      </div>
    </div>
  );
}

// Skeleton components for loading states
export function CardSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="space-y-3">
        <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
        <div className="h-3 w-full animate-pulse rounded bg-muted" />
        <div className="h-3 w-4/5 animate-pulse rounded bg-muted" />
      </div>
    </div>
  );
}

export function SkeletonOrderCard() {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <div className="h-8 w-16 animate-pulse rounded bg-muted" />
          <div className="h-4 w-24 animate-pulse rounded bg-muted" />
        </div>
        <div className="h-6 w-16 animate-pulse rounded-full bg-muted" />
      </div>
      <div className="mt-4 space-y-2">
        <div className="h-3 w-full animate-pulse rounded bg-muted" />
        <div className="h-3 w-3/4 animate-pulse rounded bg-muted" />
      </div>
      <div className="mt-4 flex justify-end">
        <div className="h-10 w-24 animate-pulse rounded bg-muted" />
      </div>
    </div>
  );
}

export function SkeletonMenuCard() {
  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <div className="h-32 animate-pulse bg-muted" />
      <div className="p-4 space-y-2">
        <div className="h-5 w-3/4 animate-pulse rounded bg-muted" />
        <div className="h-4 w-full animate-pulse rounded bg-muted" />
        <div className="h-6 w-1/3 animate-pulse rounded bg-muted" />
      </div>
    </div>
  );
}

// Aliases for backward compatibility
export function LoadingPage({ message = 'Loading...' }: { message?: string }) {
  return <PageLoader message={message} />;
}

export function SkeletonCard() {
  return <CardSkeleton />;
}
