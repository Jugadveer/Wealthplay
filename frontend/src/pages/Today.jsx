/**
 * Today — the home screen and the reason to come back.
 *
 * Four short plays, all resolving in a few minutes, plus the streak. Everything
 * on this page is generated per day and shared by every player, so a score is
 * worth comparing.
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, Flame, Snowflake } from 'lucide-react'

import { api } from '../lib/api'
import { invalidate, useQuery } from '../lib/query'
import { Badge, Button, Panel, Skeleton, cx } from '../ui'
import MarketCall from './daily/MarketCall'
import NumberSense from './daily/NumberSense'
import TickerTiles from './daily/TickerTiles'
import DailyDrill from './daily/DailyDrill'

const PLAYS = {
  ticker: { component: TickerTiles, blurb: 'Name the company in five guesses.' },
  call: { component: MarketCall, blurb: 'Higher or lower by tomorrow’s close.' },
  estimate: { component: NumberSense, blurb: 'Guess a real number. Close counts.' },
  drill: { component: DailyDrill, blurb: 'Five questions from what you have studied.' },
}

// Formatted client-side: the browser knows the reader's locale, and the server
// would need platform-specific strftime directives to match.
const dateLabel = new Date().toLocaleDateString('en-GB', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
})

export default function Today() {
  const { data, loading } = useQuery('daily:today', api.today, { ttl: 15_000 })
  const [active, setActive] = useState(null)

  const onFinish = () => {
    invalidate('daily:', 'profile')
    setActive(null)
  }

  if (loading && !data) return <TodaySkeleton />

  const plays = data?.plays ?? []
  const done = plays.filter((play) => play.done).length
  const Active = active ? PLAYS[active].component : null

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
          ? 'All four done. Come back tomorrow for a new set.'
          : `${done} of ${plays.length} finished — roughly ${Math.max(1, Math.round(((plays.length - done) * 90) / 60))} minutes left.`}
      </p>

      {Active ? (
        <div className="mt-8">
          <button
            type="button"
            onClick={() => setActive(null)}
            className="mb-4 text-sm text-ink-muted underline decoration-rule-strong underline-offset-4 hover:text-ink"
          >
            Back to today
          </button>
          <Active onFinish={onFinish} />
        </div>
      ) : (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {plays.map((play) => (
              <PlayCard key={play.kind} play={play} onOpen={() => setActive(play.kind)} />
            ))}
          </div>
          <Shortcuts />
        </>
      )}
    </div>
  )
}

function PlayCard({ play, onOpen }) {
  const blurb = PLAYS[play.kind]?.blurb ?? ''

  return (
    <Panel
      as="button"
      onClick={onOpen}
      className={cx(
        'group flex w-full flex-col items-start gap-2 p-5 text-left transition-colors',
        play.done ? 'opacity-70' : 'hover:border-ink-faint',
      )}
    >
      <div className="flex w-full items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-title">{play.label}</h2>
          <p className="mt-1 text-sm text-ink-muted">{blurb}</p>
        </div>
        {play.done ? (
          <Badge tone={play.solved ? 'up' : 'neutral'}>
            <Check size={10} />
            {play.score ? `+${play.score}` : 'done'}
          </Badge>
        ) : play.pending ? (
          <Badge tone="play">Settles tomorrow</Badge>
        ) : play.due_count ? (
          <Badge tone="play">{play.due_count} due</Badge>
        ) : (
          <Badge tone="accent">New</Badge>
        )}
      </div>

      <span className="mt-2 text-xs text-ink-faint transition-colors group-hover:text-accent">
        {play.done || play.pending ? 'Review →' : 'Play →'}
      </span>
    </Panel>
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
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {[0, 1, 2, 3].map((index) => (
          <Skeleton key={index} className="h-32 rounded-lg" />
        ))}
      </div>
    </div>
  )
}
