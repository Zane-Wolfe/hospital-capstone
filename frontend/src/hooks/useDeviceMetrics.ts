import { useState, useEffect, useCallback, useRef } from 'react'
import type { DeviceMetrics, DeviceMetricsSummary } from '../types'
import { getDeviceMetrics, getDeviceMetricsSummary } from '../api/deviceMetrics'

const REFRESH_INTERVAL_MS = 30000 // 30 seconds

export function useDeviceMetrics(autoRefresh = true) {
  const [metrics, setMetrics] = useState<DeviceMetrics[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<number | null>(null)

  const fetchMetrics = useCallback(async () => {
    setError(null)
    try {
      const data = await getDeviceMetrics()
      setMetrics(data)
    } catch (err) {
      setError('Failed to fetch device metrics')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMetrics()

    if (autoRefresh) {
      intervalRef.current = window.setInterval(fetchMetrics, REFRESH_INTERVAL_MS)
    }

    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current)
      }
    }
  }, [fetchMetrics, autoRefresh])

  return { metrics, isLoading, error, refetch: fetchMetrics }
}

export function useDeviceMetricsSummary(autoRefresh = true) {
  const [summary, setSummary] = useState<DeviceMetricsSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<number | null>(null)

  const fetchSummary = useCallback(async () => {
    setError(null)
    try {
      const data = await getDeviceMetricsSummary()
      setSummary(data)
    } catch (err) {
      setError('Failed to fetch device metrics summary')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSummary()

    if (autoRefresh) {
      intervalRef.current = window.setInterval(fetchSummary, REFRESH_INTERVAL_MS)
    }

    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current)
      }
    }
  }, [fetchSummary, autoRefresh])

  return { summary, isLoading, error, refetch: fetchSummary }
}
