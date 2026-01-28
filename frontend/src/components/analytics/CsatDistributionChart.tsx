import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

interface CsatData {
  rating: number;
  count: number;
  percentage: number;
}

interface CsatDistributionChartProps {
  data: CsatData[];
  totalRatings: number;
}

const RATING_COLORS = {
  5: '#10B981', // green - excellent
  4: '#3B82F6', // blue - good
  3: '#F59E0B', // yellow - neutral
  2: '#F97316', // orange - poor
  1: '#EF4444', // red - very poor
};

export default function CsatDistributionChart({ data, totalRatings }: CsatDistributionChartProps) {
  const chartData = data.map((item) => ({
    rating: `${item.rating} ⭐`,
    count: item.count,
    percentage: item.percentage,
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">CSAT Score Distribution</h3>
      <p className="text-sm text-gray-600 mb-4">
        Customer satisfaction ratings breakdown ({totalRatings} total ratings)
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="rating" />
          <YAxis />
          <Tooltip 
            formatter={(value: number, name: string) => {
              if (name === 'count') {
                return [`${value} ratings`, 'Count'];
              }
              return [`${value}%`, 'Percentage'];
            }}
          />
          <Legend />
          <Bar dataKey="count" name="Ratings" radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => {
              const rating = parseInt(entry.rating.split(' ')[0]);
              return (
                <Cell 
                  key={`cell-${index}`} 
                  fill={RATING_COLORS[rating as keyof typeof RATING_COLORS] || '#6B7280'} 
                />
              );
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-4 text-sm text-gray-600">
        {data.map((item) => (
          <div key={item.rating} className="flex items-center justify-between mb-1">
            <div className="flex items-center">
              <span className="mr-2">{'⭐'.repeat(item.rating)}</span>
              <span>{item.rating} stars:</span>
            </div>
            <span className="font-semibold">{item.count} ({item.percentage}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}
