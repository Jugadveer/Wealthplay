/**
 * The terminal's opening screen.
 *
 * What a desk needs before it does anything: what the account is worth, what
 * moved today, what is already held, and what the wire is saying. Everything
 * here links somewhere — this is a place to decide from, not a place to read.
 *
 * Nothing is asserted about performance until something has actually been
 * bought. An uninvested account shows its cash and an empty state, not an
 * opening balance dressed up as a portfolio value.
 */
import { Link } from 'react-router-dom'
import { ArrowRight, LineChart as LineChartIcon } from 'lucide-react'

import MarketStrip from '../../components/MarketStrip'
import Wire from '../../components/Wire'
import { api } from '../../lib/api'
import { money, percent, toneFor } from '../../lib/format'
import { useQuery } from '../../lib/query'
import { Button, EmptyState, Panel, SectionHead, Skeleton, Stat, cx } from '../../ui'
import { LineChart } from '../../ui/charts'

export default function Overview() {
  const { data, loading } = useQuery('portfolio', api.portfolio, { ttl: 30_000 })
  // The series is one point per trade, not one per day: a practice account is
  // only worth re-marking when something changes in it.
  const { data: history } = useQuery('portfolio:history', () => api.portfolioHistory(90), {
    ttl: 60_000,
  })

  if (loading && !data) return <OverviewSkeleton />
  if (!data) return null

  const holdings = data.holdings ?? []
  const invested = holdings.length > 0
  const points = history?.history ?? []

  return (
    <div className="space-y-10">
      <section>
        <Panel className="p-6">
          {invested ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <Stat label="Account value" value={money(data.total_value)} size="lg" />
              <Stat
                label="Return"
                value={percent(data.total_pnl_percent)}
                sub={money(data.total_pnl, { signed: true })}
                tone={toneFor(data.total_pnl)}
                size="lg"
              />
              <Stat label="Invested" value={money(data.invested)} />
              <Stat label="Cash" value={money(data.balance)} sub="available to commit" />
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2">
              <Stat label="Cash" value={money(data.balance)} sub="available to commit" size="lg" />
              <Stat label="Invested" value="—" sub="nothing bought yet" size="lg" />
            </div>
          )}

          {points.length > 1 && (
            <div className="mt-8 border-t border-rule pt-6">
              <p className="eyebrow">Account value against what you put in</p>
              {/* Two lines, because one cannot tell you anything. Account value
                  alone is flat until prices move and reads as broken; plotted
                  against cost, the gap between them *is* the profit, and how
                  much of the account is still in cash is visible at a glance. */}
              <div className="mt-2">
                <LineChart
                  height={220}
                  series={[
                    {
                      label: 'Account value',
                      points: points.map((point) => ({
                        x: point.timestamp,
                        y: point.portfolio_value,
                      })),
                    },
                    {
                      label: 'Invested at cost',
                      points: points.map((point) => ({
                        x: point.timestamp,
                        y: point.invested_value,
                      })),
                    },
                  ]}
                />
              </div>
              <p className="mt-3 text-xs text-ink-faint">
                The gap between the lines is cash you have not committed. Once prices move, the
                account line separating from cost is your profit.
              </p>
            </div>
          )}
        </Panel>
      </section>

      <section>
        <SectionHead
          label="Live"
          title="The tape"
          action={
            <Link
              to="/markets/trade"
              className="flex items-center gap-1 text-xs text-ink-muted transition-colors hover:text-accent"
            >
              Find something to trade
              <ArrowRight size={12} />
            </Link>
          }
        />
        <MarketStrip className="mt-4 border-t-0" />
      </section>

      <section>
        <SectionHead
          label="Your book"
          title={invested ? `${holdings.length} open ${holdings.length === 1 ? 'position' : 'positions'}` : 'No open positions'}
          action={
            invested && (
              <Link
                to="/markets/positions"
                className="flex items-center gap-1 text-xs text-ink-muted transition-colors hover:text-accent"
              >
                All positions
                <ArrowRight size={12} />
              </Link>
            )
          }
        />

        {invested ? (
          <ul className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[...holdings]
              .sort((a, b) => b.current_value - a.current_value)
              .slice(0, 6)
              .map((holding) => (
                <li key={holding.symbol}>
                  <Link
                    to={`/markets/trade/${holding.symbol}`}
                    className="flex items-center justify-between gap-3 rounded-lg border border-rule bg-paper-raised p-4 transition-colors hover:border-accent/50"
                  >
                    <div className="min-w-0">
                      <p className="num text-sm font-semibold text-ink">{holding.symbol}</p>
                      <p className="num mt-0.5 text-xs text-ink-faint">
                        {holding.quantity}
                        {' × '}
                        {money(holding.current_price, { currency: holding.currency })}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="num text-sm text-ink">{money(holding.current_value)}</p>
                      <p className={cx('num mt-0.5 text-xs', toneFor(holding.pnl_percent))}>
                        {percent(holding.pnl_percent, 1)}
                      </p>
                    </div>
                  </Link>
                </li>
              ))}
          </ul>
        ) : (
          <Panel className="mt-4">
            <EmptyState
              icon={LineChartIcon}
              title="The book is empty"
              body="Nothing has been bought yet, so there is no performance to report. Pick a listing and put the practice money to work."
              action={<Button to="/markets/trade">Open the trade screen</Button>}
            />
          </Panel>
        )}
      </section>

      <Wire heading="Market wire" limit={5} />
    </div>
  )
}

function OverviewSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-52 rounded-lg" />
      <Skeleton className="h-14 rounded-lg" />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {[0, 1, 2].map((index) => (
          <Skeleton key={index} className="h-20 rounded-lg" />
        ))}
      </div>
    </div>
  )
}
