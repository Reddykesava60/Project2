/**
 * API Service Layer for DineFlow2
 * Uses Next.js API routes as proxy to Django backend
 */

import { getAuthToken } from './api'

// Use Next.js API routes (proxied to Django backend)
const API_BASE = ''

// Generic fetch wrapper with auth
async function fetchWithAuth<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const token = getAuthToken()

    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
    }

    if (token) {
        headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    })

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'An error occurred' }))

        // Helper to extract structured error
        const getStructuredError = (e: any) => {
            if (e && (e.code === 'ITEM_UNAVAILABLE' || e.code === 'INSUFFICIENT_STOCK')) return e;
            return null;
        }

        // 1. Root object
        const rootErr = getStructuredError(error);
        if (rootErr) {
            const err = new Error(rootErr.message || 'Item unavailable')
            Object.assign(err, rootErr)
            throw err
        }

        // 2. Wrapped in array [{ code: 'ITEM_UNAVAILABLE' }]
        if (Array.isArray(error)) {
            if (error.length > 0) {
                const arrErr = getStructuredError(error[0]);
                if (arrErr) {
                    const err = new Error(arrErr.message || 'Item unavailable')
                    Object.assign(err, arrErr)
                    throw err
                }
                // Fallback for normal string array
                if (typeof error[0] === 'string') {
                    throw new Error(error[0])
                }
            }
        }

        // Handle DRF object errors (e.g. { "non_field_errors": ["Error..."] } or { "field": ["Error..."] })
        if (typeof error === 'object' && error !== null) {
            if (error.non_field_errors && Array.isArray(error.non_field_errors)) {
                throw new Error(error.non_field_errors[0])
            }
            if (error.detail) {
                throw new Error(error.detail)
            }
            if (error.error) {
                throw new Error(error.error)
            }
            if (error.message) {
                throw new Error(error.message)
            }

            // If it's a field validation error like { "items": ["Reason"] }
            // Try to find the first array value
            const values = Object.values(error)
            if (values.length > 0 && Array.isArray(values[0]) && values[0].length > 0) {
                const firstVal = values[0][0]
                // Check inside that array for our structured error
                const nestedErr = getStructuredError(firstVal);
                if (nestedErr) {
                    const err = new Error(nestedErr.message || 'Item unavailable')
                    Object.assign(err, nestedErr)
                    throw err
                }
                throw new Error(String(firstVal))
            }
        }

        throw new Error(error.detail || error.error || `API Error: ${response.status}`)
    }

    // Handle empty responses (204 No Content, etc.)
    const text = await response.text()
    if (!text) {
        return {} as T
    }
    return JSON.parse(text) as T
}

// ============================================
// Restaurant Service
// ============================================

export interface Restaurant {
    id: string
    name: string
    slug: string
    description: string
    email: string
    address: string
    status: string
    currency: string
    tax_rate: number
    qr_version: number
}

export const restaurantService = {
    async getRestaurants(): Promise<Restaurant[]> {
        return fetchWithAuth('/api/restaurants/')
    },

    async getRestaurant(id: string): Promise<Restaurant> {
        return fetchWithAuth(`/api/restaurants/${id}/`)
    },
}

// ============================================
// Menu Service
// ============================================

export interface MenuCategory {
    id: string
    name: string
    description: string
    display_order: number
    is_active: boolean
    restaurant: string
}

export interface MenuItem {
    id: string
    name: string
    description: string
    price: number
    category: string
    category_name?: string
    restaurant: string
    image?: string
    is_available: boolean
    is_active: boolean
    is_vegetarian: boolean
    is_vegan: boolean
    is_gluten_free: boolean
    times_ordered: number
    display_order: number
}

