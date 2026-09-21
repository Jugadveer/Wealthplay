/**
 * Today — the home screen and the reason to come back.
 *
 * The daily set comes first: six short plays, all resolving in a few minutes,
 * every one generated per day and shared by every player, so a score is worth
 * comparing. Below it sits the rest of the account — the practice desk, the
 * course in progress, the calibration record and the wire — because a home
 * screen that only holds today's puzzles gives you no reason to stay.
 */
import { Link } from 'react-router-dom'
import { Flame, Snowflake } from 'lucide-react'

import MarketStrip from '../components/MarketStrip'
import Wire from '../components/Wire'
import { Skeleton } from '../ui'
import DailySet, { DailySetSkeleton, remainingMinutes, useDailySet } from './daily/DailySet'
import { Desk, NextUp, Standing } from './today/Dashboard'

// Formatted client-side: the browser knows the reader's locale, and the server
// would need platform-specific strftime directives to match.
const dateLabel = new Date().toLocaleDateString('en-GB', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
})

export default function Today() {
  const { data, loading } = useDailySet()

  if (loading && !data) return <TodaySkeleton />

  const plays = data?.plays ?? []
  const done = plays.filter((play) => play.done).length

  return (
    <div className="mx-auto max-w-page px-4 py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">{dateLabel}</p>
          <h1 className="mt-1 text-headline">Today</h1>
        </div>
        <StreakBadge streak={data?.streak} />
      </header>

      <p className="mt-4 text-sm text-ink-muted">
        {done === plays.length
          ? 'All done. Come back tomorrow for a new set.'
          : `${done} of ${plays.length} finished — roughly ${remainingMinutes(plays)} minutes left.`}
      </p>

      <div className="mt-6">
        <DailySet plays={plays} backLabel="Back to today" />
      </div>

      <MarketStrip className="mt-10" />

      <section className="mt-6 grid gap-4 lg:grid-cols-3">
        <Desk />
        <NextUp />
        <Standing />
      </section>

      <Wire className="mt-12" />
      <Shortcuts />
    </div>
  )
}

function StreakBadge({ streak }) {
  if (!streak) return null

  return (
    <div className="flex items-center gap-4">
      <div className="text-right">
        <p className="eyebrow">Streak</p>
        <p className="num mt-0.5 flex items-center justify-end gap-1.5 text-xl font-semibold text-ink">
          <Flame size={16} className={streak.current > 0 ? 'text-play' : 'text-ink-faint'} />
          {streak.current}
        </p>
      </div>

      {streak.freezes > 0 && (
        <div className="text-right">
          <p className="eyebrow">Freezes</p>
          <p className="num mt-0.5 flex items-center justify-end gap-1.5 text-xl font-semibold text-ink">
            <Snowflake size={15} className="text-accent" />
            {streak.freezes}
          </p>
        </div>
      )}
    </div>
  )
}

function Shortcuts() {
  return (
    <section className="mt-12 border-t border-rule pt-6">
      <p className="eyebrow">Elsewhere</p>
      <div className="mt-3 flex flex-wrap gap-3">
        {[
          ['/learn', 'Continue a course'],
          ['/markets', 'Check your portfolio'],
          ['/play', 'Scenarios and challenges'],
          ['/progress', 'Your week in numbers'],
        ].map(([to, label]) => (
          <Link
            key={to}
            to={to}
            className="rounded border border-rule px-3 py-1.5 text-sm text-ink-muted transition-colors hover:border-ink-faint hover:text-ink"
          >
            {label}
          </Link>
        ))}
      </div>
    </section>
  )
}

function TodaySkeleton() {
  return (
    <div className="mx-auto max-w-page px-4 py-8">
      <Skeleton className="h-4 w-40" />
      <Skeleton className="mt-3 h-10 w-52" />
      <div className="mt-6">
        <DailySetSkeleton />
      </div>
    </div>
  )
}
