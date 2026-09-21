/**
 * App chrome: masthead, navigation, mentor.
 *
 * The header sits in normal document flow rather than floating over the page.
 * The old one was `fixed top-6` as a centred pill while `<main>` carried a
 * fixed `pt-28`, so on every page with its own sticky sub-header the nav
 * covered the page title.
 */
import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { Menu, Moon, Sun, X } from 'lucide-react'

import { useAuth } from '../auth/AuthContext'
import AuthDialog from '../auth/AuthDialog'
import { currentTheme, toggleTheme } from '../lib/theme'
import { cx } from '../ui'
import Mentor from './Mentor'

const NAV = [
  { to: '/today', label: 'Today' },
  { to: '/learn', label: 'Learn' },
  { to: '/markets', label: 'Markets' },
  { to: '/play', label: 'Play' },
  { to: '/progress', label: 'Progress' },
]

export default function Shell({ children, chrome = true }) {
  const { user } = useAuth()
  const location = useLocation()
  const [authMode, setAuthMode] = useState(null)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => setMenuOpen(false), [location.pathname])

  useEffect(() => {
    const open = (event) => setAuthMode(event.detail || 'signup')
    window.addEventListener('wp:auth', open)
    return () => window.removeEventListener('wp:auth', open)
  }, [])

  return (
    <div className="relative min-h-dvh">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-accent focus:px-3 focus:py-2 focus:text-sm focus:text-accent-on"
      >
        Skip to content
      </a>

      {chrome && (
        <Masthead
          user={user}
          menuOpen={menuOpen}
          onMenu={() => setMenuOpen((open) => !open)}
          onAuth={setAuthMode}
        />
      )}

      {/* Bottom padding clears the floating mentor button, which would
          otherwise sit over the last card on a phone. */}
      <main id="main" className="relative z-10 pb-24">
        {children}
      </main>

      {chrome && user && <Mentor />}

      {authMode && (
        <AuthDialog
          mode={authMode}
          onClose={() => setAuthMode(null)}
          onSwitch={() => setAuthMode((mode) => (mode === 'login' ? 'signup' : 'login'))}
        />
      )}
    </div>
  )
}

function Masthead({ user, menuOpen, onMenu, onAuth }) {
  return (
    <header className="sticky top-0 z-40 border-b border-rule bg-paper/90 backdrop-blur">
      <div className="mx-auto flex h-header max-w-page items-center gap-6 px-4">
        <Link to={user ? '/today' : '/'} className="shrink-0">
          <span className="font-display text-xl tracking-tight text-ink">WealthPlay</span>
        </Link>

        {user && (
          <nav className="hidden flex-1 items-center gap-1 md:flex" aria-label="Main">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cx(
                    'rounded px-3 py-1.5 text-sm transition-colors',
                    isActive
                      ? 'bg-paper-sunken font-medium text-ink'
                      : 'text-ink-muted hover:text-ink',
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        )}

        <div className="ml-auto flex items-center gap-1">
          <ThemeToggle />

          {user ? (
            <>
              <Link
                to="/progress"
                className="hidden rounded px-3 py-1.5 text-sm text-ink-muted transition-colors hover:text-ink sm:block"
              >
                {user.username}
              </Link>
              <button
                type="button"
                onClick={onMenu}
                aria-expanded={menuOpen}
                aria-label="Menu"
                className="rounded p-2 text-ink-muted transition-colors hover:text-ink md:hidden"
              >
                {menuOpen ? <X size={18} /> : <Menu size={18} />}
              </button>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => onAuth('login')}
                className="rounded px-3 py-1.5 text-sm text-ink-muted transition-colors hover:text-ink"
              >
                Sign in
              </button>
              <button
                type="button"
                onClick={() => onAuth('signup')}
                className="rounded bg-accent px-3 py-1.5 text-sm text-accent-on transition-colors hover:bg-accent-hover"
              >
                Start free
              </button>
            </div>
          )}
        </div>
      </div>

      {menuOpen && user && (
        <nav className="border-t border-rule md:hidden" aria-label="Main">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cx(
                  'block border-b border-rule px-4 py-3 text-sm',
                  isActive ? 'bg-paper-sunken font-medium text-ink' : 'text-ink-muted',
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      )}
    </header>
  )
}

function ThemeToggle() {
  const [theme, setTheme] = useState(currentTheme)

  return (
    <button
      type="button"
      onClick={() => setTheme(toggleTheme())}
      className="rounded p-2 text-ink-muted transition-colors hover:text-ink"
      aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
    >
      {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  )
}
