import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface SentimentData {
  sentiment: string;
  count: number;
  percentage: number;
}

interface SentimentChartProps {
  data: SentimentData[];
}

const COLORS = {
  Positive: '#10B981', // green
  Neutral: '#6B7280',  // gray
  Negative: '#EF4444', // red
};

export default function SentimentChart({ data }: SentimentChartProps) {
  const chartData = data.map((item) => ({
    sentiment: item.sentiment,
    count: item.count,
    percentage: item.percentage,
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer Sentiment Distribution</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="sentiment" />
          <YAxis />
          <Tooltip 
            formatter={(value: number, name: string) => {
              if (name === 'count') {
                return [`${value} conversations`, 'Count'];
              }
              return [`${value}%`, 'Percentage'];
            }}
          />
          <Legend />
          <Bar 
            dataKey="count" 
            fill="#3B82F6" 
            name="Conversations"
            radius={[8, 8, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-4 text-sm text-gray-600">
        {data.map((item) => (
          <div key={item.sentiment} className="flex items-center justify-between mb-1">
            <div className="flex items-center">
              <div 
                className="w-3 h-3 rounded mr-2" 
                style={{ backgroundColor: COLORS[item.sentiment as keyof typeof COLORS] || '#6B7280' }}
              />
              <span>{item.sentiment}:</span>
            </div>
            <span className="font-semibold">{item.count} ({item.percentage}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}
