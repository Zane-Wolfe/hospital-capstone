import type { DeviceMetricsSummary } from '../../types'

interface DeviceHealthSummaryProps {
  summary: DeviceMetricsSummary | null
  isLoading?: boolean
}

export function DeviceHealthSummary({ summary, isLoading }: DeviceHealthSummaryProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Device Health</h3>
        <div className="animate-pulse space-y-3">
          <div className="h-6 bg-gray-200 rounded w-1/2" />
          <div className="h-6 bg-gray-200 rounded w-2/3" />
          <div className="h-6 bg-gray-200 rounded w-1/3" />
        </div>
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Device Health</h3>
        <p className="text-sm text-gray-500">No data available</p>
      </div>
    )
  }

  const onlinePercent = summary.total_devices > 0
    ? Math.round((summary.online_count / summary.total_devices) * 100)
    : 0

  return (
    <div className="bg-white rounded-lg border p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Device Health</h3>

      <div className="space-y-3">
        {/* Online Status Bar */}
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-600">Online Devices</span>
            <span className="font-medium">{summary.online_count} / {summary.total_devices}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${onlinePercent}%` }}
            />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-2 pt-2">
          <div className="text-center">
            <div className="text-lg font-semibold text-green-600">{summary.online_count}</div>
            <div className="text-xs text-gray-500">Online</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-red-600">{summary.offline_count}</div>
            <div className="text-xs text-gray-500">Offline</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-yellow-600">{summary.low_battery_count}</div>
            <div className="text-xs text-gray-500">Low Battery</div>
          </div>
        </div>

        {/* Alerts */}
        {(summary.offline_count > 0 || summary.low_battery_count > 0) && (
          <div className="border-t pt-2 mt-2">
            {summary.offline_count > 0 && (
              <div className="flex items-center gap-2 text-xs text-red-600">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                {summary.offline_count} device{summary.offline_count > 1 ? 's' : ''} offline
              </div>
            )}
            {summary.low_battery_count > 0 && (
              <div className="flex items-center gap-2 text-xs text-yellow-600 mt-1">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                {summary.low_battery_count} device{summary.low_battery_count > 1 ? 's' : ''} low battery
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
