import client from './client'
import type { AudioEvent, EventStats, TimeSeriesPoint, HeatmapPoint } from '../types'

export interface EventFilters {
  time_range?: string
  location?: string
  event_type?: string
  sensor_id?: string
  limit?: number
}

export const getEvents = async (filters: EventFilters = {}): Promise<AudioEvent[]> => {
  const params = new URLSearchParams()
  if (filters.time_range) params.append('time_range', filters.time_range)
  if (filters.location) params.append('location', filters.location)
  if (filters.event_type) params.append('event_type', filters.event_type)
  if (filters.sensor_id) params.append('sensor_id', filters.sensor_id)
  if (filters.limit) params.append('limit', filters.limit.toString())

  const response = await client.get<AudioEvent[]>(`/api/events?${params}`)
  return response.data
}

export const getLatestEvents = async (limit: number = 10): Promise<AudioEvent[]> => {
  const response = await client.get<AudioEvent[]>(`/api/events/latest?limit=${limit}`)
  return response.data
}

export const getEventStats = async (timeRange: string = '-1h'): Promise<EventStats> => {
  const response = await client.get<EventStats>(`/api/events/stats?time_range=${timeRange}`)
  return response.data
}

export const getLoudnessTimeseries = async (
  timeRange: string = '-1h',
  window: string = '5m'
): Promise<TimeSeriesPoint[]> => {
  const response = await client.get<TimeSeriesPoint[]>(
    `/api/events/timeseries/loudness?time_range=${timeRange}&window=${window}`
  )
  return response.data
}

export const getEventCountTimeseries = async (
  timeRange: string = '-1h',
  window: string = '5m'
): Promise<TimeSeriesPoint[]> => {
  const response = await client.get<TimeSeriesPoint[]>(
    `/api/events/timeseries/count?time_range=${timeRange}&window=${window}`
  )
  return response.data
}

export const getConfidenceTimeseries = async (
  timeRange: string = '-1h',
  window: string = '5m'
): Promise<TimeSeriesPoint[]> => {
  const response = await client.get<TimeSeriesPoint[]>(
    `/api/events/timeseries/confidence?time_range=${timeRange}&window=${window}`
  )
  return response.data
}

export const getHeatmapData = async (timeRange: string = '-1h'): Promise<HeatmapPoint[]> => {
  const response = await client.get<HeatmapPoint[]>(`/api/events/heatmap?time_range=${timeRange}`)
  return response.data
}
