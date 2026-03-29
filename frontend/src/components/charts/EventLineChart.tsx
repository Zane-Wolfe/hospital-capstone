import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { format } from 'date-fns'
import type { EventTypeTimeSeries } from '../../types'

interface EventLineChartProps {
  data: EventTypeTimeSeries[]
  isLoading?: boolean
}

const COLORS = [
  '#ef4444', // red - alarms
  '#f59e0b', // amber - coughing
  '#3b82f6', // blue - speech
  '#8b5cf6', // purple - door_knock
  '#6366f1', // indigo - door_open_close
  '#6b7280', // gray - footsteps
  '#22c55e', // green - carts_rolling
]

export function EventLineChart({ data, isLoading }: EventLineChartProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-4">Events by Type</h3>
        <div className="h-64 flex items-center justify-center">
          <div className="animate-pulse text-gray-400">Loading chart data...</div>
        </div>
      </div>
    )
  }

  // Transform data for Recharts - need to pivot the data
  const timeMap = new Map<string, Record<string, number>>()

  data.forEach((series) => {
    series.data.forEach((point) => {
      const timeKey = point.time
      if (!timeMap.has(timeKey)) {
        timeMap.set(timeKey, {})
      }
      timeMap.get(timeKey)![series.event_type] = point.value
    })
  })

  const chartData = Array.from(timeMap.entries())
    .map(([time, values]) => ({
      time: format(new Date(time), 'HH:mm'),
      fullTime: format(new Date(time), 'MMM d, HH:mm'),
      ...values,
    }))
    .sort((a, b) => a.time.localeCompare(b.time))

  const eventTypes = data.map((d) => d.event_type)

  return (
    <div className="bg-white rounded-lg border p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-4">Events by Type</h3>
      {chartData.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-gray-500">
          No data available for selected time range
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 11, fill: '#6b7280' }}
              tickLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#6b7280' }}
              tickLine={{ stroke: '#e5e7eb' }}
              allowDecimals={false}
              label={{ value: 'Count', angle: -90, position: 'insideLeft', fontSize: 11, fill: '#6b7280' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                fontSize: '12px',
              }}
              labelFormatter={(_, payload) => payload[0]?.payload?.fullTime || ''}
            />
            <Legend
              wrapperStyle={{ fontSize: '11px' }}
              formatter={(value: string) => value.replace(/_/g, ' ')}
            />
            {eventTypes.map((eventType, idx) => (
              <Line
                key={eventType}
                type="monotone"
                dataKey={eventType}
                stroke={COLORS[idx % COLORS.length]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
                name={eventType}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
