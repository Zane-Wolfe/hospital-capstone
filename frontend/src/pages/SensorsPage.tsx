import { useState, useEffect } from 'react'
import { getSensors } from '../api/sensors'
import type { Sensor } from '../types'

export default function SensorsPage() {
  const [sensors, setSensors] = useState<Sensor[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchSensors = async () => {
      try {
        const data = await getSensors()
        setSensors(data)
      } catch {
        setError('Failed to load sensors')
      } finally {
        setIsLoading(false)
      }
    }

    fetchSensors()
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Sensors</h2>
        <p className="text-gray-600">View all registered audio sensors</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : sensors.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          No sensors found
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sensors.map((sensor) => (
            <div
              key={sensor.sensor_id}
              className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">
                    {sensor.sensor_id}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">{sensor.location}</p>
                </div>
                <div className="w-3 h-3 bg-green-500 rounded-full" title="Active" />
              </div>
              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Events (7d)</span>
                  <span className="font-medium text-gray-900">{sensor.event_count}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
