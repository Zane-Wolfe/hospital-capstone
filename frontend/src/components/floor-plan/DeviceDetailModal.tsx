import { format } from 'date-fns'
import type { DeviceMetrics, DevicePosition } from '../../types'

interface DeviceDetailModalProps {
  sensorId: string
  position?: DevicePosition
  metrics?: DeviceMetrics
  onClose: () => void
}

export function DeviceDetailModal({
  sensorId,
  position,
  metrics,
  onClose,
}: DeviceDetailModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-xl font-semibold">{sensorId}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          {/* Status */}
          <div className="flex items-center gap-2">
            <span
              className={`w-3 h-3 rounded-full ${
                metrics?.is_online ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="font-medium">
              {metrics?.is_online ? 'Online' : 'Offline'}
            </span>
          </div>

          {/* Position Info */}
          {position && (
            <div className="bg-gray-50 rounded-lg p-3">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Position</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">X:</span> {Math.round(position.x_coord)}px
                </div>
                <div>
                  <span className="text-gray-500">Y:</span> {Math.round(position.y_coord)}px
                </div>
                {position.label && (
                  <div className="col-span-2">
                    <span className="text-gray-500">Label:</span> {position.label}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Metrics */}
          {metrics && (
            <div className="bg-gray-50 rounded-lg p-3">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Device Metrics</h3>
              <div className="space-y-2 text-sm">
                {metrics.location && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Location:</span>
                    <span>{metrics.location}</span>
                  </div>
                )}
                {metrics.battery_percent !== null && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Battery:</span>
                    <span className={metrics.battery_percent < 20 ? 'text-red-600' : ''}>
                      {metrics.battery_percent}%
                    </span>
                  </div>
                )}
                {metrics.bandwidth_kbps !== null && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Bandwidth:</span>
                    <span>{metrics.bandwidth_kbps.toFixed(1)} kbps</span>
                  </div>
                )}
                {metrics.signal_strength_dbm !== null && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Signal:</span>
                    <span>{metrics.signal_strength_dbm} dBm</span>
                  </div>
                )}
                {metrics.firmware_version && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Firmware:</span>
                    <span>{metrics.firmware_version}</span>
                  </div>
                )}
                {metrics.last_heartbeat && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Last Seen:</span>
                    <span>{format(new Date(metrics.last_heartbeat), 'MMM d, HH:mm:ss')}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {!metrics && !position && (
            <div className="text-gray-500 text-center py-4">
              No information available for this device
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
