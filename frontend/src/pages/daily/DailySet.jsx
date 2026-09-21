/**
 * The daily set: six short plays, shared by every player, reset each morning.
 *
 * Mounted twice — on Today, where it is the reason to open the app, and under
 * Play, where someone looking for "the games" reasonably expects to find them.
 * One component so the card states, the scoring and the back-link behave the
 * same in both places.
 */
import { useState } from 'react'
import { Check } from 'lucide-react'

import { api } from '../../lib/api'
import { invalidate, useQuery } from '../../lib/query'
import { Badge, Panel, Skeleton, cx } from '../../ui'
import DailyDrill from './DailyDrill'
import Ledger from './Ledger'
import MarketCall from './MarketCall'
import NumberSense from './NumberSense'
import RankIt from './RankIt'
import TickerTiles from './TickerTiles'

export const PLAYS = {
  ticker: { component: TickerTiles, blurb: 'Name the company in five guesses.' },
  ledger: { component: Ledger, blurb: 'A five-letter money word in six tries.' },
  call: { component: MarketCall, blurb: 'Higher or lower by tomorrow’s close.' },
  rank: { component: RankIt, blurb: 'Order four companies by last year’s return.' },
  estimate: { component: NumberSense, blurb: 'Guess a real number. Close counts.' },
  drill: { component: DailyDrill, blurb: 'Five questions from what you have studied.' },
}

/** Reads the set once; the caller decides what sits around it. */
export function useDailySet() {
  return useQuery('daily:today', api.today, { ttl: 15_000 })
}

export function remainingMinutes(plays) {
  const left = plays.filter((play) => !play.done).length
  return Math.max(1, Math.round((left * 90) / 60))
}

export default function DailySet({ plays, backLabel = 'Back to the set' }) {
  const [active, setActive] = useState(null)

  // Refresh the set, but leave the game open: the reveal — the answer, the
  // definition, the real returns, the share grid — is the payoff, and closing
  // the board the moment it resolves threw it away.
  const onFinish = () => invalidate('daily:', 'profile')

  const Active = active ? PLAYS[active].component : null

  if (Active) {
    return (
      <div>
        <button
          type="button"
          onClick={() => setActive(null)}
          className="mb-4 text-sm text-ink-muted underline decoration-rule-strong underline-offset-4 hover:text-ink"
        >
          {backLabel}
        </button>
        <Active onFinish={onFinish} />
      </div>
    )
  }

  return (
    <div className="stagger grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {plays.map((play, index) => (
        <PlayCard key={play.kind} play={play} index={index} onOpen={() => setActive(play.kind)} />
      ))}
    </div>
  )
}

function PlayCard({ play, index, onOpen }) {
  const blurb = PLAYS[play.kind]?.blurb ?? ''

  return (
    <Panel
      as="button"
      onClick={onOpen}
      style={{ animationDelay: `${index * 55}ms` }}
      className={cx(
        'group flex w-full flex-col items-start gap-2 p-5 text-left transition-[border-color,transform] duration-200',
        play.done ? 'opacity-70' : 'hover:-translate-y-0.5 hover:border-accent/50',
      )}
    >
      <div className="flex w-full items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-title">{play.label}</h2>
          <p className="mt-1 text-sm text-ink-muted">{blurb}</p>
        </div>
        {play.done ? (
          <Badge tone={play.solved ? 'up' : 'neutral'}>
            <Check size={10} />
            {play.score ? `+${play.score}` : 'done'}
          </Badge>
        ) : play.pending ? (
          <Badge tone="play">Settles tomorrow</Badge>
        ) : play.in_progress ? (
          <Badge tone="accent">In progress</Badge>
        ) : play.due_count ? (
          <Badge tone="play">{play.due_count} due</Badge>
        ) : (
          <Badge tone="accent">New</Badge>
        )}
      </div>

      <span className="mt-2 text-xs text-ink-faint transition-colors group-hover:text-accent">
        {play.done || play.pending ? 'Review →' : play.in_progress ? 'Continue →' : 'Play →'}
      </span>
    </Panel>
  )
}

export function DailySetSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {[0, 1, 2, 3, 4, 5].map((index) => (
        <Skeleton key={index} className="h-32 rounded-lg" />
      ))}
    </div>
  )
}
