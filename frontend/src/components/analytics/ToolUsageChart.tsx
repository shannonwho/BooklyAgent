import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ToolData {
  tool_name: string;
  count: number;
  percentage: number;
}

interface ToolUsageChartProps {
  data: ToolData[];
  totalConversations: number;
}

export default function ToolUsageChart({ data, totalConversations }: ToolUsageChartProps) {
  // Format tool names for display (remove underscores, capitalize)
  const formatToolName = (name: string) => {
    return name
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const chartData = data.slice(0, 8).map((item) => ({
    tool: formatToolName(item.tool_name),
    count: item.count,
    percentage: item.percentage,
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Tool Usage Frequency</h3>
      <p className="text-sm text-gray-600 mb-4">
        Most frequently used agent tools ({totalConversations} conversations with tools)
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis dataKey="tool" type="category" width={120} />
          <Tooltip 
            formatter={(value: number, name: string) => {
              if (name === 'count') {
                return [`${value} uses`, 'Usage'];
              }
              return [`${value}%`, 'Percentage'];
            }}
          />
          <Legend />
          <Bar 
            dataKey="count" 
            fill="#8B5CF6" 
            name="Usage Count"
            radius={[0, 8, 8, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
      {data.length > 8 && (
        <p className="mt-2 text-xs text-gray-500">Showing top 8 tools</p>
      )}
    </div>
  );
}
