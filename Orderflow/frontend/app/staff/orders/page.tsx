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
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RefreshCw, Search, ClipboardList, Bell, Banknote, ChefHat } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function StaffOrdersPage() {
  const { user } = useAuth();
  const restaurantId = (user as any)?.restaurant_id;
  const canCollectCash = (user as any)?.can_collect_cash || false;

  const [searchQuery, setSearchQuery] = useState('');
  const [timeSort, setTimeSort] = useState<'newest' | 'oldest'>('oldest');
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'collect-cash' | 'active'>('collect-cash');
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

  // New order detection
  useEffect(() => {
    if (previousOrderCount !== null && orders.length > previousOrderCount) {
      setNewOrderAlert(true);
      const timer = setTimeout(() => setNewOrderAlert(false), 5000);
      return () => clearTimeout(timer);
    }
    setPreviousOrderCount(orders.length);
  }, [orders.length, previousOrderCount]);

  // SEGMENTED LISTS for Super Staff (can_collect_cash=true)
  // 1. Collect Cash: pending + cash payment
  const collectCashOrders = orders.filter(
    (o) => o.status === 'pending' && o.payment_method === 'cash'
  );

  // 2. Active Orders: preparing status
  const activeOrders = orders.filter(
    (o) => o.status === 'preparing'
  );

  // For Normal Staff: only preparing orders
  const normalStaffOrders = orders.filter(
    (o) => o.status === 'preparing'
  );

  // Extract unique items from normal staff orders for item filtering
  const allAvailableItems = Array.from(
    new Set(normalStaffOrders.flatMap((o) => o.items.map((i) => i.menu_item_name)))
  ).sort();

  const toggleItemFilter = (itemName: string) => {
    setSelectedItems((prev) =>
      prev.includes(itemName)
        ? prev.filter((i) => i !== itemName)
        : [...prev, itemName]
    );
  };

  // Search filter function
  const filterBySearch = (orderList: Order[]) => {
    if (!searchQuery) return orderList;
    return orderList.filter((order) =>
      (order.daily_order_number || order.id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.customer_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.items.some((item) =>
        item.menu_item_name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    );
  };

  // Sort orders by time
  const sortOrders = (orderList: Order[]) => {
    return [...orderList].sort((a, b) => {
      const timeA = new Date(a.created_at).getTime();
      const timeB = new Date(b.created_at).getTime();
      return timeSort === 'newest' ? timeB - timeA : timeA - timeB;
    });
  };

  // Apply filters and sorting
  const filteredCollectCash = sortOrders(filterBySearch(collectCashOrders));
  const filteredActiveOrders = sortOrders(filterBySearch(activeOrders));

  // Normal staff: apply item filter + search
  const filteredNormalStaff = sortOrders(
    filterBySearch(normalStaffOrders).filter((order) =>
      selectedItems.length === 0 ||
      selectedItems.some((selectedItem) =>
        order.items.some((item) => item.menu_item_name === selectedItem)
      )
    )
  );

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

  // Section component for order lists
  const OrderSection = ({
    title,
    icon: Icon,
    orders: sectionOrders,
    emptyMessage,
    badgeColor = 'bg-primary'
  }: {
    title: string;
    icon: React.ElementType;
    orders: Order[];
    emptyMessage: string;
    badgeColor?: string;
  }) => (
    <section className="mb-6">
      <div className="flex items-center gap-2 mb-3 px-1">
        <Icon className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-lg font-bold text-foreground">{title}</h2>
        <span className={cn(
          "px-2 py-0.5 rounded-full text-xs font-bold text-white",
          badgeColor
        )}>
          {sectionOrders.length}
        </span>
      </div>
      {sectionOrders.length === 0 ? (
        <div className="bg-muted/30 rounded-lg p-6 text-center border border-dashed border-border">
          <p className="text-sm text-muted-foreground">{emptyMessage}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sectionOrders.map((order) => (
            <OrderCard
              key={order.id}
              order={order}
              onComplete={() => mutate()}
              canCollectCash={canCollectCash}
            />
          ))}
        </div>
      )}
    </section>
  );

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-background">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-xl font-black text-foreground tracking-tight">
                {user?.name || 'Staff Dashboard'}
              </h1>
              <div className="flex items-center gap-1.5">
                <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
                <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                  {canCollectCash ? 'Super Staff Access' : 'Active Orders'}
                </span>
              </div>
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

        {/* Tabs for Super Staff */}
        {canCollectCash && (
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'collect-cash' | 'active')}>
            <TabsList className="mx-4 mb-3 grid w-auto grid-cols-2">
              <TabsTrigger value="collect-cash" className="min-h-[44px] gap-2">
                <Banknote className="h-4 w-4" />
                Collect Cash ({collectCashOrders.length})
              </TabsTrigger>
              <TabsTrigger value="active" className="min-h-[44px] gap-2">
                <ChefHat className="h-4 w-4" />
                Active ({activeOrders.length})
              </TabsTrigger>
            </TabsList>
          </Tabs>
        )}

        {/* Search */}
        <div className="px-4 pb-3">
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

        {/* Item Quick Filters - Only for Normal Staff */}
        {!canCollectCash && allAvailableItems.length > 0 && (
          <div className="px-4 pb-3">
            <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
              <span className="text-xs font-semibold text-muted-foreground whitespace-nowrap uppercase tracking-wider">Filter:</span>
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
              {selectedItems.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedItems([])}
                  className="flex-shrink-0 h-8 px-3 rounded-full text-xs font-medium text-muted-foreground hover:text-foreground"
                >
                  Clear
                </Button>
              )}
            </div>
          </div>
        )}
      </header>

      {/* Orders Content */}
      <div className="p-4">
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
        ) : canCollectCash ? (
          /* SUPER STAFF VIEW - Tabbed Navigation */
          activeTab === 'collect-cash' ? (
            /* Collect Cash Tab */
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
          ) : (
            /* Active Orders Tab */
            filteredActiveOrders.length === 0 ? (
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
                {filteredActiveOrders.map((order) => (
                  <OrderCard
                    key={order.id}
                    order={order}
                    onComplete={() => mutate()}
                    canCollectCash={true}
                  />
                ))}
              </div>
            )
          )
        ) : (
          /* NORMAL STAFF VIEW - Only preparing orders */
          <>
            {filteredNormalStaff.length === 0 ? (
              <EmptyState
                icon={<ClipboardList className="h-8 w-8 text-muted-foreground" />}
                title="No Active Orders"
                message={
                  searchQuery || selectedItems.length > 0
                    ? 'No orders match your filters.'
                    : 'Orders being prepared will appear here.'
                }
              />
            ) : (
              <div className="space-y-3">
                {filteredNormalStaff.map((order) => (
                  <OrderCard
                    key={order.id}
                    order={order}
                    onComplete={() => mutate()}
                    canCollectCash={false}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}
