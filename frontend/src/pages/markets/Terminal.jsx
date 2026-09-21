/**
 * The terminal chrome.
 *
 * Inside Markets the site navigation is gone and this takes its place. That is
 * deliberate: a practice trading account is a different mode of use from
 * reading a lesson, and leaving the app's five-item nav overhead invites you to
 * wander off mid-decision. What replaces it is what a desk actually needs — the
 * account value, the cash you can commit, the four screens, and one obvious way
 * out.
 *
 * The value in the header is polled, so the number you are deciding against is
 * the number the ticket will fill at.
 */
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { LogOut, Target } from 'lucide-react'

import { api } from '../../lib/api'
import { money, percent, toneFor } from '../../lib/format'
import { useQuery } from '../../lib/query'
import { cx } from '../../ui'

const SCREENS = [
  { to: '/markets', end: true, label: 'Overview' },
  { to: '/markets/positions', label: 'Positions' },
  { to: '/markets/trade', label: 'Trade' },
  { to: '/markets/analysis', label: 'Analysis' },
]

export default function Terminal({ children }) {
  return (
    <div className="min-h-dvh">
      <TerminalBar />
      <LinkedGoal />
      <main className="mx-auto max-w-wide px-4 py-7">{children}</main>
    </div>
  )
}

/**
 * What this account is for.
 *
 * Trading in the abstract teaches the mechanics and nothing about why. When a
 * goal is linked, the terminal says so on every screen and shows what is left,
 * so a decision is made against a target rather than against a score.
 */
function LinkedGoal() {
  const { data } = useQuery('goals', api.goals, { ttl: 60_000 })
  const goal = data?.goals?.find((item) => item.linked)
  if (!goal) return null

  const remaining = Math.max(0, goal.target_amount - goal.current_amount)

  return (
    <div className="border-b border-rule bg-accent/10">
      <div className="mx-auto flex max-w-wide flex-wrap items-center gap-x-6 gap-y-2 px-4 py-2.5">
        <span className="flex items-center gap-2 text-xs text-accent">
          <Target size={13} />
          Trading towards
          <strong className="font-semibold">{goal.title}</strong>
        </span>

        <div className="ml-auto flex items-center gap-5">
          <span className="num text-xs text-ink-muted">
            {money(goal.current_amount)} of {money(goal.target_amount)}
          </span>
          <span className="num text-xs text-ink-muted">{money(remaining)} to go</span>
          <Link
            to="/goals"
            className="num text-xs text-accent underline-offset-2 hover:underline"
          >
            {goal.progress_percent}%
          </Link>
        </div>
      </div>
    </div>
  )
}

function TerminalBar() {
  const navigate = useNavigate()
  const { data } = useQuery('portfolio', api.portfolio, { ttl: 30_000 })
  const invested = (data?.holdings?.length ?? 0) > 0

  return (
    <header className="sticky top-0 z-40 border-b border-rule bg-paper/95 backdrop-blur">
      <div className="mx-auto flex max-w-wide flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
        <Link to="/markets" className="flex shrink-0 items-center gap-2">
          <span className="h-2 w-2 animate-pulse rounded-full bg-up" aria-hidden="true" />
          <span className="num text-xs font-semibold uppercase tracking-[0.18em] text-ink">
            Practice terminal
          </span>
        </Link>

        <nav className="order-3 flex w-full gap-1 md:order-none md:w-auto" aria-label="Terminal">
          {SCREENS.map((screen) => (
            <NavLink
              key={screen.to}
              to={screen.to}
              end={screen.end}
              className={({ isActive }) =>
                cx(
                  'rounded px-3 py-1.5 text-sm transition-colors duration-200',
                  isActive
                    ? 'bg-accent/10 font-medium text-accent'
                    : 'text-ink-muted hover:bg-paper-sunken hover:text-ink',
                )
              }
            >
              {screen.label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-5">
          {data && (
            <>
              <Figure label="Cash" value={money(data.balance)} />
              {invested && (
                <>
                  <Figure label="Value" value={money(data.total_value)} />
                  <Figure
                    label="P&L"
                    value={percent(data.total_pnl_percent)}
                    tone={toneFor(data.total_pnl)}
                  />
                </>
              )}
            </>
          )}

          <button
            type="button"
            onClick={() => navigate('/today')}
            className="flex items-center gap-1.5 rounded border border-rule px-2.5 py-1.5 text-xs text-ink-muted transition-colors hover:border-ink-faint hover:text-ink"
          >
            <LogOut size={13} />
            Exit
          </button>
        </div>
      </div>
    </header>
  )
}

function Figure({ label, value, tone }) {
  return (
    <div className="hidden text-right sm:block">
      <p className="eyebrow">{label}</p>
      <p className={cx('num text-sm font-semibold', tone || 'text-ink')}>{value}</p>
    </div>
  )
}
