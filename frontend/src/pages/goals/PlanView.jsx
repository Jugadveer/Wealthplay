/**
 * The plan for one goal.
 *
 * Three things a goal calculator usually hides, shown here instead: what the
 * target actually costs on the day you need it, what each plan can lose as well
 * as what it can make, and — when the monthly amount is not affordable — which
 * of the three levers has to move and by how much.
 */
import { AlertTriangle, Briefcase, CalendarClock, Check, Info, ShieldCheck, TrendingUp } from 'lucide-react'

import { money, percent } from '../../lib/format'
import { Badge, Meter, Panel, cx } from '../../ui'

const PLAN_ICONS = { safe: ShieldCheck, balanced: Check, growth: TrendingUp }

export default function PlanView({ plan, chosen, onChoose }) {
  if (!plan) return null

  const inflated = plan.target_at_date > plan.target_today

  return (
    <div className="space-y-6">
      <Panel className="p-5">
        <p className="eyebrow">What it actually costs</p>
        <div className="mt-3 flex flex-wrap items-baseline gap-x-8 gap-y-2">
          <Figure label="Cost today" value={money(plan.target_today)} />
          <Figure
            label={`Cost in ${plan.years_remaining} years`}
            value={money(plan.target_at_date)}
            strong
          />
          {plan.already_saved > 0 && <Figure label="Already saved" value={money(plan.already_saved)} />}
        </div>
        {inflated && (
          <p className="measure mt-3 text-xs text-ink-muted">
            Inflated at {plan.inflation_percent}% a year. Planning against today&rsquo;s price is the
            commonest reason goals finish short.
          </p>
        )}
        {plan.category.note && (
          <p className="measure mt-2 flex gap-1.5 text-xs text-ink-faint">
            <Info size={12} className="mt-0.5 shrink-0" />
            {plan.category.note}
          </p>
        )}
      </Panel>

      <div className="grid gap-4 lg:grid-cols-3">
        {plan.plans.map((option) => (
          <PlanCard
            key={option.key}
            option={option}
            recommended={option.key === plan.recommended}
            chosen={option.key === chosen}
            onChoose={onChoose && (() => onChoose(option.key))}
          />
        ))}
      </div>

      <Feasibility feasibility={plan.feasibility} />

      {plan.implementation && <Implementation data={plan.implementation} />}

      {plan.ladder?.length > 1 && <Ladder rungs={plan.ladder} />}
      {plan.borrowing && <Borrowing loan={plan.borrowing} />}
    </div>
  )
}

function Figure({ label, value, strong }) {
  return (
    <div>
      <p className="eyebrow">{label}</p>
      <p className={cx('num mt-1', strong ? 'text-xl font-semibold text-ink' : 'text-sm text-ink-muted')}>
        {value}
      </p>
    </div>
  )
}

