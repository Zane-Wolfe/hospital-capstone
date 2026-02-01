import type { HeatmapPoint } from '../../types'

interface LocationHeatmapProps {
  data: HeatmapPoint[]
  isLoading?: boolean
}

function getHeatColor(value: number, max: number): string {
  const ratio = max > 0 ? value / max : 0
  if (ratio < 0.25) return 'bg-green-100 border-green-300'
  if (ratio < 0.5) return 'bg-yellow-100 border-yellow-300'
  if (ratio < 0.75) return 'bg-orange-100 border-orange-300'
  return 'bg-red-100 border-red-300'
}

export default function LocationHeatmap({ data, isLoading }: LocationHeatmapProps) {
  const maxCount = Math.max(...data.map((d) => d.count), 1)

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Events by Location</h3>
      {isLoading ? (
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : data.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-gray-500">
          No data available
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {data.map((point) => (
            <div
              key={point.location}
              className={`p-4 rounded-lg border-2 ${getHeatColor(point.count, maxCount)}`}
            >
              <div className="font-medium text-gray-900 truncate" title={point.location}>
                {point.location}
              </div>
              <div className="mt-2 space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Events</span>
                  <span className="font-medium">{point.count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Avg dB</span>
                  <span className="font-medium">{point.avg_loudness.toFixed(1)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center gap-4 text-sm">
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-green-100 border border-green-300 rounded"></div>
          <span className="text-gray-500">Low</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-yellow-100 border border-yellow-300 rounded"></div>
          <span className="text-gray-500">Medium</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-orange-100 border border-orange-300 rounded"></div>
          <span className="text-gray-500">High</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-red-100 border border-red-300 rounded"></div>
          <span className="text-gray-500">Very High</span>
        </div>
      </div>
    </div>
  )
}
