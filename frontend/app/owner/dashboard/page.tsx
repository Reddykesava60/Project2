'use client';

import useSWR from 'swr';
import { useAuthStore } from '@/lib/store';
import { analyticsApi, orderApi } from '@/lib/api';
import type { DashboardStats } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { SkeletonCard } from '@/components/ui/loading-states';
import { ErrorState } from '@/components/ui/error-states';
import {
  DollarSign,
  ShoppingCart,
  Clock,
  CreditCard,
  Banknote,
  TrendingUp,
  RefreshCw,
} from 'lucide-react';
import Link from 'next/link';

export default function OwnerDashboardPage() {
  const user = useAuthStore((state) => state.user);
  const restaurantId = user?.restaurant_id;

  const {
    data: statsData,
    error,
    isLoading,
    mutate,
  } = useSWR(
    restaurantId ? `/analytics/dashboard/${restaurantId}` : null,
    () => analyticsApi.getDashboard(restaurantId!),
    { refreshInterval: 30000 } // Refresh every 30 seconds
  );

  const stats = statsData?.data;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
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
        <div className="flex items-center justify-between px-4 py-4 lg:px-6">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
            <p className="text-sm text-muted-foreground">Today&apos;s Overview</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => mutate()}
            className="min-h-[44px]"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </header>

      <div className="p-4 lg:p-6 space-y-6">
        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : error || !statsData?.success ? (
          <ErrorState
            title="Failed to Load Dashboard"
            message="Unable to fetch analytics data."
            onRetry={() => mutate()}
          />
        ) : stats ? (
          <>
            {/* Stats Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {/* Today's Orders */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Today&apos;s Orders
                  </CardTitle>
                  <ShoppingCart className="h-5 w-5 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-foreground">{stats.today_orders}</p>
                  <p className="mt-1 text-sm text-muted-foreground">orders placed today</p>
                </CardContent>
              </Card>

              {/* Today's Revenue */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Today&apos;s Revenue
                  </CardTitle>
                  <DollarSign className="h-5 w-5 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-foreground">
                    {formatCurrency(stats.today_revenue)}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">total revenue</p>
                </CardContent>
              </Card>

              {/* Cash Revenue */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Cash Payments
                  </CardTitle>
                  <Banknote className="h-5 w-5 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-foreground">
                    {formatCurrency(stats.cash_revenue)}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {stats.today_revenue > 0
                      ? `${Math.round((stats.cash_revenue / stats.today_revenue) * 100)}% of total`
                      : 'no sales yet'}
                  </p>
                </CardContent>
              </Card>

              {/* Online Revenue */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Online Payments
                  </CardTitle>
                  <CreditCard className="h-5 w-5 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-foreground">
                    {formatCurrency(stats.online_revenue)}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {stats.today_revenue > 0
                      ? `${Math.round((stats.online_revenue / stats.today_revenue) * 100)}% of total`
                      : 'no sales yet'}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Pending Orders Alert */}
            {stats.pending_orders > 0 && (
              <Card className="border-warning bg-warning/5">
                <CardContent className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-warning">
                      <Clock className="h-5 w-5 text-warning-foreground" />
                    </div>
                    <div>
                      <p className="font-semibold text-foreground">
                        {stats.pending_orders} Pending Order{stats.pending_orders !== 1 && 's'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Orders waiting to be completed
                      </p>
                    </div>
                  </div>
                  <Button asChild>
                    <Link href="/owner/orders">View Orders</Link>
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Quick Actions */}
            <div className="grid gap-4 md:grid-cols-3">
              <Card className="cursor-pointer transition-shadow hover:shadow-md">
                <Link href="/owner/orders" className="block">
                  <CardContent className="flex items-center gap-4 p-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                      <ShoppingCart className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold text-foreground">View Orders</p>
                      <p className="text-sm text-muted-foreground">Manage active orders</p>
                    </div>
                  </CardContent>
                </Link>
              </Card>

              <Card className="cursor-pointer transition-shadow hover:shadow-md">
                <Link href="/owner/menu" className="block">
                  <CardContent className="flex items-center gap-4 p-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                      <TrendingUp className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold text-foreground">Menu Management</p>
                      <p className="text-sm text-muted-foreground">Edit items & categories</p>
                    </div>
                  </CardContent>
                </Link>
              </Card>

              <Card className="cursor-pointer transition-shadow hover:shadow-md">
                <Link href="/owner/staff" className="block">
                  <CardContent className="flex items-center gap-4 p-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                      <DollarSign className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold text-foreground">Staff Management</p>
                      <p className="text-sm text-muted-foreground">Manage permissions</p>
                    </div>
                  </CardContent>
                </Link>
              </Card>
            </div>
          </>
        ) : null}
      </div>
    </main>
  );
}
