'use client'

import * as React from 'react'
import { createPortal } from 'react-dom'
import { cn } from '@/lib/utils'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface MobileSheetProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    children: React.ReactNode
    title?: string
    description?: string
    className?: string
}

interface MobileSheetHeaderProps {
    children: React.ReactNode
    className?: string
}

interface MobileSheetContentProps {
    children: React.ReactNode
    className?: string
}

interface MobileSheetFooterProps {
    children: React.ReactNode
    className?: string
}

export function MobileSheet({
    open,
    onOpenChange,
    children,
    title,
    description,
    className,
}: MobileSheetProps) {
    const [mounted, setMounted] = React.useState(false)

    React.useEffect(() => {
        setMounted(true)
    }, [])

    React.useEffect(() => {
        if (open) {
            document.body.style.overflow = 'hidden'
        } else {
            document.body.style.overflow = ''
        }
        return () => {
            document.body.style.overflow = ''
        }
    }, [open])

    if (!mounted || !open) return null

    return createPortal(
        <>
            {/* Backdrop */}
            <div
                className="sheet-overlay animate-fade-in"
                onClick={() => onOpenChange(false)}
                aria-hidden="true"
            />

            {/* Sheet */}
            <div
                role="dialog"
                aria-modal="true"
                aria-labelledby={title ? 'sheet-title' : undefined}
                className={cn(
                    "sheet-content animate-slide-up flex flex-col",
                    className
                )}
            >
                {/* Handle */}
                <div className="sheet-handle" />

                {/* Header */}
                {(title || description) && (
                    <div className="px-4 pb-4 border-b">
                        <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 min-w-0">
                                {title && (
                                    <h2 id="sheet-title" className="text-xl font-semibold">
                                        {title}
                                    </h2>
                                )}
                                {description && (
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {description}
                                    </p>
                                )}
                            </div>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="touch-target -mt-1 -mr-2"
                                onClick={() => onOpenChange(false)}
                            >
                                <X className="w-6 h-6" />
                                <span className="sr-only">Close</span>
                            </Button>
                        </div>
                    </div>
                )}

                {/* Content */}
                <div className="flex-1 overflow-y-auto overscroll-contain">
                    {children}
                </div>
            </div>
        </>,
        document.body
    )
}

export function MobileSheetHeader({ children, className }: MobileSheetHeaderProps) {
    return (
        <div className={cn("px-4 py-4 border-b", className)}>
            {children}
        </div>
    )
}

export function MobileSheetContent({ children, className }: MobileSheetContentProps) {
    return (
        <div className={cn("px-4 py-4 flex-1", className)}>
            {children}
        </div>
    )
}

export function MobileSheetFooter({ children, className }: MobileSheetFooterProps) {
    return (
        <div className={cn(
            "px-4 py-4 border-t bg-background sticky bottom-0",
            "pb-safe",
            className
        )}>
            {children}
        </div>
    )
}
