/**
 * Catches render errors so one broken component does not blank the app.
 *
 * Class component because React has no hook equivalent for error boundaries.
 */
import { Component } from 'react'

/**
 * A chunk that no longer exists on the server.
 *
 * Routes are lazy, so each one is a separate hashed file. A deployment replaces
 * those filenames, and any tab still holding the previous `index.js` asks for a
 * chunk that has just been deleted — the first navigation after a deploy throws
 * "Failed to fetch dynamically imported module" and the user sees a crash page
 * for a build that is simply out of date.
 *
 * Browsers word it differently, so the match is deliberately loose.
 */
const STALE_BUILD = /dynamically imported module|Loading chunk|Importing a module script failed|error loading dynamically imported module/i

// Survives the reload, so a genuine import failure cannot become a reload loop.
const RELOAD_FLAG = 'wp:reloaded-for-stale-build'

export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    // Kept in the console rather than swallowed, so the stack is recoverable
    // in development and by a monitoring hook in production.
    console.error('Render failed:', error, info.componentStack)

    // A missing chunk is not a broken app, it is an old one. Fetch the new
    // build instead of asking the user to work out that reloading fixes it.
    if (STALE_BUILD.test(error?.message || '') && !sessionStorage.getItem(RELOAD_FLAG)) {
      try {
        sessionStorage.setItem(RELOAD_FLAG, '1')
      } catch {
        // Private browsing can refuse storage. Reloading once is still right;
        // without the flag a second failure lands on the message below.
      }
      window.location.reload()
    }
  }

  componentDidMount() {
    // Clear the flag only after the app has stayed up for a while, not on
    // mount. Clearing it immediately would re-arm the reload before the failing
    // navigation had even happened, so a chunk that is genuinely missing —
    // rather than merely replaced — would reload forever.
    this.settled = setTimeout(() => {
      try {
        sessionStorage.removeItem(RELOAD_FLAG)
      } catch {
        /* storage unavailable; nothing to clear */
      }
    }, 10_000)
  }

  componentWillUnmount() {
    clearTimeout(this.settled)
  }

  render() {
    if (!this.state.error) return this.props.children

    const stale = STALE_BUILD.test(this.state.error?.message || '')

    return (
      <div className="mx-auto flex min-h-dvh max-w-page flex-col justify-center px-4">
        <p className="eyebrow">Something broke</p>
        <h1 className="mt-3 text-headline">
          {stale ? 'A new version is available.' : 'This page failed to render.'}
        </h1>
        <p className="measure mt-3 text-sm text-ink-muted">
          {stale
            ? 'This tab was open while the site updated. Reloading picks up the new version.'
            : 'Your data is safe — this is a display problem. Reloading usually clears it.'}
        </p>
        <div className="mt-6 flex gap-3">
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="rounded bg-accent px-4 py-2 text-sm text-accent-on hover:bg-accent-hover"
          >
            Reload
          </button>
          <a
            href="/"
            className="rounded border border-rule px-4 py-2 text-sm text-ink-muted hover:text-ink"
          >
            Go home
          </a>
        </div>

        {import.meta.env.DEV && (
          <pre className="mt-8 overflow-auto rounded border border-rule bg-paper-sunken p-4 text-xs text-ink-muted">
            {this.state.error.stack}
          </pre>
        )}
      </div>
    )
  }
}
