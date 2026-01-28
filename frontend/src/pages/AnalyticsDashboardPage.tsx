import { useState, useEffect } from 'react';
import { BarChart3, MessageSquare, Star, CheckCircle, TrendingUp } from 'lucide-react';
import { analyticsApi } from '../services/analytics';
import type {
  DashboardMetrics,
  SatisfactionMetrics,
  TopicAnalytics,
  ConversationListResponse,
  SentimentDistribution,
  ToolUsageStats,
} from '../types';
import MetricCard from '../components/analytics/MetricCard';
import TopicChart from '../components/analytics/TopicChart';
import SatisfactionChart from '../components/analytics/SatisfactionChart';
import TrendChart from '../components/analytics/TrendChart';
import ConversationStats from '../components/analytics/ConversationStats';
import SentimentChart from '../components/analytics/SentimentChart';
import ToolUsageChart from '../components/analytics/ToolUsageChart';

export default function AnalyticsDashboardPage() {
  const [timeRange, setTimeRange] = useState('7d');
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState<DashboardMetrics | null>(null);
  const [satisfactionData, setSatisfactionData] = useState<SatisfactionMetrics | null>(null);
  const [topicData, setTopicData] = useState<TopicAnalytics | null>(null);
  const [conversations, setConversations] = useState<ConversationListResponse | null>(null);
  const [sentimentData, setSentimentData] = useState<SentimentDistribution | null>(null);
  const [toolUsageData, setToolUsageData] = useState<ToolUsageStats | null>(null);

  useEffect(() => {
    loadData();
  }, [timeRange]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [dashboard, satisfaction, topics, convs, sentiment, toolUsage] = await Promise.all([
        analyticsApi.getDashboard(timeRange),
        analyticsApi.getSatisfaction(timeRange),
        analyticsApi.getTopics(timeRange),
        analyticsApi.getConversations(20, 0),
        analyticsApi.getSentimentDistribution(timeRange),
        analyticsApi.getToolUsage(timeRange),
      ]);
      setDashboardData(dashboard);
      setSatisfactionData(satisfaction);
      setTopicData(topics);
      setConversations(convs);
      setSentimentData(sentiment);
      setToolUsageData(toolUsage);
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="mt-2 text-gray-600">Track customer satisfaction and support topics</p>
        </div>

        {/* Time Range Selector */}
        <div className="mb-6 flex items-center space-x-4">
          <label className="text-sm font-medium text-gray-700">Time Range:</label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>

        {/* Overview Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Total Conversations"
            value={dashboardData?.total_conversations || 0}
            icon={<MessageSquare className="h-5 w-5" />}
          />
          <MetricCard
            title="Average CSAT Score"
            value={dashboardData?.avg_csat_score ? `${dashboardData.avg_csat_score.toFixed(1)}/5` : 'N/A'}
            icon={<Star className="h-5 w-5" />}
          />
          <MetricCard
            title="Resolution Rate"
            value={dashboardData?.resolution_rate ? `${dashboardData.resolution_rate.toFixed(1)}%` : '0%'}
            icon={<CheckCircle className="h-5 w-5" />}
          />
          <MetricCard
            title="Volume Trend"
            value={dashboardData?.volume_trend.length || 0}
            subtitle="Data points"
            icon={<TrendingUp className="h-5 w-5" />}
          />
        </div>

        {/* Charts Row 1 - Support Topics and Sentiment Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {topicData && topicData.distribution.length > 0 && (
            <TopicChart data={topicData.distribution} />
          )}
          {sentimentData && sentimentData.distribution.length > 0 && (
            <SentimentChart data={sentimentData.distribution} />
          )}
        </div>

        {/* Charts Row 2 - Conversation Volume Trend */}
        {dashboardData ? (
          <div className="mb-8">
            <TrendChart
              data={dashboardData.volume_trend || []}
              title="Conversation Volume Trend"
              yAxisLabel="Conversations"
            />
          </div>
        ) : null}

        {/* CSAT Score Over Time - Main CSAT Widget */}
        {satisfactionData && satisfactionData.csat_trend && satisfactionData.csat_trend.length > 0 ? (
          <div className="mb-8">
            <SatisfactionChart data={satisfactionData.csat_trend} />
          </div>
        ) : null}

        {/* Tool Usage Chart - Full width for VP of Engineering */}
        {toolUsageData && toolUsageData.tools.length > 0 && (
          <div className="mb-8">
            <ToolUsageChart 
              data={toolUsageData.tools} 
              totalConversations={toolUsageData.total_conversations_with_tools}
            />
          </div>
        )}

        {/* Satisfaction Breakdown */}
        {satisfactionData && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <MetricCard
              title="Avg Response Time"
              value={
                satisfactionData.response_times.avg_seconds
                  ? `${Math.round(satisfactionData.response_times.avg_seconds / 60)}m`
                  : 'N/A'
              }
              subtitle="Average conversation duration"
            />
            <MetricCard
              title="Resolved"
              value={satisfactionData.resolution_breakdown.resolved}
              subtitle={`${satisfactionData.resolution_breakdown.resolution_rate.toFixed(1)}% resolution rate`}
            />
            <MetricCard
              title="Escalated"
              value={satisfactionData.resolution_breakdown.escalated}
              subtitle={`${satisfactionData.resolution_breakdown.escalation_rate.toFixed(1)}% escalation rate`}
            />
          </div>
        )}

        {/* Top Topics */}
        {dashboardData && dashboardData.top_topics.length > 0 && (
          <div className="mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Support Topics</h3>
              <div className="space-y-3">
                {dashboardData.top_topics.map((topic, index) => (
                  <div key={topic.topic} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-gray-500 w-8">{index + 1}.</span>
                      <span className="text-sm text-gray-900">{topic.topic}</span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">{topic.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Conversation Stats */}
        {conversations && conversations.conversations.length > 0 && (
          <div className="mb-8">
            <ConversationStats conversations={conversations.conversations} />
          </div>
        )}

        {/* Empty State */}
        {(!dashboardData || dashboardData.total_conversations === 0) && (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
            <p className="text-gray-600">
              Start having conversations with the support agent to see analytics data.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
