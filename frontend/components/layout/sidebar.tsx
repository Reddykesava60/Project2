'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useAuth } from '@/contexts/auth-context'
import {
  LayoutDashboard,
  Store,
  FileText,
  Activity,
  CreditCard,
  ShoppingBag,
  Menu as MenuIcon,
  Users,
  BarChart3,
  QrCode,
  Shield,
  Package,
} from 'lucide-react'

interface NavItem {
  label: string
  href: string
  icon: React.ReactNode
}

export function Sidebar() {
  const pathname = usePathname()
  const { user } = useAuth()

  const adminNav: NavItem[] = [
    { label: 'Dashboard', href: '/admin/dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
    { label: 'Restaurants', href: '/admin/restaurants', icon: <Store className="w-5 h-5" /> },
    { label: 'Audit Logs', href: '/admin/audit-logs', icon: <FileText className="w-5 h-5" /> },
    { label: 'System Health', href: '/admin/system-health', icon: <Activity className="w-5 h-5" /> },
    { label: 'Billing', href: '/admin/billing', icon: <CreditCard className="w-5 h-5" /> },
  ]

  const ownerNav: NavItem[] = [
    { label: 'Dashboard', href: '/owner/dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
    { label: 'Orders', href: '/owner/orders', icon: <ShoppingBag className="w-5 h-5" /> },
    { label: 'Menu', href: '/owner/menu', icon: <MenuIcon className="w-5 h-5" /> },
    { label: 'Staff', href: '/owner/staff', icon: <Users className="w-5 h-5" /> },
    { label: 'Analytics', href: '/owner/analytics', icon: <BarChart3 className="w-5 h-5" /> },
    { label: 'QR Management', href: '/owner/qr-management', icon: <QrCode className="w-5 h-5" /> },
    { label: 'Security', href: '/owner/security', icon: <Shield className="w-5 h-5" /> },
  ]

  const staffNav: NavItem[] = [
    { label: 'Active Orders', href: '/staff/orders', icon: <ShoppingBag className="w-5 h-5" /> },
    { label: 'Create Cash Order', href: '/staff/create-order', icon: <Package className="w-5 h-5" /> },
  ]

  let navItems: NavItem[] = []
  if (user?.role === 'platform_admin') navItems = adminNav
  if (user?.role === 'restaurant_owner') navItems = ownerNav
  if (user?.role === 'staff') navItems = staffNav

  return (
    <aside className="w-64 bg-card border-r border-border min-h-screen">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-primary">DineFlow</h1>
      </div>

      <nav className="px-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              {item.icon}
              <span className="font-medium">{item.label}</span>
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
