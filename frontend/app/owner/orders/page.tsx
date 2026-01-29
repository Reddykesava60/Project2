'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { useAuthStore } from '@/lib/store';
import { orderApi } from '@/lib/api';
import type { Order } from '@/lib/types';
import { OrderCard } from '@/components/staff/order-card';
import { SkeletonOrderCard } from '@/components/ui/loading-states';
import { ErrorState, EmptyState } from '@/components/ui/error-states';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RefreshCw, Search, Banknote, ChefHat, CheckCircle2 } from 'lucide-react';

export default function OwnerOrdersPage() {
  const user = useAuthStore((state) => state.user);
  const restaurantId = user?.restaurant_id;

  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'collect-cash' | 'active' | 'completed'>('collect-cash');

  const {
    data: ordersData,
    error,
    isLoading,
    mutate,
  } = useSWR(
    restaurantId ? `/owner/orders/${restaurantId}` : null,
    () => orderApi.getAll(restaurantId!),
    { refreshInterval: 5000 }
  );

  const ordersDataResponse = ordersData?.data;
  const orders = (Array.isArray(ordersDataResponse)
    ? ordersDataResponse
    : (ordersDataResponse as any)?.results || []) as Order[];

  // SEGMENTED LISTS FOR ACTIVE ORDERS
  // 1. Collect Cash: pending + cash payment
  const collectCashOrders = orders.filter(
    (o) => o.status === 'pending' && o.payment_method === 'cash'
  );
  
  // 2. Active Orders: preparing status
  const preparingOrders = orders.filter(
    (o) => o.status === 'preparing'
  );

  // Completed orders
  const completedOrders = orders.filter(
    (o) => o.status === 'completed'
  );

  // Total active count for tab badge
  const activeOrdersCount = collectCashOrders.length + preparingOrders.length;

  // Search filter function
  const filterBySearch = (orderList: Order[]) => {
    if (!searchQuery) return orderList;
    return orderList.filter((order) =>
      (order.daily_order_number || order.order_number || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.customer_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.items.some((item) =>
        item.menu_item_name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    );
  };

  // Sort orders by time (oldest first for active, newest first for completed)
  const sortOrders = (orderList: Order[], newestFirst = false) => {
    return [...orderList].sort((a, b) => {
      const timeA = new Date(a.created_at).getTime();
      const timeB = new Date(b.created_at).getTime();
      return newestFirst ? timeB - timeA : timeA - timeB;
    });
  };

  // Apply filters and sorting
  const filteredCollectCash = sortOrders(filterBySearch(collectCashOrders));
  const filteredPreparing = sortOrders(filterBySearch(preparingOrders));
  const filteredCompleted = sortOrders(filterBySearch(completedOrders), true);

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
            <h1 className="text-2xl font-bold text-foreground">Orders</h1>
            <p className="text-sm text-muted-foreground">
              {activeOrdersCount} active, {completedOrders.length} completed today
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => mutate()}
            className="min-h-[44px]"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'collect-cash' | 'active' | 'completed')}>
          <TabsList className="mx-4 mb-3 grid w-auto grid-cols-3 lg:mx-6">
            <TabsTrigger value="collect-cash" className="min-h-[44px] gap-1.5">
              <Banknote className="h-4 w-4" />
              <span className="hidden sm:inline">Collect</span> ({collectCashOrders.length})
            </TabsTrigger>
            <TabsTrigger value="active" className="min-h-[44px] gap-1.5">
              <ChefHat className="h-4 w-4" />
              <span className="hidden sm:inline">Active</span> ({preparingOrders.length})
            </TabsTrigger>
            <TabsTrigger value="completed" className="min-h-[44px] gap-1.5">
              <CheckCircle2 className="h-4 w-4" />
              <span className="hidden sm:inline">Done</span> ({completedOrders.length})
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Search */}
        <div className="px-4 pb-3 lg:px-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search orders..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-11 pl-9"
            />
          </div>
        </div>
      </header>

      {/* Orders Content */}
      <div className="p-4 lg:p-6">
        {isLoading ? (
          <>
            <SkeletonOrderCard />
            <SkeletonOrderCard />
            <SkeletonOrderCard />
          </>
        ) : error || !ordersData?.success ? (
          <ErrorState
            title="Failed to Load Orders"
            message="Unable to fetch orders. Please try again."
            onRetry={() => mutate()}
          />
        ) : activeTab === 'collect-cash' ? (
          /* COLLECT CASH TAB */
          filteredCollectCash.length === 0 ? (
            <EmptyState
              icon={<Banknote className="h-8 w-8 text-muted-foreground" />}
              title="No Pending Cash Orders"
              message={
                searchQuery
                  ? 'No orders match your search.'
                  : 'Cash orders awaiting collection will appear here.'
              }
            />
          ) : (
            <div className="space-y-3">
              {filteredCollectCash.map((order) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  onComplete={() => mutate()}
                  canCollectCash={true}
                />
              ))}
            </div>
          )
        ) : activeTab === 'active' ? (
          /* ACTIVE TAB */
          filteredPreparing.length === 0 ? (
            <EmptyState
              icon={<ChefHat className="h-8 w-8 text-muted-foreground" />}
              title="No Active Orders"
              message={
                searchQuery
                  ? 'No orders match your search.'
                  : 'Orders being prepared will appear here.'
              }
            />
          ) : (
            <div className="space-y-3">
              {filteredPreparing.map((order) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  onComplete={() => mutate()}
                  canCollectCash={true}
                />
              ))}
            </div>
          )
        ) : (
          /* COMPLETED TAB */
          filteredCompleted.length === 0 ? (
            <EmptyState
              icon={<CheckCircle2 className="h-8 w-8 text-muted-foreground" />}
              title="No Completed Orders"
              message={
                searchQuery
                  ? 'No orders match your search.'
                  : 'Completed orders will appear here.'
              }
            />
          ) : (
            <div className="space-y-3">
              {filteredCompleted.map((order) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  onComplete={() => mutate()}
                  canCollectCash={true}
                />
              ))}
            </div>
          )
        )}
      </div>
    </main>
  );
}
