import type { DeviceMetrics } from '../../types'

interface DeviceInfoPopoverProps {
  sensorId: string
  metrics?: DeviceMetrics
  x: number
  y: number
}

export function DeviceInfoPopover({ sensorId, metrics, x, y }: DeviceInfoPopoverProps) {
  return (
    <div
      className="absolute bg-white rounded-lg shadow-lg p-3 z-50 pointer-events-none"
      style={{
        left: x + 20,
        top: y - 10,
        minWidth: '150px',
      }}
    >
      <div className="text-sm font-semibold text-gray-900 mb-1">{sensorId}</div>
      {metrics ? (
        <div className="text-xs text-gray-600 space-y-0.5">
          <div className="flex items-center gap-1">
            <span
              className={`w-2 h-2 rounded-full ${
                metrics.is_online ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            {metrics.is_online ? 'Online' : 'Offline'}
          </div>
          {metrics.battery_percent !== null && (
            <div>Battery: {metrics.battery_percent}%</div>
          )}
          {metrics.location && <div>Location: {metrics.location}</div>}
        </div>
      ) : (
        <div className="text-xs text-gray-500">No metrics available</div>
      )}
    </div>
  )
}
