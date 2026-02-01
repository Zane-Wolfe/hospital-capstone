import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import EventCard from './EventCard'
import type { AudioEvent } from '../../types'

const mockEvent: AudioEvent = {
  time: '2024-01-15T10:30:00Z',
  sensor_id: 'sensor_001',
  location: 'ICU',
  event_type: 'alarm',
  loudness: 75.5,
  confidence: 0.92,
}

describe('EventCard', () => {
  it('renders event type', () => {
    render(<EventCard event={mockEvent} />)
    expect(screen.getByText(/alarm/i)).toBeInTheDocument()
  })

  it('renders location', () => {
    render(<EventCard event={mockEvent} />)
    expect(screen.getByText(/ICU/i)).toBeInTheDocument()
  })

  it('renders sensor ID', () => {
    render(<EventCard event={mockEvent} />)
    expect(screen.getByText(/sensor_001/i)).toBeInTheDocument()
  })

  it('renders loudness value', () => {
    render(<EventCard event={mockEvent} />)
    expect(screen.getByText(/75\.5/)).toBeInTheDocument()
  })

  it('renders confidence as percentage', () => {
    render(<EventCard event={mockEvent} />)
    expect(screen.getByText(/92%/)).toBeInTheDocument()
  })

  it('applies highlight class when isNew is true', () => {
    const { container } = render(<EventCard event={mockEvent} isNew={true} />)
    expect(container.firstChild).toHaveClass('ring-2')
  })

  it('does not apply highlight class when isNew is false', () => {
    const { container } = render(<EventCard event={mockEvent} isNew={false} />)
    expect(container.firstChild).not.toHaveClass('ring-2')
  })
})
