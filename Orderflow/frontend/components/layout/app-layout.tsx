'use client'

import { Sidebar } from './sidebar'
import { TopBar } from './topbar'
import { BottomNav } from './bottom-nav'
import { MobileHeader } from './mobile-header'
import { useAuth } from '@/contexts/auth-context'
import { cn } from '@/lib/utils'

interface AppLayoutProps {
  children: React.ReactNode
  restaurantName?: string
  title?: string
  showBack?: boolean
  onBack?: () => void
  rightAction?: React.ReactNode
}

export function AppLayout({
  children,
  restaurantName,
  title,
  showBack,
  onBack,
  rightAction,
}: AppLayoutProps) {
  const { user } = useAuth()
  const isStaff = user?.role === 'staff'
  const isOwner = user?.role === 'restaurant_owner'
  const showBottomNav = isStaff || isOwner
  const mobileTitle = title || restaurantName || 'DineFlow'

  return (
    <div className="min-h-screen-dvh bg-background text-foreground">
      <div className="flex h-screen-dvh flex-col md:flex-row overflow-hidden">
        {/* Sidebar for desktop */}
        <div className="hidden md:block">
          <Sidebar />
        </div>

        {/* Main column */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Mobile header */}
          <div className="md:hidden">
            <MobileHeader
              title={mobileTitle}
              showBack={showBack}
              onBack={onBack}
              rightAction={rightAction}
            />
          </div>

          {/* Desktop top bar */}
          <div className="hidden md:block">
            <TopBar restaurantName={restaurantName} />
          </div>

          {/* Content */}
          <main
            className={cn(
              'flex-1 overflow-y-auto bg-background p-4 md:p-6',
              showBottomNav && 'main-with-bottom-nav md:pb-6'
            )}
          >
            <div className="mx-auto w-full max-w-5xl">{children}</div>
          </main>

          {/* Bottom Navigation for staff/owner on mobile */}
          {showBottomNav && (
            <div className="md:hidden">
              <BottomNav role={isStaff ? 'staff' : 'restaurant_owner'} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
