/**
 * Deposits and SIPs — the instruments goal mode adds.
 *
 * Only rendered when a goal is linked. Trading a goal with stocks alone teaches
 * the wrong lesson about how goals actually get met: the deposit is the part
 * that cannot fall, and the SIP is the part that keeps buying whatever the
 * market did that month.
 */
import { useState } from 'react'
import { Landmark, Repeat } from 'lucide-react'

import { api } from '../../lib/api'
import { money, percent, toneFor } from '../../lib/format'
import { notifyError, notifySuccess } from '../../lib/notify'
import { invalidate, useQuery } from '../../lib/query'
import { Badge, Button, Panel, SectionHead, cx } from '../../ui'

export default function GoalInstruments() {
  const { data } = useQuery('instruments', api.instruments, { ttl: 30_000 })
  if (!data?.goal_mode) return null

  const refresh = () => invalidate('instruments', 'portfolio', 'goals')

  return (
    <div className="space-y-8">
      <SectionHead
        label="Goal mode"
        title={`Funding ${data.goal.title}`}
        action={<Badge tone="accent">Beyond stocks</Badge>}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Deposits data={data} onChange={refresh} />
        <Sips data={data} onChange={refresh} />
      </div>
    </div>
  )
}

function Deposits({ data, onChange }) {
  const [principal, setPrincipal] = useState('')
  const [tenure, setTenure] = useState(12)
  const [busy, setBusy] = useState(false)

  async function open(event) {
    event.preventDefault()
    setBusy(true)
    try {
      const result = await api.openDeposit(Number(principal), Number(tenure))
      notifySuccess('Deposit opened', `${money(result.deposit.principal)} at ${result.deposit.rate_percent}%`)
      setPrincipal('')
      onChange()
    } catch (error) {
      notifyError(error.message)
    } finally {
      setBusy(false)
    }
  }

  async function close(deposit) {
    setBusy(true)
    try {
      const result = await api.closeDeposit(deposit.id)
      if (result.broken_early) {
        notifyError('Broken early', `${money(result.lost_to_penalty)} lost to the penalty`)
      } else {
        notifySuccess('Matured', money(result.proceeds))
      }
      onChange()
    } catch (error) {
      notifyError(error.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Panel className="p-5">
      <div className="flex items-center gap-2">
        <Landmark size={15} className="text-accent" />
        <h3 className="font-display text-title">Fixed deposits</h3>
      </div>
      <p className="measure mt-2 text-xs text-ink-muted">
        Cannot fall. Breaking one early costs a percentage point off the rate, exactly as a bank
        would charge.
      </p>

      <form onSubmit={open} className="mt-4 flex flex-wrap items-end gap-2">
        <label className="block">
          <span className="eyebrow">Amount</span>
          <input
            type="number"
            min={data.available.min_deposit}
            value={principal}
            onChange={(event) => setPrincipal(event.target.value)}
            placeholder={String(data.available.min_deposit)}
            className="mt-1.5 h-9 w-32 rounded border border-rule-strong bg-paper px-3 text-sm text-ink outline-none focus:border-accent"
          />
        </label>
        <label className="block">
          <span className="eyebrow">Tenure</span>
          <select
            value={tenure}
            onChange={(event) => setTenure(event.target.value)}
            className="mt-1.5 h-9 rounded border border-rule-strong bg-paper px-2 text-sm text-ink outline-none focus:border-accent"
          >
            {data.available.deposit_rates.map((band) => (
              <option key={band.tenure_months} value={band.tenure_months}>
                {band.tenure_months} months · {band.rate_percent}%
              </option>
            ))}
          </select>
        </label>
        <Button size="sm" type="submit" disabled={busy || !principal}>
          Open
        </Button>
      </form>

      {data.deposits.length > 0 && (
        <ul className="mt-5 divide-y divide-rule border-t border-rule">
          {data.deposits.map((deposit) => (
            <li key={deposit.id} className="flex flex-wrap items-center gap-3 py-3">
              <div className="min-w-0 flex-1">
                <p className="num text-sm text-ink">{money(deposit.current_value)}</p>
                <p className="num mt-0.5 text-[11px] text-ink-faint">
                  {money(deposit.principal)} at {deposit.rate_percent}% ·{' '}
                  {deposit.matured
                    ? 'matured'
                    : `${deposit.matures_in_days} days to maturity`}
                </p>
              </div>
              <span className="num text-xs text-up">+{money(deposit.interest_so_far)}</span>
              <Button size="sm" variant="secondary" onClick={() => close(deposit)} disabled={busy}>
                {deposit.matured ? 'Withdraw' : 'Break'}
              </Button>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  )
}

function Sips({ data, onChange }) {
  const [instrument, setInstrument] = useState('index')
  const [amount, setAmount] = useState('')
  const [busy, setBusy] = useState(false)

  async function start(event) {
    event.preventDefault()
    setBusy(true)
    try {
      const result = await api.startSip(instrument, Number(amount))
      notifySuccess('SIP set up', `${money(result.sip.monthly_amount)} into ${result.sip.label}`)
      setAmount('')
      onChange()
    } catch (error) {
      notifyError(error.message)
    } finally {
      setBusy(false)
    }
  }

  async function run() {
    setBusy(true)
    try {
      const result = await api.runSips()
      notifySuccess('Instalments bought', `${result.executed.length} SIP${result.executed.length === 1 ? '' : 's'} run`)
      onChange()
    } catch (error) {
      notifyError(error.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Panel className="p-5">
      <div className="flex items-center gap-2">
        <Repeat size={15} className="text-accent" />
        <h3 className="font-display text-title">SIPs</h3>
      </div>
      <p className="measure mt-2 text-xs text-ink-muted">
        A fixed amount every month, whatever the price. Units are bought at that month&rsquo;s NAV, so
        the average cost is a real average rather than a claim about one.
      </p>

      <form onSubmit={start} className="mt-4 flex flex-wrap items-end gap-2">
        <label className="block">
          <span className="eyebrow">Fund</span>
          <select
            value={instrument}
            onChange={(event) => setInstrument(event.target.value)}
            className="mt-1.5 h-9 rounded border border-rule-strong bg-paper px-2 text-sm text-ink outline-none focus:border-accent"
          >
            {data.available.funds.map((fund) => (
              <option key={fund.key} value={fund.key}>
                {fund.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="eyebrow">Monthly</span>
          <input
            type="number"
            min={data.available.min_sip}
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            placeholder={String(data.available.min_sip)}
            className="mt-1.5 h-9 w-28 rounded border border-rule-strong bg-paper px-3 text-sm text-ink outline-none focus:border-accent"
          />
        </label>
        <Button size="sm" type="submit" disabled={busy || !amount}>
          Start
        </Button>
      </form>

      {data.sips.length > 0 && (
        <>
          <ul className="mt-5 divide-y divide-rule border-t border-rule">
            {data.sips.map((sip) => (
              <li key={sip.id} className="py-3">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="text-sm text-ink">{sip.label}</span>
                  <span className="num text-sm text-ink">{money(sip.current_value)}</span>
                </div>
                <div className="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-[11px] text-ink-faint">
                  <span className="num">{money(sip.monthly_amount)} a month</span>
                  <span className="num">{sip.units} units</span>
                  <span className="num">avg {sip.average_cost}</span>
                  <span className="num">NAV {sip.nav}</span>
                  <span className={cx('num', toneFor(sip.pnl))}>{percent(sip.pnl_percent, 1)}</span>
                  {!sip.active && <Badge>Stopped</Badge>}
                </div>
              </li>
            ))}
          </ul>

          <Button size="sm" variant="secondary" className="mt-4" onClick={run} disabled={busy}>
            Buy this month&rsquo;s instalments
          </Button>
        </>
      )}
    </Panel>
  )
}
