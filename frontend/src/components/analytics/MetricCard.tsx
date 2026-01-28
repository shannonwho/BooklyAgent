import { TrendingUp, TrendingDown } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number | null;
  subtitle?: string;
  trend?: number;
  icon?: React.ReactNode;
}

export default function MetricCard({ title, value, subtitle, trend, icon }: MetricCardProps) {
  const displayValue = value !== null && value !== undefined ? value : 'N/A';
  const trendUp = trend !== undefined && trend > 0;
  const trendDown = trend !== undefined && trend < 0;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>
      <div className="flex items-baseline">
        <p className="text-3xl font-bold text-gray-900">{displayValue}</p>
        {trend !== undefined && (
          <div className={`ml-2 flex items-center ${trendUp ? 'text-green-600' : trendDown ? 'text-red-600' : 'text-gray-600'}`}>
            {trendUp ? <TrendingUp className="h-4 w-4" /> : trendDown ? <TrendingDown className="h-4 w-4" /> : null}
            <span className="ml-1 text-sm font-medium">
              {trend > 0 ? '+' : ''}{trend.toFixed(1)}%
            </span>
          </div>
        )}
      </div>
      {subtitle && <p className="mt-2 text-sm text-gray-500">{subtitle}</p>}
    </div>
  );
}
