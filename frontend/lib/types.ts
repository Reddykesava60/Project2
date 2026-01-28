// ============================================
// CORE TYPES FOR RESTAURANT ORDERING SAAS
// ============================================

// User Roles
export type UserRole = 'platform_admin' | 'restaurant_owner' | 'staff';

// Order Types
export type OrderType = 'customer_qr_online' | 'customer_qr_cash' | 'staff_cash';
export type PaymentMethod = 'online' | 'cash';
export type PaymentStatus = 'pending' | 'paid' | 'failed';
export type OrderStatus = 'pending' | 'preparing' | 'ready' | 'completed' | 'cancelled';

// ============================================
// USER & AUTHENTICATION
// ============================================

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  restaurant_id?: string;
  can_collect_cash: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// ============================================
// RESTAURANT
// ============================================

export interface Restaurant {
  id: string;
  name: string;
  slug: string;
  description?: string;
  logo_url?: string;
  address?: string;
  phone?: string;
  is_active: boolean;
  owner_id?: string;
  qr_code_url?: string;
  subscription_status: 'active' | 'suspended' | 'cancelled';
  created_at: string;
  updated_at: string;
}

// ============================================
// MENU
// ============================================

export interface MenuCategory {
  id: string;
  restaurant_id: string;
  name: string;
  description?: string;
  sort_order: number;
  is_active: boolean;
  items: MenuItem[];
}

export interface MenuItem {
  id: string;
  category_id: string;
  name: string;
  description?: string;
  price: number;
  image_url?: string;
  is_available: boolean;
  is_veg: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

// ============================================
// ORDERS
// ============================================

export interface OrderItem {
  id: string;
  order_id: string;
  menu_item_id: string;
  menu_item_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  menu_item_image_url?: string;
  notes?: string;
}

export interface Order {
  id: string;
  restaurant_id: string;
  daily_order_number: string; // e.g., "A23"
  order_type: OrderType;
  status: OrderStatus;
  payment_method: PaymentMethod;
  payment_status: PaymentStatus;
  customer_name: string;
  items: OrderItem[];
  subtotal: number;
  tax: number;
  total: number;
  is_parcel: boolean;
  spicy_level: 'normal' | 'medium' | 'high';
  qr_code_url?: string;
  notes?: string;
  created_by_staff_id?: string;
  completed_by_staff_id?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

// ============================================
// CART (Client-side only)
// ============================================

export interface CartItem {
  menu_item: MenuItem;
  quantity: number;
  notes?: string;
}

export interface Cart {
  restaurant_id: string;
  items: CartItem[];
  customer_name: string;
  payment_method: PaymentMethod;
  is_parcel: boolean;
  spicy_level: 'normal' | 'medium' | 'high';
}

// ============================================
// STAFF MANAGEMENT
// ============================================

export interface StaffMember {
  id: string;
  user_id: string;
  restaurant_id: string;
  name: string;
  email: string;
  can_collect_cash: boolean;
  is_active: boolean;
  created_at: string;
}

// ============================================
// ANALYTICS (MVP)
// ============================================

export interface DashboardStats {
  today_orders: number;
  today_revenue: number;
  cash_revenue: number;
  online_revenue: number;
  pending_orders: number;
  orders_by_hour: { hour: number; count: number }[];
}

// ============================================
// API RESPONSE TYPES
// ============================================

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

// ============================================
// AUDIT LOG
// ============================================

export interface AuditLog {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  user_id: string;
  user_email: string;
  details?: Record<string, unknown>;
  created_at: string;
}
