export interface User {
  username: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface AudioEvent {
  time: string
  sensor_id: string
  location: string
  event_type: string
  confidence: number
  loudness_db: number
}

export interface EventStats {
  total_events: number
  avg_confidence: number
  avg_loudness: number
  event_types: Record<string, number>
}

export interface TimeSeriesPoint {
  time: string
  value: number
}

export interface HeatmapPoint {
  location: string
  count: number
  avg_loudness: number
}

export interface Sensor {
  sensor_id: string
  location: string
  last_seen: string | null
  event_count: number
}

export interface WebSocketMessage {
  type: 'initial' | 'event' | 'ping' | 'pong' | 'subscribed' | 'unsubscribed'
  data?: AudioEvent | AudioEvent[]
  topic?: string
}
