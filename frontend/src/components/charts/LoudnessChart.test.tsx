import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import LoudnessChart from './LoudnessChart'
import type { TimeSeriesPoint } from '../../types'

const mockData: TimeSeriesPoint[] = [
  { time: '2024-01-15T10:00:00Z', value: 65.0 },
  { time: '2024-01-15T10:05:00Z', value: 70.0 },
  { time: '2024-01-15T10:10:00Z', value: 68.0 },
]

describe('LoudnessChart', () => {
  it('renders chart title', () => {
    render(<LoudnessChart data={mockData} isLoading={false} />)
    expect(screen.getByText(/loudness/i)).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(<LoudnessChart data={[]} isLoading={true} />)
    expect(screen.getByTestId('chart-loading')).toBeInTheDocument()
  })

  it('shows no data message when data is empty', () => {
    render(<LoudnessChart data={[]} isLoading={false} />)
    expect(screen.getByText(/no data/i)).toBeInTheDocument()
  })

  it('renders chart when data is provided', () => {
    const { container } = render(<LoudnessChart data={mockData} isLoading={false} />)
    expect(container.querySelector('.recharts-wrapper')).toBeInTheDocument()
  })
})
