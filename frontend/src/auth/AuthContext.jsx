/**
 * Session state.
 *
 * The session check no longer blocks rendering. Previously an `AuthWrapper`
 * held the entire app — including the public landing page — behind a spinner
 * until `/users/profile/` answered. Now the app paints immediately and the
 * check resolves alongside it; only guarded routes wait.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'

import { api, ensureCsrf } from '../lib/api'
import { invalidate } from '../lib/query'

const AuthContext = createContext(null)

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [checked, setChecked] = useState(false)
  const started = useRef(false)

  const refresh = useCallback(async () => {
    try {
      setUser(await api.profile())
    } catch {
      // A 401 here is the normal signed-out case, not an error worth surfacing.
      setUser(null)
    } finally {
      setChecked(true)
    }
  }, [])

  useEffect(() => {
    // StrictMode invokes effects twice in development; this keeps it to one
    // request rather than two.
    if (started.current) return
    started.current = true

    ensureCsrf().then(refresh)
  }, [refresh])

  const signIn = useCallback(
    async (username, password) => {
      await ensureCsrf()
      const result = await api.login(username, password)
      setUser(result.user)
      invalidate('')
      return result.user
    },
    [],
  )

  const signUp = useCallback(async (payload) => {
    await ensureCsrf()
    const result = await api.signup(payload)
    setUser(result.user)
    invalidate('')
    return result.user
  }, [])

  const signOut = useCallback(async () => {
    // Clear locally first so the UI responds even if the request is slow.
    setUser(null)
    invalidate('')
    try {
      await api.logout()
    } finally {
      window.location.assign('/')
    }
  }, [])

  const value = useMemo(
    () => ({ user, checked, signIn, signUp, signOut, refresh }),
    [user, checked, signIn, signUp, signOut, refresh],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
