import { useWebSocket } from '../hooks/useWebSocket'
import { useEventStats } from '../hooks/useEvents'
import EventFeed from '../components/events/EventFeed'

export default function DashboardPage() {
  const { events, isConnected } = useWebSocket()
  const { stats, isLoading: statsLoading } = useEventStats('-1h')

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <p className="text-gray-600">Real-time monitoring of hospital audio events</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500">Total Events (1h)</div>
          <div className="mt-2 text-3xl font-bold text-gray-900">
            {statsLoading ? '...' : stats?.total_events ?? 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500">Avg Loudness</div>
          <div className="mt-2 text-3xl font-bold text-gray-900">
            {statsLoading ? '...' : `${stats?.avg_loudness?.toFixed(1) ?? 0} dB`}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500">Avg Confidence</div>
          <div className="mt-2 text-3xl font-bold text-gray-900">
            {statsLoading ? '...' : `${((stats?.avg_confidence ?? 0) * 100).toFixed(0)}%`}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500">Event Types</div>
          <div className="mt-2 text-3xl font-bold text-gray-900">
            {statsLoading ? '...' : Object.keys(stats?.event_types ?? {}).length}
          </div>
        </div>
      </div>

      {/* Event Type Breakdown */}
      {stats && Object.keys(stats.event_types).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Event Types (Last Hour)</h3>
          <div className="flex flex-wrap gap-3">
            {Object.entries(stats.event_types).map(([type, count]) => (
              <div
                key={type}
                className="px-4 py-2 bg-gray-100 rounded-lg flex items-center gap-2"
              >
                <span className="font-medium text-gray-700">{type}</span>
                <span className="bg-primary-100 text-primary-800 px-2 py-0.5 rounded-full text-sm">
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Live Event Feed */}
      <EventFeed events={events} isConnected={isConnected} maxItems={15} />
    </div>
  )
}
