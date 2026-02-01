import { useState, useCallback } from 'react'
import { useEvents } from '../hooks/useEvents'
import EventCard from '../components/events/EventCard'
import EventFilters from '../components/events/EventFilters'

// 1. Define the interface with optional properties (?)
interface FilterState {
  time_range: string;
  location?: string;    // Added ? to make it optional
  event_type?: string;  // Added ? to make it optional
}

export default function EventsPage() {
  // 2. Pass the interface to useState
  const [filters, setFilters] = useState<FilterState>({
    time_range: '-1h',
    location: undefined,
    event_type: undefined,
  })

  const { events, isLoading, error } = useEvents({
    ...filters,
    limit: 200,
  })

  // 3. Now 'newFilters' (inferred from state) automatically accepts optional keys
  const handleFilterChange = useCallback((newFilters: FilterState) => {
    setFilters(newFilters)
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Events</h2>
        <p className="text-gray-600">Browse and filter historical audio events</p>
      </div>

      <EventFilters onFilterChange={handleFilterChange} />

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="text-sm text-gray-500">
            Showing {events.length} events
          </div>
          {events.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              No events found for the selected filters
            </div>
          ) : (
            events.map((event, index) => (
              <EventCard key={`${event.time}-${event.sensor_id}-${index}`} event={event} />
            ))
          )}
        </div>
      )}
    </div>
  )
}