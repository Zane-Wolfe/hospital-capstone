import { useState, useEffect, useCallback } from 'react'
import type { FloorPlan } from '../types'
import {
  getFloorPlans,
  getFloorPlan,
  createFloorPlan,
  updateFloorPlan,
  deleteFloorPlan,
} from '../api/floorPlans'

export function useFloorPlans() {
  const [floorPlans, setFloorPlans] = useState<FloorPlan[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchFloorPlans = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await getFloorPlans()
      setFloorPlans(data)
    } catch (err) {
      setError('Failed to fetch floor plans')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchFloorPlans()
  }, [fetchFloorPlans])

  const create = useCallback(
    async (name: string, image: File, description?: string) => {
      const newPlan = await createFloorPlan(name, image, description)
      setFloorPlans((prev) => [newPlan, ...prev])
      return newPlan
    },
    []
  )

  const update = useCallback(
    async (
      id: number,
      data: { name?: string; description?: string; is_active?: boolean },
      image?: File
    ) => {
      const updated = await updateFloorPlan(id, data, image)
      setFloorPlans((prev) => prev.map((fp) => (fp.id === id ? updated : fp)))
      return updated
    },
    []
  )

  const remove = useCallback(async (id: number) => {
    await deleteFloorPlan(id)
    setFloorPlans((prev) => prev.filter((fp) => fp.id !== id))
  }, [])

  return {
    floorPlans,
    isLoading,
    error,
    refetch: fetchFloorPlans,
    create,
    update,
    remove,
  }
}

export function useFloorPlan(id: number | null) {
  const [floorPlan, setFloorPlan] = useState<FloorPlan | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchFloorPlan = useCallback(async () => {
    if (id === null) {
      setFloorPlan(null)
      return
    }
    setIsLoading(true)
    setError(null)
    try {
      const data = await getFloorPlan(id)
      setFloorPlan(data)
    } catch (err) {
      setError('Failed to fetch floor plan')
    } finally {
      setIsLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchFloorPlan()
  }, [fetchFloorPlan])

  return { floorPlan, isLoading, error, refetch: fetchFloorPlan }
}
