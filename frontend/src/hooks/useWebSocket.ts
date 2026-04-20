import { useState, useEffect, useCallback, useRef } from 'react'
import type { AudioEvent, DeviceMetrics, WebSocketMessage } from '../types'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

interface UseWebSocketOptions {
  onEvent?: (event: AudioEvent) => void
  onInitial?: (events: AudioEvent[]) => void
  onDeviceUpdate?: (metrics: DeviceMetrics) => void
}

/**
 * Sort events by time descending (newest first)
 */
function sortEventsByTimeDesc(events: AudioEvent[]): AudioEvent[] {
  return [...events].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime())
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false)
  const [events, setEvents] = useState<AudioEvent[]>([])
  const [eventCount, setEventCount] = useState(0) // Increments on each new event for triggering refetches
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const optionsRef = useRef(options)

  optionsRef.current = options

  const connect = useCallback(() => {
    const token = localStorage.getItem('access_token')
    if (!token) return

    const ws = new WebSocket(`${WS_URL}/ws/events?token=${token}`)

    ws.onopen = () => {
      setIsConnected(true)
    }

    ws.onclose = () => {
      setIsConnected(false)
      // Attempt reconnect after 3 seconds
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect()
      }, 3000)
    }

    ws.onerror = () => {
      ws.close()
    }

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)

        if (message.type === 'initial' && Array.isArray(message.data)) {
          // Sort initial events by time descending (newest first)
          const sortedEvents = sortEventsByTimeDesc(message.data)
          setEvents(sortedEvents)
          optionsRef.current.onInitial?.(sortedEvents)
        } else if (message.type === 'event' && message.data && !Array.isArray(message.data)) {
          setEvents((prev) => [message.data as AudioEvent, ...prev.slice(0, 99)])
          setEventCount((prev) => prev + 1) // Increment counter for triggering refetches
          optionsRef.current.onEvent?.(message.data as AudioEvent)
        } else if (message.type === 'device_update' && message.data && !Array.isArray(message.data)) {
          optionsRef.current.onDeviceUpdate?.(message.data as DeviceMetrics)
        } else if (message.type === 'ping') {
          ws.send(JSON.stringify({ type: 'pong' }))
        }
      } catch {
        // Ignore parse errors
      }
    }

    wsRef.current = ws
  }, [])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    events,
    eventCount, // Increments on each new event - use as dependency to trigger refetches
    connect,
    disconnect,
  }
}
