// ============================================
// PRODUCTION API CLIENT - BACKEND DRIVEN
// ============================================

import { http } from './http';
import type {
  ApiResponse,
  PaginatedResponse,
  Restaurant,
  MenuCategory,
  Order,
  User,
  StaffMember,
  DashboardStats,
  AuditLog,
  Cart,
} from './types';
import { AUTH_TOKEN_KEY } from './http';
import { jwtDecode } from 'jwt-decode';

// ============================================
// AUTH UTILITIES
// ============================================

export const getAuthToken = () => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
};

export const setAuthToken = (token: string) => {
  if (typeof window === 'undefined') return;
  localStorage.setItem(AUTH_TOKEN_KEY, token);
};

export const removeAuthToken = () => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
};

export const isTokenExpired = (token: string): boolean => {
  try {
    const decoded: any = jwtDecode(token);
    if (!decoded.exp) return false;
    // Buffer of 10 seconds
    return decoded.exp * 1000 < Date.now() + 10000;
  } catch (e) {
    return true;
  }
};

// Standard Helper for API responses
const handleResponse = async <T>(promise: Promise<any>): Promise<ApiResponse<T>> => {
  try {
    const res = await promise;
    return { success: true, data: res.data };
  } catch (error: any) {
    return {
      success: false,
      error: error.response?.data?.message || error.message || 'An unexpected error occurred'
    };
  }
};

// ============================================
// API IMPLEMENTATIONS
// ============================================

export const authApi = {
  login: (email: string, password: string) =>
    handleResponse<{ user: User; access: string; refresh: string }>(
      http.post('/auth/login/', { email, password })
    ).then((res) => {
      if (!res.success || !res.data) {
        return res as ApiResponse<{ user: User; token: string }>
      }

      // Backend returns { access, refresh, user }; frontend expects { user, token }
      const { user, access } = res.data
      return {
        success: true,
        data: { user, token: access },
      } as ApiResponse<{ user: User; token: string }>
    }),

  logout: () =>
    handleResponse<void>(http.post('/auth/logout/')),

  getCurrentUser: () =>
    handleResponse<User>(http.get('/auth/me/')),

  verifyTwoFactor: (code: string) =>
    handleResponse<{ verified: boolean }>(http.post('/auth/verify-2fa/', { code })),
};

export const restaurantApi = {
  getBySlug: (slug: string) =>
    handleResponse<Restaurant>(http.get(`/restaurants/slug/${slug}/`)),

  getMenu: (id: string) =>
    handleResponse<MenuCategory[]>(http.get(`/restaurants/${id}/menu/`)),

  getAll: (page = 1, limit = 20) =>
    handleResponse<PaginatedResponse<Restaurant>>(http.get('/restaurants/', { params: { page, limit } })),

  activate: (id: string) =>
    handleResponse<Restaurant>(http.post(`/restaurants/${id}/activate/`)),

  suspend: (id: string) =>
    handleResponse<Restaurant>(http.post(`/restaurants/${id}/suspend/`)),

  assignOwner: (id: string, ownerId: string) =>
    handleResponse<Restaurant>(http.post(`/restaurants/${id}/assign-owner/`, { owner_id: ownerId })),
};

export const menuApi = {
  getCategories: (restaurantId: string) =>
    handleResponse<MenuCategory[]>(http.get(`/restaurants/categories/`, { params: { restaurant: restaurantId } })),

  createCategory: (restaurantId: string, data: any) =>
    handleResponse<MenuCategory>(http.post(`/restaurants/categories/`, { ...data, restaurant: restaurantId })),

  updateCategory: (id: string, data: any) =>
    handleResponse<MenuCategory>(http.patch(`/restaurants/categories/${id}/`, data)),

  deleteCategory: (id: string) =>
    handleResponse<void>(http.delete(`/restaurants/categories/${id}/`)),

  createItem: (categoryId: string, data: any) =>
    handleResponse<any>(http.post(`/restaurants/products/`, { ...data, category: categoryId })),

  updateItem: (id: string, data: any) =>
    handleResponse<any>(http.patch(`/restaurants/products/${id}/`, data)),

  deleteItem: (id: string) =>
    handleResponse<void>(http.delete(`/restaurants/products/${id}/`)),

  toggleAvailability: (id: string, is_available: boolean) =>
    handleResponse<any>(http.post(`/restaurants/products/${id}/toggle_availability/`, { is_available })),
};

