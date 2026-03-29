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

// Floor Plans
export interface FloorPlan {
  id: number
  name: string
  description: string | null
  width_px: number
  height_px: number
  is_active: boolean
  created_at: string
  updated_at: string
}

// Device Positions
export interface DevicePosition {
  id: number
  sensor_id: string
  floor_plan_id: number
  x_coord: number
  y_coord: number
  label: string | null
  created_at: string
  updated_at: string
}

export interface DevicePositionCreate {
  sensor_id: string
  floor_plan_id: number
  x_coord: number
  y_coord: number
  label?: string
}

export interface BulkPositionUpdate {
  sensor_id: string
  x_coord: number
  y_coord: number
}

// Device Metrics
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

// Positional Heatmap
export interface PositionalHeatmapPoint {
  sensor_id: string
  x_coord: number
  y_coord: number
  value: number
  metric_type: 'db' | 'count' | string
}

// Event Type Time Series
export interface EventTypeTimeSeries {
  event_type: string
  data: TimeSeriesPoint[]
}

// Date Range
export interface DateRange {
  start: Date
  end: Date
  preset: '1h' | '24h' | '7d' | '30d' | null
}
