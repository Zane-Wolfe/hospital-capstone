import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'
import type { TimeSeriesPoint } from '../../types'

interface LoudnessChartProps {
  data: TimeSeriesPoint[]
  isLoading?: boolean
}

export default function LoudnessChart({ data, isLoading }: LoudnessChartProps) {
  const chartData = data.map((point) => ({
    time: new Date(point.time).getTime(),
    value: point.value,
  }))

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Loudness Over Time</h3>
      {isLoading ? (
        <div className="h-64 flex items-center justify-center" data-testid="chart-loading">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : data.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-gray-500" data-testid="chart-no-data">
          No data available
        </div>
      ) : (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="time"
                type="number"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(value) => format(new Date(value), 'HH:mm')}
                stroke="#6b7280"
                fontSize={12}
              />
              <YAxis
                stroke="#6b7280"
                fontSize={12}
                tickFormatter={(value) => `${value} dB`}
              />
              <Tooltip
                labelFormatter={(value) => format(new Date(value), 'MMM d, HH:mm:ss')}
                formatter={(value: number) => [`${value.toFixed(1)} dB`, 'Loudness']}
                contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