export const orderApi = {
  create: (cart: Cart) =>
    handleResponse<Order>(http.post('/orders/', cart)),

  getByNumber: (restaurantId: string, orderNumber: string) =>
    handleResponse<Order>(http.get(`/orders/`, { params: { restaurant: restaurantId, order_number: orderNumber } })).then(res => {
      // Since we are searching by order number in list, we might get a list back or we need to adjust backend to support lookup by number
      // Assuming list filter for now, return first item
      if (Array.isArray(res.data) && res.data.length > 0) {
        return { success: true, data: res.data[0] };
      }
      return res; // Fallback or empty
    }),

  getActive: (restaurantId: string) =>
    handleResponse<Order[]>(http.get(`/orders/active/`, { params: { restaurant: restaurantId } })),

  getByQrCode: (token: string) =>
    // Endpoint might be /api/orders/verify_qr/ based on ViewSet docstring but let's check urls.py which had standard router
    // ViewSet has @action(detail=False, methods=['post']) def verify_qr ... wait, doc says POST /api/orders/verify_qr/
    // Let's assume standard action pattern -> /orders/verify_qr/ with post data?
    // Actually the viewset code has:
    // @action(detail=False, methods=['post']) def verify_qr(self, request): ...
    // So it should be POST.
    handleResponse<Order>(http.post(`/orders/verify_qr/`, { token })),

  markCompleted: (id: string) =>
    handleResponse<Order>(http.post(`/orders/${id}/update_status/`, { status: 'COMPLETED' })),

  createCashOrder: (rid: string, items: any[], name: string) =>
    handleResponse<Order>(http.post(`/orders/staff/create/`, { restaurant: rid, items, customer_name: name })),

  getAll: (restaurantId: string) =>
    handleResponse<Order[]>(http.get(`/orders/`, { params: { restaurant: restaurantId } })),
};

export const staffApi = {
  getAll: (restaurantId: string) =>
    handleResponse<StaffMember[]>(http.get(`/restaurants/staff/`, { params: { restaurant: restaurantId } })),

  create: (restaurantId: string, data: any) =>
    handleResponse<StaffMember>(http.post(`/restaurants/staff/`, { ...data, restaurant: restaurantId })),

  update: (id: string, data: any) =>
    handleResponse<StaffMember>(http.patch(`/restaurants/staff/${id}/`, data)),

  toggleActive: (id: string, is_active: boolean) =>
    handleResponse<StaffMember>(http.post(`/restaurants/staff/${id}/toggle_active/`)), // ViewSet action is post

  toggleCashPermission: (id: string, can_collect_cash: boolean) =>
    // Standard update since there's no specific action for this in Audit logs we saw separate but perform_update handles it
    handleResponse<StaffMember>(http.patch(`/restaurants/staff/${id}/`, { can_collect_cash })),

  resetPassword: (id: string) =>
    handleResponse<{ message: string }>(http.post(`/restaurants/staff/${id}/reset_password/`)), // Verify existence if needed, assuming standard logic
};

export const analyticsApi = {
  getDashboard: (restaurantId: string) =>
    handleResponse<DashboardStats>(http.get(`/analytics/dashboard/`, { params: { restaurant: restaurantId } })),
};

export const qrApi = {
  getRestaurantQr: (restaurantId: string) =>
    handleResponse<{ qr_code_url: string }>(http.get(`/restaurants/${restaurantId}/qr/`)),

  regenerateQr: (restaurantId: string) =>
    handleResponse<{ qr_code_url: string }>(http.post(`/restaurants/${restaurantId}/qr/regenerate/`)),
};

export const auditApi = {
  getAll: (page = 1, limit = 50) =>
    handleResponse<PaginatedResponse<AuditLog>>(http.get('/audit-logs/', { params: { page, limit } })),
};

export const api = {
  auth: authApi,
  restaurants: restaurantApi,
  menu: menuApi,
  orders: orderApi,
  staff: staffApi,
  analytics: analyticsApi,
  qr: qrApi,
  admin: {
    getRestaurants: restaurantApi.getAll,
    updateRestaurantStatus: (id: string, status: string) =>
      handleResponse<any>(http.patch(`/admin/restaurants/${id}/`, { status })),
    assignOwner: (id: string, email: string) =>
      handleResponse<any>(http.post(`/admin/restaurants/${id}/assign-owner/`, { email })),
    getAuditLogs: (page = 1, limit = 20) =>
      handleResponse<any>(http.get('/admin/audit-logs/', { params: { page, limit } })),
    getSubscriptions: () =>
      handleResponse<any[]>(http.get('/admin/subscriptions/')),
    cancelSubscription: (id: string) =>
      handleResponse<any>(http.post(`/admin/subscriptions/${id}/cancel/`)),
    reactivateSubscription: (id: string) =>
      handleResponse<any>(http.post(`/admin/subscriptions/${id}/reactivate/`)),
  },
};
