/**
 * One course: its modules, in order, with progress.
 */
import { Link, useParams } from 'react-router-dom'
import { Check, Circle } from 'lucide-react'

import { api } from '../lib/api'
import { useQuery } from '../lib/query'
import { Badge, Meter, PageHeader, Skeleton, cx } from '../ui'

export default function Course() {
  const { courseId } = useParams()
  const { data, loading } = useQuery(`course:${courseId}`, () => api.course(courseId), {
    ttl: 60_000,
  })

  if (loading && !data) {
    return (
      <div className="mx-auto max-w-page px-4 py-8">
        <Skeleton className="h-10 w-72" />
        <Skeleton className="mt-6 h-64" />
      </div>
    )
  }

  if (!data) return null

  const done = data.modules.filter((module) => module.status === 'completed').length
  const nextUp = data.modules.find((module) => module.status !== 'completed') ?? data.modules[0]

  return (
    <div className="mx-auto max-w-page px-4 py-8">
      <Link
        to="/learn"
        className="text-sm text-ink-muted underline decoration-rule-strong underline-offset-4 hover:text-ink"
      >
        All courses
      </Link>

      <PageHeader
        className="mt-4"
        eyebrow={data.level}
        title={data.title}
        lede={data.summary}
        action={
          <Link
            to={`/learn/${courseId}/${nextUp.id}`}
            className="rounded bg-accent px-4 py-2.5 text-sm text-accent-on transition-colors hover:bg-accent-hover"
          >
            {done === 0 ? 'Start course' : done === data.modules.length ? 'Review' : 'Continue'}
          </Link>
        }
      />

      <div className="mt-6 flex items-center gap-4">
        <Meter value={done} max={data.modules.length} className="max-w-xs" />
        <span className="num text-xs text-ink-muted">
          {done} of {data.modules.length} · {data.estimated_minutes} min total
        </span>
      </div>

      <ol className="mt-8 border-t border-rule">
        {data.modules.map((module, index) => (
          <li key={module.id}>
            <Link
              to={`/learn/${courseId}/${module.id}`}
              className="flex items-start gap-4 border-b border-rule py-4 transition-colors hover:bg-paper-raised"
            >
              <span className="mt-0.5 shrink-0">
                {module.status === 'completed' ? (
                  <Check size={18} className="text-up" />
                ) : (
                  <Circle size={18} className="text-ink-faint" strokeWidth={1.5} />
                )}
              </span>

              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <span className="num text-xs text-ink-faint">
                    {String(index + 1).padStart(2, '0')}
                  </span>
                  <h2
                    className={cx(
                      'font-display text-title',
                      module.status === 'completed' ? 'text-ink-muted' : 'text-ink',
                    )}
                  >
                    {module.title}
                  </h2>
                  {module.status === 'in_progress' && <Badge tone="play">In progress</Badge>}
                </div>
                <p className="mt-1 line-clamp-2 text-sm text-ink-muted">{module.summary}</p>
              </div>

              <span className="num shrink-0 text-xs text-ink-faint">
                {module.estimated_minutes} min · {module.xp_reward} XP
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </div>
  )
}
