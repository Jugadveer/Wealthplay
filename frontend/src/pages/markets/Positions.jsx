/**
 * The practice portfolio: value over time, and what is held.
 */
import { Link } from 'react-router-dom'
import { Briefcase } from 'lucide-react'

import { api } from '../../lib/api'
import { money, percent, toneFor } from '../../lib/format'
import { useQuery } from '../../lib/query'
import { Button, EmptyState, Panel, Skeleton, cx } from '../../ui'
import { LineChart } from '../../ui/charts'

export default function Holdings() {
  const { data, loading } = useQuery('portfolio', api.portfolio, { ttl: 20_000 })
  const { data: history } = useQuery('portfolio:history', () => api.portfolioHistory(90), {
    ttl: 60_000,
  })

  if (loading && !data) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-28 rounded-lg" />
        <Skeleton className="h-64 rounded-lg" />
      </div>
    )
  }

  if (!data) return null

  const points = history?.history ?? []
  const hasCurve = points.length > 1

  return (
    <div className="space-y-6">
      {/* The account figures live in the terminal bar, which is on screen the
          whole time. Repeating them here would be the third copy on one screen. */}
      <Panel className="p-6">
        {hasCurve ? (
          <div className="mt-8 border-t border-rule pt-6">
            <p className="eyebrow">Account value, every trade so far</p>
            <div className="mt-2">
              <LineChart
                height={240}
                series={[
                  {
                    label: 'Account value',
                    points: points.map((p) => ({ x: p.timestamp, y: p.portfolio_value })),
                  },
                  {
                    label: 'Invested at cost',
                    points: points.map((p) => ({ x: p.timestamp, y: p.invested_value })),
                  },
                ]}
              />
            </div>
          </div>
        ) : (
          <p className="text-xs text-ink-faint">
            The value chart starts once you have made a trade.
          </p>
        )}
      </Panel>

      {data.holdings.length === 0 ? (
        <Panel>
          <EmptyState
            icon={Briefcase}
            title="Nothing held yet"
            body="Buy something and it appears here with live valuation. There is no real money involved, so a bad first trade costs nothing but a lesson."
            action={<Button to="/markets/trade">Browse stocks</Button>}
          />
        </Panel>
      ) : (
        <Panel className="overflow-hidden">
          <table className="w-full text-sm">
            <caption className="sr-only">Your holdings</caption>
            <thead>
              <tr className="border-b border-rule text-left">
                {['Stock', 'Qty', 'Avg cost', 'Price', 'Value', 'P&L'].map((heading, index) => (
                  <th
                    key={heading}
                    scope="col"
                    className={cx(
                      'px-4 py-3 text-[10px] font-semibold uppercase tracking-wider text-ink-faint',
                      index > 0 && 'text-right',
                    )}
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.holdings.map((holding) => (
                <tr key={holding.symbol} className="border-b border-rule last:border-0">
                  <td className="px-4 py-3">
                    <Link
                      to={`/markets/trade/${holding.symbol}`}
                      className="block hover:text-accent"
                    >
                      <span className="num font-semibold text-ink">{holding.symbol}</span>
                      <span className="block text-xs text-ink-faint">{holding.sector}</span>
                    </Link>
                  </td>
                  <td className="num px-4 py-3 text-right text-ink-muted">{holding.quantity}</td>
                  <td className="num px-4 py-3 text-right text-ink-muted">
                    {money(holding.avg_price)}
                  </td>
                  <td className="num px-4 py-3 text-right text-ink">
                    {money(holding.current_price)}
                  </td>
                  <td className="num px-4 py-3 text-right text-ink">
                    {money(holding.current_value)}
                  </td>
                  <td className={cx('num px-4 py-3 text-right', toneFor(holding.pnl))}>
                    {percent(holding.pnl_percent)}
                    <span className="block text-xs opacity-80">
                      {money(holding.pnl, { signed: true })}
                    </span>
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
