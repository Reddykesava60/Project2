'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Order, OrderStatus } from '@/types'
import { orderApi } from '@/lib/api'

interface UseOrdersOptions {
  restaurantId?: string
  status?: OrderStatus | OrderStatus[]
  pollingInterval?: number // in milliseconds
  enabled?: boolean
}

interface UseOrdersReturn {
  orders: Order[]
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  lastUpdated: Date | null
}

/**
 * Hook for fetching and polling orders with real-time updates
 * Uses polling as Phase 1 implementation, can be upgraded to SSE/WebSocket
 */
export function useOrders(options: UseOrdersOptions = {}): UseOrdersReturn {
  const {
    restaurantId,
    status,
    pollingInterval = 5000, // Default 5 seconds
    enabled = true,
  } = options

  const [orders, setOrders] = useState<Order[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  const fetchOrders = useCallback(async () => {
    if (!enabled) return

    try {
      // Build query params
      if (!restaurantId) {
        setOrders([])
        setLastUpdated(new Date())
        setError(null)
        return
      }

      const response = await orderApi.getAll(restaurantId)
      const apiOrders = (response.success && Array.isArray(response.data) ? response.data : []) as any[]

      // Optional client-side status filter (backend already enforces staff scoping)
      const statusArray = status ? (Array.isArray(status) ? status : [status]) : []
      const filtered = statusArray.length
        ? apiOrders.filter((o) => statusArray.includes((o.status || '').toLowerCase()))
        : apiOrders

      setOrders(filtered as Order[])
      setLastUpdated(new Date())
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch orders')
    } finally {
      setIsLoading(false)
    }
  }, [enabled, restaurantId, status])

  // Initial fetch
  useEffect(() => {
    if (enabled) {
      fetchOrders()
    }
  }, [enabled, fetchOrders])

  // Setup polling
  useEffect(() => {
    if (!enabled || pollingInterval <= 0) return

    intervalRef.current = setInterval(fetchOrders, pollingInterval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [enabled, pollingInterval, fetchOrders])

  return {
    orders,
    isLoading,
    error,
    refetch: fetchOrders,
    lastUpdated,
  }
}

/**
 * Hook for subscribing to order status updates via SSE (Phase 2)
 */
export function useOrderUpdates(
  restaurantId: string,
  onNewOrder?: (order: Order) => void,
  onOrderUpdate?: (order: Order) => void
) {
  const [connected, setConnected] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)

  useEffect(() => {
    // SSE implementation (Phase 2)
    // const eventSource = new EventSource(`/api/orders/stream?restaurant_id=${restaurantId}`)
    // 
    // eventSource.onopen = () => setConnected(true)
    // eventSource.onerror = () => setConnected(false)
    // 
    // eventSource.addEventListener('new_order', (event) => {
    //   const order = JSON.parse(event.data)
    //   onNewOrder?.(order)
    // })
    // 
    // eventSource.addEventListener('order_update', (event) => {
    //   const order = JSON.parse(event.data)
    //   onOrderUpdate?.(order)
    // })
    // 
    // eventSourceRef.current = eventSource
    // 
    // return () => {
    //   eventSource.close()
    // }
  }, [restaurantId, onNewOrder, onOrderUpdate])

  return { connected }
}

/**
 * Hook for order notification sounds and browser notifications
 */
export function useOrderNotifications() {
  const [notificationsEnabled, setNotificationsEnabled] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().then(permission => {
        setNotificationsEnabled(permission === 'granted')
      })
    } else if ('Notification' in window && Notification.permission === 'granted') {
      setNotificationsEnabled(true)
    }

    // Create audio element for notification sound
    audioRef.current = new Audio('/sounds/notification.mp3')
  }, [])

  const playNotificationSound = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0
      audioRef.current.play().catch(() => {
        // Audio play might be blocked by browser
        console.log('Audio notification blocked by browser')
      })
    }
  }, [])

  const showBrowserNotification = useCallback((title: string, body: string) => {
    if (notificationsEnabled && 'Notification' in window) {
      new Notification(title, {
        body,
        icon: '/icon.png',
        tag: 'order-notification',
      })
    }
  }, [notificationsEnabled])

  const notifyNewOrder = useCallback((order: Order) => {
    playNotificationSound()
    showBrowserNotification(
      `New Order #${order.orderNumber}`,
      `${order.items.length} items - ${order.paymentMethod === 'cash' ? 'Cash' : 'UPI'}`
    )
  }, [playNotificationSound, showBrowserNotification])

  return {
    notificationsEnabled,
    playNotificationSound,
    showBrowserNotification,
    notifyNewOrder,
  }
}

/**
 * Hook to track online/offline status with reconnection handling
 */
export function useConnectionStatus() {
  const [isOnline, setIsOnline] = useState(true)
  const [wasOffline, setWasOffline] = useState(false)

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      if (wasOffline) {
        // Trigger refetch when coming back online
        setWasOffline(false)
      }
    }

    const handleOffline = () => {
      setIsOnline(false)
      setWasOffline(true)
    }

    setIsOnline(navigator.onLine)
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [wasOffline])

  return { isOnline, wasOffline }
}
