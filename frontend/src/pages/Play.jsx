/**
 * Games: scenarios, market calls, and the leaderboard.
 */
import { useState } from 'react'

import { api } from '../lib/api'
import { useQuery } from '../lib/query'
import { Badge, PageHeader, Panel, SectionHead, Skeleton, Stat, Tabs, cx } from '../ui'
import Leaderboard from './play/Leaderboard'
import Prediction from './play/Prediction'
import Scenarios from './play/Scenarios'

const TABS = [
  { value: 'prediction', label: 'Market Oracle' },
  { value: 'scenarios', label: 'Scenarios' },
  { value: 'board', label: 'Leaderboard' },
]

const PANELS = { prediction: Prediction, scenarios: Scenarios, board: Leaderboard }

export default function Play() {
  const [tab, setTab] = useState('prediction')
  const { data: stats } = useQuery('challenge:stats', api.challengeStats, { ttl: 30_000 })

  const Panel_ = PANELS[tab]

  return (
    <div className="mx-auto max-w-page px-4 py-8">
      <PageHeader
        eyebrow="Games"
        title="The arena"
        lede="Read a chart, work through a decision, climb the board. Scored on reasoning as much as outcome."
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
        <Panel_ />
      </div>
    </div>
  )
}
