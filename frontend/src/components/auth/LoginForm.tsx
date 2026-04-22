import { useState } from 'react'
import { useAuth } from '../../hooks/useAuth'

interface LoginFormProps {
  onSuccess?: () => void
}

export default function LoginForm({ onSuccess }: LoginFormProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [focusedField, setFocusedField] = useState<'username' | 'password' | null>(null)
  const { login } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      await login(username, password)
      onSuccess?.()
    } catch {
      setError('Invalid username or password')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      {error && (
        <div
          className="px-4 py-3 rounded-lg font-mono text-[12px]"
          style={{
            background: 'var(--c-error-bg)',
            border: '1px solid var(--c-error-border)',
            color: 'var(--c-error-text)',
          }}
        >
          {error}
        </div>
      )}

      {(['username', 'password'] as const).map((field) => (
        <div key={field} className="flex flex-col gap-[7px]">
          <label
            htmlFor={field}
            className="font-mono text-[12px] font-medium capitalize"
            style={{ color: 'var(--c-text-2)' }}
          >
            {field}
          </label>
          <input
            id={field}
            type={field === 'password' ? 'password' : 'text'}
            value={field === 'username' ? username : password}
            onChange={(e) =>
              field === 'username' ? setUsername(e.target.value) : setPassword(e.target.value)
            }
            onFocus={() => setFocusedField(field)}
            onBlur={() => setFocusedField(null)}
            required
            autoComplete={field === 'username' ? 'username' : 'current-password'}
            style={{
              width: '100%',
              background: 'var(--c-surface-deep)',
              border: `1px solid ${focusedField === field ? 'var(--c-border-focus)' : 'var(--c-border)'}`,
              borderRadius: '8px',
              color: 'var(--c-text)',
              fontFamily: 'inherit',
              fontSize: '13px',
              letterSpacing: '0.01em',
              padding: '10px 12px',
              outline: 'none',
              boxShadow: focusedField === field ? '0 0 0 3px rgba(59,130,246,0.10)' : 'none',
              transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
            }}
          />
        </div>
      ))}

      <button
        type="submit"
        disabled={isLoading}
        className="w-full font-display-mono text-[13px] font-semibold rounded-lg py-[11px] transition-all duration-150"
        style={{
          background: isLoading ? 'var(--c-cyan)' : 'var(--c-cyan)',
          color: 'var(--c-btn-login-text)',
          opacity: isLoading ? 0.6 : 1,
          cursor: isLoading ? 'not-allowed' : 'pointer',
          boxShadow: isLoading ? 'none' : 'var(--glow-login-btn)',
          border: 'none',
          fontWeight: 600,
        }}
        onMouseEnter={(e) => {
          if (!isLoading) (e.currentTarget as HTMLButtonElement).style.boxShadow = 'var(--glow-login-btn-hov)'
        }}
        onMouseLeave={(e) => {
          if (!isLoading) (e.currentTarget as HTMLButtonElement).style.boxShadow = 'var(--glow-login-btn)'
        }}
      >
        {isLoading ? 'Signing in…' : 'Sign In'}
      </button>
    </form>
  )
}
