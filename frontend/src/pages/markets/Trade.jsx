/**
 * The trade ticket.
 *
 * The rationale box is the teaching mechanism: writing down why, before
 * committing, is the habit the whole simulator exists to build. Nex reacts to
 * the reasoning rather than approving or rejecting the trade.
 *
 * A sell returns a discipline score — computed from the actual price action,
 * not generated — because beginners sell winners early and losers late.
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Sparkles } from 'lucide-react'

import { api } from '../../lib/api'
import { money, percent, toneFor } from '../../lib/format'
import { announceUnlocks, notifySuccess } from '../../lib/notify'
import { invalidate, useQuery } from '../../lib/query'
import { Badge, Button, Panel, Skeleton, Stat, cx } from '../../ui'
import { LineChart } from '../../ui/charts'

export default function Trade({ symbol, onDone }) {
  const { data: stock, loading } = useQuery(`stock:${symbol}`, () => api.stock(symbol), {
    ttl: 30_000,
  })
  const { data: portfolio } = useQuery('portfolio', api.portfolio, { ttl: 20_000 })

  const [side, setSide] = useState('buy')
  const [quantity, setQuantity] = useState('')
  const [rationale, setRationale] = useState('')
  const [critique, setCritique] = useState(null)
  const [outcome, setOutcome] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (loading && !stock) return <Skeleton className="h-96 rounded-lg" />
  if (!stock) return null

  const qty = Number(quantity) || 0
  const held = stock.holding?.quantity ?? 0
  const cash = portfolio?.balance ?? 0

  // Prices display in the stock's own currency; the order settles in INR, which
  // is what the cash balance is held in.
  const format = (value) => money(value, { currency: stock.currency })
  const cost = qty * stock.price_inr
  const foreign = stock.currency !== 'INR'

  const tooExpensive = side === 'buy' && cost > cash
  const tooMany = side === 'sell' && qty > held
  const canSubmit = qty > 0 && !tooExpensive && !tooMany && !busy

  async function askNex() {
    if (!rationale.trim()) return
    setBusy(true)
    try {
      const result = await api.critiqueTrade({
        symbol,
        action: side,
        quantity: qty || 1,
        rationale,
      })
      setCritique(result)
    } finally {
      setBusy(false)
    }
  }

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')

    try {
      const payload = { symbol, quantity: qty }
      const result = side === 'buy' ? await api.buy(payload) : await api.sell(payload)

      if (rationale.trim()) {
        await api.shareRationale({ symbol, action: side.toUpperCase(), rationale }).catch(() => {})
      }

      setOutcome(result)
      notifySuccess(result.message)
      announceUnlocks(result)
      setQuantity('')
      invalidate('portfolio', 'stocks', `stock:${symbol}`, 'profile')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-5">
      <Link
        to="/markets/trade"
        className="inline-flex items-center gap-1.5 text-sm text-ink-muted hover:text-ink"
      >
        <ArrowLeft size={14} />
        All stocks
      </Link>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
        <Panel className="p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="num text-2xl font-semibold text-ink">{stock.symbol}</h2>
                {stock.is_custom && <Badge>simulated</Badge>}
              </div>
              <p className="mt-0.5 text-sm text-ink-muted">{stock.name}</p>
            </div>
            <div className="text-right">
              <p className="num text-2xl font-semibold text-ink">{format(stock.current_price)}</p>
              <p className={cx('num text-sm', toneFor(stock.change_percent))}>
                {percent(stock.change_percent)}
              </p>
            </div>
          </div>

          <div className="mt-6">
            <LineChart
              height={240}
              formatY={format}
              series={[
                {
                  label: stock.symbol,
                  points: (stock.price_history || []).map((point) => ({
                    x: point.date,
                    y: point.close ?? point.price,
                  })),
                },
              ]}
            />
          </div>

          <dl className="mt-6 grid grid-cols-2 gap-5 border-t border-rule pt-5 sm:grid-cols-4">
            <Stat label="90-day high" value={format(stock.summary.high)} />
            <Stat label="90-day low" value={format(stock.summary.low)} />
            <Stat label="Average" value={format(stock.summary.average)} />
            <Stat label="Sector" value={stock.sector} />
          </dl>
        </Panel>

        <div className="space-y-4">
          <Panel className="p-5">
            <div className="grid grid-cols-2 gap-1 rounded bg-paper-sunken p-1">
              {['buy', 'sell'].map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setSide(value)}
                  className={cx(
                    'rounded py-1.5 text-sm font-medium capitalize transition-colors',
                    side === value ? 'bg-paper-raised text-ink shadow-raise' : 'text-ink-muted',
                  )}
                >
                  {value}
                </button>
              ))}
            </div>

            <form onSubmit={submit} className="mt-4 space-y-4">
              <label className="block">
                <span className="eyebrow">Quantity</span>
                <input
                  type="number"
                  inputMode="numeric"
                  min="1"
                  step="1"
                  value={quantity}
                  onChange={(event) => setQuantity(event.target.value)}
                  placeholder="0"
                  className="num mt-1 h-11 w-full rounded border border-rule-strong bg-paper px-3 text-lg text-ink outline-none transition-colors focus:border-accent"
                />
              </label>

              <dl className="space-y-1.5 text-sm">
                <Row
                  label="Order value"
                  value={money(cost)}
                  hint={foreign ? `${format(qty * stock.current_price)} at ₹${(stock.price_inr / stock.current_price).toFixed(2)}/$` : null}
                  emphasis
                />
                <Row
                  label={side === 'buy' ? 'Cash available' : 'Shares held'}
                  value={side === 'buy' ? money(cash) : `${held}`}
                />
              </dl>

              <label className="block">
                <span className="eyebrow">Why this trade?</span>
                <textarea
                  value={rationale}
                  onChange={(event) => setRationale(event.target.value)}
                  rows={3}
                  maxLength={140}
                  placeholder="One sentence — writing it down is the point…"
                  className="mt-1 w-full resize-none rounded border border-rule-strong bg-paper px-3 py-2 text-sm text-ink outline-none transition-colors focus:border-accent"
                />
                <span className="mt-1 block text-right text-[11px] text-ink-faint">
                  {rationale.length}/140
                </span>
              </label>

              {rationale.trim() && !critique && (
                <Button type="button" size="sm" variant="ghost" onClick={askNex} disabled={busy}>
                  <Sparkles size={13} />
                  Ask Nex about this reasoning
                </Button>
              )}

              {critique?.available && (
                <p className="rounded border border-rule bg-paper-sunken p-3 text-sm leading-relaxed text-ink-muted">
                  {critique.critique}
                </p>
              )}

              {(tooExpensive || tooMany || error) && (
                <p role="alert" aria-live="polite" className="text-xs text-down">
                  {error ||
                    (tooExpensive
                      ? `That costs ${money(cost)} but you have ${money(cash)}.`
                      : `You hold ${held} ${stock.symbol}.`)}
                </p>
              )}

              <Button type="submit" className="w-full" size="lg" disabled={!canSubmit}>
                {busy ? 'Placing…' : `${side === 'buy' ? 'Buy' : 'Sell'} ${qty || ''} ${stock.symbol}`.trim()}
              </Button>
            </form>
          </Panel>

          {outcome && <Outcome outcome={outcome} onDone={onDone} />}
        </div>
      </div>
    </div>
  )
}

function Row({ label, value, hint, emphasis }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <dt className="text-ink-muted">{label}</dt>
      <dd className="text-right">
        <span className={cx('num', emphasis ? 'font-semibold text-ink' : 'text-ink-muted')}>
          {value}
        </span>
        {hint && <span className="num block text-[11px] text-ink-faint">{hint}</span>}
      </dd>
    </div>
  )
}

function Outcome({ outcome, onDone }) {
  const discipline = outcome.sell_discipline

  return (
    <Panel className="border-l-2 border-l-up p-5">
      <p className="text-sm text-ink">{outcome.message}</p>

      {outcome.newly_unlocked_achievements?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {outcome.newly_unlocked_achievements.map((achievement) => (
            <Badge key={achievement.id} tone="play">
              {achievement.name} · +{achievement.xp_reward} XP
            </Badge>
          ))}
        </div>
      )}

      {discipline && (
        <div className="mt-4 border-t border-rule pt-4">
          <div className="flex items-baseline justify-between">
            <p className="eyebrow">Exit discipline</p>
            <span className="num text-lg font-semibold text-ink">{discipline.score}/100</span>
          </div>
          <p className="mt-2 text-sm text-ink-muted">{discipline.verdict}</p>
          <ul className="mt-3 space-y-1.5 text-xs text-ink-faint">
            {discipline.reasons.map((reason) => (
              <li key={reason} className="flex gap-2">
                <span aria-hidden="true">·</span>
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      <Button size="sm" variant="secondary" className="mt-4" onClick={onDone}>
        View portfolio
      </Button>
    </Panel>
  )
}
