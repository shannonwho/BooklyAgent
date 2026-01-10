// Book types
export interface Book {
  id: number;
  isbn: string;
  title: string;
  author: string;
  genre: string;
  price: number;
  description: string;
  cover_image: string | null;
  stock_quantity: number;
  rating: number;
  num_reviews: number;
  page_count: number;
}

export interface BookListResponse {
  books: Book[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// User types
export interface User {
  id: number;
  email: string;
  name: string;
  phone: string | null;
  favorite_genres: string[];
  shipping_address: ShippingAddress | null;
}

export interface ShippingAddress {
  name: string;
  street: string;
  city: string;
  state: string;
  zip: string;
  country: string;
}

export interface DemoAccount {
  email: string;
  name: string;
  description: string;
  preferences: string[];
}

// Auth types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  phone?: string;
  favorite_genres?: string[];
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Cart types
export interface CartItem {
  id: number;
  book_id: number;
  book_title: string;
  book_author: string;
  book_cover: string | null;
  book_price: number;
  quantity: number;
  subtotal: number;
}

export interface Cart {
  items: CartItem[];
  total_items: number;
  subtotal: number;
  shipping: number;
  total: number;
}

// Order types
export interface OrderItem {
  id: number;
  book_id: number;
  book_title: string;
  book_author: string;
  book_cover: string | null;
  quantity: number;
  price_per_unit: number;
  subtotal: number;
}

export interface Order {
  id: number;
  order_number: string;
  status: OrderStatus;
  total_amount: number;
  subtotal: number;
  shipping_cost: number;
  tax: number;
  shipping_address: ShippingAddress;
  shipping_method: string;
  tracking_number: string | null;
  carrier: string | null;
  estimated_delivery: string | null;
  items: OrderItem[];
  order_date: string;
  shipped_date: string | null;
  delivered_date: string | null;
  return_requested: boolean;
  return_approved: boolean;
  refund_amount: number;
}

export type OrderStatus =
  | 'pending'
  | 'processing'
  | 'shipped'
  | 'delivered'
  | 'cancelled'
  | 'returned';

// Chat types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export interface WebSocketMessage {
  type: 'message' | 'stream' | 'typing' | 'tool_use' | 'tool_result' | 'message_complete' | 'error' | 'connected' | 'pong';
  content?: string;
  message?: string;
  tool?: string;
  status?: boolean | string;
  session_id?: string;
}

// Genre types
export const GENRES = [
  'Fiction',
  'Sci-Fi',
  'Mystery',
  'Romance',
  'Self-Help',
  'Biography',
  'History',
  'Business',
  'Fantasy',
  'Thriller',
] as const;

export type Genre = typeof GENRES[number];
