import { useState, useEffect, useCallback } from 'react'
import { useDateRange } from '../hooks/useDateRange'
import { useLoudnessTimeseries } from '../hooks/useEvents'
import { DateRangePicker } from '../components/charts/DateRangePicker'
import { LoudnessBarChart } from '../components/charts/LoudnessBarChart'
import { EventLineChart } from '../components/charts/EventLineChart'
import { getEventsByTypeTimeseries } from '../api/events'
import type { EventTypeTimeSeries } from '../types'

export function HistoricalDataPage() {
  const { dateRange, setPreset, setCustomRange, timeRangeString } = useDateRange('24h')
  const [window, setWindow] = useState('15m')

  // Loudness data
  const { data: loudnessData, isLoading: loudnessLoading } = useLoudnessTimeseries(
    timeRangeString,
    window
  )

  // Event type data (custom fetch since hook doesn't exist)
  const [eventTypeData, setEventTypeData] = useState<EventTypeTimeSeries[]>([])
  const [eventTypeLoading, setEventTypeLoading] = useState(true)

  const fetchEventTypeData = useCallback(async () => {
    setEventTypeLoading(true)
    try {
      const data = await getEventsByTypeTimeseries(timeRangeString, window)
      setEventTypeData(data)
    } catch (err) {
      console.error('Failed to fetch event type data:', err)
    } finally {
      setEventTypeLoading(false)
    }
  }, [timeRangeString, window])

  useEffect(() => {
    fetchEventTypeData()
  }, [fetchEventTypeData])

  // Adjust window based on date range
  useEffect(() => {
    if (dateRange.preset === '1h') {
      setWindow('5m')
    } else if (dateRange.preset === '24h') {
      setWindow('15m')
    } else if (dateRange.preset === '7d') {
      setWindow('1h')
    } else if (dateRange.preset === '30d') {
      setWindow('6h')
    }
  }, [dateRange.preset])

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Historical Data</h1>
      </div>

      {/* Date Range Picker */}
      <DateRangePicker
        dateRange={dateRange}
        onPresetSelect={setPreset}
        onCustomRangeSelect={setCustomRange}
      />

      {/* Aggregation Window Selector */}
      <div className="flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700">Aggregation Window:</label>
        <select
          value={window}
          onChange={(e) => setWindow(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="1m">1 minute</option>
          <option value="5m">5 minutes</option>
          <option value="15m">15 minutes</option>
          <option value="30m">30 minutes</option>
          <option value="1h">1 hour</option>
          <option value="6h">6 hours</option>
          <option value="1d">1 day</option>
        </select>
      </div>

      {/* Charts */}
      <div className="space-y-6">
        <LoudnessBarChart data={loudnessData} isLoading={loudnessLoading} />
        <EventLineChart data={eventTypeData} isLoading={eventTypeLoading} />
      </div>

      {/* Data Summary */}
      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Data Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Data Points (Loudness):</span>
            <span className="ml-2 font-medium">{loudnessData.length}</span>
          </div>
          <div>
            <span className="text-gray-500">Event Types:</span>
            <span className="ml-2 font-medium">{eventTypeData.length}</span>
          </div>
          {loudnessData.length > 0 && (
            <>
              <div>
                <span className="text-gray-500">Avg Loudness:</span>
                <span className="ml-2 font-medium">
                  {(loudnessData.reduce((sum, d) => sum + d.value, 0) / loudnessData.length).toFixed(1)} dB
                </span>
              </div>
              <div>
                <span className="text-gray-500">Max Loudness:</span>
                <span className="ml-2 font-medium">
                  {Math.max(...loudnessData.map((d) => d.value)).toFixed(1)} dB
                </span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
