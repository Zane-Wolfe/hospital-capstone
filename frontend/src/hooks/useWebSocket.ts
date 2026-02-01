import { useState, useEffect, useCallback, useRef } from 'react'
import type { AudioEvent, WebSocketMessage } from '../types'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

interface UseWebSocketOptions {
  onEvent?: (event: AudioEvent) => void
  onInitial?: (events: AudioEvent[]) => void
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const [isConnected, setIsConnected] = useState(false)
  const [events, setEvents] = useState<AudioEvent[]>([])
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
          setEvents(message.data)
          optionsRef.current.onInitial?.(message.data)
        } else if (message.type === 'event' && message.data && !Array.isArray(message.data)) {
          setEvents((prev) => [message.data as AudioEvent, ...prev.slice(0, 99)])
          optionsRef.current.onEvent?.(message.data as AudioEvent)
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
    connect,
    disconnect,
  }
}
