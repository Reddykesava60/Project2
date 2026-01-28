'use client'

import { useEffect, useState } from 'react'
import { AppLayout } from '@/components/layout/app-layout'
import { withAuth } from '@/components/auth/with-auth'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { SystemHealth } from '@/types'
import { Activity, Database, Zap, CreditCard, CheckCircle2, XCircle } from 'lucide-react'

function SystemHealthPage() {
  const [health, setHealth] = useState<SystemHealth>({
    status: 'HEALTHY',
    uptime: 99.98,
    lastChecked: new Date().toISOString(),
    services: {
      database: 'UP',
      cache: 'UP',
      payments: 'UP',
    },
  })

  useEffect(() => {
    // Fetch system health from API
    // This would be a real-time monitoring endpoint
  }, [])

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'destructive' | 'secondary'> = {
      HEALTHY: 'success',
      DEGRADED: 'secondary',
      DOWN: 'destructive',
    }
    return <Badge variant={variants[status]}>{status}</Badge>
  }

  const ServiceStatus = ({ name, status, icon }: { name: string; status: string; icon: React.ReactNode }) => (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {icon}
            <CardTitle className="text-base">{name}</CardTitle>
          </div>
          {status === 'UP' ? (
            <CheckCircle2 className="w-5 h-5 text-green-500" />
          ) : (
            <XCircle className="w-5 h-5 text-destructive" />
          )}
        </div>
      </CardHeader>
      <CardContent>
        <Badge variant={status === 'UP' ? 'success' : 'destructive'}>{status}</Badge>
      </CardContent>
    </Card>
  )

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">System Health</h1>
          <p className="text-muted-foreground mt-1">
            Monitor platform infrastructure and services
          </p>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Overall System Status</CardTitle>
                <CardDescription>Last checked: {new Date(health.lastChecked).toLocaleString()}</CardDescription>
              </div>
              {getStatusBadge(health.status)}
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4 border rounded-lg">
                <Activity className="w-8 h-8 mx-auto text-primary mb-2" />
                <div className="text-2xl font-bold">{health.uptime}%</div>
                <p className="text-sm text-muted-foreground">Uptime (30 days)</p>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <Zap className="w-8 h-8 mx-auto text-primary mb-2" />
                <div className="text-2xl font-bold">45ms</div>
                <p className="text-sm text-muted-foreground">Avg Response Time</p>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <CheckCircle2 className="w-8 h-8 mx-auto text-green-500 mb-2" />
                <div className="text-2xl font-bold">3/3</div>
                <p className="text-sm text-muted-foreground">Services Operational</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div>
          <h2 className="text-xl font-semibold mb-4">Service Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ServiceStatus
              name="Database"
              status={health.services.database}
              icon={<Database className="w-5 h-5 text-primary" />}
            />
            <ServiceStatus
              name="Cache"
              status={health.services.cache}
              icon={<Zap className="w-5 h-5 text-primary" />}
            />
            <ServiceStatus
              name="Payment Gateway"
              status={health.services.payments}
              icon={<CreditCard className="w-5 h-5 text-primary" />}
            />
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Recent Incidents</CardTitle>
            <CardDescription>System issues and resolutions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-muted-foreground">
              No incidents in the last 30 days
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}

export default withAuth(SystemHealthPage, ['PLATFORM_ADMIN'])
