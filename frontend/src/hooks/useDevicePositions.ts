import { useState, useEffect, useCallback } from 'react'
import type { DevicePosition, DevicePositionCreate, BulkPositionUpdate } from '../types'
import {
  getDevicePositions,
  createDevicePosition,
  updateDevicePosition,
  deleteDevicePosition,
  bulkUpdatePositions,
} from '../api/devicePositions'

export function useDevicePositions(floorPlanId?: number) {
  const [positions, setPositions] = useState<DevicePosition[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPositions = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await getDevicePositions(floorPlanId)
      setPositions(data)
    } catch (err) {
      setError('Failed to fetch device positions')
    } finally {
      setIsLoading(false)
    }
  }, [floorPlanId])

  useEffect(() => {
    fetchPositions()
  }, [fetchPositions])

  const create = useCallback(async (data: DevicePositionCreate) => {
    const newPosition = await createDevicePosition(data)
    setPositions((prev) => [...prev, newPosition])
    return newPosition
  }, [])

  const update = useCallback(
    async (sensorId: string, data: Partial<Omit<DevicePositionCreate, 'sensor_id'>>) => {
      const updated = await updateDevicePosition(sensorId, data)
      setPositions((prev) =>
        prev.map((p) => (p.sensor_id === sensorId ? updated : p))
      )
      return updated
    },
    []
  )

  const remove = useCallback(async (sensorId: string) => {
    await deleteDevicePosition(sensorId)
    setPositions((prev) => prev.filter((p) => p.sensor_id !== sensorId))
  }, [])

  const bulkUpdate = useCallback(async (updates: BulkPositionUpdate[]) => {
    const updatedPositions = await bulkUpdatePositions(updates)
    setPositions((prev) =>
      prev.map((p) => {
        const updated = updatedPositions.find((u) => u.sensor_id === p.sensor_id)
        return updated || p
      })
    )
    return updatedPositions
  }, [])

  const updateLocalPosition = useCallback(
    (sensorId: string, x: number, y: number) => {
      setPositions((prev) =>
        prev.map((p) =>
          p.sensor_id === sensorId ? { ...p, x_coord: x, y_coord: y } : p
        )
      )
    },
    []
  )

  return {
    positions,
    isLoading,
    error,
    refetch: fetchPositions,
    create,
    update,
    remove,
    bulkUpdate,
    updateLocalPosition,
  }
}
