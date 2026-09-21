/**
 * Progress: the streak calendar, achievements, goals and the weekly recap.
 */
import { useState } from 'react'
import { Flame, Lock, Snowflake, Target, Trophy } from 'lucide-react'

import { useAuth } from '../auth/AuthContext'
import { api } from '../lib/api'
import { money, percent, shortDate } from '../lib/format'
import { invalidate, useQuery } from '../lib/query'
import {
  Badge,
  Button,
  EmptyState,
  Meter,
  PageHeader,
  Panel,
  SectionHead,
  Skeleton,
  Stat,
  cx,
} from '../ui'

const LEVEL_THRESHOLDS = { beginner: 750, intermediate: 1200, advanced: 2500 }

export default function Progress() {
  const { user, signOut } = useAuth()

  return (
    <div className="mx-auto max-w-page px-4 py-8">
      <PageHeader
        eyebrow={user?.username}
        title="Your progress"
        action={
          <Button variant="ghost" size="sm" onClick={signOut}>
            Sign out
          </Button>
        }
      />

      <div className="mt-8 space-y-12">
        <Level user={user} />
        <StreakCalendar />
        <Recap />
        <Achievements />
        <Goals />
      </div>
    </div>
  )
}

function Level({ user }) {
  if (!user) return null

  const target = LEVEL_THRESHOLDS[user.level] ?? 750
  const remaining = Math.max(0, target - user.xp)

  return (
    <Panel className="grid gap-6 p-6 sm:grid-cols-3">
      <Stat label="Level" value={user.level} size="lg" />
      <Stat label="XP" value={user.xp.toLocaleString('en-IN')} size="lg" />
      <div>
        <p className="eyebrow">Next level</p>
        <Meter value={user.xp} max={target} className="mt-3" />
        <p className="mt-2 text-xs text-ink-muted">
          {remaining === 0 ? 'Top of this tier.' : `${remaining.toLocaleString('en-IN')} XP to go`}
        </p>
      </div>
    </Panel>
  )
}

function StreakCalendar() {
  const { data } = useQuery('daily:streak', api.streak, { ttl: 60_000 })
  if (!data) return null

  return (
    <section>
      <SectionHead label="Consistency" title="Your streak" />

      <Panel className="mt-4 p-6">
        <div className="flex flex-wrap items-center gap-8">
          <Stat
            label="Current"
            value={
              <span className="flex items-center gap-2">
                <Flame size={18} className={data.current > 0 ? 'text-play' : 'text-ink-faint'} />
                {data.current}
              </span>
            }
            size="lg"
          />
          <Stat label="Longest" value={data.longest} />
          <Stat
            label="Freezes"
            value={
              <span className="flex items-center gap-2">
                <Snowflake size={16} className="text-accent" />
                {data.freezes}
              </span>
            }
            sub="each covers one missed day"
          />
          <Stat label="Days active" value={data.total_days} />
        </div>

        <div className="mt-6 border-t border-rule pt-5">
          <p className="eyebrow">Last fortnight</p>
          <div className="mt-3 flex gap-1.5">
            {data.calendar.map((day) => (
              <div
                key={day.date}
                title={`${shortDate(day.date)}: ${day.active ? 'active' : 'no activity'}`}
                className={cx(
                  'h-8 flex-1 rounded-sm',
                  day.active ? 'bg-play' : 'bg-paper-sunken',
                )}
              />
            ))}
          </div>
        </div>

        {data.at_risk && (
          <p className="mt-4 rounded border border-play/40 bg-play/5 p-3 text-sm text-ink">
            You have not played today. One more missed day and a freeze gets spent.
          </p>
        )}
      </Panel>
    </section>
  )
}

function Recap() {
  const { data } = useQuery('daily:recap', api.recap, { ttl: 300_000 })
  if (!data) return null

  return (
    <section>
      <SectionHead label="This week" title="Where you are" />

      <Panel className="mt-4 p-6">
        <div className="grid gap-6 sm:grid-cols-4">
          <Stat label="Puzzles solved" value={data.stats.puzzles} sub="of 7 days" />
          <Stat label="Recall accuracy" value={`${Math.round(data.stats.accuracy)}%`} />
          <Stat label="Portfolio" value={percent(data.stats.portfolio_return)} />
          <Stat label="Weakest topic" value={data.stats.weak_topic} />
        </div>

        {data.narrative_available ? (
          <p className="measure mt-6 border-t border-rule pt-5 text-sm leading-relaxed text-ink-muted">
            {data.narrative}
          </p>
        ) : (
          <p className="mt-6 border-t border-rule pt-5 text-xs text-ink-faint">
            The written summary needs a language model and none answered. The numbers above are
            computed from your activity.
          </p>
        )}
      </Panel>
    </section>
  )
}

