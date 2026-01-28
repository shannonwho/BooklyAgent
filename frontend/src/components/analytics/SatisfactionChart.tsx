import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface SatisfactionChartProps {
  data: Array<{ date: string; avg_csat: number }>;
}

export default function SatisfactionChart({ data }: SatisfactionChartProps) {
  const chartData = data.map((item) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    'CSAT Score': item.avg_csat,
  }));

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">CSAT Score Over Time</h3>
        <div className="flex items-center justify-center h-[300px]">
          <p className="text-gray-500">No CSAT data available for this time period</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">CSAT Score Over Time</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={[0, 5]} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="CSAT Score" stroke="#3B82F6" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
