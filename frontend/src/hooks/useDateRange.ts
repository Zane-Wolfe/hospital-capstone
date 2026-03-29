import { useState, useCallback, useMemo } from 'react'
import { subHours, subDays } from 'date-fns'
import type { DateRange } from '../types'

type Preset = '1h' | '24h' | '7d' | '30d'

const PRESETS: Record<Preset, () => { start: Date; end: Date }> = {
  '1h': () => ({ start: subHours(new Date(), 1), end: new Date() }),
  '24h': () => ({ start: subHours(new Date(), 24), end: new Date() }),
  '7d': () => ({ start: subDays(new Date(), 7), end: new Date() }),
  '30d': () => ({ start: subDays(new Date(), 30), end: new Date() }),
}

export function useDateRange(initialPreset: Preset = '1h') {
  const [dateRange, setDateRange] = useState<DateRange>(() => ({
    ...PRESETS[initialPreset](),
    preset: initialPreset,
  }))

  const setPreset = useCallback((preset: Preset) => {
    const { start, end } = PRESETS[preset]()
    setDateRange({ start, end, preset })
  }, [])

  const setCustomRange = useCallback((start: Date, end: Date) => {
    setDateRange({ start, end, preset: null })
  }, [])

  const timeRangeString = useMemo(() => {
    if (dateRange.preset) {
      return `-${dateRange.preset}`
    }
    // For custom range, return ISO timestamp
    return dateRange.start.toISOString()
  }, [dateRange])

  return {
    dateRange,
    setPreset,
    setCustomRange,
    timeRangeString,
  }
}
