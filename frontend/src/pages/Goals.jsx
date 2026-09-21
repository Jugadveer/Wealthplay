/**
 * Goals — its own page, because a goal is a plan rather than a line item.
 *
 * Three things live here that did not exist when goals were a form inside
 * Progress: a real plan per goal with the allocation and the arithmetic behind
 * it, a monthly contribution so the practice account behaves like one being fed
 * from a salary, and goal-based trading — pointing the practice account at one
 * goal so that every trade moves it.
 */
import { useState } from 'react'
import { ArrowRight, Link2, Plus, Target, Trash2, Wallet } from 'lucide-react'

import { api } from '../lib/api'
import { money, shortDate } from '../lib/format'
import { notifyError, notifySuccess } from '../lib/notify'
import { invalidate, useQuery } from '../lib/query'
import { Badge, Button, EmptyState, Meter, PageHeader, Panel, Skeleton, cx } from '../ui'
import GoalDialog, { GOAL_ICONS } from './goals/GoalDialog'
import PlanView from './goals/PlanView'

export default function Goals() {
  const { data, loading } = useQuery('goals', api.goals, { ttl: 30_000 })
  const [adding, setAdding] = useState(false)
  const [openGoal, setOpenGoal] = useState(null)

  if (loading && !data) return <GoalsSkeleton />

  const goals = data?.goals ?? []
  const refresh = () => invalidate('goals', 'portfolio')

  return (
    <div className="mx-auto max-w-page px-4 py-8">
      <PageHeader
        eyebrow="Planning"
        title="Goals"
        lede="A goal is four numbers: what it costs, when you need it, what you have, and what you can put aside. Everything else here follows from those."
        action={
          <Button onClick={() => setAdding(true)}>
            <Plus size={15} />
            New goal
          </Button>
        }
      />

      <Account account={data?.account} onChange={refresh} />

      {goals.length === 0 ? (
        <Panel className="mt-8">
          <EmptyState
            icon={Target}
            title="No goals yet"
            body="Name the thing, the cost and the date, and this turns into a monthly amount with a plan behind it."
            action={<Button onClick={() => setAdding(true)}>Set your first goal</Button>}
          />
        </Panel>
      ) : (
        <div className="stagger mt-8 space-y-4">
          {goals.map((goal, index) => (
            <GoalCard
              key={goal.id}
              goal={goal}
              index={index}
              open={openGoal === goal.id}
              onToggle={() => setOpenGoal(openGoal === goal.id ? null : goal.id)}
              onChange={refresh}
            />
          ))}
        </div>
      )}

      {adding && (
        <GoalDialog
          onClose={() => setAdding(false)}
          onCreated={(goal) => {
            setAdding(false)
            setOpenGoal(goal.id)
            notifySuccess('Goal created', `${goal.title} — ${money(goal.target_amount)}`)
            refresh()
          }}
        />
      )}
    </div>
  )
}

/**
 * The practice account as a funded thing rather than a fixed pot.
 *
 * A simulator that only ever starts at ₹50,000 teaches trading but not saving.
 * Declaring a monthly amount and paying it in is the habit the app is actually
 * about, so it sits at the top of the page.
 */
