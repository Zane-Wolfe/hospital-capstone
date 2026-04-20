import { useState, useCallback } from 'react'
import { useWebSocket } from './useWebSocket'
import type { AudioEvent, DeviceMetrics } from '../types'

export interface SensorDbEntry {
  loudness_db: number
  timestamp: string
  isStale: boolean
}

const STALE_THRESHOLD_MS = 30_000 // treat value as stale after 30s of no new events

interface UseSensorDbLevelsOptions {
  /** Called whenever the server pushes a device_update message (heartbeat received). */
  onDeviceUpdate?: (metrics: DeviceMetrics) => void
}

/**
 * Subscribes to the WebSocket and maintains the latest audio level
 * received per sensor. Returns a Map keyed by sensor_id.
 */
export function useSensorDbLevels(options: UseSensorDbLevelsOptions = {}): {
  dbLevels: Map<string, SensorDbEntry>
  isConnected: boolean
} {
  const [dbLevels, setDbLevels] = useState<Map<string, SensorDbEntry>>(new Map())

  const markStaleEntries = useCallback(() => {
    const now = Date.now()
    setDbLevels((prev) => {
      let changed = false
      const next = new Map(prev)
      for (const [id, entry] of next) {
        const age = now - new Date(entry.timestamp).getTime()
        const shouldBeStale = age > STALE_THRESHOLD_MS
        if (shouldBeStale !== entry.isStale) {
          next.set(id, { ...entry, isStale: shouldBeStale })
          changed = true
        }
      }
      return changed ? next : prev
    })
  }, [])

  const handleEvent = useCallback(
    (event: AudioEvent) => {
      setDbLevels((prev) => {
        const next = new Map(prev)
        next.set(event.sensor_id, {
          loudness_db: event.loudness_db,
          timestamp: event.time,
          isStale: false,
        })
        return next
      })
      // Check staleness lazily after updating
      setTimeout(markStaleEntries, STALE_THRESHOLD_MS + 500)
    },
    [markStaleEntries],
  )

  const handleInitial = useCallback(
    (events: AudioEvent[]) => {
      // Seed map with the most recent event per sensor from the initial batch
      const latest = new Map<string, AudioEvent>()
      for (const e of events) {
        const existing = latest.get(e.sensor_id)
        if (!existing || new Date(e.time) > new Date(existing.time)) {
          latest.set(e.sensor_id, e)
        }
      }
      const now = Date.now()
      setDbLevels(() => {
        const next = new Map<string, SensorDbEntry>()
        for (const [id, e] of latest) {
          const age = now - new Date(e.time).getTime()
          next.set(id, {
            loudness_db: e.loudness_db,
            timestamp: e.time,
            isStale: age > STALE_THRESHOLD_MS,
          })
        }
        return next
      })
    },
    [],
  )

  const { isConnected } = useWebSocket({
    onEvent: handleEvent,
    onInitial: handleInitial,
    onDeviceUpdate: options.onDeviceUpdate,
  })

  return { dbLevels, isConnected }
}
