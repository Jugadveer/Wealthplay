/**
 * Play — everything playable, in one place.
 *
 * The daily set leads, because someone who opens "Play" looking for the games
 * should find them rather than only the two long-form modes. The set itself is
 * the same component Today mounts, so the card states and scoring cannot drift
 * between the two pages.
 */
import { useState } from 'react'

import { api } from '../lib/api'
import { useQuery } from '../lib/query'
import { PageHeader, Panel, Stat, Tabs } from '../ui'
import DailySet, { DailySetSkeleton, remainingMinutes, useDailySet } from './daily/DailySet'
import Leaderboard from './play/Leaderboard'
import Prediction from './play/Prediction'
import Scenarios from './play/Scenarios'

const TABS = [
  { value: 'daily', label: 'Daily set' },
  { value: 'prediction', label: 'Market Oracle' },
  { value: 'scenarios', label: 'Scenarios' },
  { value: 'board', label: 'Leaderboard' },
]

export default function Play() {
  const [tab, setTab] = useState('daily')
  const { data: stats } = useQuery('challenge:stats', api.challengeStats, { ttl: 30_000 })

  return (
    <div className="mx-auto max-w-page px-4 py-8">
      <PageHeader
        eyebrow="Games"
        title="Play"
        lede="Six short plays that reset every morning, plus two that never run out. Scored on reasoning as much as outcome."
      />

      {stats && (
        <Panel className="mt-6 grid gap-6 p-5 sm:grid-cols-4">
          <Stat label="Total score" value={stats.total_score} />
          <Stat label="Current streak" value={stats.current_streak} />
          <Stat label="Best streak" value={stats.best_streak} />
          <Stat label="Accuracy" value={`${stats.win_rate}%`} />
        </Panel>
      )}

      <div className="mt-6">
        <Tabs items={TABS} value={tab} onChange={setTab} />
      </div>

      <div className="mt-6">
        {tab === 'daily' && <TodaysGames />}
        {tab === 'prediction' && <Prediction />}
        {tab === 'scenarios' && <Scenarios />}
        {tab === 'board' && <Leaderboard />}
      </div>
    </div>
  )
}

/** The same set Today shows, with a line saying how much of it is left. */
function TodaysGames() {
  const { data, loading } = useDailySet()

  if (loading && !data) return <DailySetSkeleton />

  const plays = data?.plays ?? []
  const done = plays.filter((play) => play.done).length

  return (
    <div>
      <p className="mb-4 text-sm text-ink-muted">
        {done === plays.length
          ? 'All done for today. A new set lands tomorrow morning.'
          : `${done} of ${plays.length} finished — roughly ${remainingMinutes(plays)} minutes left. Everyone gets the same set, so a score is worth comparing.`}
      </p>
      <DailySet plays={plays} backLabel="Back to the set" />
    </div>
  )
}
