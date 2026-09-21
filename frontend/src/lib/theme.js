/**
 * Light/dark theme.
 *
 * Both themes are designed, not inverted: each has its own token values in
 * index.css. The choice follows the OS until the reader overrides it, and the
 * override is remembered.
 */

const STORAGE_KEY = 'wp-theme'

function systemPrefersDark() {
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
}

function read() {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    // Private windows and blocked storage both throw; fall back to the OS.
    return null
  }
}

/** Apply the stored or system theme. Called once before React mounts. */
export function initTheme() {
  const stored = read()
  document.documentElement.dataset.theme =
    stored || (systemPrefersDark() ? 'dark' : 'light')

  // Keep following the OS for as long as the reader has not chosen.
  window.matchMedia?.('(prefers-color-scheme: dark)').addEventListener?.('change', (event) => {
    if (!read()) document.documentElement.dataset.theme = event.matches ? 'dark' : 'light'
  })
}

export const currentTheme = () => document.documentElement.dataset.theme || 'light'

/** Flip the theme and remember the choice. */
export function toggleTheme() {
  const next = currentTheme() === 'dark' ? 'light' : 'dark'
  document.documentElement.dataset.theme = next
  try {
    localStorage.setItem(STORAGE_KEY, next)
  } catch {
    // Not remembering is acceptable; not applying it is not.
  }
  return next
}