export const menuService = {
    async getCategories(restaurantId: string): Promise<MenuCategory[]> {
        return fetchWithAuth(`/api/menu/categories/?restaurant=${restaurantId}`)
    },

    async createCategory(data: Partial<MenuCategory>): Promise<MenuCategory> {
        return fetchWithAuth('/api/menu/categories/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
    },

    async getItems(restaurantId: string, categoryId?: string): Promise<MenuItem[]> {
        let url = `/api/menu/items/?restaurant=${restaurantId}`
        if (categoryId) {
            url += `&category=${categoryId}`
        }
        return fetchWithAuth(url)
    },

    async createItem(data: Partial<MenuItem>): Promise<MenuItem> {
        return fetchWithAuth('/api/menu/items/', {
            method: 'POST',
            body: JSON.stringify(data),
        })
    },

    async updateItem(id: string, data: Partial<MenuItem>): Promise<MenuItem> {
        return fetchWithAuth(`/api/menu/items/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        })
    },

    async deleteItem(id: string): Promise<void> {
        return fetchWithAuth(`/api/menu/items/${id}/`, {
            method: 'DELETE',
        })
    },

    async toggleAvailability(id: string): Promise<{ is_available: boolean }> {
        return fetchWithAuth(`/api/menu/items/${id}/toggle/`, {
            method: 'POST',
        })
    },
}

// ============================================
// Order Service
// ============================================

export interface OrderItem {
    id: string
    menu_item: string
    menu_item_name: string
    price_at_order: number
    quantity: number
    subtotal: number
}

export interface Order {
    id: string
    order_number: string
    daily_sequence: number
    restaurant: string
    customer_name?: string
    payment_method: 'cash' | 'upi'  // Backend uses lowercase
    payment_status: 'pending' | 'success'  // Backend ONLY has pending/success
    status: 'pending' | 'preparing' | 'completed'  // Backend ONLY has these 3
    subtotal: number
    tax: number
    total_amount: number
    items: OrderItem[]
    created_at: string
    updated_at: string
    completed_at?: string
    created_by_staff?: string
    created_by_staff_name?: string
}

export interface DashboardStats {
    today_orders: number
    completed_orders: number
    pending_orders: number
    today_revenue: number
    orders_trend: number
    revenue_trend: number
}

export const orderService = {
    async getOrders(restaurantId: string, filters?: Record<string, string>): Promise<Order[]> {
        let url = `/api/orders/?restaurant=${restaurantId}`
        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value) url += `&${key}=${value}`
            })
        }
        return fetchWithAuth(url)
    },

    async getActiveOrders(restaurantId: string): Promise<Order[]> {
        return fetchWithAuth(`/api/orders/active/?restaurant=${restaurantId}`)
    },

    async updateStatus(orderId: string, status: string): Promise<Order> {
        return fetchWithAuth(`/api/orders/${orderId}/status/`, {
            method: 'POST',
            body: JSON.stringify({ status }),
        })
    },

    async collectPayment(orderId: string): Promise<Order> {
        return fetchWithAuth(`/api/orders/${orderId}/payment/`, {
            method: 'POST',
        })
    },

    async getDashboardStats(restaurantId: string): Promise<DashboardStats> {
        return fetchWithAuth(`/api/dashboard/stats/?restaurant=${restaurantId}`)
    },
}

// ============================================
// Public API (No Auth Required)
// ============================================

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export interface PublicMenuItem {
    id: string
    name: string
    description: string
    price: number
    image?: string
    is_available: boolean
    is_vegetarian: boolean
    is_vegan: boolean
    is_gluten_free: boolean
}

export interface PublicCategory {
    id: string
    name: string
    description: string
    items: PublicMenuItem[]
}

export interface PublicMenu {
    restaurant: {
        id: string
        name: string
        slug: string
        currency: string
    }
    categories: PublicCategory[]
}

export const publicService = {
    async getMenu(slug: string): Promise<PublicMenu> {
        const response = await fetch(`${BACKEND_URL}/api/public/r/${slug}/menu/`)
        if (!response.ok) {
            throw new Error('Restaurant not found')
        }
        return response.json()
    },

    async createOrder(slug: string, data: {
        items: { menu_item_id: string; quantity: number }[]
        customer_name?: string
        payment_method: 'cash' | 'upi'  // Backend uses lowercase: cash or upi
        privacy_accepted?: boolean
        table_number?: string
        is_parcel?: boolean
        spicy_level?: string
    }): Promise<Order> {
        const response = await fetch(`${BACKEND_URL}/api/public/r/${slug}/order/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...data,
                privacy_accepted: data.privacy_accepted ?? true, // Default to true for GDPR
            }),
        })
        if (!response.ok) {
            const error = await response.json().catch(() => ({} as any))
            if (error && (error.code === 'ITEM_UNAVAILABLE' || error.code === 'INSUFFICIENT_STOCK')) {
                const err = new Error(error.message || 'This item is out of stock or no longer available.')
                Object.assign(err, error)
                throw err
            }
            throw new Error(error.error || error.detail || error.message || 'Failed to create order')
        }
        const result = await response.json()
        // Backend returns { success: true, order: {...} } format
        return result.order || result
    },

    async getOrderStatus(slug: string, orderId: string): Promise<Order> {
        const response = await fetch(`${BACKEND_URL}/api/public/r/${slug}/order/${orderId}/status/`)
        if (!response.ok) {
            throw new Error('Order not found')
        }
        return response.json()
    },

    async createPaymentOrder(slug: string, orderId: string): Promise<{
        razorpay_order_id: string
        razorpay_key_id: string
        amount: number
        currency: string
    }> {
        const response = await fetch(`${BACKEND_URL}/api/public/r/${slug}/order/${orderId}/payment/create/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        })
        if (!response.ok) {
            const error = await response.json().catch(() => ({}))
            throw new Error(error.detail || error.error || 'Failed to create payment order')
        }
        return response.json()
    },

    async verifyPayment(slug: string, orderId: string, data: {
        razorpay_payment_id: string
        razorpay_order_id: string
        razorpay_signature: string
    }): Promise<{ success: boolean; order_number: string }> {
        const response = await fetch(`${BACKEND_URL}/api/public/r/${slug}/order/${orderId}/payment/verify/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        })
        if (!response.ok) {
            const error = await response.json().catch(() => ({}))
            throw new Error(error.detail || error.error || 'Payment verification failed')
        }
        return response.json()
    },

    // NEW UPI FLOW
    // NEW: Step 1 - Reservation
    async createReservation(slug: string, data: {
        items: { menu_item_id: string; quantity: number }[]
        customer_name?: string
        table_number?: string
        is_parcel?: boolean
        spicy_level?: string
        privacy_accepted?: boolean
        payment_method: 'cash' | 'upi'
    }): Promise<{
        success: boolean
        reservation_id: string
        expires_at: string
        total_amount: number
        message: string
    }> {
        const response = await fetch(`${BACKEND_URL}/api/public/r/${slug}/reserve/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        })
        if (!response.ok) {
            const error = await response.json().catch(() => ({} as any))
            if (error && (error.code === 'ITEM_UNAVAILABLE' || error.code === 'INSUFFICIENT_STOCK')) {
                const err = new Error(error.message || 'This item is out of stock or no longer available.')
                Object.assign(err, error)
                throw err
            }
            throw new Error(error.error || error.detail || error.message || 'Failed to reserve order')
        }
        return response.json()
    },

    // NEW: Step 2 - Initiate Payment (with Reservation)
    async initiateUPIPayment(slug: string, reservation_id: string): Promise<{
        success: boolean
        payment_token: string
        razorpay_order_id: string
        razorpay_key_id: string
        amount: number
        currency: string
        total_amount: number
    }> {
        const response = await fetch(`${BACKEND_URL}/api/public/r/${slug}/payment/initiate/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reservation_id }),
        })
        if (!response.ok) {
            const error = await response.json().catch(() => ({} as any))
            throw new Error(error.error || error.detail || error.message || 'Failed to initiate payment')
        }
        return response.json()
    },

    async verifyUPIPayment(slug: string, data: {
        payment_token: string
        razorpay_payment_id: string
        razorpay_order_id: string
        razorpay_signature: string
    }): Promise<{
        success: boolean
        order: Order
        message: string
    }> {
        const response = await fetch(`${BACKEND_URL}/api/public/r/${slug}/payment/verify/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        })
        if (!response.ok) {
            const error = await response.json().catch(() => ({} as any))
            if (error && (error.code === 'ITEM_UNAVAILABLE' || error.code === 'INSUFFICIENT_STOCK')) {
                const err = new Error(error.message || 'This item is out of stock or no longer available.')
                Object.assign(err, error)
                throw err
            }
            throw new Error(error.error || error.detail || error.message || 'Payment verification failed')
        }
        return response.json()
    },
}
