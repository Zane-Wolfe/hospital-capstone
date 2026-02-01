import { useState, useEffect, useCallback } from 'react'
import type { AudioEvent, EventStats, TimeSeriesPoint, HeatmapPoint } from '../types'
import {
  getEvents,
  getEventStats,
  getLoudnessTimeseries,
  getEventCountTimeseries,
  getConfidenceTimeseries,
  getHeatmapData,
  EventFilters,
} from '../api/events'

export function useEvents(filters: EventFilters = {}) {
  const [events, setEvents] = useState<AudioEvent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchEvents = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await getEvents(filters)
      setEvents(data)
    } catch (err) {
      setError('Failed to fetch events')
    } finally {
      setIsLoading(false)
    }
  }, [filters.time_range, filters.location, filters.event_type, filters.sensor_id, filters.limit])

  useEffect(() => {
    fetchEvents()
  }, [fetchEvents])

  return { events, isLoading, error, refetch: fetchEvents }
}

export function useEventStats(timeRange: string = '-1h') {
  const [stats, setStats] = useState<EventStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await getEventStats(timeRange)
      setStats(data)
    } catch (err) {
      setError('Failed to fetch stats')
    } finally {
      setIsLoading(false)
    }
  }, [timeRange])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  return { stats, isLoading, error, refetch: fetchStats }
}

export function useLoudnessTimeseries(timeRange: string = '-1h', window: string = '5m') {
  const [data, setData] = useState<TimeSeriesPoint[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await getLoudnessTimeseries(timeRange, window)
      setData(result)
    } catch (err) {
      setError('Failed to fetch loudness data')
    } finally {
      setIsLoading(false)
    }
  }, [timeRange, window])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}

export function useEventCountTimeseries(timeRange: string = '-1h', window: string = '5m') {
  const [data, setData] = useState<TimeSeriesPoint[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await getEventCountTimeseries(timeRange, window)
      setData(result)
    } catch (err) {
      setError('Failed to fetch event count data')
    } finally {
      setIsLoading(false)
    }
  }, [timeRange, window])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}

export function useConfidenceTimeseries(timeRange: string = '-1h', window: string = '5m') {
  const [data, setData] = useState<TimeSeriesPoint[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await getConfidenceTimeseries(timeRange, window)
      setData(result)
    } catch (err) {
      setError('Failed to fetch confidence data')
    } finally {
      setIsLoading(false)
    }
  }, [timeRange, window])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}

export function useHeatmap(timeRange: string = '-1h') {
  const [data, setData] = useState<HeatmapPoint[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await getHeatmapData(timeRange)
      setData(result)
    } catch (err) {
      setError('Failed to fetch heatmap data')
    } finally {
      setIsLoading(false)
    }
  }, [timeRange])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, isLoading, error, refetch: fetchData }
}
