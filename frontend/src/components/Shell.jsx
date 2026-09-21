/**
 * App chrome: header, navigation, mentor.
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
import Toaster from './Toaster'
import ZoneCurtain from './ZoneCurtain'

const NAV = [
  { to: '/today', label: 'Today' },
  { to: '/learn', label: 'Learn' },
  { to: '/markets', label: 'Markets' },
  { to: '/play', label: 'Play' },
  { to: '/progress', label: 'Progress' },
]

/**
 * The section of the app a path belongs to.
 *
 * Writing it to `data-zone` on <html> is what makes each section feel like a
 * place: index.css redefines --accent per zone, so the nav, the rules, the
 * meters and the first chart series all shift together.
 */
function zoneFor(pathname) {
  const root = pathname.split('/')[1]
  return NAV.some((item) => item.to === `/${root}`) ? root : ''
}

export default function Shell({ children, chrome = true }) {
  const { user } = useAuth()
  const location = useLocation()
  const [authMode, setAuthMode] = useState(null)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => setMenuOpen(false), [location.pathname])

  const zone = zoneFor(location.pathname)

  useEffect(() => {
    document.documentElement.dataset.zone = zone
  }, [zone])

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
        <SiteHeader
          user={user}
          menuOpen={menuOpen}
          onMenu={() => setMenuOpen((open) => !open)}
          onAuth={setAuthMode}
        />
      )}

      {/* Keyed on the path so every navigation replays the entry animation:
          without it, moving between sections swapped the text and nothing else,
          which read as one long page rather than as arriving somewhere.
          Bottom padding clears the floating mentor button. */}
      <main id="main" key={location.pathname} className="relative z-10 rise pb-24">
        {children}
      </main>

      {chrome && user && <Mentor />}
      {chrome && <ZoneCurtain zone={zone} />}
      <Toaster />

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

function SiteHeader({ user, menuOpen, onMenu, onAuth }) {
  return (
    <header className="sticky top-0 z-40 border-b border-rule bg-paper/90 backdrop-blur">
      <div className="mx-auto flex h-header max-w-page items-center gap-6 px-4">
        <Link to={user ? '/today' : '/'} className="flex shrink-0 items-center gap-2.5">
          {/* The same mark as the favicon, so the tab and the header agree. */}
          <svg viewBox="0 0 32 32" className="h-6 w-6" aria-hidden="true">
            <rect width="32" height="32" rx="7" className="fill-ink" />
            <path
              d="M7 21.5 13 15l4.5 4.5L25 11"
              fill="none"
              className="stroke-paper"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="font-display text-lg font-semibold tracking-tight text-ink">
            WealthPlay
          </span>
        </Link>

        {user && (
          <nav className="hidden flex-1 items-center gap-1 md:flex" aria-label="Main">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                // The active item carries the section's own colour, so the
                // nav answers "where am I" before the page has rendered.
                className={({ isActive }) =>
                  cx(
                    'relative rounded px-3 py-1.5 text-sm transition-colors duration-200',
                    isActive
                      ? 'bg-accent/10 font-medium text-accent'
                      : 'text-ink-muted hover:bg-paper-sunken hover:text-ink',
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
                className="rounded bg-ink px-3.5 py-2 text-sm font-medium text-paper transition-colors duration-200 hover:bg-ink/90"
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
                  isActive
                    ? 'border-l-2 border-l-accent bg-accent/10 font-medium text-accent'
                    : 'text-ink-muted',
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
