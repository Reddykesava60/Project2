'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
    ClipboardList,
    PlusCircle,
    LayoutDashboard,
    UtensilsCrossed,
    Users,
    LucideIcon
} from 'lucide-react'

interface NavItem {
    href: string
    label: string
    icon: LucideIcon
}

interface BottomNavProps {
  role: 'staff' | 'restaurant_owner'
}

const staffNavItems: NavItem[] = [
    { href: '/staff/orders', label: 'Orders', icon: ClipboardList },
]

const ownerNavItems: NavItem[] = [
    { href: '/owner/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/owner/orders', label: 'Orders', icon: ClipboardList },
    { href: '/owner/menu', label: 'Menu', icon: UtensilsCrossed },
    { href: '/owner/staff', label: 'Staff', icon: Users },
]

export function BottomNav({ role }: BottomNavProps) {
    const pathname = usePathname()
    const navItems = role === 'staff' ? staffNavItems : ownerNavItems

    const renderPrimaryAction = () => {
        if (role === 'staff') {
            return (
                <Link
                    href="/staff/create-order"
                    className="flex flex-col items-center justify-center gap-1 rounded-full bg-primary text-primary-foreground px-5 py-3 shadow-lg shadow-primary/30 active:scale-[0.98] transition-transform"
                    aria-label="Create order"
                >
                    <PlusCircle className="w-6 h-6" />
                    <span className="text-xs font-semibold">New</span>
                </Link>
            )
        }

        return (
            <Link
                href="/owner/menu"
                className="flex flex-col items-center justify-center gap-1 rounded-full bg-primary text-primary-foreground px-5 py-3 shadow-lg shadow-primary/25 active:scale-[0.98] transition-transform"
                aria-label="Add menu item"
            >
                <PlusCircle className="w-6 h-6" />
                <span className="text-xs font-semibold">Add</span>
            </Link>
        )
    }

    return (
        <nav className="fixed bottom-0 left-0 right-0 z-50 bg-background/95 backdrop-blur border-t border-border bottom-nav-container">
            <div className="mx-auto flex h-full max-w-xl items-center justify-between px-3 gap-2">
                {navItems.map((item) => {
                    const isActive = pathname.startsWith(item.href)
                    const Icon = item.icon

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "touch-target flex-1 flex flex-col items-center justify-center gap-1 rounded-xl text-xs font-semibold transition-colors",
                                isActive
                                    ? "bg-primary/10 text-primary ring-1 ring-primary/30"
                                    : "text-muted-foreground hover:text-foreground"
                            )}
                            aria-label={item.label}
                        >
                            <Icon className={cn(
                                "w-6 h-6 transition-transform",
                                isActive && "scale-110"
                            )} />
                            <span className="truncate">{item.label}</span>
                        </Link>
                    )
                })}

                {renderPrimaryAction()}
            </div>
        </nav>
    )
}
