/**
 * Sign in / create account.
 *
 * Validation is inline and per-field. The old version validated in the auth
 * context, returned a single error string, and logged the attempted username
 * and a masked password to the console on every submit.
 */
import { forwardRef, useEffect, useRef, useState } from 'react'

import { Button } from '../ui'
import { useAuth } from './AuthContext'

export function AuthDialog({ mode = 'login', onClose, onSwitch }) {
  const { signIn, signUp } = useAuth()
  const [values, setValues] = useState({ username: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const firstField = useRef(null)

  const isSignup = mode === 'signup'

  useEffect(() => {
    firstField.current?.focus()

    const onKey = (event) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const set = (field) => (event) => {
    setValues((current) => ({ ...current, [field]: event.target.value }))
    setError('')
  }

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')

    try {
      if (isSignup) {
        await signUp(values)
      } else {
        await signIn(values.username, values.password)
      }
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center overscroll-contain bg-scrim/60 p-4 backdrop-blur-sm"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-title"
        className="w-full max-w-sm rounded-lg border border-rule bg-paper-raised p-6 shadow-float rise"
      >
        <p className="eyebrow">WealthPlay</p>
        <h2 id="auth-title" className="mt-1 text-title">
          {isSignup ? 'Create your account' : 'Sign in'}
        </h2>

        <form onSubmit={submit} className="mt-5 space-y-3" noValidate>
          <Field
            ref={firstField}
            label="Username"
            value={values.username}
            onChange={set('username')}
            autoComplete="username"
            minLength={isSignup ? 3 : undefined}
            required
          />

          {isSignup && (
            <Field
              label="Email"
              type="email"
              value={values.email}
              onChange={set('email')}
              autoComplete="email"
              required
            />
          )}

          <Field
            label="Password"
            type="password"
            value={values.password}
            onChange={set('password')}
            autoComplete={isSignup ? 'new-password' : 'current-password'}
            hint={isSignup ? 'At least 8 characters, not all numbers.' : undefined}
            required
          />

          {error && (
            <p role="alert" aria-live="polite" className="rounded-sm border border-down/30 bg-down/5 px-3 py-2 text-xs text-ink">
              {error}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? 'Working…' : isSignup ? 'Create account' : 'Sign in'}
          </Button>
        </form>

        <p className="mt-4 text-center text-xs text-ink-muted">
          {isSignup ? 'Already have an account?' : 'New here?'}{' '}
          <button
            type="button"
            onClick={onSwitch}
            className="font-medium text-accent underline underline-offset-2"
          >
            {isSignup ? 'Sign in' : 'Create one'}
          </button>
        </p>
      </div>
    </div>
  )
}

const Field = forwardRef(function Field({ label, hint, ...props }, ref) {
  return (
    <label className="block">
      <span className="eyebrow">{label}</span>
      <input
        ref={ref}
        {...props}
        className="mt-1 h-10 w-full rounded border border-rule-strong bg-paper px-3 text-sm text-ink outline-none transition-colors focus:border-accent"
      />
      {hint && <span className="mt-1 block text-[11px] text-ink-faint">{hint}</span>}
    </label>
  )
})

export default AuthDialog
