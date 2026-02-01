import client from './client'
import type { Sensor } from '../types'

export const getSensors = async (): Promise<Sensor[]> => {
  const response = await client.get<Sensor[]>('/api/sensors')
  return response.data
}

export const getSensor = async (sensorId: string): Promise<Sensor> => {
  const response = await client.get<Sensor>(`/api/sensors/${sensorId}`)
  return response.data
}

export const getLocations = async (): Promise<string[]> => {
  const response = await client.get<string[]>('/api/sensors/locations')
  return response.data
}
