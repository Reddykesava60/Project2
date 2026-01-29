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
  LogOut,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

interface SidebarNavProps {
  items: NavItem[];
  title: string;
  onLogout?: () => void;
}

export function SidebarNav({ items, title, onLogout }: SidebarNavProps) {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 hidden h-screen w-64 border-r border-sidebar-border bg-sidebar lg:block">
      <div className="flex h-full flex-col">
        {/* Logo/Title */}
        <div className="flex h-16 items-center border-b border-sidebar-border px-6">
          <h1 className="text-lg font-semibold text-sidebar-foreground">{title}</h1>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 space-y-1 overflow-y-auto p-4">
          {items.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex min-h-[48px] items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-sidebar-accent text-sidebar-primary'
                    : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                )}
              >
                {item.icon}
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Logout */}
        {onLogout && (
          <div className="border-t border-sidebar-border p-4">
            <Button
              variant="ghost"
              className="w-full justify-start gap-3 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              onClick={onLogout}
            >
              <LogOut className="h-5 w-5" />
              Logout
            </Button>
          </div>
        )}
      </div>
    </aside>
  );
}

// Pre-configured sidebars for each role
export function OwnerSidebar({ onLogout }: { onLogout?: () => void }) {
  const items: NavItem[] = [
    { href: '/owner/dashboard', label: 'Dashboard', icon: <Home className="h-5 w-5" /> },
    { href: '/owner/orders', label: 'Orders', icon: <ClipboardList className="h-5 w-5" /> },
    { href: '/owner/menu', label: 'Menu', icon: <UtensilsCrossed className="h-5 w-5" /> },
    { href: '/staff/stock', label: 'Stock Control', icon: <UtensilsCrossed className="h-5 w-5" /> }, // Owner accesses Staff Stock Page
    { href: '/owner/staff', label: 'Staff', icon: <Users className="h-5 w-5" /> },
    { href: '/owner/qr', label: 'QR Code', icon: <QrCode className="h-5 w-5" /> },
    { href: '/owner/analytics', label: 'Analytics', icon: <BarChart3 className="h-5 w-5" /> },
    { href: '/owner/settings', label: 'Settings', icon: <Settings className="h-5 w-5" /> },
  ];
  return <SidebarNav items={items} title="Restaurant Manager" onLogout={onLogout} />;
}

export function AdminSidebar({ onLogout }: { onLogout?: () => void }) {
  const items: NavItem[] = [
    { href: '/admin/dashboard', label: 'Dashboard', icon: <Home className="h-5 w-5" /> },
    { href: '/admin/restaurants', label: 'Restaurants', icon: <Building2 className="h-5 w-5" /> },
    { href: '/admin/audit', label: 'Audit Logs', icon: <ScrollText className="h-5 w-5" /> },
    { href: '/admin/settings', label: 'Settings', icon: <Settings className="h-5 w-5" /> },
  ];
  return <SidebarNav items={items} title="Platform Admin" onLogout={onLogout} />;
}
