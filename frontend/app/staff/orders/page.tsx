'use client';

import { useState, useEffect } from 'react';
import useSWR from 'swr';
import { useAuth } from '@/contexts/auth-context';
import { orderApi } from '@/lib/api';
import type { Order } from '@/lib/types';
import { OrderCard } from '@/components/staff/order-card';
import { SkeletonOrderCard } from '@/components/ui/loading-states';
import { ErrorState, EmptyState } from '@/components/ui/error-states';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RefreshCw, Search, ClipboardList, Bell } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function StaffOrdersPage() {
  const { user } = useAuth();
  const restaurantId = (user as any)?.restaurant_id;

  const [searchQuery, setSearchQuery] = useState('');
  const [paymentFilter, setPaymentFilter] = useState<string>('all');
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [timeSort, setTimeSort] = useState<'newest' | 'oldest'>('oldest');
  const [newOrderAlert, setNewOrderAlert] = useState(false);
  const [previousOrderCount, setPreviousOrderCount] = useState<number | null>(null);

  const {
    data: ordersData,
    error,
    isLoading,
    mutate,
  } = useSWR(
    restaurantId ? `/staff/orders/${restaurantId}` : null,
    () => orderApi.getActive(restaurantId!),
    { refreshInterval: 5000 } // Poll every 5 seconds per PRD
  );

  const orders = ordersData?.data || [];

  // Extract unique items from active orders for filtering
  const allAvailableItems = Array.from(
    new Set(orders.flatMap((o) => o.items.map((i) => i.menu_item_name)))
  ).sort();

  // New order detection
  useEffect(() => {
    if (previousOrderCount !== null && orders.length > previousOrderCount) {
      setNewOrderAlert(true);
      // Auto-dismiss after 5 seconds
      const timer = setTimeout(() => setNewOrderAlert(false), 5000);
      return () => clearTimeout(timer);
    }
    setPreviousOrderCount(orders.length);
  }, [orders.length, previousOrderCount]);

  const toggleItemFilter = (itemName: string) => {
    setSelectedItems((prev) =>
      prev.includes(itemName)
        ? prev.filter((i) => i !== itemName)
        : [...prev, itemName]
    );
  };

  // Filter orders based on search, payment status, and selected items
  const filteredOrders = orders.filter((order) => {
    const matchesSearch =
      searchQuery === '' ||
      (order.daily_order_number || order.order_number || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.customer_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.items.some((item) =>
        item.menu_item_name.toLowerCase().includes(searchQuery.toLowerCase())
      );

    const matchesPayment =
      paymentFilter === 'all' || order.payment_status === paymentFilter;

    const matchesItems =
      selectedItems.length === 0 ||
      selectedItems.every((selectedItem) =>
        order.items.some((item) => item.menu_item_name === selectedItem)
      );

    return matchesSearch && matchesPayment && matchesItems;
  });

  // Sort by creation time (respecting timeSort) and status priority
  const sortedOrders = [...filteredOrders].sort((a, b) => {
    // 1. Status Priority: Ready orders first, then Preparing, then Pending
    const statusOrder = { ready: 0, preparing: 1, pending: 2 };
    const statusDiff = (statusOrder[a.status as keyof typeof statusOrder] || 3) -
      (statusOrder[b.status as keyof typeof statusOrder] || 3);

    if (statusDiff !== 0) return statusDiff;

    // 2. Time Sorting: Within same status, sort by creation time
    const timeA = new Date(a.created_at).getTime();
    const timeB = new Date(b.created_at).getTime();

    return timeSort === 'newest' ? timeB - timeA : timeA - timeB;
  });

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
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-black text-foreground tracking-tight">Active Orders</h1>
            <div className="flex items-center gap-1.5 bg-muted/50 px-2 py-1 rounded-full border border-border">
              <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground whitespace-nowrap">Live</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setTimeSort(prev => prev === 'newest' ? 'oldest' : 'newest')}
              className="h-9 px-3 gap-2 font-bold"
            >
              <RefreshCw className={cn("h-4 w-4 transition-transform duration-500", timeSort === 'newest' && "rotate-180")} />
              <span className="text-xs uppercase">{timeSort === 'newest' ? 'Newest' : 'Oldest'} First</span>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => mutate()}
              className="min-h-[40px] min-w-[40px] rounded-full hover:bg-primary/10 hover:text-primary transition-colors"
            >
              <RefreshCw className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* New Order Alert */}
        {newOrderAlert && (
          <div className="flex items-center gap-2 bg-primary px-4 py-2 text-primary-foreground">
            <Bell className="h-4 w-4" />
            <span className="text-sm font-medium">New order received!</span>
          </div>
        )}

        {/* Filters */}
        <div className="space-y-3 px-4 pb-3">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search orders..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-11 pl-9"
              />
            </div>
            <Select value={paymentFilter} onValueChange={setPaymentFilter}>
              <SelectTrigger className="h-11 w-[130px]">
                <SelectValue placeholder="Payment" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                {/* Backend exposes payment_status='success' for paid orders */}
                <SelectItem value="success">Paid</SelectItem>
                <SelectItem value="pending">Unpaid</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Item Quick Filters */}
          {allAvailableItems.length > 0 && (
            <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
              <span className="text-xs font-semibold text-muted-foreground whitespace-nowrap uppercase tracking-wider">Filter Items:</span>
              {allAvailableItems.map((item) => (
                <Button
                  key={item}
                  variant={selectedItems.includes(item) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => toggleItemFilter(item)}
                  className={cn(
                    "flex-shrink-0 h-8 px-3 rounded-full text-xs font-medium transition-all",
                    selectedItems.includes(item)
                      ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
                      : "hover:bg-primary/5 hover:text-primary hover:border-primary/30"
                  )}
                >
                  {item}
                </Button>
              ))}
            </div>
          )}
        </div>
      </header>

      {/* Orders List */}
      <div className="p-4 space-y-4">
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
            title="No Active Orders"
            message={
              searchQuery || paymentFilter !== 'all' || selectedItems.length > 0
                ? 'No orders match your filters.'
                : 'New orders will appear here automatically.'
            }
          />
        ) : (
          sortedOrders.map((order) => (
            <OrderCard
              key={order.id}
              order={order}
              onComplete={() => mutate()}
              canCollectCash={user?.can_collect_cash || false}
            />
          ))
        )}
      </div>
    </main>
  );
}
