'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { ChevronLeft } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MobileHeaderProps {
    title: string
    subtitle?: string
    showBack?: boolean
    onBack?: () => void
    rightAction?: React.ReactNode
    className?: string
}

export function MobileHeader({
    title,
    subtitle,
    showBack = false,
    onBack,
    rightAction,
    className,
}: MobileHeaderProps) {
    const router = useRouter()

    const handleBack = () => {
        if (onBack) {
            onBack()
        } else {
            router.back()
        }
    }

    return (
        <header className={cn(
            "sticky top-0 z-40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 border-b",
            "px-4 flex items-center gap-3 min-h-[var(--header-height)] header-safe",
            className
        )}>
            {/* Left section */}
            <div className="flex items-center gap-2 flex-shrink-0">
                {showBack && (
                    <Button
                        variant="ghost"
                        size="icon"
                        className="touch-target -ml-2"
                        onClick={handleBack}
                    >
                        <ChevronLeft className="w-6 h-6" />
                        <span className="sr-only">Go back</span>
                    </Button>
                )}
            </div>

            {/* Center section - Title */}
            <div className="flex-1 min-w-0">
                <h1 className="font-semibold text-lg truncate">{title}</h1>
                {subtitle && (
                    <p className="text-sm text-muted-foreground truncate">{subtitle}</p>
                )}
            </div>

            {/* Right section */}
            <div className="flex items-center gap-1 flex-shrink-0">
                {rightAction}
            </div>
        </header>
    )
}
