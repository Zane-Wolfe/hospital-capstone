import { useEffect, useRef, useState } from 'react'

const LOW_BATTERY_THRESHOLD = 20
const DB_MIN = -80
const DB_MAX = 0

function formatRelativeTime(isoString: string | null): string {
  if (!isoString) return 'Never'
  const diff = Date.now() - new Date(isoString).getTime()
  const seconds = Math.floor(diff / 1000)
  if (seconds < 30) return 'just now'
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

function dbToFill(db: number): number {
  return Math.max(0, Math.min(100, ((db - DB_MIN) / (DB_MAX - DB_MIN)) * 100))
}

/** Zone color for the level bar — works on both light and dark backgrounds */
function dbToBarColor(db: number): string {
  if (db > -12) return '#e8294a' // near clipping — red
  if (db > -30) return '#e8920a' // moderate — amber
  return '#00a857'               // quiet — green
}

export interface SensorCardProps {
  sensorId: string
  location: string | null
  isOnline: boolean
  batteryPercent: number | null
  lastHeartbeat: string | null
  loudnessDb: number | null
  isDbStale: boolean
}

export function SensorCard({
  sensorId,
  location,
  isOnline,
  batteryPercent,
  lastHeartbeat,
  loudnessDb,
  isDbStale,
}: SensorCardProps) {
  const [flash, setFlash] = useState(false)
  const prevDb = useRef(loudnessDb)
  const [relTime, setRelTime] = useState(() => formatRelativeTime(lastHeartbeat))

  useEffect(() => {
    if (loudnessDb !== null && loudnessDb !== prevDb.current) {
      setFlash(true)
      prevDb.current = loudnessDb
      const t = setTimeout(() => setFlash(false), 350)
      return () => clearTimeout(t)
    }
  }, [loudnessDb])

  useEffect(() => {
    setRelTime(formatRelativeTime(lastHeartbeat))
    const id = setInterval(() => setRelTime(formatRelativeTime(lastHeartbeat)), 30_000)
    return () => clearInterval(id)
  }, [lastHeartbeat])

  const batteryLow = batteryPercent !== null && batteryPercent < LOW_BATTERY_THRESHOLD
  const hasLiveData = loudnessDb !== null && !isDbStale
  const fillPct = loudnessDb !== null ? dbToFill(loudnessDb) : 0
  const barColor = loudnessDb !== null ? dbToBarColor(loudnessDb) : 'transparent'

  const statusCssVar = `var(${isOnline ? '--c-green' : '--c-red'})`

  return (
    <article
      className="relative rounded-xl overflow-hidden dot-grid"
      style={{
        background: 'var(--c-surface)',
        border: `1px solid ${flash ? 'var(--c-flash-border)' : 'var(--c-border)'}`,
        boxShadow: flash ? 'var(--c-flash-shadow)' : 'var(--c-shadow-card)',
        transition: 'border-color 0.2s, box-shadow 0.2s',
      }}
      onMouseEnter={(e) => {
        if (!flash) (e.currentTarget as HTMLElement).style.borderColor = 'var(--c-border-hov)'
      }}
      onMouseLeave={(e) => {
        if (!flash) (e.currentTarget as HTMLElement).style.borderColor = 'var(--c-border)'
      }}
    >
      {/* Left-edge status stripe */}
      <div
        aria-hidden="true"
        className="absolute left-0 top-0 bottom-0 w-[3px]"
        style={{
          backgroundColor: statusCssVar,
          boxShadow: isOnline ? 'var(--glow-stripe-online)' : 'none',
          opacity: isOnline ? 1 : 0.7,
        }}
      />

      <div className="pl-[18px] pr-4 pt-4 pb-4 flex flex-col">
        {/* ── Row 1: sensor ID + status badge ── */}
        <div className="flex items-center justify-between gap-2">
          <span
            className="font-display-mono text-[10.5px] tracking-[0.18em] uppercase truncate"
            style={{ color: 'var(--c-text)' }}
          >
            {sensorId}
          </span>
          <span
            className="inline-flex items-center gap-[5px] shrink-0 font-mono text-[9.5px] tracking-[0.14em] uppercase"
            style={{ color: statusCssVar }}
          >
            <span
              className="w-[5px] h-[5px] rounded-full shrink-0"
              style={{
                backgroundColor: statusCssVar,
                boxShadow: isOnline ? 'var(--glow-dot-online)' : 'none',
                animation: isOnline ? 'var(--anim-dot)' : 'none',
              }}
            />
            {isOnline ? 'Online' : 'Offline'}
          </span>
        </div>

        {/* ── Row 2: location ── */}
        <p
          className="font-mono text-[9.5px] tracking-wider truncate mt-[3px] mb-4"
          style={{ color: 'var(--c-text-2)' }}
        >
          {location ?? 'Location unknown'}
        </p>

        {/* ── Row 3: dB number ── */}
        <div className="flex items-baseline justify-center gap-[7px] mb-3">
          <span
            className={['db-number font-display-mono text-[3.4rem] leading-none tabular-nums select-none', flash ? 'db-flash' : ''].join(' ')}
            style={{
              color: hasLiveData
                ? 'var(--c-cyan)'
                : isDbStale && loudnessDb !== null
                  ? 'var(--c-stale-db)'
                  : 'var(--c-text-4)',
              textShadow: hasLiveData ? 'var(--glow-db)' : 'none',
            }}
          >
            {loudnessDb !== null ? loudnessDb.toFixed(1) : '\u2014'}
          </span>
          <span
            className="font-mono text-[9.5px] tracking-[0.22em] uppercase pb-[3px]"
            style={{ color: hasLiveData ? 'var(--c-cyan-dim)' : 'var(--c-text-3)' }}
          >
            dBFS
          </span>
        </div>

        {/* ── Level bar ── */}
        <div
          aria-label={`Signal level: ${loudnessDb !== null ? loudnessDb.toFixed(1) + ' dBFS' : 'no data'}`}
          className="w-full h-[4px] rounded-full overflow-hidden mb-[6px]"
          style={{ backgroundColor: 'var(--c-level-track)' }}
        >
          <div
            className="level-bar-fill h-full rounded-full"
            style={{
              width: `${fillPct}%`,
              backgroundColor: hasLiveData ? barColor : 'transparent',
              boxShadow: hasLiveData ? `0 0 8px ${barColor}55` : 'none',
              transition: 'width 120ms linear, background-color 300ms ease',
            }}
          />
        </div>

        {/* dBFS scale ticks */}
        <div className="flex justify-between mb-3">
          {['-80', '-60', '-40', '-20', '0'].map((v) => (
            <span
              key={v}
              className="font-mono text-[8px] tabular-nums"
              style={{ color: 'var(--c-scale-tick)' }}
            >
              {v}
            </span>
          ))}
        </div>

        {/* Stale indicator */}
        {isDbStale && loudnessDb !== null && (
          <p
            className="font-mono text-[8.5px] tracking-[0.2em] uppercase text-center -mt-1 mb-2"
            style={{ color: 'var(--c-text-3)' }}
          >
            · stale ·
          </p>
        )}

        {/* ── Footer: battery + last seen ── */}
        <div
          className="flex items-center justify-between pt-3 mt-auto"
          style={{ borderTop: '1px solid var(--c-divider)' }}
        >
          <div className="font-mono text-[9.5px]">
            {batteryPercent === null ? (
              <span style={{ color: 'var(--c-text-3)' }}>no battery</span>
            ) : batteryLow ? (
              <span className="flex items-center gap-[6px]" style={{ color: 'var(--c-red)' }}>
                <BatteryIcon percent={batteryPercent} />
                Needs Charging
              </span>
            ) : (
              <span className="flex items-center gap-[6px]" style={{ color: 'var(--c-green)' }}>
                <BatteryIcon percent={batteryPercent} />
                Healthy
              </span>
            )}
          </div>

          <span
            className="font-mono text-[9.5px] tabular-nums"
            style={{ color: 'var(--c-text-2)' }}
          >
            {relTime}
          </span>
        </div>
      </div>
    </article>
  )
}

function BatteryIcon({ percent }: { percent: number }) {
  const fillWidth = Math.round(11 * Math.max(0, Math.min(1, percent / 100)))
  return (
    <svg className="w-[15px] h-[10px] shrink-0" viewBox="0 0 20 12" fill="none">
      <rect x="0.5" y="0.5" width="15" height="11" rx="2" stroke="currentColor" strokeWidth="1.1" />
      {fillWidth > 0 && (
        <rect
          x="2"
          y="2"
          width={fillWidth}
          height="8"
          rx="1"
          fill="currentColor"
          style={{ transition: 'width 0.3s ease' }}
        />
      )}
      <path d="M16.5 4v4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <path d="M18.5 4v4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  )
}
