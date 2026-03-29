import client from './client'
import type { DeviceMetrics, DeviceMetricsSummary } from '../types'

export async function getDeviceMetrics(): Promise<DeviceMetrics[]> {
  const response = await client.get<DeviceMetrics[]>('/api/device-metrics')
  return response.data
}

export async function getDeviceMetricsSummary(): Promise<DeviceMetricsSummary> {
  const response = await client.get<DeviceMetricsSummary>('/api/device-metrics/summary')
  return response.data
}

export async function getDeviceMetricsBySensorId(sensorId: string): Promise<DeviceMetrics> {
  const response = await client.get<DeviceMetrics>(`/api/device-metrics/${sensorId}`)
  return response.data
}
