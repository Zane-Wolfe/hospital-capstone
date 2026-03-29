import { format } from 'date-fns'
import type { DeviceMetrics } from '../../types'
import { StatusBadge } from './StatusBadge'
import { BatteryIndicator } from './BatteryIndicator'

interface DeviceRowProps {
  device: DeviceMetrics
  onClick?: () => void
}

export function DeviceRow({ device, onClick }: DeviceRowProps) {
  return (
    <tr
      className="hover:bg-gray-50 cursor-pointer"
      onClick={onClick}
    >
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="text-sm font-medium text-gray-900">{device.sensor_id}</div>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="text-sm text-gray-600">{device.location || '--'}</div>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <StatusBadge isOnline={device.is_online} />
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <BatteryIndicator percent={device.battery_percent} />
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="text-sm text-gray-600">
          {device.bandwidth_kbps !== null
            ? `${device.bandwidth_kbps.toFixed(1)} kbps`
            : '--'}
        </div>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="text-sm text-gray-500">
          {device.last_heartbeat
            ? format(new Date(device.last_heartbeat), 'MMM d, HH:mm:ss')
            : 'Never'}
        </div>
      </td>
    </tr>
  )
}