function PlanCard({ option, recommended, chosen, onChoose }) {
  const Icon = PLAN_ICONS[option.key] ?? Check

  return (
    <Panel
      as={onChoose ? 'button' : 'div'}
      onClick={onChoose}
      className={cx(
        'flex flex-col p-5 text-left transition-colors duration-200',
        chosen ? 'border-accent' : onChoose && 'hover:border-rule-strong',
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Icon size={15} className="text-accent" />
          <h3 className="font-display text-title">{option.label}</h3>
        </div>
        {recommended && <Badge tone="accent">Recommended</Badge>}
      </div>

      <p className="num mt-4 text-2xl font-semibold text-ink">
        {money(option.monthly_required)}
      </p>
      <p className="text-xs text-ink-faint">a month</p>

      <dl className="mt-4 space-y-1.5 border-t border-rule pt-3 text-xs">
        <Row label="Equity" value={`${option.equity_percent}%`} />
        <Row label="Assumed return" value={`${option.expected_return_percent}%`} />
        <Row label="Projected" value={money(option.projected)} />
        {option.downside < option.projected && (
          <Row label="If markets fall hard" value={money(option.downside)} tone="text-down" />
        )}
      </dl>

      <p className="measure mt-3 text-xs leading-relaxed text-ink-muted">{option.summary}</p>

      {option.allocation.length > 0 && (
        <ul className="mt-3 space-y-2 border-t border-rule pt-3">
          {option.allocation.map((row) => (
            <li key={row.instrument}>
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-xs text-ink">{row.instrument}</span>
                <span className="num text-xs text-ink-muted">{row.share}%</span>
              </div>
              <p className="mt-1 text-[11px] leading-snug text-ink-faint">{row.why}</p>
            </li>
          ))}
        </ul>
      )}

      {option.caution && (
        <p className="measure mt-3 border-t border-rule pt-3 text-[11px] leading-snug text-play">
          {option.caution}
        </p>
      )}
    </Panel>
  )
}

function Row({ label, value, tone }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <dt className="text-ink-muted">{label}</dt>
      <dd className={cx('num font-medium', tone || 'text-ink')}>{value}</dd>
    </div>
  )
}

function Feasibility({ feasibility }) {
  if (!feasibility) return null

  if (!feasibility.known) {
    return (
      <Panel className="p-5">
        <p className="text-sm text-ink-muted">{feasibility.message}</p>
      </Panel>
    )
  }

  return (
    <Panel
      className={cx('border-l-2 p-5', feasibility.achievable ? 'border-l-up' : 'border-l-play')}
    >
      <p className="eyebrow">{feasibility.achievable ? 'Affordable' : 'Something has to move'}</p>
      <p className="measure mt-2 text-sm text-ink">{feasibility.message}</p>

      <div className="mt-4 flex flex-wrap gap-x-8 gap-y-2">
        <Figure label="Needed each month" value={money(feasibility.monthly_required)} />
        <Figure label="You said you can manage" value={money(feasibility.monthly_capacity)} />
      </div>

      {!feasibility.achievable && (
        <Meter
          value={feasibility.monthly_capacity}
          max={feasibility.monthly_required}
          tone="play"
          className="mt-4"
        />
      )}
    </Panel>
  )
}

/**
 * The allocation turned into things a person can actually go and do.
 *
 * "45% equity" is correct and unactionable. This is the rupee amount per sleeve,
 * the instrument types, what an index fund is holding at today's prices, and
 * when to look at any of it again.
 */
function Implementation({ data }) {
  return (
    <div className="space-y-4">
      <SectionLabel>How to actually do this, every month</SectionLabel>

      <div className="grid gap-4 lg:grid-cols-3">
        {data.sleeves.map((sleeve) => (
          <Panel key={sleeve.key} className="flex flex-col p-5">
            <div className="flex items-baseline justify-between gap-3">
              <h3 className="font-display text-title">{sleeve.name}</h3>
              <span className="num text-xs text-ink-faint">{sleeve.share}%</span>
            </div>
            <p className="num mt-2 text-xl font-semibold text-accent">{money(sleeve.monthly)}</p>
            <p className="text-xs text-ink-faint">a month</p>

            <ul className="mt-4 space-y-3 border-t border-rule pt-3">
              {sleeve.instruments.map((item) => (
                <li key={item.type}>
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="text-xs font-medium text-ink">{item.type}</span>
                    <span className="num text-xs text-ink-muted">{money(item.monthly)}</span>
                  </div>
                  <p className="mt-1 text-[11px] leading-snug text-ink-faint">
                    {item.detail} <span className="num">~{item.rate}%</span>
                  </p>
                </li>
              ))}
            </ul>

            {sleeve.holds?.length > 0 && (
              <div className="mt-4 border-t border-rule pt-3">
                <p className="eyebrow">What the index holds, priced now</p>
                <ul className="mt-2 space-y-1">
                  {sleeve.holds.slice(0, 4).map((hold) => (
                    <li key={hold.symbol} className="flex items-baseline justify-between gap-2">
                      <span className="num text-[11px] text-ink">{hold.symbol}</span>
                      <span className="num text-[11px] text-ink-muted">{money(hold.price)}</span>
                      <span
                        className={cx(
                          'num w-12 text-right text-[11px]',
                          hold.change_percent >= 0 ? 'text-up' : 'text-down',
                        )}
                      >
                        {percent(hold.change_percent, 1)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <p className="measure mt-auto pt-4 text-[11px] leading-snug text-ink-muted">
              {sleeve.why}
            </p>
            {sleeve.action && (
              <p className="mt-2 text-[11px] leading-snug text-accent">{sleeve.action}</p>
            )}
          </Panel>
        ))}
      </div>

      <Panel className="p-5">
        <div className="flex items-center gap-2">
          <CalendarClock size={15} className="text-ink-faint" />
          <p className="eyebrow">When to look at it</p>
        </div>
        <ul className="mt-3 divide-y divide-rule border-t border-rule">
          {data.cadence.map((entry) => (
            <li key={entry.period} className="grid gap-1 py-3 sm:grid-cols-[9rem_1fr] sm:gap-4">
              <span className="num text-xs text-ink-faint">{entry.period}</span>
              <div>
                <p className="text-sm text-ink">{entry.action}</p>
                <p className="measure mt-0.5 text-[11px] leading-snug text-ink-muted">
                  {entry.detail}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </Panel>

      <p className="measure flex gap-1.5 text-[11px] leading-snug text-ink-faint">
        <AlertTriangle size={12} className="mt-0.5 shrink-0" />
        {data.disclaimer}
      </p>
    </div>
  )
}

function SectionLabel({ children }) {
  return (
    <div className="border-t border-rule pt-4">
      <h3 className="text-title">{children}</h3>
    </div>
  )
}

/** The deposit ladder for the protected portion. */
function Ladder({ rungs }) {
  return (
    <Panel className="p-5">
      <p className="eyebrow">Deposit ladder for the protected part</p>
      <p className="measure mt-2 text-xs text-ink-muted">
        One deposit per year rather than a single long one, so part of the money matures every year
        and a partial need never forces you to break the whole amount.
      </p>

      <ul className="mt-4 divide-y divide-rule border-t border-rule">
        {rungs.map((rung) => (
          <li key={rung.tenure_years} className="flex items-baseline justify-between gap-3 py-2.5">
            <span className="text-sm text-ink">
              {rung.tenure_years}-year deposit
            </span>
            <span className="num text-xs text-ink-muted">{money(rung.amount)}</span>
            <span className="num w-28 text-right text-xs text-up">
              {money(rung.value_at_maturity)}
            </span>
          </li>
        ))}
      </ul>
    </Panel>
  )
}

/** The loan side, for goals people normally part-fund with borrowing. */
function Borrowing({ loan }) {
  return (
    <Panel className="p-5">
      <div className="flex items-center gap-2">
        <Briefcase size={15} className="text-ink-faint" />
        <p className="eyebrow">If you borrowed half instead</p>
      </div>

      <div className="mt-3 flex flex-wrap gap-x-8 gap-y-2">
        <Figure label="Loan" value={money(loan.principal)} />
        <Figure label={`EMI at ${loan.rate_percent}% for ${loan.years}y`} value={money(loan.monthly)} strong />
        <Figure label="Interest paid" value={money(loan.total_interest)} />
        <Figure label="Total repaid" value={money(loan.total_repaid)} />
      </div>

      <p className="measure mt-3 text-xs leading-relaxed text-ink-muted">{loan.note}</p>
    </Panel>
  )
}
