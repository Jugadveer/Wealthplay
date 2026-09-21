/**
 * 404. Every dead end needs a way back.
 */
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

export default function NotFound() {
  const { user } = useAuth()

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-page flex-col justify-center px-4">
      <p className="eyebrow">Error 404</p>
      <h1 className="mt-3 text-display">This page isn't here.</h1>
      <p className="measure mt-4 text-ink-muted">
        The link may be old, or the address slightly off. Nothing is broken on your side.
      </p>

      <nav className="mt-8 flex flex-wrap gap-3">
        {(user
          ? [
              ['/today', "Today's edition"],
              ['/learn', 'Courses'],
              ['/markets', 'Markets'],
            ]
          : [['/', 'Home']]
        ).map(([to, label]) => (
          <Link
            key={to}
            to={to}
            className="rounded border border-rule px-4 py-2 text-sm text-ink-muted transition-colors hover:border-ink-faint hover:text-ink"
          >
            {label}
          </Link>
        ))}
      </nav>
    </div>
  )
}
