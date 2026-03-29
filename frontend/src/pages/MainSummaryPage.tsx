import { Link } from 'react-router-dom'
import { useEventStats, useEvents } from '../hooks/useEvents'
import { useDeviceMetricsSummary } from '../hooks/useDeviceMetrics'
import { StatCard } from '../components/summary/StatCard'
import { QuickEventsList } from '../components/summary/QuickEventsList'
import { DeviceHealthSummary } from '../components/summary/DeviceHealthSummary'

export function MainSummaryPage() {
  const { stats, isLoading: statsLoading } = useEventStats('-1h')
  const { events, isLoading: eventsLoading } = useEvents({ time_range: '-1h', limit: 5 })
  const { summary, isLoading: summaryLoading } = useDeviceMetricsSummary()

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard Summary</h1>
        <span className="text-sm text-gray-500">Last hour</span>
      </div>

      {/* Stat Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Events"
          value={statsLoading ? '...' : (stats?.total_events ?? 0)}
          subtitle="Last hour"
          color="blue"
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          }
        />
        <StatCard
          title="Avg Loudness"
          value={statsLoading ? '...' : `${stats?.avg_loudness?.toFixed(1) ?? 0} dB`}
          subtitle="Average level"
          color="green"
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
            </svg>
          }
        />
        <StatCard
          title="Online Devices"
          value={summaryLoading ? '...' : `${summary?.online_count ?? 0} / ${summary?.total_devices ?? 0}`}
          subtitle="Active sensors"
          color={summary && summary.offline_count > 0 ? 'yellow' : 'green'}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
            </svg>
          }
        />
        <StatCard
          title="Alerts"
          value={summaryLoading ? '...' : (summary?.offline_count ?? 0) + (summary?.low_battery_count ?? 0)}
          subtitle="Require attention"
          color={(summary?.offline_count ?? 0) + (summary?.low_battery_count ?? 0) > 0 ? 'red' : 'gray'}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
        />
      </div>

      {/* Middle Row - Events and Device Health */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <QuickEventsList events={events} isLoading={eventsLoading} />
        <DeviceHealthSummary summary={summary} isLoading={summaryLoading} />
      </div>

      {/* Event Types Breakdown */}
      {stats && Object.keys(stats.event_types).length > 0 && (
        <div className="bg-white rounded-lg border p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Event Types (Last Hour)</h3>
          <div className="flex flex-wrap gap-3">
            {Object.entries(stats.event_types)
              .sort(([, a], [, b]) => b - a)
              .map(([type, count]) => (
                <div
                  key={type}
                  className="px-3 py-2 bg-gray-50 rounded-lg text-sm"
                >
                  <span className="font-medium text-gray-900">{count}</span>
                  <span className="text-gray-500 ml-1">{type.replace(/_/g, ' ')}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to="/live"
          className="p-4 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors"
        >
          <h3 className="font-medium text-blue-900">Live Data</h3>
          <p className="text-sm text-blue-700 mt-1">View real-time floor plan with heatmap</p>
        </Link>
        <Link
          to="/history"
          className="p-4 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors"
        >
          <h3 className="font-medium text-purple-900">Historical Data</h3>
          <p className="text-sm text-purple-700 mt-1">Analyze trends and patterns</p>
        </Link>
        <Link
          to="/devices"
          className="p-4 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors"
        >
          <h3 className="font-medium text-green-900">Device Status</h3>
          <p className="text-sm text-green-700 mt-1">Manage and monitor sensors</p>
        </Link>
      </div>
    </div>
  )
}
