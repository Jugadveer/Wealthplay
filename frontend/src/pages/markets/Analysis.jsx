/**
 * Portfolio analysis.
 *
 * Computed findings and model-written ones are visually distinct and labelled
 * as such. The old page blended both under one "AI Recommendations" heading,
 * so a hardcoded sentence was indistinguishable from a generated one — and it
 * fetched ESG, copy-trading and hindsight data that it then never rendered.
 */
import { useState } from 'react'
import { Leaf, PieChart, Users } from 'lucide-react'

import { api } from '../../lib/api'
import { money, percent, toneFor } from '../../lib/format'
import { useQuery } from '../../lib/query'
import { Badge, Button, EmptyState, Panel, SectionHead, Skeleton, Stat, cx } from '../../ui'
import { Breakdown, LineChart } from '../../ui/charts'

const PERIODS = [
  { value: '2020-pandemic', label: 'Pandemic 2020' },
  { value: '2008-crash', label: 'Credit crisis 2008' },
  { value: '2022-ratehike', label: 'Rate hikes 2022' },
]

export default function Analysis() {
  const { data, loading } = useQuery('portfolio:analysis', api.portfolioAnalysis, { ttl: 60_000 })

  if (loading && !data) return <Skeleton className="h-96 rounded-lg" />
  if (!data) return null

  if (!data.holdings.length) {
    return (
      <Panel>
        <EmptyState
          icon={PieChart}
          title="Nothing to analyse yet"
          body="Concentration, sector exposure and risk review all need positions to work from."
          action={<Button to="/markets/trade">Browse stocks</Button>}
        />
      </Panel>
    )
  }

  return (
    <div className="space-y-10">
      <Performance totals={data.totals} />
      <Concentration concentration={data.concentration} nudge={data.nudge} holdings={data.holdings} />
      <Review review={data.review} />
      <Esg esg={data.esg} />
      <Hindsight />
      <CopyTrading />
    </div>
  )
}

function Performance({ totals }) {
  return (
    <section>
      <SectionHead label="Position" title="Performance" />
      <Panel className="mt-4 grid gap-6 p-6 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Invested" value={money(totals.invested)} />
        <Stat label="Current value" value={money(totals.current_value)} />
        <Stat
          label="Profit and loss"
          value={money(totals.total_pnl, { signed: true })}
          tone={toneFor(totals.total_pnl)}
        />
        <Stat
          label="Return"
          value={percent(totals.total_pnl_percent)}
          tone={toneFor(totals.total_pnl_percent)}
        />
      </Panel>
    </section>
  )
}

function Concentration({ concentration, nudge, holdings }) {
  const sectors = Object.entries(concentration.sectors).map(([label, share]) => ({
    label,
    value: holdings
      .filter((holding) => (holding.sector || 'Unknown') === label)
      .reduce((sum, holding) => sum + holding.current_value, 0),
    share,
  }))

  return (
    <section>
      <SectionHead label="Risk" title="Concentration" />

      <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_300px]">
        <Panel className="p-6">
          <Breakdown items={sectors} />
        </Panel>

        <Panel
          className={cx(
            'border-l-2 p-5',
            nudge.severity === 'high'
              ? 'border-l-down'
              : nudge.severity === 'moderate'
                ? 'border-l-play'
                : 'border-l-up',
          )}
        >
          <p className="eyebrow">Diversification</p>
          <p className="num mt-1 text-3xl font-semibold text-ink">
            {concentration.score}
            <span className="text-base text-ink-faint">/100</span>
          </p>
          <p className="mt-3 text-sm leading-relaxed text-ink-muted">{nudge.message}</p>
          <p className="mt-3 text-[11px] text-ink-faint">
            Herfindahl index across sectors. Higher is more spread out.
          </p>
        </Panel>
      </div>
    </section>
  )
}

function Review({ review }) {
  if (!review.available) {
    return (
      <section>
        <SectionHead label="Coaching" title="Risk review" />
        <Panel className="mt-4 p-5">
          <p className="text-sm text-ink-muted">
            The review needs at least one open position to have something to read.
          </p>
        </Panel>
      </section>
    )
  }

  return (
    <section>
      {/* Not badged as written by Nex any more, because it is not. The review
          is worked out from the holdings themselves — the model, handed this
          exact portfolio at 92% in one sector, called it well diversified and
          advised buying more of that sector. */}
      <SectionHead
        label="Coaching"
        title="Risk review"
        action={<Badge>Calculated from your holdings</Badge>}
      />

      <Panel className="mt-4 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <p className="measure font-display text-title text-ink">{review.headline}</p>
          {review.concentration_grade && (
            <div className="text-right">
              <p className="eyebrow">Grade</p>
              <p className="num text-2xl font-semibold text-ink">{review.concentration_grade}</p>
            </div>
          )}
        </div>

        <ul className="mt-5 space-y-2.5 border-t border-rule pt-5">
          {review.risks.map((risk) => (
            <li key={risk} className="measure flex gap-2.5 text-sm leading-relaxed text-ink-muted">
              <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-ink-faint" aria-hidden="true" />
              {risk}
            </li>
          ))}
        </ul>

        {review.next_step && (
          <p className="measure mt-5 border-t border-rule pt-4 text-sm text-ink">
            <span className="eyebrow mr-2">Next</span>
            {review.next_step}
          </p>
        )}
      </Panel>
    </section>
  )
}

