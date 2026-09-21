/**
 * Leaderboards by score and by streak.
 *
 * The caller's own row is marked, which is the only thing most people are
 * looking for.
 */
import { useState } from 'react'

import { api } from '../../lib/api'
import { useQuery } from '../../lib/query'
import { EmptyState, Panel, Skeleton, Tabs, cx } from '../../ui'

const BOARDS = [
  { value: 'scores', label: 'By score' },
  { value: 'streaks', label: 'By streak' },
]

export default function Leaderboard() {
  const [board, setBoard] = useState('scores')
  const { data, loading } = useQuery(`leaderboard:${board}`, () => api.leaderboard(board), {
    ttl: 60_000,
  })

  return (
    <div className="space-y-4">
      <Tabs items={BOARDS} value={board} onChange={setBoard} />

      {loading && !data ? (
        <Skeleton className="h-64 rounded-lg" />
      ) : !data?.leaderboard.length ? (
        <Panel>
          <EmptyState title="Nobody on the board yet" body="Play a round and you are first." />
        </Panel>
      ) : (
        <Panel className="overflow-hidden">
          <table className="w-full text-sm">
            <caption className="sr-only">Leaderboard {board === 'scores' ? 'by score' : 'by streak'}</caption>
            <thead>
              <tr className="border-b border-rule text-left">
                {['#', 'Player', 'Score', 'Streak', 'Accuracy'].map((heading, index) => (
                  <th
                    key={heading}
                    scope="col"
                    className={cx(
                      'px-4 py-3 text-[10px] font-semibold uppercase tracking-wider text-ink-faint',
                      index > 1 && 'text-right',
                    )}
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.leaderboard.map((row) => (
                <tr
                  key={row.rank}
                  className={cx(
                    'border-b border-rule last:border-0',
                    row.is_you && 'bg-accent/5',
                  )}
                >
                  <td className="num px-4 py-3 text-ink-faint">{row.rank}</td>
                  <td className="px-4 py-3 text-ink">
                    {row.username}
                    {row.is_you && <span className="ml-2 text-xs text-accent">you</span>}
                  </td>
                  <td className="num px-4 py-3 text-right text-ink">{row.total_score}</td>
                  <td className="num px-4 py-3 text-right text-ink-muted">{row.current_streak}</td>
                  <td className="num px-4 py-3 text-right text-ink-muted">
                    {row.accuracy === null ? '—' : `${row.accuracy}%`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  )
}
