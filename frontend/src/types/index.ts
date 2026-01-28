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

// Analytics types
export interface DashboardMetrics {
  total_conversations: number;
  avg_csat_score: number | null;
  resolution_rate: number;
  top_topics: Array<{ topic: string; count: number }>;
  volume_trend: Array<{ date: string; count: number }>;
  time_range: string;
}

export interface SatisfactionMetrics {
  csat_trend: Array<{ date: string; avg_csat: number }>;
  sentiment: {
    total_with_sentiment: number;
    avg_sentiment_score: number | null;
  };
  response_times: {
    avg_seconds: number | null;
    min_seconds: number | null;
    max_seconds: number | null;
  };
  resolution_breakdown: {
    total: number;
    resolved: number;
    escalated: number;
    resolution_rate: number;
    escalation_rate: number;
  };
}

export interface TopicDistribution {
  topic: string;
  count: number;
  success_rate: number | null;
  escalation_rate: number | null;
}

export interface TopicAnalytics {
  distribution: TopicDistribution[];
  trends: Array<{ date: string; [topic: string]: string | number }>;
  time_range: string;
}

export interface ConversationAnalytics {
  session_id: string;
  user_email: string | null;
  started_at: string;
  ended_at: string | null;
  message_count: number;
  tool_count: number;
  tools_used: string[] | null;
  sentiment_score: number | null;
  csat_score: number | null;
  resolved: boolean;
  escalated: boolean;
  duration_seconds: number | null;
}

export interface ConversationListResponse {
  conversations: ConversationAnalytics[];
  limit: number;
  offset: number;
}

export interface SentimentDistribution {
  distribution: Array<{ sentiment: string; count: number; percentage: number }>;
  total: number;
  time_range: string;
}

export interface ToolUsageStats {
  tools: Array<{ tool_name: string; count: number; percentage: number }>;
  total_conversations_with_tools: number;
  time_range: string;
}

export interface CsatDistribution {
  distribution: Array<{ rating: number; count: number; percentage: number }>;
  total_ratings: number;
  time_range: string;
}

export interface TrendData {
  metric: string;
  time_range: string;
  trends: Array<{ date: string; value: number } | { date: string; [key: string]: string | number }>;
}
