import { useState } from 'react'
import { useDeviceMetrics, useDeviceMetricsSummary } from '../hooks/useDeviceMetrics'
import { DeviceTable } from '../components/device-status/DeviceTable'
import { StatCard } from '../components/summary/StatCard'
import { DeviceDetailModal } from '../components/floor-plan/DeviceDetailModal'

export function DeviceStatusPage() {
  const { metrics, isLoading, refetch } = useDeviceMetrics()
  const { summary, isLoading: summaryLoading } = useDeviceMetricsSummary()
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null)

  const selectedMetrics = metrics.find((m) => m.sensor_id === selectedDeviceId)

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Device Status</h1>
        <button
          onClick={refetch}
          className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-md flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Devices"
          value={summaryLoading ? '...' : (summary?.total_devices ?? 0)}
          color="blue"
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
            </svg>
          }
        />
        <StatCard
          title="Online"
          value={summaryLoading ? '...' : (summary?.online_count ?? 0)}
          color="green"
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728m-9.9-2.829a5 5 0 010-7.07m7.072 0a5 5 0 010 7.07M13 12a1 1 0 11-2 0 1 1 0 012 0z" />
            </svg>
          }
        />
        <StatCard
          title="Offline"
          value={summaryLoading ? '...' : (summary?.offline_count ?? 0)}
          color={summary && summary.offline_count > 0 ? 'red' : 'gray'}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3" />
            </svg>
          }
        />
        <StatCard
          title="Low Battery"
          value={summaryLoading ? '...' : (summary?.low_battery_count ?? 0)}
          color={summary && summary.low_battery_count > 0 ? 'yellow' : 'gray'}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 10V7a3 3 0 00-3-3H6a3 3 0 00-3 3v6a3 3 0 003 3h4m4 0v3m0 0l-3-3m3 3l3-3m-6-9V4m0 0H9m3 0h3" />
            </svg>
          }
        />
      </div>

      {/* Device Table */}
      <DeviceTable
        devices={metrics}
        isLoading={isLoading}
        onDeviceClick={setSelectedDeviceId}
      />

      {/* Device Detail Modal */}
      {selectedDeviceId && selectedMetrics && (
        <DeviceDetailModal
          sensorId={selectedDeviceId}
          metrics={selectedMetrics}
          onClose={() => setSelectedDeviceId(null)}
        />
      )}

      {/* Help Text */}
      <div className="text-sm text-gray-500 bg-gray-50 rounded-lg p-4">
        <p>
          <strong>Status Updates:</strong> Device status is refreshed every 30 seconds.
          Devices are marked offline if no heartbeat is received for 5 minutes.
        </p>
        <p className="mt-2">
          <strong>Low Battery:</strong> Devices with battery level below 20% are flagged.
        </p>
      </div>
    </div>
  )
}
