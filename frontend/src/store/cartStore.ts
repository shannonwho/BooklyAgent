import { create } from 'zustand';
import type { Cart, CartItem } from '../types';
import { cartApi } from '../services/api';

interface CartState {
  cart: Cart | null;
  isLoading: boolean;
  error: string | null;
  fetchCart: () => Promise<void>;
  addToCart: (bookId: number, quantity?: number) => Promise<void>;
  updateQuantity: (itemId: number, quantity: number) => Promise<void>;
  removeItem: (itemId: number) => Promise<void>;
  clearCart: () => Promise<void>;
  clearError: () => void;
}

const emptyCart: Cart = {
  items: [],
  total_items: 0,
  subtotal: 0,
  shipping: 0,
  total: 0,
};

export const useCartStore = create<CartState>((set, get) => ({
  cart: null,
  isLoading: false,
  error: null,

  fetchCart: async () => {
    set({ isLoading: true, error: null });
    try {
      const cart = await cartApi.getCart();
      set({ cart, isLoading: false });
    } catch (error: any) {
      // If not authenticated, use empty cart
      if (error.response?.status === 401) {
        set({ cart: emptyCart, isLoading: false });
      } else {
        set({
          error: error.response?.data?.detail || 'Failed to fetch cart',
          isLoading: false,
        });
      }
    }
  },

  addToCart: async (bookId: number, quantity = 1) => {
    set({ isLoading: true, error: null });
    try {
      const cart = await cartApi.addToCart(bookId, quantity);
      set({ cart, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to add item to cart',
        isLoading: false,
      });
      throw error;
    }
  },

  updateQuantity: async (itemId: number, quantity: number) => {
    set({ isLoading: true, error: null });
    try {
      const cart = await cartApi.updateCartItem(itemId, quantity);
      set({ cart, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to update quantity',
        isLoading: false,
      });
      throw error;
    }
  },

  removeItem: async (itemId: number) => {
    set({ isLoading: true, error: null });
    try {
      const cart = await cartApi.removeFromCart(itemId);
      set({ cart, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to remove item',
        isLoading: false,
      });
      throw error;
    }
  },

  clearCart: async () => {
    set({ isLoading: true, error: null });
    try {
      const cart = await cartApi.clearCart();
      set({ cart, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Failed to clear cart',
        isLoading: false,
      });
      throw error;
    }
  },

  clearError: () => set({ error: null }),
}));
