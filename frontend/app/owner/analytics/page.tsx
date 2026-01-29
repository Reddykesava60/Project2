'use client'

import useSWR from 'swr'
import { AppLayout } from '@/components/layout/app-layout'
import { withAuth } from '@/components/auth/with-auth'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { analyticsApi } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { ErrorState } from '@/components/ui/error-states'
import { SkeletonCard } from '@/components/ui/loading-states'

type RevenuePoint = { date: string; revenue: number }
type OrdersByHourPoint = { hour: string; orders: number }
type PaymentMethodPoint = { name: string; value: number; color: string }

const PAYMENT_COLORS: Record<string, string> = {
  cash: '#10b981',   // Backend uses lowercase
  upi: '#3b82f6',    // Backend uses 'upi' not 'ONLINE'
}

function AnalyticsPage() {
  const user = useAuthStore((state) => state.user)
  const restaurantId = user?.restaurant_id

  const { data, error, isLoading } = useSWR(
    restaurantId ? `/analytics/daily/${restaurantId}` : null,
    () => analyticsApi.getDaily(restaurantId!),
    { revalidateOnFocus: false }
  )

  const analytics = data?.data as any

  const revenueData: RevenuePoint[] =
    analytics?.daily_breakdown?.map((d: any) => ({
      date: d.date?.slice(5) ?? '',
      revenue: d.revenue ?? 0,
    })) ?? []

  const ordersByHour: OrdersByHourPoint[] =
    analytics?.hourly_breakdown?.map((h: any) => ({
      hour: h.hour ?? '',
      orders: h.orders ?? 0,
    })) ?? []

  const paymentMethods: PaymentMethodPoint[] =
    analytics?.payment_breakdown?.map((p: any) => ({
      name: p.method === 'cash' ? 'Cash' : 'UPI',  // Backend uses lowercase: cash/upi
      value: p.revenue ?? 0,
      color: PAYMENT_COLORS[p.method] ?? '#3b82f6',
    })) ?? []

  return (
    <AppLayout title="Analytics">
      <div className="space-y-4">
        {/* Mobile-optimized tabs */}
        <Tabs defaultValue="overview" className="space-y-4">
          <div className="scroll-container">
            <TabsList className="inline-flex w-auto min-w-full">
              <TabsTrigger value="overview" className="min-h-touch px-4">Overview</TabsTrigger>
              <TabsTrigger value="orders" className="min-h-touch px-4">Orders</TabsTrigger>
              <TabsTrigger value="revenue" className="min-h-touch px-4">Revenue</TabsTrigger>
              <TabsTrigger value="menu" className="min-h-touch px-4">Menu</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="overview" className="space-y-4">
            {isLoading ? (
              <div className="grid grid-cols-1 gap-4">
                <SkeletonCard />
                <SkeletonCard />
              </div>
            ) : error || !data?.success ? (
              <ErrorState
                title="Failed to Load Analytics"
                message="Unable to fetch analytics data."
              />
            ) : (
              <div className="grid grid-cols-1 gap-4">
                <Card className="mobile-card">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Revenue Trend (7 Days)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={revenueData}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                        <YAxis hide />
                        <Tooltip />
                        <Line type="monotone" dataKey="revenue" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card className="mobile-card">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">Payment Methods</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-around">
                      <ResponsiveContainer width={150} height={150}>
                        <PieChart>
                          <Pie
                            data={paymentMethods}
                            cx="50%"
                            cy="50%"
                            innerRadius={40}
                            outerRadius={60}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {paymentMethods.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="space-y-2">
                        {paymentMethods.map((method) => (
                          <div key={method.name} className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: method.color }} />
                            <span className="text-sm">
                              {method.name}: {method.value.toFixed(0)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          <TabsContent value="orders" className="space-y-4">
            <Card className="mobile-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Orders by Hour</CardTitle>
                <CardDescription className="text-xs">Peak ordering times</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={ordersByHour}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="hour" tick={{ fontSize: 10 }} interval={1} />
                    <YAxis hide />
                    <Tooltip />
                    <Bar dataKey="orders" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="revenue" className="space-y-3">
            {/* Revenue Summary Cards */}
            <div className="surface-card p-4 rounded-xl">
              <div className="text-sm text-muted-foreground mb-1">Today</div>
              <div className="text-3xl font-bold">$2,350</div>
              <div className="text-sm text-muted-foreground">45 orders</div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="surface-card p-4 rounded-xl">
                <div className="text-sm text-muted-foreground mb-1">This Week</div>
                <div className="text-xl font-bold">$18,456</div>
                <div className="text-xs text-green-600">+12% from last week</div>
              </div>
              <div className="surface-card p-4 rounded-xl">
                <div className="text-sm text-muted-foreground mb-1">This Month</div>
                <div className="text-xl font-bold">$67,890</div>
                <div className="text-xs text-green-600">+8% from last month</div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="menu" className="space-y-3">
            <h3 className="text-sm font-medium text-muted-foreground">Top Selling Items</h3>
            {[
              { name: 'Margherita Pizza', orders: 45, revenue: 675 },
              { name: 'Caesar Salad', orders: 32, revenue: 384 },
              { name: 'Pasta Carbonara', orders: 28, revenue: 392 },
            ].map((item, index) => (
              <div key={index} className="surface-card p-4 rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-bold">
                    #{index + 1}
                  </div>
                  <div>
                    <p className="font-medium">{item.name}</p>
                    <p className="text-sm text-muted-foreground">{item.orders} orders</p>
                  </div>
                </div>
                <div className="text-lg font-bold">${item.revenue}</div>
              </div>
            ))}
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  )
}

export default withAuth(AnalyticsPage, ['RESTAURANT_OWNER'])
