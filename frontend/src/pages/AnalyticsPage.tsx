import { useState } from 'react'
import {
  useEventStats,
  useLoudnessTimeseries,
  useEventCountTimeseries,
  useConfidenceTimeseries,
  useHeatmap,
} from '../hooks/useEvents'
import LoudnessChart from '../components/charts/LoudnessChart'
import EventCountChart from '../components/charts/EventCountChart'
import ConfidenceChart from '../components/charts/ConfidenceChart'
import CategoryPieChart from '../components/charts/CategoryPieChart'
import LocationHeatmap from '../components/heatmap/LocationHeatmap'

const timeRanges = [
  { value: '-1h', label: '1 Hour', window: '5m' },
  { value: '-6h', label: '6 Hours', window: '15m' },
  { value: '-24h', label: '24 Hours', window: '1h' },
  { value: '-7d', label: '7 Days', window: '6h' },
]

export default function AnalyticsPage() {
  const [selectedRange, setSelectedRange] = useState(timeRanges[0])

  const { stats, isLoading: statsLoading } = useEventStats(selectedRange.value)
  const { data: loudnessData, isLoading: loudnessLoading } = useLoudnessTimeseries(
    selectedRange.value,
    selectedRange.window
  )
  const { data: countData, isLoading: countLoading } = useEventCountTimeseries(
    selectedRange.value,
    selectedRange.window
  )
  const { data: confidenceData, isLoading: confidenceLoading } = useConfidenceTimeseries(
    selectedRange.value,
    selectedRange.window
  )
  const { data: heatmapData, isLoading: heatmapLoading } = useHeatmap(selectedRange.value)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analytics</h2>
          <p className="text-gray-600">Visualize and analyze audio event data</p>
        </div>
        <div className="flex gap-2">
          {timeRanges.map((range) => (
            <button
              key={range.value}
              onClick={() => setSelectedRange(range)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                selectedRange.value === range.value
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LoudnessChart data={loudnessData} isLoading={loudnessLoading} />
        <EventCountChart data={countData} isLoading={countLoading} />
        <ConfidenceChart data={confidenceData} isLoading={confidenceLoading} />
        <CategoryPieChart
          data={stats?.event_types ?? {}}
          isLoading={statsLoading}
        />
      </div>

      {/* Location Heatmap */}
      <LocationHeatmap data={heatmapData} isLoading={heatmapLoading} />
    </div>
  )
}
