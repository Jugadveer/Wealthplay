/**
 * The blocks below the daily set on the signed-in home.
 *
 * The set is the reason to open the app; these are the reasons to stay in it.
 * Each block is a single query with its own cache key, so one slow provider
 * never holds up the rest of the page.
 */
import { Link } from 'react-router-dom'
import { ArrowRight, BookOpen, Wallet } from 'lucide-react'

import { api } from '../../lib/api'
import { money, percent, toneFor } from '../../lib/format'
import { useQuery } from '../../lib/query'
import { Badge, Meter, Panel, Skeleton, cx } from '../../ui'

/** The practice account at a glance, with a way straight into it. */
export function Desk() {
  const { data, loading } = useQuery('portfolio', api.portfolio, { ttl: 30_000 })

  if (loading && !data) return <Skeleton className="h-40 rounded-lg" />
  if (!data) return null

  const holdings = data.holdings ?? []
  const top = [...holdings].sort((a, b) => b.current_value - a.current_value).slice(0, 3)

  return (
    <Panel className="p-5">
      <div className="flex items-baseline justify-between gap-3">
        <p className="eyebrow">Practice account</p>
        <Link
          to="/markets"
          className="flex items-center gap-1 text-xs text-ink-muted transition-colors hover:text-accent"
        >
          Open the desk
          <ArrowRight size={12} />
        </Link>
      </div>

      <div className="mt-3 flex flex-wrap items-baseline gap-x-6 gap-y-1">
        <p className="num text-2xl font-semibold text-ink">{money(data.total_value)}</p>
        <p className={cx('num text-sm', toneFor(data.total_pnl_percent))}>
          {percent(data.total_pnl_percent)} all time
        </p>
      </div>

      {top.length > 0 ? (
        <ul className="mt-4 divide-y divide-rule border-t border-rule">
          {top.map((holding) => (
            <li key={holding.symbol} className="flex items-baseline justify-between gap-3 py-2">
              <span className="num text-xs font-semibold text-ink">{holding.symbol}</span>
              <span className="num text-xs text-ink-muted">{money(holding.current_value)}</span>
              <span className={cx('num w-16 text-right text-xs', toneFor(holding.pnl_percent))}>
                {percent(holding.pnl_percent, 1)}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 border-t border-rule pt-4 text-sm text-ink-muted">
          Nothing held yet. <Link to="/markets" className="text-accent underline underline-offset-2">Buy something</Link> and
          watch what it does.
        </p>
      )}
    </Panel>
  )
}

/** The course to open next: the one in progress, else the first unfinished. */
export function NextUp() {
  const { data, loading } = useQuery('courses', api.courses, { ttl: 120_000 })

  if (loading && !data) return <Skeleton className="h-40 rounded-lg" />

  const courses = data?.courses ?? []
  const unlocked = courses.filter((course) => course.completed_modules < course.module_count)
  const started = unlocked.find((course) => course.completed_modules > 0)
  const next = started ?? unlocked[0]

  if (!next) return null

  return (
    <Panel className="flex flex-col p-5">
      <div className="flex items-baseline justify-between gap-3">
        <p className="eyebrow">{started ? 'Pick up where you left off' : 'Start here'}</p>
        <Badge>{next.level}</Badge>
      </div>

      <h3 className="mt-3 flex items-start gap-2 font-display text-title text-ink">
        <BookOpen size={16} className="mt-1 shrink-0 text-accent" strokeWidth={1.75} />
        {next.title}
      </h3>
      <p className="measure mt-2 line-clamp-3 text-sm text-ink-muted">{next.summary}</p>

      <div className="mt-auto pt-4">
        <Meter value={next.completed_modules} max={next.module_count} />
        <div className="mt-2 flex items-baseline justify-between">
          <span className="num text-[11px] text-ink-faint">
            {next.completed_modules}/{next.module_count} modules · {next.estimated_minutes} min
          </span>
          <Link
            to={`/learn/${next.id}`}
            className="flex items-center gap-1 text-xs text-ink-muted transition-colors hover:text-accent"
          >
            {started ? 'Continue' : 'Open'}
            <ArrowRight size={12} />
          </Link>
        </div>
      </div>
    </Panel>
  )
}

/** Where the learner stands in the prediction game, and what it says about them. */
export function Standing() {
  const { data } = useQuery('challenge:calibration', api.calibration, { ttl: 120_000 })
  if (!data || !data.total_calls) return null

  return (
    <Panel className="p-5">
      <div className="flex items-baseline justify-between gap-3">
        <p className="eyebrow">Calibration</p>
        <Link
          to="/progress"
          className="flex items-center gap-1 text-xs text-ink-muted transition-colors hover:text-accent"
        >
          The detail
          <ArrowRight size={12} />
        </Link>
      </div>

      <p className="num mt-3 text-2xl font-semibold text-ink">
        {data.calibration_gap === null ? '—' : `${data.calibration_gap} pts`}
      </p>
      <p className="measure mt-2 text-sm text-ink-muted">{data.verdict}</p>
      <p className="num mt-3 border-t border-rule pt-3 text-[11px] text-ink-faint">
        <Wallet size={11} className="mr-1 inline" />
        {data.total_calls} calls scored on how sure you said you were
      </p>
    </Panel>
  )
}
