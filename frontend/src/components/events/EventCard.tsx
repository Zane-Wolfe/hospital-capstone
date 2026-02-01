import { format } from 'date-fns'
import type { AudioEvent } from '../../types'

interface EventCardProps {
  event: AudioEvent
}

const eventTypeColors: Record<string, string> = {
  alarms: 'bg-red-100 text-red-800',
  carts_rolling: 'bg-amber-100 text-amber-800',
  coughing: 'bg-pink-100 text-pink-800',
  door_knock: 'bg-purple-100 text-purple-800',
  door_open_close: 'bg-indigo-100 text-indigo-800',
  footsteps: 'bg-green-100 text-green-800',
  speech: 'bg-blue-100 text-blue-800',
  default: 'bg-gray-100 text-gray-800',
}

export default function EventCard({ event }: EventCardProps) {
  const colorClass = eventTypeColors[event.event_type] || eventTypeColors.default
  const confidencePercent = Math.round(event.confidence * 100)

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${colorClass}`}>
              {event.event_type}
            </span>
            <span className="text-xs text-gray-500">
              {format(new Date(event.time), 'MMM d, HH:mm:ss')}
            </span>
          </div>
          <div className="text-sm text-gray-600 space-y-1">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>{event.location}</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
              <span>{event.sensor_id}</span>
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-semibold text-gray-900">
            {event.loudness_db.toFixed(1)} dB
          </div>
          <div className="text-xs text-gray-500">
            {confidencePercent}% confidence
          </div>
        </div>
      </div>
    </div>
  )
}
