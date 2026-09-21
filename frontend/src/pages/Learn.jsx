/**
 * Course index.
 *
 * Locked courses now say exactly what unlocks them. The old grid rendered a
 * padlock and the words "Complete prerequisites to unlock" without naming any.
 */
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Lock } from 'lucide-react'

import { useAuth } from '../auth/AuthContext'
import { api } from '../lib/api'
import { useQuery } from '../lib/query'
import { Badge, Meter, PageHeader, Panel, Skeleton, Tabs, cx } from '../ui'

const LEVELS = [
  { value: 'all', label: 'All' },
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
]

export default function Learn() {
  const { user } = useAuth()
  const { data, loading } = useQuery('courses', api.courses, { ttl: 300_000 })
  const [level, setLevel] = useState('all')

  const courses = useMemo(() => {
    const all = data?.courses ?? data ?? []
    return level === 'all' ? all : all.filter((course) => course.level === level)
  }, [data, level])

  const xp = user?.xp ?? 0

  return (
    <div className="mx-auto max-w-page px-4 py-8">
      <PageHeader
        eyebrow="Courses"
        title="Learn"
        lede="Twenty-five courses, from what a savings account actually does through to valuation. Finish a module and its questions join your daily drill."
      />

      <div className="mt-6">
        <Tabs items={LEVELS} value={level} onChange={setLevel} />
      </div>

      {loading && !data ? (
        <div className="mt-6 grid gap-px bg-rule sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }, (_, index) => (
            <Skeleton key={index} className="h-36 bg-paper" />
          ))}
        </div>
      ) : (
        <div className="mt-6 grid gap-px border border-rule bg-rule sm:grid-cols-2 lg:grid-cols-3">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} xp={xp} />
          ))}
        </div>
      )}
    </div>
  )
}

function CourseCard({ course, xp }) {
  const locked = xp < course.xp_to_unlock
  const completed = course.completed_modules ?? 0
  const total = course.module_count ?? course.modules?.length ?? 0

  const body = (
    <>
      <div className="flex items-start justify-between gap-3">
        <Badge tone={locked ? 'neutral' : 'accent'}>{course.level}</Badge>
        {locked && <Lock size={14} className="text-ink-faint" />}
      </div>

      <h2 className={cx('mt-3 font-display text-title', locked && 'text-ink-muted')}>
        {course.title}
      </h2>

      <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-ink-muted">
        {course.summary}
      </p>

      <div className="mt-auto pt-4">
        {locked ? (
          <p className="text-xs text-ink-faint">
            Unlocks at {course.xp_to_unlock.toLocaleString('en-IN')} XP — you have{' '}
            <span className="num">{xp.toLocaleString('en-IN')}</span>.
          </p>
        ) : (
          <>
            <div className="flex items-baseline justify-between text-xs text-ink-faint">
              <span>
                {total} module{total === 1 ? '' : 's'} · {course.estimated_minutes} min
              </span>
              <span className="num">
                {completed}/{total}
              </span>
            </div>
            <Meter value={completed} max={total} className="mt-1.5" />
          </>
        )}
      </div>
    </>
  )

  const className = 'flex min-h-[170px] flex-col bg-paper p-5 transition-colors'

  if (locked) {
    return <article className={cx(className, 'opacity-60')}>{body}</article>
  }

  return (
    <Link
      to={`/learn/${course.id}`}
      className={cx(className, 'hover:bg-paper-raised')}
    >
      {body}
    </Link>
  )
}