function Account({ account, onChange }) {
  const [amount, setAmount] = useState('')
  const [busy, setBusy] = useState(false)

  if (!account) return null

  const monthly = account.monthly_contribution

  async function save(event) {
    event.preventDefault()
    setBusy(true)
    try {
      await api.setContribution(Number(amount) || 0)
      setAmount('')
      notifySuccess('Monthly amount set', `${money(Number(amount) || 0)} a month`)
      onChange()
    } catch (error) {
      notifyError(error.message)
    } finally {
      setBusy(false)
    }
  }

  async function pay() {
    setBusy(true)
    try {
      const result = await api.payContribution()
      notifySuccess('Paid in', `${money(result.credited)} added to the practice account`)
      onChange()
    } catch (error) {
      notifyError(error.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Panel className="mt-8 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Practice account</p>
          <p className="num mt-1.5 text-xl font-semibold text-ink">{money(account.total_value)}</p>
          <p className="mt-0.5 text-xs text-ink-faint">
            {money(account.balance)} in cash
            {account.total_contributed > 0 && ` · ${money(account.total_contributed)} paid in so far`}
          </p>
        </div>

        {monthly > 0 ? (
          <div className="flex flex-wrap items-center gap-3">
            <div className="text-right">
              <p className="eyebrow">Monthly</p>
              <p className="num mt-0.5 text-sm font-semibold text-ink">{money(monthly)}</p>
            </div>
            {account.contribution_due ? (
              <Button size="sm" onClick={pay} disabled={busy}>
                <Wallet size={14} />
                Pay in this month
              </Button>
            ) : (
              <Badge tone="up">This month paid</Badge>
            )}
          </div>
        ) : (
          <form onSubmit={save} className="flex items-end gap-2">
            <label className="block">
              <span className="eyebrow">What can you invest monthly?</span>
              <input
                type="number"
                min="0"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                placeholder="10000"
                className="mt-1.5 h-9 w-36 rounded border border-rule-strong bg-paper px-3 text-sm text-ink outline-none transition-colors focus:border-accent"
              />
            </label>
            <Button size="sm" type="submit" disabled={busy || !amount}>
              Set
            </Button>
          </form>
        )}
      </div>

      {monthly > 0 && (
        <p className="measure mt-3 border-t border-rule pt-3 text-xs text-ink-muted">
          Paying in monthly is the habit the simulator is for. It credits the practice account once
          per calendar month, the same way a SIP debits yours.
        </p>
      )}
    </Panel>
  )
}

function GoalCard({ goal, index, open, onToggle, onChange }) {
  const Icon = GOAL_ICONS[goal.icon] ?? Target
  const [busy, setBusy] = useState(false)

  async function toggleLink() {
    setBusy(true)
    try {
      await api.linkGoal(goal.id, !goal.linked)
      notifySuccess(
        goal.linked ? 'Unlinked' : 'Goal-based trading on',
        goal.linked
          ? 'The practice account no longer reports against this goal.'
          : `Trades now count towards ${goal.title}.`,
      )
      onChange()
    } catch (error) {
      notifyError(error.message)
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    setBusy(true)
    try {
      await api.deleteGoal(goal.id)
      onChange()
    } catch (error) {
      notifyError(error.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Panel style={{ animationDelay: `${index * 55}ms` }} className="overflow-hidden">
      <div className="flex flex-wrap items-start gap-4 p-5">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded bg-accent/10 text-accent">
          <Icon size={18} strokeWidth={1.75} />
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <h2 className="font-display text-title">{goal.title}</h2>
            <span className="eyebrow">{goal.category_label}</span>
            {goal.linked && <Badge tone="accent">Trading towards this</Badge>}
          </div>

          <Meter
            value={goal.current_amount}
            max={goal.target_amount}
            tone={goal.linked ? 'accent' : 'play'}
            className="mt-3"
          />

          <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-xs text-ink-muted">
            <span className="num">
              {money(goal.current_amount)} of {money(goal.target_amount)}
            </span>
            <span>Target {shortDate(goal.target_date)}</span>
            {goal.plan && (
              <span className="num">
                {money(
                  goal.plan.plans.find((option) => option.key === goal.plan_choice)
                    ?.monthly_required ?? 0,
                )}{' '}
                a month needed
              </span>
            )}
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-1.5">
          <Button size="sm" variant="secondary" onClick={onToggle}>
            {open ? 'Hide plan' : 'The plan'}
          </Button>
          <button
            type="button"
            onClick={toggleLink}
            disabled={busy}
            title={goal.linked ? 'Stop trading towards this goal' : 'Trade towards this goal'}
            className={cx(
              'rounded border p-2 transition-colors',
              goal.linked
                ? 'border-accent/50 text-accent'
                : 'border-rule text-ink-faint hover:border-ink-faint hover:text-ink',
            )}
          >
            <Link2 size={14} />
          </button>
          <button
            type="button"
            onClick={remove}
            disabled={busy}
            aria-label={`Delete ${goal.title}`}
            className="rounded border border-rule p-2 text-ink-faint transition-colors hover:border-down/40 hover:text-down"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {open && goal.plan && (
        <div className="border-t border-rule bg-paper p-5">
          <PlanView plan={goal.plan} chosen={goal.plan_choice} />

          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-rule pt-5">
            <p className="measure text-xs text-ink-muted">
              {goal.linked
                ? 'This goal is linked to the practice account, so its progress is your account value. Every trade moves it.'
                : 'Link this goal to the practice account and its progress becomes your account value — so trading is practising for this, not in the abstract.'}
            </p>
            <Button size="sm" variant="secondary" to="/markets" className="shrink-0">
              Open the terminal
              <ArrowRight size={13} />
            </Button>
          </div>
        </div>
      )}
    </Panel>
  )
}

function GoalsSkeleton() {
  return (
    <div className="mx-auto max-w-page space-y-4 px-4 py-8">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-10 w-48" />
      <Skeleton className="h-24 rounded-lg" />
      {[0, 1].map((index) => (
        <Skeleton key={index} className="h-28 rounded-lg" />
      ))}
    </div>
  )
}