function Esg({ esg }) {
  if (!esg.available) return null

  return (
    <section>
      <SectionHead label="Exposure" title="Carbon and governance" />
      <Panel className="mt-4 p-6">
        <div className="grid gap-6 sm:grid-cols-3">
          <Stat label="ESG score" value={esg.esg_score} sub="value-weighted" />
          <Stat label="Carbon intensity" value={esg.carbon_intensity} sub="lower is better" />
          <Stat label="Highest carbon" value={esg.highest_carbon_sector} />
        </div>
        <p className="measure mt-5 border-t border-rule pt-4 text-sm text-ink-muted">
          <Leaf size={13} className="mr-1.5 inline text-up" />
          {esg.note}
        </p>
      </Panel>
    </section>
  )
}

/**
 * Replays the current holdings through a past crash.
 *
 * "What would this have done in 2008?" teaches drawdown far better than a
 * volatility number does.
 */
function Hindsight() {
  const [period, setPeriod] = useState(PERIODS[0].value)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)

  async function run() {
    setBusy(true)
    try {
      setResult(await api.hindsight(period))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section>
      <SectionHead label="Stress test" title="Hindsight replay" />

      <Panel className="mt-4 p-6">
        <p className="measure text-sm text-ink-muted">
          Hold your current positions through a past market period and see what would have
          happened, using real closing prices.
        </p>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          {PERIODS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setPeriod(option.value)}
              className={cx(
                'rounded border px-3 py-1.5 text-sm transition-colors',
                period === option.value
                  ? 'border-accent bg-accent/5 text-ink'
                  : 'border-rule text-ink-muted hover:text-ink',
              )}
            >
              {option.label}
            </button>
          ))}
          <Button size="sm" onClick={run} disabled={busy}>
            {busy ? 'Replaying…' : 'Run'}
          </Button>
        </div>

        {result && !result.available && (
          <p className="mt-5 border-t border-rule pt-4 text-sm text-ink-muted">{result.reason}</p>
        )}

        {result?.available && (
          <div className="mt-6 border-t border-rule pt-5">
            <div className="grid gap-5 sm:grid-cols-3">
              <Stat
                label="Return"
                value={percent(result.summary.return_percent)}
                tone={toneFor(result.summary.return_percent)}
              />
              <Stat
                label="Worst drawdown"
                value={percent(result.summary.max_drawdown_percent)}
                tone="text-down"
                sub="peak to trough"
              />
              <Stat label="End value" value={money(result.summary.end_value)} />
            </div>

            <div className="mt-6">
              <LineChart
                height={220}
                series={[
                  {
                    label: result.period.label,
                    points: result.series.map((point) => ({ x: point.date, y: point.value })),
                  },
                ]}
              />
            </div>
          </div>
        )}
      </Panel>
    </section>
  )
}

function CopyTrading() {
  const { data } = useQuery('copy-trading', api.copyTrading, { ttl: 120_000 })
  if (!data) return null

  const hasContent = data.top_traders.length > 0 || data.feed.length > 0
  if (!hasContent) return null

  return (
    <section>
      <SectionHead label="Community" title="What others are doing" />

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {data.top_traders.length > 0 && (
          <Panel className="p-5">
            <p className="eyebrow">
              <Users size={11} className="mr-1 inline" />
              Top of the board
            </p>
            <ul className="mt-3 divide-y divide-rule">
              {data.top_traders.slice(0, 6).map((trader) => (
                <li key={trader.user_id} className="flex items-baseline justify-between gap-3 py-2.5">
                  <span className="text-sm text-ink">{trader.username}</span>
                  <span className="flex items-baseline gap-4">
                    <span className={cx('num text-sm', toneFor(trader.portfolio_return_percent))}>
                      {percent(trader.portfolio_return_percent)}
                    </span>
                    <span className="num text-xs text-ink-faint">{trader.score} pts</span>
                  </span>
                </li>
              ))}
            </ul>
          </Panel>
        )}

        {data.feed.length > 0 && (
          <Panel className="p-5">
            <p className="eyebrow">Recent rationales</p>
            <ul className="mt-3 space-y-3">
              {data.feed.slice(0, 6).map((post) => (
                <li key={post.id} className="border-b border-rule pb-3 last:border-0 last:pb-0">
                  <div className="flex items-baseline gap-2">
                    <Badge tone={post.action === 'BUY' ? 'up' : post.action === 'SELL' ? 'down' : 'neutral'}>
                      {post.action}
                    </Badge>
                    <span className="num text-xs font-semibold text-ink">{post.symbol}</span>
                    <span className="text-xs text-ink-faint">{post.username}</span>
                  </div>
                  <p className="mt-1.5 text-sm text-ink-muted">{post.rationale}</p>
                </li>
              ))}
            </ul>
          </Panel>
        )}
      </div>
    </section>
  )
}
