/**
 * Catches render errors so one broken component does not blank the app.
 *
 * Class component because React has no hook equivalent for error boundaries.
 */
import { Component } from 'react'

export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    // Kept in the console rather than swallowed, so the stack is recoverable
    // in development and by a monitoring hook in production.
    console.error('Render failed:', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <div className="mx-auto flex min-h-dvh max-w-page flex-col justify-center px-4">
        <p className="eyebrow">Something broke</p>
        <h1 className="mt-3 text-headline">This page failed to render.</h1>
        <p className="measure mt-3 text-sm text-ink-muted">
          Your data is safe — this is a display problem. Reloading usually clears it.
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
