import { format } from 'date-fns'
import type { DateRange } from '../../types'

type Preset = '1h' | '24h' | '7d' | '30d'

interface DateRangePickerProps {
  dateRange: DateRange
  onPresetSelect: (preset: Preset) => void
  onCustomRangeSelect: (start: Date, end: Date) => void
}

const presets: { value: Preset; label: string }[] = [
  { value: '1h', label: '1 Hour' },
  { value: '24h', label: '24 Hours' },
  { value: '7d', label: '7 Days' },
  { value: '30d', label: '30 Days' },
]

export function DateRangePicker({
  dateRange,
  onPresetSelect,
  onCustomRangeSelect,
}: DateRangePickerProps) {
  const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const start = new Date(e.target.value)
    if (!isNaN(start.getTime())) {
      onCustomRangeSelect(start, dateRange.end)
    }
  }

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const end = new Date(e.target.value)
    if (!isNaN(end.getTime())) {
      onCustomRangeSelect(dateRange.start, end)
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-4 p-4 bg-white rounded-lg border">
      {/* Preset Buttons */}
      <div className="flex gap-2">
        {presets.map((preset) => (
          <button
            key={preset.value}
            onClick={() => onPresetSelect(preset.value)}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              dateRange.preset === preset.value
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {preset.label}
          </button>
        ))}
      </div>

      <div className="h-6 w-px bg-gray-300" />

      {/* Custom Range */}
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-600">From:</label>
        <input
          type="datetime-local"
          value={format(dateRange.start, "yyyy-MM-dd'T'HH:mm")}
          onChange={handleStartChange}
          className="px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        />
        <label className="text-sm text-gray-600">To:</label>
        <input
          type="datetime-local"
          value={format(dateRange.end, "yyyy-MM-dd'T'HH:mm")}
          onChange={handleEndChange}
          className="px-2 py-1 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
    </div>
  )
}
