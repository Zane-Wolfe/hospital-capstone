import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { format } from 'date-fns'
import type { TimeSeriesPoint } from '../../types'

interface LoudnessBarChartProps {
  data: TimeSeriesPoint[]
  isLoading?: boolean
}

export function LoudnessBarChart({ data, isLoading }: LoudnessBarChartProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-4">Loudness Levels (dB)</h3>
        <div className="h-64 flex items-center justify-center">
          <div className="animate-pulse text-gray-400">Loading chart data...</div>
        </div>
      </div>
    )
  }

  const chartData = data.map((point) => ({
    time: format(new Date(point.time), 'HH:mm'),
    value: Math.round(point.value * 10) / 10,
    fullTime: format(new Date(point.time), 'MMM d, HH:mm'),
  }))

  return (
    <div className="bg-white rounded-lg border p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-4">Loudness Levels (dB)</h3>
      {chartData.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-gray-500">
          No data available for selected time range
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={256}>
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 11, fill: '#6b7280' }}
              tickLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#6b7280' }}
              tickLine={{ stroke: '#e5e7eb' }}
              domain={['auto', 'auto']}
              label={{ value: 'dB', angle: -90, position: 'insideLeft', fontSize: 11, fill: '#6b7280' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                fontSize: '12px',
              }}
              formatter={(value: number) => [`${value} dB`, 'Loudness']}
              labelFormatter={(_, payload) => payload[0]?.payload?.fullTime || ''}
            />
            <Bar
              dataKey="value"
              fill="#3b82f6"
              radius={[4, 4, 0, 0]}
              maxBarSize={50}
            />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
