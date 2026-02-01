import type { AudioEvent } from '../../types'
import EventCard from './EventCard'

interface EventFeedProps {
  events: AudioEvent[]
  isConnected: boolean
  maxItems?: number
}

export default function EventFeed({ events, isConnected, maxItems = 20 }: EventFeedProps) {
  const displayEvents = events.slice(0, maxItems)

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Live Event Feed</h3>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-500">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
      <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
        {displayEvents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No events yet. Waiting for audio events...
          </div>
        ) : (
          displayEvents.map((event, index) => (
            <EventCard key={`${event.time}-${event.sensor_id}-${index}`} event={event} />
          ))
        )}
      </div>
    </div>
  )
}
