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
  loudness_dba: number
}

export interface WebSocketMessage {
  type: 'initial' | 'event' | 'device_update' | 'ping' | 'pong' | 'subscribed' | 'unsubscribed'
  data?: AudioEvent | AudioEvent[] | DeviceMetrics
  topic?: string
}

export interface DeviceMetrics {
  id: number
  sensor_id: string
  location: string | null
  battery_percent: number | null
  bandwidth_kbps: number | null
  signal_strength_dbm: number | null
  firmware_version: string | null
  last_heartbeat: string | null
  is_online: boolean
  created_at: string
  updated_at: string
}

export interface DeviceMetricsSummary {
  total_devices: number
  online_count: number
  offline_count: number
  low_battery_count: number
}
