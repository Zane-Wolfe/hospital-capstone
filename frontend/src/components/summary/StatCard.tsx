interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon?: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'gray'
}

const colorClasses = {
  blue: 'bg-blue-50 border-blue-200 text-blue-600',
  green: 'bg-green-50 border-green-200 text-green-600',
  yellow: 'bg-yellow-50 border-yellow-200 text-yellow-600',
  red: 'bg-red-50 border-red-200 text-red-600',
  gray: 'bg-gray-50 border-gray-200 text-gray-600',
}

const iconBgClasses = {
  blue: 'bg-blue-100',
  green: 'bg-green-100',
  yellow: 'bg-yellow-100',
  red: 'bg-red-100',
  gray: 'bg-gray-100',
}

export function StatCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  color = 'blue',
}: StatCardProps) {
  return (
    <div className={`rounded-lg border p-4 ${colorClasses[color]}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-1 text-2xl font-semibold">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-gray-500">{subtitle}</p>}
          {trend && trendValue && (
            <div className="mt-2 flex items-center gap-1 text-xs">
              {trend === 'up' && (
                <span className="text-green-600">+{trendValue}</span>
              )}
              {trend === 'down' && (
                <span className="text-red-600">-{trendValue}</span>
              )}
              {trend === 'neutral' && (
                <span className="text-gray-500">{trendValue}</span>
              )}
            </div>
          )}
        </div>
        {icon && (
          <div className={`p-2 rounded-lg ${iconBgClasses[color]}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  )
}
