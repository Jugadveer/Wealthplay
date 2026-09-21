/**
 * Market Call — one binary call, settled by tomorrow's close.
 *
 * The delay is the point: a call you cannot immediately check forces a real
 * opinion rather than pattern-matching against a result you already saw. The
 * previous day's call is settled and scored here.
 */
import { useEffect, useState } from 'react'
import { TrendingDown, TrendingUp } from 'lucide-react'

import { api } from '../../lib/api'
import { money, percent } from '../../lib/format'
import { LineChart } from '../../ui/charts'
import { Badge, Button, Panel, cx } from '../../ui'

export default function MarketCall() {
  const [round, setRound] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api.marketCall().then(setRound).catch(() => setRound(null))
  }, [])

  async function call(direction) {
    setBusy(true)
    try {
      setRound(await api.submitCall({ call: direction }))
    } finally {
      setBusy(false)
    }
  }

  if (!round) return <Panel className="h-64 animate-pulse" />

  const currency = round.currency
  const format = (value) => money(value, { currency })

  return (
    <div className="space-y-4">
      {round.yesterday && <Settlement result={round.yesterday} />}

      <Panel className="p-6">
        <header className="flex items-start justify-between gap-4">
          <div>
            <p className="eyebrow">Puzzle two</p>
            <h2 className="mt-1 text-headline">Market Call</h2>
          </div>
          {round.your_call && (
            <Badge tone="accent">
              You said {round.your_call} · settles {new Date(round.settles).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
            </Badge>
          )}
        </header>

        <p className="mt-4 text-sm text-ink-muted">{round.question}</p>

        <div className="mt-5">
          <LineChart
            series={[
              {
                label: round.name,
                points: round.series.map((point) => ({ x: point.date, y: point.close })),
              },
            ]}
            formatY={format}
            height={200}
          />
        </div>

        {round.your_call ? (
          <p className="mt-5 border-t border-rule pt-4 text-sm text-ink-muted">
            Your call is locked in. Come back tomorrow to see how it settled — that wait is
            deliberate.
          </p>
        ) : (
          <div className="mt-5 grid grid-cols-2 gap-3">
            <Button variant="secondary" size="lg" disabled={busy} onClick={() => call('higher')}>
              <TrendingUp size={16} className="text-up" />
              Higher
            </Button>
            <Button variant="secondary" size="lg" disabled={busy} onClick={() => call('lower')}>
              <TrendingDown size={16} className="text-down" />
              Lower
            </Button>
          </div>
        )}
      </Panel>
    </div>
  )
}

function Settlement({ result }) {
  return (
    <Panel
      className={cx('border-l-2 p-5', result.correct ? 'border-l-up' : 'border-l-down')}
    >
      <p className="eyebrow">Yesterday&rsquo;s call, settled</p>
      <p className="mt-2 text-sm text-ink">
        You said <strong className="font-semibold">{result.your_call}</strong> on {result.name}. It
        closed <strong className="font-semibold">{result.outcome}</strong>, moving{' '}
        <span className={result.move_percent >= 0 ? 'num text-up' : 'num text-down'}>
          {percent(result.move_percent)}
        </span>
        .
      </p>
      <Badge tone={result.correct ? 'up' : 'down'} className="mt-3">
        {result.correct ? 'Called it · +25 XP' : 'Missed'}
      </Badge>
    </Panel>
  )
}
