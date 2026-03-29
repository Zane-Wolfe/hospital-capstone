import { useState } from 'react'
import type { Sensor } from '../../types'

interface DevicePositionFormProps {
  floorPlanId: number
  availableSensors: Sensor[]
  existingSensorIds: string[]
  onSubmit: (sensorId: string, x: number, y: number, label?: string) => Promise<void>
  onCancel: () => void
}

export function DevicePositionForm({
  floorPlanId: _floorPlanId,
  availableSensors,
  existingSensorIds,
  onSubmit,
  onCancel,
}: DevicePositionFormProps) {
  // floorPlanId available for future use (e.g., showing floor plan name)
  void _floorPlanId
  const [sensorId, setSensorId] = useState('')
  const [xCoord, setXCoord] = useState('')
  const [yCoord, setYCoord] = useState('')
  const [label, setLabel] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const unplacedSensors = availableSensors.filter(
    (s) => !existingSensorIds.includes(s.sensor_id)
  )

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!sensorId) {
      setError('Please select a sensor')
      return
    }
    const x = parseFloat(xCoord)
    const y = parseFloat(yCoord)
    if (isNaN(x) || isNaN(y)) {
      setError('Please enter valid coordinates')
      return
    }

    setIsSubmitting(true)
    setError(null)
    try {
      await onSubmit(sensorId, x, y, label.trim() || undefined)
    } catch (err) {
      setError('Failed to add device position')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">Add Device to Floor Plan</h2>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sensor *
            </label>
            <select
              value={sensorId}
              onChange={(e) => setSensorId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select a sensor</option>
              {unplacedSensors.map((sensor) => (
                <option key={sensor.sensor_id} value={sensor.sensor_id}>
                  {sensor.sensor_id} ({sensor.location})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                X Coordinate *
              </label>
              <input
                type="number"
                value={xCoord}
                onChange={(e) => setXCoord(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="X position in pixels"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Y Coordinate *
              </label>
              <input
                type="number"
                value={yCoord}
                onChange={(e) => setYCoord(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="Y position in pixels"
              />
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Label
            </label>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Optional display label"
            />
          </div>

          {error && (
            <div className="mb-4 text-red-600 text-sm">{error}</div>
          )}

          <p className="text-xs text-gray-500 mb-4">
            Tip: You can also drag devices to position them after adding.
          </p>

          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Adding...' : 'Add Device'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
