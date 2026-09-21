/**
 * Scenario runs: a sequence of financial decisions with consequences.
 *
 * One balance carries through the whole run, so choices compound. Each
 * scenario previously reset the displayed "current capital" to its own
 * starting amount, which read as an unexplained loss.
 */
import { useState } from 'react'
import { ArrowRight, Check, X } from 'lucide-react'

import { api } from '../../lib/api'
import { money, toneFor } from '../../lib/format'
import { invalidate } from '../../lib/query'
import { Badge, Button, EmptyState, Meter, Panel, Stat, cx } from '../../ui'
import { Columns } from '../../ui/charts'

export default function Scenarios() {
  const [run, setRun] = useState(null)
  const [question, setQuestion] = useState(null)
  const [outcome, setOutcome] = useState(null)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)

  async function start() {
    setBusy(true)
    setResult(null)
    setOutcome(null)
    try {
      const started = await api.startScenarioRun()
      setRun(started.run_id)
      setQuestion(await api.scenarioRun(started.run_id))
    } finally {
      setBusy(false)
    }
  }

  async function choose(optionId) {
    setBusy(true)
    try {
      setOutcome(await api.answerScenario({ run_id: run, option_id: optionId }))
    } finally {
      setBusy(false)
    }
  }

  async function advance() {
    setBusy(true)
    try {
      if (outcome.completed) {
        setResult(await api.scenarioResult(run))
        setQuestion(null)
        invalidate('challenge:', 'profile')
      } else {
        setQuestion(await api.scenarioRun(run))
      }
      setOutcome(null)
    } finally {
      setBusy(false)
    }
  }

  if (result) return <Result result={result} onRestart={start} />

  if (!question) {
    return (
      <Panel>
        <EmptyState
          title="Work through a decision"
          body="Four situations with real trade-offs — a windfall, a tax deadline, a market drop. Your balance carries from one to the next."
          action={
            <Button size="lg" onClick={start} disabled={busy}>
              {busy ? 'Setting up…' : 'Start a run'}
            </Button>
          }
        />
      </Panel>
    )
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]">
      <Panel className="p-6">
        <div className="flex items-center justify-between gap-4">
          <span className="eyebrow">
            Decision {question.question_number} of {question.total_questions}
          </span>
          <span className="num text-sm text-ink-muted">{question.total_score} pts</span>
        </div>
        <Meter value={question.question_number - 1} max={question.total_questions} className="mt-3" />

        <h2 className="mt-6 font-display text-headline">{question.scenario.title}</h2>
        <p className="measure mt-3 text-[15px] leading-relaxed text-ink-muted">
          {question.scenario.description}
        </p>

        {outcome ? (
          <Outcome outcome={outcome} onNext={advance} busy={busy} />
        ) : (
          <div className="mt-6 space-y-2">
            {question.choices.map((choice) => (
              <button
                key={choice.id}
                type="button"
                disabled={busy}
                onClick={() => choose(choice.id)}
                className="flex w-full items-start gap-3 rounded border border-rule px-4 py-3 text-left text-sm text-ink-muted transition-colors hover:border-ink-faint hover:text-ink"
              >
                <Badge className="mt-0.5 shrink-0">{choice.type.toLowerCase()}</Badge>
                <span className="flex-1">{choice.text}</span>
              </button>
            ))}
          </div>
        )}
      </Panel>

      <aside className="space-y-4">
        <Panel className="p-5">
          <Stat label="Balance" value={money(question.running_balance)} size="lg" />
          <p className="mt-2 text-xs text-ink-faint">Carries through the whole run.</p>
        </Panel>
      </aside>
    </div>
  )
}

function Outcome({ outcome, onNext, busy }) {
  return (
    <div className="mt-6 border-t border-rule pt-5">
      <div className="flex flex-wrap items-center gap-3">
        <Badge tone={outcome.was_best_choice ? 'up' : 'neutral'}>
          {outcome.was_best_choice ? (
            <>
              <Check size={10} /> Best available
            </>
          ) : (
            <>
              <X size={10} /> {outcome.score_earned} of {outcome.best_available}
            </>
          )}
        </Badge>
        <span className={cx('num text-sm', toneFor(outcome.balance_change))}>
          {money(outcome.balance_change, { signed: true })}
        </span>
      </div>

      <p className="measure mt-4 text-sm leading-relaxed text-ink">{outcome.why_it_matters}</p>
      <p className="measure mt-2 text-sm leading-relaxed text-ink-muted">
        {outcome.mentor_feedback}
      </p>

      {outcome.better_choice && (
        <p className="measure mt-3 rounded border border-play/40 bg-play/5 p-3 text-sm text-ink">
          A stronger option: {outcome.better_choice}
        </p>
      )}

      <div className="mt-5">
        <div className="flex items-baseline justify-between">
          <p className="eyebrow">Where this leaves you</p>
          <p className="num text-[11px] text-ink-faint">
            projected at {outcome.growth_rate_percent}% a year
          </p>
        </div>
        <div className="mt-2">
          <Columns
            height={110}
            formatValue={(value) => money(value, { decimals: 0 })}
            items={[
              { label: 'Now', value: outcome.running_balance },
              { label: 'In a year', value: outcome.projected_one_year },
            ]}
          />
        </div>
      </div>

      <Button className="mt-5" onClick={onNext} disabled={busy}>
        {outcome.completed ? 'See results' : 'Next decision'}
        <ArrowRight size={15} />
      </Button>
    </div>
  )
}

function Result({ result, onRestart }) {
  return (
    <Panel className="p-6">
      <p className="eyebrow">Run complete</p>
      <p className="num mt-2 text-display text-ink">
        {result.total_score}
        <span className="text-2xl text-ink-faint">/{result.max_score}</span>
      </p>

      <div className="mt-5 grid gap-5 border-y border-rule py-5 sm:grid-cols-3">
        <Stat label="Accuracy" value={`${result.accuracy}%`} />
        <Stat label="Final balance" value={money(result.final_balance)} />
        <Stat label="XP earned" value={result.xp_awarded} />
      </div>

      <ol className="mt-5 space-y-3">
        {result.decisions.map((decision, index) => (
          <li key={index} className="border-b border-rule pb-3 last:border-0">
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-sm font-medium text-ink">{decision.scenario}</span>
              <Badge tone={decision.was_best ? 'up' : 'neutral'}>{decision.score} pts</Badge>
            </div>
            <p className="mt-1 text-sm text-ink-muted">{decision.choice}</p>
          </li>
        ))}
      </ol>

      <Button className="mt-6" onClick={onRestart}>
        Play another run
      </Button>
    </Panel>
  )
}
