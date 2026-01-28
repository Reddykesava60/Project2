'use client'

import { useEffect, useState } from 'react'
import { AppLayout } from '@/components/layout/app-layout'
import { withAuth } from '@/components/auth/with-auth'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { BillingInfo } from '@/types'
import { formatCurrency, formatDate } from '@/lib/utils'
import { DollarSign, TrendingUp, CreditCard } from 'lucide-react'

function BillingPage() {
  const [billingData, setBillingData] = useState<BillingInfo[]>([])
  const [stats, setStats] = useState({
    totalRevenue: 0,
    activeSubscriptions: 0,
    pendingPayments: 0,
  })

  useEffect(() => {
    // Fetch billing data from API
    setBillingData([
      {
        restaurantId: 'rest-1',
        planId: 'plan-1',
        planName: 'Professional',
        status: 'ACTIVE',
        currentPeriodStart: '2026-01-01T00:00:00Z',
        currentPeriodEnd: '2026-02-01T00:00:00Z',
        ordersThisMonth: 234,
        amount: 299,
      },
      {
        restaurantId: 'rest-2',
        planId: 'plan-2',
        planName: 'Enterprise',
        status: 'ACTIVE',
        currentPeriodStart: '2026-01-01T00:00:00Z',
        currentPeriodEnd: '2026-02-01T00:00:00Z',
        ordersThisMonth: 567,
        amount: 599,
      },
    ])

    setStats({
      totalRevenue: 125430,
      activeSubscriptions: 42,
      pendingPayments: 2,
    })
  }, [])

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'destructive' | 'secondary'> = {
      ACTIVE: 'success',
      SUSPENDED: 'destructive',
      CANCELLED: 'secondary',
    }
    return <Badge variant={variants[status]}>{status}</Badge>
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Billing & Revenue</h1>
          <p className="text-muted-foreground mt-1">
            Platform subscription and payment management
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
              <DollarSign className="w-5 h-5 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(stats.totalRevenue)}</div>
              <p className="text-xs text-muted-foreground mt-1">This month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Subscriptions</CardTitle>
              <TrendingUp className="w-5 h-5 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.activeSubscriptions}</div>
              <p className="text-xs text-muted-foreground mt-1">Restaurants</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Payments</CardTitle>
              <CreditCard className="w-5 h-5 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.pendingPayments}</div>
              <p className="text-xs text-muted-foreground mt-1">Requires attention</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Restaurant Subscriptions</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Restaurant ID</TableHead>
                  <TableHead>Plan</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Orders This Month</TableHead>
                  <TableHead>Period</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {billingData.map((billing) => (
                  <TableRow key={billing.restaurantId}>
                    <TableCell className="font-mono text-sm">
                      {billing.restaurantId}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{billing.planName}</Badge>
                    </TableCell>
                    <TableCell>{getStatusBadge(billing.status)}</TableCell>
                    <TableCell>{billing.ordersThisMonth}</TableCell>
                    <TableCell className="text-sm">
                      {formatDate(billing.currentPeriodStart)} -{' '}
                      {formatDate(billing.currentPeriodEnd)}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(billing.amount)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}

export default withAuth(BillingPage, ['PLATFORM_ADMIN'])
