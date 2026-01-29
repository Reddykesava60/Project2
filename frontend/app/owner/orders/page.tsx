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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RefreshCw, Search, ClipboardList } from 'lucide-react';

export default function OwnerOrdersPage() {
  const user = useAuthStore((state) => state.user);
  const restaurantId = user?.restaurant_id;

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'active' | 'completed'>('active');

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

  // Separate active and completed orders (backend only has pending/preparing/completed)
  const activeOrders = orders.filter(
    (o) => o.status === 'pending' || o.status === 'preparing'
  );
  const completedOrders = orders.filter(
    (o) => o.status === 'completed'
  );

  const currentOrders = activeTab === 'active' ? activeOrders : completedOrders;

  // Filter orders
  const filteredOrders = currentOrders.filter((order) => {
    const matchesSearch =
      searchQuery === '' ||
      order.daily_order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.customer_name.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  // Sort orders
  const sortedOrders = [...filteredOrders].sort((a, b) => {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

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
              {activeOrders.length} active, {completedOrders.length} completed today
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
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'active' | 'completed')}>
          <TabsList className="mx-4 mb-3 grid w-auto grid-cols-2 lg:mx-6">
            <TabsTrigger value="active" className="min-h-[44px]">
              Active ({activeOrders.length})
            </TabsTrigger>
            <TabsTrigger value="completed" className="min-h-[44px]">
              Completed ({completedOrders.length})
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Filters */}
        <div className="flex gap-2 px-4 pb-3 lg:px-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search orders..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-11 pl-9"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="h-11 w-[130px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              {activeTab === 'active' ? (
                <>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="preparing">Preparing</SelectItem>
                </>
              ) : (
                <>
                  <SelectItem value="completed">Completed</SelectItem>
                </>
              )}
            </SelectContent>
          </Select>
        </div>
      </header>

      {/* Orders List */}
      <div className="p-4 lg:p-6 space-y-4">
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
        ) : sortedOrders.length === 0 ? (
          <EmptyState
            icon={<ClipboardList className="h-8 w-8 text-muted-foreground" />}
            title={activeTab === 'active' ? 'No Active Orders' : 'No Completed Orders'}
            message={
              searchQuery || statusFilter !== 'all'
                ? 'No orders match your filters.'
                : activeTab === 'active'
                  ? 'New orders will appear here.'
                  : 'Completed orders will appear here.'
            }
          />
        ) : (
          sortedOrders.map((order) => (
            <OrderCard
              key={order.id}
              order={order}
              onComplete={() => mutate()}
              canCollectCash={true} // Owners can always collect cash
            />
          ))
        )}
      </div>
    </main>
  );
}
