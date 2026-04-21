import type { DeviceMetrics } from '../types'
import { useDeviceMetrics } from '../hooks/useDeviceMetrics'
import { useSensorDbLevels } from '../hooks/useSensorDbLevels'
import { SensorCard } from '../components/SensorCard'
import Header from '../components/layout/Header'

function SkeletonCard() {
  return (
    <div
      className="relative rounded-xl overflow-hidden dot-grid animate-pulse"
      style={{
        background: 'var(--c-surface)',
        border: '1px solid var(--c-border)',
      }}
    >
      <div className="absolute left-0 top-0 bottom-0 w-[3px]" style={{ backgroundColor: 'var(--c-skeleton)' }} />

      <div className="pl-[18px] pr-4 pt-4 pb-4 flex flex-col gap-0">
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="h-2.5 w-28 rounded" style={{ background: 'var(--c-skeleton)' }} />
          <div className="h-4 w-14 rounded-full" style={{ background: 'var(--c-skeleton)' }} />
        </div>
        <div className="h-2 w-20 rounded mb-4" style={{ background: 'var(--c-skeleton-2)' }} />
        <div className="flex justify-center mb-3">
          <div className="h-14 w-32 rounded" style={{ background: 'var(--c-skeleton-2)' }} />
        </div>
        <div className="h-1 w-full rounded-full mb-1" style={{ background: 'var(--c-skeleton-2)' }} />
        <div className="h-2 w-full rounded mb-4" style={{ background: 'var(--c-skeleton-2)', opacity: 0.6 }} />
        <div
          className="flex items-center justify-between pt-3"
          style={{ borderTop: '1px solid var(--c-divider)' }}
        >
          <div className="h-2.5 w-20 rounded" style={{ background: 'var(--c-skeleton)' }} />
          <div className="h-2.5 w-14 rounded" style={{ background: 'var(--c-skeleton-2)' }} />
        </div>
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[52vh] gap-6 select-none">
      <svg
        width="56"
        height="56"
        viewBox="0 0 56 56"
        fill="none"
        strokeLinecap="round"
        style={{ stroke: 'var(--c-text-4)', strokeWidth: '1.2' }}
      >
        <line x1="28" y1="10" x2="28" y2="38" />
        <path d="M18 21 Q28 13 38 21" />
        <path d="M12 15 Q28 4 44 15" />
        <path d="M23 38 L18 50 M33 38 L38 50" />
        <line x1="14" y1="50" x2="42" y2="50" />
        <line x1="9" y1="9" x2="47" y2="47" style={{ stroke: 'var(--c-red)', opacity: 0.3 }} strokeWidth="1.4" />
      </svg>
      <div className="text-center" style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <p className="font-display-mono text-[11px] tracking-[0.3em] uppercase" style={{ color: 'var(--c-text-3)' }}>
          No sensors connected
        </p>
        <p className="font-mono text-[9.5px] tracking-[0.2em] uppercase" style={{ color: 'var(--c-text-3)' }}>
          Waiting for heartbeat…
        </p>
      </div>
    </div>
  )
}

export function DashboardPage() {
  const { metrics: devices, isLoading, updateDevice } = useDeviceMetrics()
  const { dbLevels, isConnected } = useSensorDbLevels({ onDeviceUpdate: updateDevice })

  const onlineCount = devices.filter((d) => d.is_online).length

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--c-page-bg)' }}>
      <Header wsConnected={isConnected} />

      <main className="px-4 py-7 sm:px-6 lg:px-8 max-w-screen-2xl mx-auto">
        {/* Page sub-header */}
        {!isLoading && devices.length > 0 && (
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="font-display-mono text-[11px] tracking-[0.25em] uppercase" style={{ color: 'var(--c-text-2)' }}>
                Sensor Fleet
              </h1>
              <p className="font-mono text-[9.5px] tracking-[0.15em] uppercase mt-[3px]" style={{ color: 'var(--c-text-3)' }}>
                {onlineCount} / {devices.length} online
              </p>
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : devices.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {devices.map((device: DeviceMetrics) => {
              const entry = dbLevels.get(device.sensor_id)
              return (
                <SensorCard
                  key={device.sensor_id}
                  sensorId={device.sensor_id}
                  location={device.location}
                  isOnline={device.is_online}
                  batteryPercent={device.battery_percent}
                  lastHeartbeat={device.last_heartbeat}
                  loudnessDb={entry?.loudness_db ?? null}
                  isDbStale={entry?.isStale ?? false}
                />
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}
