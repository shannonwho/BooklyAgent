import api from './api';
import type {
  DashboardMetrics,
  SatisfactionMetrics,
  TopicAnalytics,
  ConversationListResponse,
  TrendData,
  SentimentDistribution,
  ToolUsageStats,
  CsatDistribution,
} from '../types';

export const analyticsApi = {
  getDashboard: async (timeRange: string = '7d'): Promise<DashboardMetrics> => {
    const response = await api.get<DashboardMetrics>(`/analytics/dashboard`, {
      params: { time_range: timeRange },
    });
    return response.data;
  },

  getSatisfaction: async (timeRange: string = '7d'): Promise<SatisfactionMetrics> => {
    const response = await api.get<SatisfactionMetrics>(`/analytics/satisfaction`, {
      params: { time_range: timeRange },
    });
    return response.data;
  },

  getTopics: async (timeRange: string = '7d'): Promise<TopicAnalytics> => {
    const response = await api.get<TopicAnalytics>(`/analytics/topics`, {
      params: { time_range: timeRange },
    });
    return response.data;
  },

  getConversations: async (
    limit: number = 50,
    offset: number = 0,
    topic?: string,
    userEmail?: string
  ): Promise<ConversationListResponse> => {
    const params: Record<string, string> = {
      limit: limit.toString(),
      offset: offset.toString(),
    };
    if (topic) params.topic = topic;
    if (userEmail) params.user_email = userEmail;
    
    const response = await api.get<ConversationListResponse>(`/analytics/conversations`, { params });
    return response.data;
  },

  getTrends: async (metric: string = 'conversations', timeRange: string = '7d'): Promise<TrendData> => {
    const response = await api.get<TrendData>(`/analytics/trends`, {
      params: { metric, time_range: timeRange },
    });
    return response.data;
  },

  submitRating: async (sessionId: string, rating: number, comment?: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post('/analytics/rating', {
      session_id: sessionId,
      rating,
      comment,
    });
    return response.data;
  },

  getSentimentDistribution: async (timeRange: string = '7d'): Promise<SentimentDistribution> => {
    const response = await api.get<SentimentDistribution>(`/analytics/sentiment-distribution`, {
      params: { time_range: timeRange },
    });
    return response.data;
  },

  getToolUsage: async (timeRange: string = '7d'): Promise<ToolUsageStats> => {
    const response = await api.get<ToolUsageStats>(`/analytics/tool-usage`, {
      params: { time_range: timeRange },
    });
    return response.data;
  },

  getCsatDistribution: async (timeRange: string = '7d'): Promise<CsatDistribution> => {
    const response = await api.get<CsatDistribution>(`/analytics/csat-distribution`, {
      params: { time_range: timeRange },
    });
    return response.data;
  },
};
