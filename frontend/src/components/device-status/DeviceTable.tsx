import { useState, useMemo } from 'react'
import type { DeviceMetrics } from '../../types'
import { DeviceRow } from './DeviceRow'

interface DeviceTableProps {
  devices: DeviceMetrics[]
  isLoading?: boolean
  onDeviceClick?: (sensorId: string) => void
}

type SortField = 'sensor_id' | 'location' | 'is_online' | 'battery_percent' | 'bandwidth_kbps' | 'last_heartbeat'
type SortDirection = 'asc' | 'desc'

export function DeviceTable({ devices, isLoading, onDeviceClick }: DeviceTableProps) {
  const [sortField, setSortField] = useState<SortField>('sensor_id')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')
  const [filter, setFilter] = useState('')

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const filteredAndSortedDevices = useMemo(() => {
    let result = [...devices]

    // Filter
    if (filter) {
      const lowerFilter = filter.toLowerCase()
      result = result.filter(
        (d) =>
          d.sensor_id.toLowerCase().includes(lowerFilter) ||
          d.location?.toLowerCase().includes(lowerFilter)
      )
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0
      switch (sortField) {
        case 'sensor_id':
          comparison = a.sensor_id.localeCompare(b.sensor_id)
          break
        case 'location':
          comparison = (a.location || '').localeCompare(b.location || '')
          break
        case 'is_online':
          comparison = Number(b.is_online) - Number(a.is_online)
          break
        case 'battery_percent':
          comparison = (a.battery_percent ?? -1) - (b.battery_percent ?? -1)
          break
        case 'bandwidth_kbps':
          comparison = (a.bandwidth_kbps ?? -1) - (b.bandwidth_kbps ?? -1)
          break
        case 'last_heartbeat':
          comparison = new Date(a.last_heartbeat || 0).getTime() - new Date(b.last_heartbeat || 0).getTime()
          break
      }
      return sortDirection === 'asc' ? comparison : -comparison
    })

    return result
  }, [devices, filter, sortField, sortDirection])

  const SortHeader = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
    <th
      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center gap-1">
        {children}
        {sortField === field && (
          <span className="text-blue-600">
            {sortDirection === 'asc' ? '↑' : '↓'}
          </span>
        )}
      </div>
    </th>
  )

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border">
        <div className="p-4 border-b">
          <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="p-4 space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border overflow-hidden">
      <div className="p-4 border-b">
        <input
          type="text"
          placeholder="Search by ID or location..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <SortHeader field="sensor_id">Sensor ID</SortHeader>
              <SortHeader field="location">Location</SortHeader>
              <SortHeader field="is_online">Status</SortHeader>
              <SortHeader field="battery_percent">Battery</SortHeader>
              <SortHeader field="bandwidth_kbps">Bandwidth</SortHeader>
              <SortHeader field="last_heartbeat">Last Seen</SortHeader>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredAndSortedDevices.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  {filter ? 'No devices match your search' : 'No devices found'}
                </td>
              </tr>
            ) : (
              filteredAndSortedDevices.map((device) => (
                <DeviceRow
                  key={device.sensor_id}
                  device={device}
                  onClick={() => onDeviceClick?.(device.sensor_id)}
                />
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="px-4 py-3 border-t text-sm text-gray-500">
        Showing {filteredAndSortedDevices.length} of {devices.length} devices
      </div>
    </div>
  )
}