function Achievements() {
  const { data, loading } = useQuery('achievements', api.achievements, { ttl: 60_000 })

  if (loading && !data) return <Skeleton className="h-64 rounded-lg" />
  if (!data) return null

  const groups = data.achievements.reduce((acc, achievement) => {
    ;(acc[achievement.category] ||= []).push(achievement)
    return acc
  }, {})

  return (
    <section>
      <SectionHead
        label="Milestones"
        title="Achievements"
        action={
          <span className="num text-sm text-ink-muted">
            {data.total_unlocked}/{data.total_available}
          </span>
        }
      />

      <div className="mt-4 space-y-6">
        {Object.entries(groups).map(([category, items]) => (
          <div key={category}>
            <p className="eyebrow">{category}</p>
            <div className="mt-2 grid gap-px border border-rule bg-rule sm:grid-cols-2 lg:grid-cols-3">
              {items.map((achievement) => (
                <div
                  key={achievement.id}
                  className={cx('bg-paper p-4', !achievement.unlocked && 'opacity-55')}
                >
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="text-sm font-medium text-ink">{achievement.name}</h3>
                    {achievement.unlocked ? (
                      <Trophy size={14} className="shrink-0 text-play" />
                    ) : (
                      <Lock size={13} className="shrink-0 text-ink-faint" />
                    )}
                  </div>
                  <p className="mt-1 text-xs leading-relaxed text-ink-muted">
                    {achievement.description}
                  </p>
                  <p className="num mt-2 text-[11px] text-ink-faint">
                    {achievement.unlocked
                      ? `Unlocked ${shortDate(achievement.unlocked_at)}`
                      : `+${achievement.xp_reward} XP`}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

function Goals() {
  const { data } = useQuery('goals', api.goals, { ttl: 60_000 })
  const [adding, setAdding] = useState(false)

  const goals = data?.goals ?? []

  return (
    <section>
      <SectionHead
        label="Planning"
        title="Goals"
        action={
          <Button size="sm" variant="secondary" onClick={() => setAdding((open) => !open)}>
            {adding ? 'Cancel' : 'Add a goal'}
          </Button>
        }
      />

      {adding && <GoalForm onDone={() => setAdding(false)} />}

      {goals.length === 0 && !adding ? (
        <Panel className="mt-4">
          <EmptyState
            icon={Target}
            title="No goals set"
            body="A goal turns an abstract number into a monthly amount. Name the thing, the cost, and the date."
            action={<Button onClick={() => setAdding(true)}>Set your first goal</Button>}
          />
        </Panel>
      ) : (
        <div className="mt-4 space-y-3">
          {goals.map((goal) => (
            <Panel key={goal.id} className="p-5">
              <div className="flex flex-wrap items-baseline justify-between gap-3">
                <h3 className="font-display text-title">{goal.title}</h3>
                <span className="num text-sm text-ink-muted">
                  {money(goal.current_amount)} of {money(goal.target_amount)}
                </span>
              </div>
              <Meter
                value={goal.current_amount}
                max={goal.target_amount}
                tone="play"
                className="mt-3"
              />
              <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-ink-muted">
                <span>Target {shortDate(goal.target_date)}</span>
                {goal.monthly_sip > 0 && (
                  <span className="num">{money(goal.monthly_sip)} a month needed</span>
                )}
              </div>
            </Panel>
          ))}
        </div>
      )}
    </section>
  )
}

function GoalForm({ onDone }) {
  const [values, setValues] = useState({ title: '', target_amount: '', target_date: '' })
  const [busy, setBusy] = useState(false)

  const set = (field) => (event) =>
    setValues((current) => ({ ...current, [field]: event.target.value }))

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    try {
      await api.createGoal(values)
      invalidate('goals')
      onDone()
    } finally {
      setBusy(false)
    }
  }

  return (
    <Panel className="mt-4 p-5">
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-[2fr_1fr_1fr_auto] sm:items-end">
        <Field label="What for" value={values.title} onChange={set('title')} required />
        <Field
          label="Cost"
          type="number"
          min="1"
          value={values.target_amount}
          onChange={set('target_amount')}
          required
        />
        <Field
          label="By when"
          type="date"
          value={values.target_date}
          onChange={set('target_date')}
          required
        />
        <Button type="submit" disabled={busy}>
          Save
        </Button>
      </form>
    </Panel>
  )
}

function Field({ label, ...props }) {
  return (
    <label className="block">
      <span className="eyebrow">{label}</span>
      <input
        {...props}
        className="mt-1 h-10 w-full rounded border border-rule-strong bg-paper px-3 text-sm text-ink outline-none transition-colors focus:border-accent"
      />
    </label>
  )
}
