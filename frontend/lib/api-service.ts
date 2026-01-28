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
    payment_method: 'CASH' | 'ONLINE'
    payment_status: 'PENDING' | 'SUCCESS' | 'FAILED' | 'REFUNDED'
    status: 'PENDING' | 'AWAITING_PAYMENT' | 'PREPARING' | 'READY' | 'COMPLETED' | 'CANCELLED'
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
        payment_method: 'CASH' | 'ONLINE'
        privacy_accepted?: boolean
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
            const error = await response.json().catch(() => ({}))
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
}
