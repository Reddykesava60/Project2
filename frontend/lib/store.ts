// ============================================
// ZUSTAND STORE - Cart only (as per PRD)
// All other state comes from API
// ============================================

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { CartItem, MenuItem, PaymentMethod } from './types';
import { authApi } from './api';

interface CartStore {
  restaurantId: string | null;
  restaurantSlug: string | null;
  items: CartItem[];
  customerName: string;
  paymentMethod: PaymentMethod;
  isParcel: boolean;
  spicyLevel: 'normal' | 'medium' | 'high';

  // Actions
  setRestaurant: (id: string, slug: string) => void;
  addItem: (item: MenuItem, quantity?: number) => void;
  removeItem: (itemId: string) => void;
  updateQuantity: (itemId: string, quantity: number) => void;
  setCustomerName: (name: string) => void;
  setPaymentMethod: (method: PaymentMethod) => void;
  setParcel: (isParcel: boolean) => void;
  setSpicyLevel: (level: 'normal' | 'medium' | 'high') => void;
  clearCart: () => void;

  // Computed
  getTotal: () => number;
  getItemCount: () => number;
}

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      restaurantId: null,
      restaurantSlug: null,
      items: [],
      customerName: '',
      paymentMethod: 'upi',  // Backend uses 'upi' for online payments
      isParcel: false,
      spicyLevel: 'normal',

      setRestaurant: (id, slug) => {
        const state = get();
        // Clear cart if switching restaurants
        if (state.restaurantId && state.restaurantId !== id) {
          set({
            restaurantId: id,
            restaurantSlug: slug,
            items: [],
            customerName: '',
            paymentMethod: 'upi',  // Backend uses 'upi' for online payments
            isParcel: false,
            spicyLevel: 'normal',
          });
        } else {
          set({ restaurantId: id, restaurantSlug: slug });
        }
      },

      addItem: (item, quantity = 1) => {
        set((state) => {
          const existingIndex = state.items.findIndex(
            (i) => i.menu_item.id === item.id
          );

          if (existingIndex >= 0) {
            const newItems = [...state.items];
            newItems[existingIndex].quantity += quantity;
            return { items: newItems };
          }

          return {
            items: [...state.items, { menu_item: item, quantity }],
          };
        });
      },

      removeItem: (itemId) => {
        set((state) => ({
          items: state.items.filter((i) => i.menu_item.id !== itemId),
        }));
      },

      updateQuantity: (itemId, quantity) => {
        if (quantity <= 0) {
          get().removeItem(itemId);
          return;
        }

        set((state) => ({
          items: state.items.map((i) =>
            i.menu_item.id === itemId ? { ...i, quantity } : i
          ),
        }));
      },

      setCustomerName: (name) => set({ customerName: name }),

      setPaymentMethod: (method) => set({ paymentMethod: method }),

      setParcel: (isParcel) => set({ isParcel }),

      setSpicyLevel: (level) => set({ spicyLevel: level }),

      clearCart: () =>
        set({
          items: [],
          customerName: '',
          paymentMethod: 'upi',  // Backend uses 'upi' for online payments
          isParcel: false,
          spicyLevel: 'normal',
        }),

      getTotal: () => {
        const { items } = get();
        return items.reduce(
          (total, item) => total + item.menu_item.price * item.quantity,
          0
        );
      },

      getItemCount: () => {
        const { items } = get();
        return items.reduce((count, item) => count + item.quantity, 0);
      },
    }),
    {
      name: 'restaurant-cart',
      partialize: (state) => ({
        restaurantId: state.restaurantId,
        restaurantSlug: state.restaurantSlug,
        items: state.items,
        customerName: state.customerName,
        paymentMethod: state.paymentMethod,
        isParcel: state.isParcel,
        spicyLevel: state.spicyLevel,
      }),
    }
  )
);

// ============================================
// AUTH CONTEXT STORE (Read-only from API)
// ============================================

import type { User } from './types';

interface AuthStore {
  user: User | null;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  initSession: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>()((set) => ({
  user: null,
  isLoading: true,
  setUser: (user) => set({ user, isLoading: false }),
  setLoading: (isLoading) => set({ isLoading }),
  initSession: async () => {
    set({ isLoading: true });
    const response = await authApi.getCurrentUser();
    if (response.success && response.data) {
      set({ user: response.data, isLoading: false });
    } else {
      set({ user: null, isLoading: false });
    }
  },
}));
