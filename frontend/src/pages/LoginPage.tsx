import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useEffect } from 'react'
import LoginForm from '../components/auth/LoginForm'

export default function LoginPage() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/')
    }
  }, [isAuthenticated, navigate])

  return (
    <div
      className="min-h-screen flex items-center justify-center dot-grid px-4"
      style={{ backgroundColor: 'var(--c-page-bg)' }}
    >
      <div className="w-full max-w-[360px]">

        {/* Wordmark */}
        <div className="flex flex-col items-center mb-8">
          <LoginWaveform />
          <h1
            className="font-display-mono text-[11px] tracking-[0.3em] uppercase text-center mt-5"
            style={{ color: 'var(--c-text-2)' }}
          >
            Hospital Audio Monitor
          </h1>
          <p
            className="font-mono text-[9px] tracking-[0.2em] uppercase mt-2"
            style={{ color: 'var(--c-text-3)' }}
          >
            Secure Dashboard Access
          </p>
        </div>

        {/* Card */}
        <div
          className="rounded-xl overflow-hidden"
          style={{
            background: 'var(--c-surface)',
            border: '1px solid var(--c-border)',
            boxShadow: '0 24px 64px rgba(0,0,0,0.3)',
          }}
        >
          {/* Green accent line */}
          <div
            className="h-[1px] w-full"
            style={{ background: 'linear-gradient(90deg, transparent, var(--c-green), transparent)' }}
          />
          <div className="px-7 py-8">
            <LoginForm onSuccess={() => navigate('/')} />
          </div>
        </div>

        <p
          className="font-mono text-[8.5px] tracking-[0.25em] uppercase text-center mt-6"
          style={{ color: 'var(--c-text-3)' }}
        >
          Authorized Personnel Only
        </p>
      </div>
    </div>
  )
}

function LoginWaveform() {
  const bars = [4, 10, 18, 26, 16, 22, 12, 20, 8, 14, 6]
  return (
    <svg width="88" height="32" viewBox="0 0 88 32" fill="none" aria-hidden="true">
      {bars.map((h, i) => {
        const y = (32 - h) / 2
        return (
          <rect
            key={i}
            x={i * 8 + 1}
            y={y}
            width="5"
            height={h}
            rx="2.5"
            style={{
              fill: 'var(--c-green)',
              opacity: 0.3 + (h / 26) * 0.65,
            }}
          />
        )
      })}
    </svg>
  )
}
