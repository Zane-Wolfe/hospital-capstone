import { useState, useEffect } from 'react'
import { getLocations } from '../../api/sensors'

interface EventFiltersProps {
  onFilterChange: (filters: {
    time_range: string
    location?: string
    event_type?: string
  }) => void
}

const timeRanges = [
  { value: '-15m', label: 'Last 15 minutes' },
  { value: '-1h', label: 'Last hour' },
  { value: '-6h', label: 'Last 6 hours' },
  { value: '-24h', label: 'Last 24 hours' },
  { value: '-7d', label: 'Last 7 days' },
]

const eventTypes = [
  { value: '', label: 'All types' },
  { value: 'alarms', label: 'Alarms' },
  { value: 'carts_rolling', label: 'Carts Rolling' },
  { value: 'coughing', label: 'Coughing' },
  { value: 'door_knock', label: 'Door Knock' },
  { value: 'door_open_close', label: 'Door Open/Close' },
  { value: 'footsteps', label: 'Footsteps' },
  { value: 'speech', label: 'Speech' },
]

export default function EventFilters({ onFilterChange }: EventFiltersProps) {
  const [timeRange, setTimeRange] = useState('-1h')
  const [location, setLocation] = useState('')
  const [eventType, setEventType] = useState('')
  const [locations, setLocations] = useState<string[]>([])

  useEffect(() => {
    getLocations()
      .then(setLocations)
      .catch(() => setLocations([]))
  }, [])

  useEffect(() => {
    onFilterChange({
      time_range: timeRange,
      location: location || undefined,
      event_type: eventType || undefined,
    })
  }, [timeRange, location, eventType, onFilterChange])

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Time Range
          </label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
          >
            {timeRanges.map((range) => (
              <option key={range.value} value={range.value}>
                {range.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Location
          </label>
          <select
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
          >
            <option value="">All locations</option>
            {locations.map((loc) => (
              <option key={loc} value={loc}>
                {loc}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Event Type
          </label>
          <select
            value={eventType}
            onChange={(e) => setEventType(e.target.value)}
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
          >
            {eventTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}
