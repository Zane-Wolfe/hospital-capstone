import { format } from 'date-fns'
import type { AudioEvent } from '../../types'

interface QuickEventsListProps {
  events: AudioEvent[]
  isLoading?: boolean
}

const eventTypeColors: Record<string, string> = {
  alarms: 'bg-red-100 text-red-800',
  coughing: 'bg-yellow-100 text-yellow-800',
  speech: 'bg-blue-100 text-blue-800',
  door_knock: 'bg-purple-100 text-purple-800',
  door_open_close: 'bg-indigo-100 text-indigo-800',
  footsteps: 'bg-gray-100 text-gray-800',
  carts_rolling: 'bg-green-100 text-green-800',
}

export function QuickEventsList({ events, isLoading }: QuickEventsListProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Events</h3>
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse flex items-center gap-2">
              <div className="w-16 h-5 bg-gray-200 rounded" />
              <div className="flex-1 h-4 bg-gray-200 rounded" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border p-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Events</h3>
      {events.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-4">No recent events</p>
      ) : (
        <ul className="space-y-2">
          {events.slice(0, 5).map((event, idx) => (
            <li key={idx} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-0.5 rounded text-xs font-medium ${
                    eventTypeColors[event.event_type] || 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {event.event_type.replace(/_/g, ' ')}
                </span>
                <span className="text-gray-500">{event.sensor_id}</span>
              </div>
              <span className="text-gray-400 text-xs">
                {format(new Date(event.time), 'HH:mm:ss')}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
