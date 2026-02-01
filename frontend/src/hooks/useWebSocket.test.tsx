import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useWebSocket } from './useWebSocket'

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = []
  url: string
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  readyState = 0

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  send = vi.fn()
  close = vi.fn()

  simulateOpen() {
    this.readyState = 1
    this.onopen?.()
  }

  simulateMessage(data: object) {
    this.onmessage?.({ data: JSON.stringify(data) })
  }

  simulateClose() {
    this.readyState = 3
    this.onclose?.()
  }

  simulateError() {
    this.onerror?.(new Event('error'))
  }
}

const originalWebSocket = global.WebSocket

describe('useWebSocket', () => {
  beforeEach(() => {
    MockWebSocket.instances = []
    global.WebSocket = MockWebSocket as unknown as typeof WebSocket
  })

  afterEach(() => {
    global.WebSocket = originalWebSocket
  })

  it('creates WebSocket connection with correct URL', () => {
    renderHook(() => useWebSocket('test-token'))
    
    expect(MockWebSocket.instances.length).toBe(1)
    expect(MockWebSocket.instances[0].url).toContain('test-token')
  })

  it('returns connected status after open', () => {
    const { result } = renderHook(() => useWebSocket('test-token'))
    
    act(() => {
      MockWebSocket.instances[0].simulateOpen()
    })

    expect(result.current.isConnected).toBe(true)
  })

  it('returns disconnected status after close', () => {
    const { result } = renderHook(() => useWebSocket('test-token'))
    
    act(() => {
      MockWebSocket.instances[0].simulateOpen()
    })

    act(() => {
      MockWebSocket.instances[0].simulateClose()
    })

    expect(result.current.isConnected).toBe(false)
  })

  it('calls onMessage callback when receiving message', () => {
    const onMessage = vi.fn()
    renderHook(() => useWebSocket('test-token', { onMessage }))
    
    act(() => {
      MockWebSocket.instances[0].simulateOpen()
    })

    const testData = { type: 'event', data: { id: 1 } }
    act(() => {
      MockWebSocket.instances[0].simulateMessage(testData)
    })

    expect(onMessage).toHaveBeenCalledWith(testData)
  })

  it('provides sendMessage function', () => {
    const { result } = renderHook(() => useWebSocket('test-token'))
    
    act(() => {
      MockWebSocket.instances[0].simulateOpen()
    })

    result.current.sendMessage({ type: 'subscribe', channel: 'events' })

    expect(MockWebSocket.instances[0].send).toHaveBeenCalledWith(
      JSON.stringify({ type: 'subscribe', channel: 'events' })
    )
  })

  it('does not create connection when token is empty', () => {
    renderHook(() => useWebSocket(''))
    expect(MockWebSocket.instances.length).toBe(0)
  })
})
