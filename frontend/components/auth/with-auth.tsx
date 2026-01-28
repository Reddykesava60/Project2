'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import type { UserRole } from '@/types'

export function withAuth(Component: React.ComponentType, allowedRoles?: UserRole[]) {
  return function ProtectedRoute(props: any) {
    const { user, isLoading } = useAuth()
    const router = useRouter()

    useEffect(() => {
      if (!isLoading) {
        if (!user) {
          router.push('/login')
        } else if (allowedRoles && !allowedRoles.includes(user.role)) {
          // Redirect to appropriate dashboard based on user role
          switch (user.role) {
            case 'platform_admin':
              router.push('/admin/dashboard')
              break
            case 'restaurant_owner':
              router.push('/owner/dashboard')
              break
            case 'staff':
              router.push('/staff/orders')
              break
          }
        }
      }
    }, [user, isLoading, router])

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading...</p>
          </div>
        </div>
      )
    }

    if (!user || (allowedRoles && !allowedRoles.includes(user.role))) {
      return null
    }

    return <Component {...props} />
  }
}
