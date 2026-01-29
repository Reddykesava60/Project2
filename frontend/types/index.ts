// User and Authentication Types
// NOTE: Role values mirror backend `User.Role` values exactly
// ('platform_admin', 'restaurant_owner', 'staff') for consistency.
export type UserRole = 'platform_admin' | 'restaurant_owner' | 'staff'

export interface User {
  id: string
  email: string
  name: string
  firstName?: string
  lastName?: string
  role: UserRole
  isVerified?: boolean
  restaurantId?: string
  restaurantName?: string
  // Runtime snake_case support
  restaurant_id?: string
  can_manage_stock?: boolean

  // Staff-specific permissions (only for STAFF role, but owners also have these)
  canCollectCash?: boolean
  canOverrideOrders?: boolean
  canManageStock?: boolean

  // Security
  twoFactorEnabled: boolean
  lastLoginIp?: string

  // Timestamps
  createdAt: string
  updatedAt?: string
  lastLoginAt?: string
}

export interface AuthToken {
  accessToken: string
  refreshToken?: string
  expiresAt: string
  user: User
}

// Restaurant Types
export type RestaurantStatus = 'ACTIVE' | 'SUSPENDED' | 'INACTIVE'
export type SubscriptionTier = 'BASIC' | 'PREMIUM' | 'ENTERPRISE'

export interface Restaurant {
  id: string
  name: string
  slug: string
  status: RestaurantStatus

  // Owner info
  ownerId: string
  ownerName: string
  ownerEmail: string

  // Contact
  address?: string
  email?: string

  // Branding
  logo?: string
  primaryColor?: string

  // Subscription
  subscriptionTier: SubscriptionTier
  subscriptionActive: boolean
  subscriptionExpiresAt?: string

  // QR Code settings
  qrVersion: number

  // Settings
  timezone: string
  currency: string

  // Timestamps
  createdAt: string
  updatedAt: string
}

// Menu Types
export interface MenuCategory {
  id: string
  name: string
  description?: string
  restaurantId: string
  displayOrder: number
  isActive: boolean
  itemCount?: number
  createdAt: string
  updatedAt: string
}

export interface MenuItem {
  id: string
  name: string
  description?: string
  price: number
  categoryId: string
  categoryName: string
  restaurantId: string
  image?: string
  stock_quantity?: number | null

  // Availability
  isAvailable: boolean
  is_active?: boolean
  isActive?: boolean
  availableFrom?: string  // Time format "HH:mm"
  availableUntil?: string // Time format "HH:mm"

  // Analytics
  timesOrdered: number

  // Ordering
  displayOrder: number

  // Versioning for concurrency
  version: number

  createdAt: string
  updatedAt: string
}

// Order Types - MUST match backend lowercase values
export type PaymentMethod = 'cash' | 'upi'
export type PaymentStatus = 'pending' | 'success'
export type OrderStatus = 'pending' | 'preparing' | 'completed'

// Order status transitions (for validation) - matches backend state machine
export const ALLOWED_ORDER_TRANSITIONS: Record<OrderStatus, OrderStatus[]> = {
  'pending': ['preparing'],
  'preparing': ['completed'],
  'completed': [],
}

export interface OrderItem {
  id: string
  orderId: string
  menuItemId: string
  menuItemName: string
  priceAtOrder: number  // Snapshot of price at order time
  quantity: number
  subtotal: number
}

export interface Order {
  id: string
  orderNumber: string  // e.g., "A23" - human-readable daily number
  dailySequence: number
  restaurantId: string
  restaurantName?: string

  // Order type
  orderType: 'qr_customer' | 'staff_cash'

  // Customer info (optional for staff orders)
  customerName?: string

  // Payment
  paymentMethod: PaymentMethod
  paymentStatus: PaymentStatus

  // Order status
  status: OrderStatus

  // Amounts
  subtotal: number
  tax: number
  totalAmount: number

  // Items
  items: OrderItem[]

  // Staff tracking
  createdByStaffId?: string
  createdByStaffName?: string
  completedByStaffId?: string
  completedByStaffName?: string

  // Cash collection tracking (for audit trail)
  cashCollectedByStaffId?: string
  cashCollectedByStaffName?: string
  cashCollectedAt?: string
  cashCollectedIp?: string

  // Timestamps
  createdAt: string
  updatedAt: string
  completedAt?: string

  // QR verification
  qrSignature?: string
  qrTimestamp?: number

  // Versioning for concurrency
  version: number
}

// Staff Types
export interface Staff {
  id: string
  name: string
  email: string
  restaurantId: string
  isActive: boolean

  // Permissions
  canCollectCash: boolean  // Required for creating cash orders & collecting payments
  canOverrideOrders: boolean  // Emergency override capability

  // Security
  twoFactorEnabled: boolean
  lastLoginIp?: string

  // Timestamps
  createdAt: string
  updatedAt: string
  lastLoginAt?: string
  deactivatedAt?: string
}

// Cash Audit Log for tracking all cash-related actions
export type CashAuditAction =
  | 'CASH_COLLECTED'
  | 'CASH_ORDER_CREATED'
  | 'CASH_REFUND'
  | 'PAYMENT_OVERRIDE'

export interface CashAuditLog {
  id: string
  orderId: string
  orderNumber: string
  restaurantId: string
  staffId: string
  staffName: string
  action: CashAuditAction
  actionDisplay: string
  amount: number
  notes?: string
  ipAddress?: string
  createdAt: string
}

// Staff activity for audit purposes
export interface StaffActivity {
  id: string
  staffId: string
  staffName: string
  action: AuditAction
  orderId?: string
  orderNumber?: string
  amount?: number
  ipAddress: string
  userAgent?: string
  createdAt: string
  details?: Record<string, any>
}

