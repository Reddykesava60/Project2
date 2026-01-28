'use client'

import { useEffect, useState } from 'react'
import { AppLayout } from '@/components/layout/app-layout'
import { withAuth } from '@/components/auth/with-auth'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { QRCodeData } from '@/types'
import { QrCode, Download, RefreshCw, ExternalLink } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

function QRManagementPage() {
  const [qrData, setQrData] = useState<QRCodeData>({
    restaurantId: 'rest-1',
    qrCodeUrl: '/api/qr/restaurant-1.png',
    publicUrl: 'https://dineflow.app/r/italian-place',
    generatedAt: '2024-01-15T00:00:00Z',
    scansCount: 234,
  })

  const scanAnalytics = [
    { date: 'Mon', scans: 12 },
    { date: 'Tue', scans: 19 },
    { date: 'Wed', scans: 15 },
    { date: 'Thu', scans: 22 },
    { date: 'Fri', scans: 35 },
    { date: 'Sat', scans: 48 },
    { date: 'Sun', scans: 42 },
  ]

  const handleDownloadPNG = () => {
    // Implement QR code PNG download
    console.log('Download PNG')
  }

  const handleDownloadPDF = () => {
    // Implement QR code PDF download
    console.log('Download PDF')
  }

  const handleRegenerate = () => {
    // Implement QR code regeneration with confirmation
    console.log('Regenerate QR')
  }

  return (
    <AppLayout title="QR Code">
      <div className="space-y-4">
        {/* QR Code Display */}
        <div className="surface-card p-6 rounded-xl text-center">
          <div className="w-48 h-48 mx-auto bg-muted rounded-xl flex items-center justify-center mb-4">
            <QrCode className="w-24 h-24 text-muted-foreground" />
          </div>
          
          <button 
            className="flex items-center gap-2 p-3 bg-muted rounded-lg w-full touch-action-manipulation active:scale-[0.98] transition-transform"
            onClick={() => window.open(qrData.publicUrl, '_blank')}
          >
            <ExternalLink className="w-4 h-4 text-muted-foreground flex-shrink-0" />
            <span className="text-sm text-primary truncate flex-1 text-left">
              {qrData.publicUrl}
            </span>
          </button>
          
          <div className="grid grid-cols-2 gap-3 mt-4">
            <Button onClick={handleDownloadPNG} className="min-h-touch">
              <Download className="w-4 h-4 mr-2" />
              PNG
            </Button>
            <Button onClick={handleDownloadPDF} variant="outline" className="min-h-touch">
              <Download className="w-4 h-4 mr-2" />
              PDF
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="surface-card p-4 rounded-xl">
            <div className="text-sm text-muted-foreground mb-1">Total Scans</div>
            <div className="text-2xl font-bold">{qrData.scansCount}</div>
          </div>
          <div className="surface-card p-4 rounded-xl">
            <div className="text-sm text-muted-foreground mb-1">Conversion</div>
            <div className="text-2xl font-bold">68%</div>
          </div>
        </div>

        {/* Scan Chart */}
        <Card className="mobile-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Scans (7 Days)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={scanAnalytics}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis hide />
                <Tooltip />
                <Bar dataKey="scans" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <div className="space-y-2">
          <div className="flex justify-between items-center p-4 surface-card rounded-xl">
            <span className="text-sm">Average daily scans</span>
            <span className="font-bold">27.6</span>
          </div>
          <div className="flex justify-between items-center p-4 surface-card rounded-xl">
            <span className="text-sm">Peak day (Saturday)</span>
            <span className="font-bold">48 scans</span>
          </div>
        </div>

        {/* Regenerate Section */}
        <div className="surface-card p-4 rounded-xl border-destructive/20">
          <p className="text-sm text-muted-foreground mb-3">
            Generated: {new Date(qrData.generatedAt).toLocaleDateString()}
          </p>
          <Button onClick={handleRegenerate} variant="destructive" className="w-full min-h-touch">
            <RefreshCw className="w-4 h-4 mr-2" />
            Regenerate QR Code
          </Button>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            ⚠️ This will invalidate the current QR code
          </p>
        </div>
      </div>
    </AppLayout>
  )
}

export default withAuth(QRManagementPage, ['RESTAURANT_OWNER'])
