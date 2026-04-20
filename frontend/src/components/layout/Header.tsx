import { useAuth } from '../../hooks/useAuth'
import { useTheme } from '../../context/ThemeContext'

interface HeaderProps {
  wsConnected?: boolean
}

export default function Header({ wsConnected }: HeaderProps) {
  const { user, logout } = useAuth()
  const { theme, toggle } = useTheme()

  const wsLineColor = wsConnected === undefined
    ? 'var(--c-divider)'
    : wsConnected
      ? 'var(--c-green)'
      : 'var(--c-amber)'

  return (
    <header className="sticky top-0 z-20">
      {/* 1px live-status line across very top */}
      <div
        className="h-[1px] w-full transition-colors duration-700"
        style={{ backgroundColor: wsLineColor }}
      />

      <div
        className="flex items-center justify-between px-5 py-[11px] max-w-screen-2xl mx-auto backdrop-blur-sm"
        style={{
          backgroundColor: 'var(--c-header-bg)',
          borderBottom: '1px solid var(--c-divider)',
        }}
      >
        {/* Left: wordmark */}
        <div className="flex items-center gap-3">
          <WaveformMark />
          <div className="flex flex-col leading-none gap-[3px]">
            <span
              className="font-display-mono text-[10.5px] tracking-[0.25em] uppercase"
              style={{ color: 'var(--c-text)' }}
            >
              Hospital Audio Monitor
            </span>
            <span
              className="font-mono text-[8.5px] tracking-[0.18em] uppercase"
              style={{ color: 'var(--c-text-3)' }}
            >
              Real-time Sensor Dashboard
            </span>
          </div>
        </div>

        {/* Right: WS indicator + theme toggle + username + logout */}
        <div className="flex items-center gap-3">
          {/* WebSocket live indicator */}
          {wsConnected !== undefined && (
            <div className="hidden sm:flex items-center gap-[7px]">
              <span
                className="w-[5px] h-[5px] rounded-full shrink-0"
                style={{
                  backgroundColor: wsConnected ? 'var(--c-green)' : 'var(--c-amber)',
                  boxShadow: wsConnected ? 'var(--glow-dot-online)' : 'none',
                  animation: wsConnected ? 'var(--anim-dot)' : 'none',
                }}
              />
              <span
                className="font-mono text-[9px] tracking-[0.2em] uppercase"
                style={{ color: wsConnected ? 'var(--c-green)' : 'var(--c-amber)', opacity: 0.8 }}
              >
                {wsConnected ? 'Live' : 'Reconnecting'}
              </span>
            </div>
          )}

          {/* Theme toggle */}
          <button
            onClick={toggle}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            className="flex items-center justify-center w-[30px] h-[30px] rounded-lg transition-all duration-150"
            style={{
              border: '1px solid var(--c-border)',
              color: 'var(--c-text-3)',
              backgroundColor: 'transparent',
            }}
            onMouseEnter={(e) => {
              const el = e.currentTarget as HTMLButtonElement
              el.style.borderColor = 'var(--c-border-hov)'
              el.style.color = 'var(--c-text)'
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLButtonElement
              el.style.borderColor = 'var(--c-border)'
              el.style.color = 'var(--c-text-3)'
            }}
          >
            {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
          </button>

          {user?.username && (
            <span
              className="hidden sm:block font-mono text-[9.5px] tracking-wide"
              style={{ color: 'var(--c-text-3)' }}
            >
              {user.username}
            </span>
          )}

          <button
            onClick={logout}
            className="font-mono text-[9.5px] tracking-[0.18em] uppercase px-3 py-[7px] rounded-lg transition-all duration-150"
            style={{
              border: '1px solid var(--c-border)',
              color: 'var(--c-text-3)',
              backgroundColor: 'transparent',
            }}
            onMouseEnter={(e) => {
              const el = e.currentTarget as HTMLButtonElement
              el.style.borderColor = 'var(--c-border-hov)'
              el.style.color = 'var(--c-text)'
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLButtonElement
              el.style.borderColor = 'var(--c-border)'
              el.style.color = 'var(--c-text-3)'
            }}
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  )
}

function WaveformMark() {
  const bars = [
    { h: 6,  y: 9  },
    { h: 12, y: 6  },
    { h: 20, y: 2  },
    { h: 14, y: 5  },
    { h: 8,  y: 8  },
  ]
  return (
    <svg width="22" height="24" viewBox="0 0 22 24" fill="none" aria-hidden="true">
      {bars.map((b, i) => (
        <rect
          key={i}
          x={i * 4 + 1}
          y={b.y}
          width="3"
          height={b.h}
          rx="1.5"
          style={{ fill: 'var(--c-green)', opacity: 0.45 + i * 0.1 }}
        />
      ))}
    </svg>
  )
}

function SunIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1" x2="12" y2="3" />
      <line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1" y1="12" x2="3" y2="12" />
      <line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  )
}