// Audit Log Types
export type AuditAction =
  | 'USER_LOGIN'
  | 'USER_LOGOUT'
  | 'RESTAURANT_CREATED'
  | 'RESTAURANT_SUSPENDED'
  | 'RESTAURANT_ACTIVATED'
  | 'ORDER_CREATED'
  | 'ORDER_COMPLETED'
  | 'ORDER_CANCELLED'
  | 'ORDER_REFUNDED'
  | 'MENU_ITEM_CREATED'
  | 'MENU_ITEM_UPDATED'
  | 'MENU_ITEM_DELETED'
  | 'STAFF_CREATED'
  | 'STAFF_DEACTIVATED'
  | 'PASSWORD_RESET'
  | 'QR_REGENERATED'
  | '2FA_ENABLED'
  | '2FA_DISABLED'
  | 'CASH_COLLECTED'
  | 'CASH_ORDER_CREATED'

export interface AuditLog {
  id: string
  actorId: string
  actorName: string
  actorRole: UserRole
  action: AuditAction
  restaurantId?: string
  targetId?: string
  targetType?: string
  metadata?: Record<string, any>
  ipAddress?: string
  createdAt: string
}

// Analytics Types
export interface DashboardKPI {
  todayOrders: number
  todayRevenue: number
  cashRevenue: number
  onlineRevenue: number
  pendingOrders: number
  completedOrders: number

  // Comparison with yesterday
  ordersTrend: number  // Percentage change
  revenueTrend: number // Percentage change
}

export interface HourlyOrderData {
  hour: number  // 0-23
  hourLabel: string  // "9 AM", "10 AM", etc.
  orders: number
  revenue: number
}

export interface DailyOrderData {
  date: string
  orders: number
  revenue: number
  cashRevenue: number
  onlineRevenue: number
}

export interface TopMenuItem {
  itemId: string
  itemName: string
  categoryName: string
  quantity: number
  revenue: number
  percentageOfTotal: number
}

export interface PaymentMethodBreakdown {
  cash: number
  online: number
  cashPercentage: number
  onlinePercentage: number
}

export interface AnalyticsSummary {
  period: 'today' | 'week' | 'month'
  totalOrders: number
  totalRevenue: number
  averageOrderValue: number
  paymentBreakdown: PaymentMethodBreakdown
  topItems: TopMenuItem[]
  hourlyDistribution: HourlyOrderData[]
  dailyTrend?: DailyOrderData[]
  peakHours: number[]  // Array of peak hour indices (0-23)
}

// QR Management Types
export interface QRCodeData {
  restaurantId: string
  qrCodeUrl: string
  publicUrl: string
  generatedAt: string
  scansCount: number
}

// System Health Types
export interface SystemHealth {
  status: 'HEALTHY' | 'DEGRADED' | 'DOWN'
  uptime: number
  lastChecked: string
  services: {
    database: 'UP' | 'DOWN'
    cache: 'UP' | 'DOWN'
    payments: 'UP' | 'DOWN'
  }
}

// Billing Types
export interface BillingPlan {
  id: string
  name: string
  price: number
  maxOrders: number
  maxStaff: number
  features: string[]
}

export interface BillingInfo {
  restaurantId: string
  planId: string
  planName: string
  status: 'ACTIVE' | 'SUSPENDED' | 'CANCELLED'
  currentPeriodStart: string
  currentPeriodEnd: string
  ordersThisMonth: number
  amount: number
}

// Cart Types (Customer UI)
export interface CartItem {
  menuItem: MenuItem
  quantity: number
}

export interface Cart {
  restaurantId: string
  items: CartItem[]
  subtotal: number
  tax: number
  total: number
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    pageSize: number
    totalPages: number
    totalCount: number
  }
}

// Filter Types
export interface OrderFilters {
  paymentMethod?: PaymentMethod
  paymentStatus?: PaymentStatus
  orderStatus?: OrderStatus
  startDate?: string
  endDate?: string
  search?: string
}

export interface AuditLogFilters {
  actorRole?: UserRole
  action?: AuditAction
  startDate?: string
  endDate?: string
  restaurantId?: string
}

export interface StaffActivityLog {
  id: string
  staffId: string
  staffName: string
  action: string
  description: string
  createdAt: string
}

// Customer Information (GDPR Compliant)
export interface CustomerInfo {
  name: string
  privacyAccepted: boolean
  privacyAcceptedAt?: string
}

// Checkout Types
export interface CheckoutData {
  restaurantSlug: string
  items: {
    menuItemId: string
    quantity: number
  }[]
  customerInfo: CustomerInfo
  paymentMethod: PaymentMethod
}

// Order Confirmation
export interface OrderConfirmation {
  orderId: string
  orderNumber: string
  restaurantName: string
  estimatedReadyTime: string
  totalAmount: number
  paymentMethod: PaymentMethod
  paymentStatus: PaymentStatus
  status: OrderStatus
  qrCodeUrl?: string
  items: OrderItem[]
  createdAt: string
}

// Payment Intent (for online payments)
export interface PaymentIntent {
  clientSecret: string
  paymentId: string
  amount: number
  currency: string
  status: 'pending' | 'processing' | 'succeeded' | 'failed'
}

// Security Settings (Owner)
export interface SecuritySettings {
  twoFactorEnabled: boolean
  lastPasswordChange: string
  loginHistory: LoginHistory[]
  apiKeys?: ApiKey[]
}

export interface LoginHistory {
  id: string
  ipAddress: string
  userAgent: string
  location?: string
  status: 'success' | 'failed'
  createdAt: string
}

export interface ApiKey {
  id: string
  name: string
  prefix: string
  lastUsedAt?: string
  createdAt: string
  expiresAt?: string
}
