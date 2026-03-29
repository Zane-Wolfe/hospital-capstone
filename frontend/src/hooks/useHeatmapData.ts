import { useState, useEffect, useCallback } from 'react'
import client from '../api/client'
import type { PositionalHeatmapPoint } from '../types'

interface UseHeatmapDataOptions {
  floorPlanId: number | null
  timeRange: string
  metric: 'db' | 'count' | string
}

export function useHeatmapData({ floorPlanId, timeRange, metric }: UseHeatmapDataOptions) {
  const [data, setData] = useState<PositionalHeatmapPoint[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    if (floorPlanId === null) {
      setData([])
      return
    }

    setIsLoading(true)
    setError(null)
    try {
      const response = await client.get<PositionalHeatmapPoint[]>(
        '/api/events/heatmap-by-position',
        {
          params: {
            floor_plan_id: floorPlanId,
            time_range: timeRange,
            metric,
          },
        }
      )
      setData(response.data)
    } catch (err) {
      setError('Failed to fetch heatmap data')
    } finally {
      setIsLoading(false)
    }
  }, [floorPlanId, timeRange, metric])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}
