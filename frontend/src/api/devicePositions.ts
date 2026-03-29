import client from './client'
import type { DevicePosition, DevicePositionCreate, BulkPositionUpdate } from '../types'

export async function getDevicePositions(floorPlanId?: number): Promise<DevicePosition[]> {
  const params = floorPlanId !== undefined ? { floor_plan_id: floorPlanId } : {}
  const response = await client.get<DevicePosition[]>('/api/device-positions', { params })
  return response.data
}

export async function getDevicePosition(sensorId: string): Promise<DevicePosition> {
  const response = await client.get<DevicePosition>(`/api/device-positions/${sensorId}`)
  return response.data
}

export async function createDevicePosition(data: DevicePositionCreate): Promise<DevicePosition> {
  const response = await client.post<DevicePosition>('/api/device-positions', data)
  return response.data
}

export async function updateDevicePosition(
  sensorId: string,
  data: Partial<Omit<DevicePositionCreate, 'sensor_id'>>
): Promise<DevicePosition> {
  const response = await client.put<DevicePosition>(`/api/device-positions/${sensorId}`, data)
  return response.data
}

export async function deleteDevicePosition(sensorId: string): Promise<void> {
  await client.delete(`/api/device-positions/${sensorId}`)
}

export async function bulkUpdatePositions(
  positions: BulkPositionUpdate[]
): Promise<DevicePosition[]> {
  const response = await client.put<DevicePosition[]>('/api/device-positions/bulk', {
    positions,
  })
  return response.data
}
