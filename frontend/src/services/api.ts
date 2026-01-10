import axios from 'axios';
import type {
  Book,
  BookListResponse,
  User,
  TokenResponse,
  LoginRequest,
  RegisterRequest,
  Cart,
  Order,
  DemoAccount,
  ShippingAddress,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/register', data);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  getDemoAccounts: async (): Promise<DemoAccount[]> => {
    const response = await api.get<DemoAccount[]>('/auth/demo-accounts');
    return response.data;
  },
};

// Books API
export const booksApi = {
  getBooks: async (params: {
    page?: number;
    page_size?: number;
    genre?: string;
    search?: string;
    min_price?: number;
    max_price?: number;
    in_stock?: boolean;
    sort_by?: string;
    sort_order?: string;
  }): Promise<BookListResponse> => {
    const response = await api.get<BookListResponse>('/books', { params });
    return response.data;
  },

  getBook: async (id: number): Promise<Book> => {
    const response = await api.get<Book>(`/books/${id}`);
    return response.data;
  },

  getFeaturedBooks: async (limit = 8): Promise<Book[]> => {
    const response = await api.get<Book[]>('/books/featured', { params: { limit } });
    return response.data;
  },

  getRecommendations: async (limit = 8): Promise<Book[]> => {
    const response = await api.get<Book[]>('/books/recommendations', { params: { limit } });
    return response.data;
  },

  getSimilarBooks: async (bookId: number, limit = 4): Promise<Book[]> => {
    const response = await api.get<Book[]>(`/books/${bookId}/similar`, { params: { limit } });
    return response.data;
  },

  getGenres: async (): Promise<{ genre: string; count: number }[]> => {
    const response = await api.get('/books/genres');
    return response.data;
  },
};

// Cart API
export const cartApi = {
  getCart: async (): Promise<Cart> => {
    const response = await api.get<Cart>('/cart');
    return response.data;
  },

  addToCart: async (bookId: number, quantity = 1): Promise<Cart> => {
    const response = await api.post<Cart>('/cart/add', { book_id: bookId, quantity });
    return response.data;
  },

  updateCartItem: async (itemId: number, quantity: number): Promise<Cart> => {
    const response = await api.put<Cart>(`/cart/${itemId}`, { book_id: 0, quantity });
    return response.data;
  },

  removeFromCart: async (itemId: number): Promise<Cart> => {
    const response = await api.delete<Cart>(`/cart/${itemId}`);
    return response.data;
  },

  clearCart: async (): Promise<Cart> => {
    const response = await api.delete<Cart>('/cart');
    return response.data;
  },
};

// Orders API
export const ordersApi = {
  getOrders: async (): Promise<{ orders: Order[]; total: number }> => {
    const response = await api.get('/orders');
    return response.data;
  },

  getOrder: async (id: number): Promise<Order> => {
    const response = await api.get<Order>(`/orders/${id}`);
    return response.data;
  },

  getOrderByNumber: async (orderNumber: string): Promise<Order> => {
    const response = await api.get<Order>(`/orders/by-number/${orderNumber}`);
    return response.data;
  },

  checkout: async (data: {
    shipping_address: ShippingAddress;
    shipping_method: string;
  }): Promise<{ order_number: string; total_amount: number; estimated_delivery: string }> => {
    const response = await api.post('/orders/checkout', data);
    return response.data;
  },
};

// Profile API
export const profileApi = {
  getProfile: async (): Promise<User & { created_at: string; last_login: string | null }> => {
    const response = await api.get('/profile');
    return response.data;
  },

  updateProfile: async (data: {
    name?: string;
    phone?: string;
    favorite_genres?: string[];
    shipping_address?: ShippingAddress;
    newsletter_subscribed?: boolean;
  }): Promise<User> => {
    const response = await api.put('/profile', data);
    return response.data;
  },

  updatePreferences: async (genres: string[]): Promise<void> => {
    await api.put('/profile/preferences', genres);
  },
};

export default api;
