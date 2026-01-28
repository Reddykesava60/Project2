'use client';

import React from "react"

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  ClipboardList,
  QrCode,
  Settings,
  Home,
  Users,
  BarChart3,
  UtensilsCrossed,
  Building2,
  ScrollText,
} from 'lucide-react';

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

interface BottomNavProps {
  items: NavItem[];
}

export function BottomNav({ items }: BottomNavProps) {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background pb-safe">
      <div className="flex h-16 items-center justify-around">
        {items.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex min-h-[48px] min-w-[48px] flex-col items-center justify-center gap-1 px-3 py-2 text-xs font-medium transition-colors',
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              <span className="h-6 w-6">{item.icon}</span>
              <span className="truncate">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

// Pre-configured navigation for each role
export function StaffBottomNav() {
  const items: NavItem[] = [
    { href: '/staff/orders', label: 'Orders', icon: <ClipboardList className="h-6 w-6" /> },
    { href: '/staff/scan', label: 'Scan', icon: <QrCode className="h-6 w-6" /> },
    { href: '/staff/new-order', label: 'New Order', icon: <UtensilsCrossed className="h-6 w-6" /> },
  ];
  return <BottomNav items={items} />;
}

export function OwnerMobileNav() {
  const items: NavItem[] = [
    { href: '/owner/dashboard', label: 'Dashboard', icon: <Home className="h-6 w-6" /> },
    { href: '/owner/orders', label: 'Orders', icon: <ClipboardList className="h-6 w-6" /> },
    { href: '/owner/menu', label: 'Menu', icon: <UtensilsCrossed className="h-6 w-6" /> },
    { href: '/owner/staff', label: 'Staff', icon: <Users className="h-6 w-6" /> },
    { href: '/owner/settings', label: 'Settings', icon: <Settings className="h-6 w-6" /> },
  ];
  return <BottomNav items={items} />;
}

export function CustomerBottomNav({ restaurantSlug }: { restaurantSlug: string }) {
  const items: NavItem[] = [
    { href: `/r/${restaurantSlug}`, label: 'Menu', icon: <UtensilsCrossed className="h-6 w-6" /> },
    { href: `/r/${restaurantSlug}/cart`, label: 'Cart', icon: <ClipboardList className="h-6 w-6" /> },
  ];
  return <BottomNav items={items} />;
}

export function AdminBottomNav() {
  const items: NavItem[] = [
    { href: '/admin/restaurants', label: 'Restaurants', icon: <Building2 className="h-6 w-6" /> },
    { href: '/admin/analytics', label: 'Analytics', icon: <BarChart3 className="h-6 w-6" /> },
    { href: '/admin/audit', label: 'Audit Log', icon: <ScrollText className="h-6 w-6" /> },
  ];
  return <BottomNav items={items} />;
}
