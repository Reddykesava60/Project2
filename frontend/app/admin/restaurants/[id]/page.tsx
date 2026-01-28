'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { AppLayout } from '@/components/layout/app-layout'
import { withAuth } from '@/components/auth/with-auth'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Restaurant } from '@/types'
import { formatDate, formatDateTime } from '@/lib/utils'
import { ArrowLeft, Store, Mail, MapPin, Calendar } from 'lucide-react'

function RestaurantDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [restaurant, setRestaurant] = useState<Restaurant | null>(null)

  useEffect(() => {
    // Fetch restaurant details from API
    // Example data
    setRestaurant({
      id: params.id as string,
      name: 'The Italian Place',
      slug: 'italian-place',
      status: 'ACTIVE',
      ownerId: 'owner-1',
      ownerName: 'John Doe',
      ownerEmail: 'john@italian.com',
      address: '123 Main St, New York, NY 10001',
      subscriptionTier: 'PREMIUM',
      subscriptionActive: true,
      qrVersion: 1,
      timezone: 'Asia/Kolkata',
      currency: 'INR',
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-15T10:00:00Z',
    })
  }, [params.id])

  if (!restaurant) {
    return (
      <AppLayout>
        <div className="text-center py-12">Loading...</div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-bold">{restaurant.name}</h1>
            <p className="text-muted-foreground mt-1">Restaurant Details</p>
          </div>
          <Badge variant={restaurant.status === 'ACTIVE' ? 'default' : 'destructive'} className={restaurant.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : ''}>
            {restaurant.status}
          </Badge>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Restaurant Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-start gap-3">
                  <Store className="w-5 h-5 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">Restaurant Name</p>
                    <p className="text-sm text-muted-foreground">{restaurant.name}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Mail className="w-5 h-5 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">Owner Email</p>
                    <p className="text-sm text-muted-foreground">{restaurant.ownerEmail}</p>
                  </div>
                </div>
                {restaurant.address && (
                  <div className="flex items-start gap-3">
                    <MapPin className="w-5 h-5 text-muted-foreground mt-0.5" />
                    <div>
                      <p className="text-sm font-medium">Address</p>
                      <p className="text-sm text-muted-foreground">{restaurant.address}</p>
                    </div>
                  </div>
                )}
                <div className="flex items-start gap-3">
                  <Calendar className="w-5 h-5 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">Created</p>
                    <p className="text-sm text-muted-foreground">
                      {formatDateTime(restaurant.createdAt)}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button className="w-full" variant="outline">
                View Orders
              </Button>
              <Button className="w-full" variant="outline">
                View Menu
              </Button>
              <Button className="w-full" variant="outline">
                View Staff
              </Button>
              <Button className="w-full" variant="destructive">
                Suspend Restaurant
              </Button>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="stats" className="w-full">
          <TabsList>
            <TabsTrigger value="stats">Statistics</TabsTrigger>
            <TabsTrigger value="activity">Activity Log</TabsTrigger>
            <TabsTrigger value="billing">Billing</TabsTrigger>
          </TabsList>
          <TabsContent value="stats" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Total Orders</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">1,234</div>
                  <p className="text-xs text-muted-foreground">All time</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">$45,678</div>
                  <p className="text-xs text-muted-foreground">All time</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Active Staff</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">8</div>
                  <p className="text-xs text-muted-foreground">Members</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          <TabsContent value="activity">
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground text-center">
                  No recent activity
                </p>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="billing">
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground text-center">
                  Billing information
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  )
}

export default withAuth(RestaurantDetailPage, ['PLATFORM_ADMIN'])
