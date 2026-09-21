/**
 * Progress: the streak calendar, achievements, goals and the weekly recap.
 */
import { useEffect, useState } from 'react'
import { Flame, Lock, Rocket, Snowflake, Trophy } from 'lucide-react'

import { useAuth } from '../auth/AuthContext'
import { api } from '../lib/api'
import { percent, shortDate } from '../lib/format'
import { useQuery } from '../lib/query'
import {
  Button,
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
      <Launch />

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
        <Calibration />
        <StreakCalendar />
        <Recap />
        <Achievements />
      </div>
    </div>
  )
}

/**
 * One rocket across the page on arrival.
 *
 * Progress is the page where the app should feel pleased with you, and it gets
 * no curtain in front of it — a page you open constantly should not make you
 * wait to see it. So the celebration happens on the page instead: it flies
 * once, behind the content, and cannot take a click. Skipped for anyone who has
 * asked for reduced motion.
 */
function Launch() {
  const [flying, setFlying] = useState(
    () => !window.matchMedia?.('(prefers-reduced-motion: reduce)').matches,
  )

  useEffect(() => {
    if (!flying) return undefined
    const timer = setTimeout(() => setFlying(false), 1900)
    return () => clearTimeout(timer)
  }, [flying])

  if (!flying) return null

  return (
    <div className="rocket-flight" aria-hidden="true">
      <span className="rocket-trail" />
      <Rocket size={20} strokeWidth={1.75} className="-rotate-45" />
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

/**
 * Calibration — the one thing here a quiz app cannot show you.
 *
 * Being right often is easy on easy calls. Being right 70% of the times you
 * said 70% is a separate, harder skill, and it is the one that transfers to
 * actually risking money. A perfectly calibrated player sits on the diagonal.
 */
function Calibration() {
  const { data } = useQuery('challenge:calibration', api.calibration, { ttl: 60_000 })
  if (!data) return null

  const measured = data.bands.filter((band) => band.calls > 0)

  return (
    <section>
      <SectionHead label="The hard skill" title="Calibration" />

      <Panel className="mt-4 p-5">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <Stat
            label="Calibration gap"
            value={data.calibration_gap === null ? '—' : `${data.calibration_gap} pts`}
            sub="Average distance between what you claimed and what happened"
            size="lg"
          />
          <p className="num text-xs text-ink-faint">{data.total_calls} calls</p>
        </div>

        {measured.length > 0 && (
          <ul className="mt-6 space-y-3 border-t border-rule pt-5">
            {measured.map((band) => (
              <li key={band.label}>
                <div className="flex items-baseline justify-between gap-3 text-xs">
                  <span className="num text-ink-muted">
                    Said {band.label} · {band.calls} {band.calls === 1 ? 'call' : 'calls'}
                  </span>
                  <span
                    className={cx(
                      'num font-semibold',
                      Math.abs(band.actual - band.stated) <= 10 ? 'text-up' : 'text-down',
                    )}
                  >
                    right {band.actual}%
                  </span>
                </div>
                {/* Two bars on one track: the claim, then what happened. The
                    gap between them is the whole point of the panel. */}
                <div className="relative mt-1.5 h-2 w-full overflow-hidden rounded-sm bg-paper-sunken">
                  <div
                    className="absolute inset-y-0 left-0 bg-accent/30"
                    style={{ width: `${band.stated}%` }}
                  />
                  <div
                    className="absolute inset-y-0 left-0 border-r-2 border-ink"
                    style={{ width: `${band.actual}%` }}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}

        <p className="measure mt-5 text-sm text-ink-muted">{data.verdict}</p>
      </Panel>
    </section>
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
    (acc[achievement.category] ||= []).push(achievement)
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
