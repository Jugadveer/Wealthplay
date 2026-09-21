/**
 * Market Oracle — read a chart, make a call, defend it.
 *
 * The rationale box earns points whether or not the call lands, because the
 * reasoning is the skill. Feedback grades the reasoning independently of the
 * outcome, so a lucky guess does not read as a win.
 *
 * The hint is generated from the actual series. It used to be a hardcoded
 * fallback string that shipped with the typo "the volume volume surge".
 */
import { useEffect, useState } from 'react'
import { Lightbulb, TrendingDown, TrendingUp } from 'lucide-react'

import { api } from '../../lib/api'
import { invalidate } from '../../lib/query'
import { Badge, Button, Panel, Skeleton, Tabs, cx } from '../../ui'
import { LineChart } from '../../ui/charts'

const LEVELS = [
  { value: 'beginner', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
]

export default function Prediction() {
  const [difficulty, setDifficulty] = useState('beginner')
  const [round, setRound] = useState(null)
  const [call, setCall] = useState(null)
  const [rationale, setRationale] = useState('')
  const [confidence, setConfidence] = useState(70)
  const [hint, setHint] = useState(null)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    loadRound(difficulty)
  }, [difficulty])

  function loadRound(level) {
    setRound(null)
    setCall(null)
    setRationale('')
    setConfidence(70)
    setHint(null)
    setResult(null)
    api.predictionQuestion(level).then(setRound).catch(() => setRound(null))
  }

  async function askForHint() {
    setBusy(true)
    try {
      setHint(await api.predictionHint(round.stock_symbol))
    } finally {
      setBusy(false)
    }
  }

  async function submit() {
    setBusy(true)
    try {
      const outcome = await api.submitPrediction({
        question_id: round.id,
        stock_symbol: round.stock_symbol,
        prediction: call,
        rationale,
        confidence,
      })
      setResult(outcome)
      invalidate('challenge:', 'profile')
    } finally {
      setBusy(false)
    }
  }

  if (!round) return <Skeleton className="h-96 rounded-lg" />

  const series = (round.chart_data || []).map((point) => ({
    x: point.date,
    y: point.close ?? point.price,
  }))

  // Bank questions use synthetic price data under a real company name, so no
  // currency symbol is attached — printing one would assert a price that is not
  // real. Live rounds use the listing's own currency.
  const fromBank = round.source === 'bank'
  const formatY = (value) =>
    fromBank
      ? value.toLocaleString('en-IN', { maximumFractionDigits: 0 })
      : `${round.currency === 'USD' ? '$' : '₹'}${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

  return (
    <div className="space-y-4">
      <Tabs items={LEVELS} value={difficulty} onChange={setDifficulty} />

      <Panel className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-title">{round.stock_name}</h2>
            <p className="num mt-0.5 text-xs text-ink-faint">{round.stock_symbol}</p>
          </div>
          <Badge>{fromBank ? `${round.difficulty} · practice data` : 'live chart'}</Badge>
        </div>

        <div className="mt-5">
          <LineChart
            height={260}
            series={[{ label: round.stock_symbol, points: series }]}
            formatY={formatY}
          />
        </div>

        <p className="measure mt-5 border-t border-rule pt-5 text-[15px] text-ink">
          {round.question}
        </p>

        {result ? (
          <Result result={result} onNext={() => loadRound(difficulty)} />
        ) : (
          <div className="mt-5 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              {[
                ['bullish', 'Higher', TrendingUp, 'text-up'],
                ['bearish', 'Lower', TrendingDown, 'text-down'],
              ].map(([value, label, Icon, tone]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setCall(value)}
                  className={cx(
                    'flex items-center justify-center gap-2 rounded border py-3 text-sm font-medium transition-colors',
                    call === value
                      ? 'border-accent bg-accent/5 text-ink'
                      : 'border-rule text-ink-muted hover:text-ink',
                  )}
                >
                  <Icon size={16} className={tone} />
                  {label}
                </button>
              ))}
            </div>

            <div>
              <div className="flex items-baseline justify-between">
                <span className="eyebrow">How sure are you?</span>
                <span className="num text-sm font-semibold text-accent">{confidence}%</span>
              </div>
              <input
                type="range"
                min={50}
                max={100}
                step={5}
                value={confidence}
                onChange={(event) => setConfidence(Number(event.target.value))}
                aria-label="Confidence in this call"
                className="mt-2 w-full accent-[rgb(var(--accent))]"
              />
              <p className="mt-1 text-[11px] text-ink-faint">
                Below 50% you would call it the other way, so the scale starts there. This is what
                your calibration is measured against.
              </p>
            </div>

            <label className="block">
              <span className="eyebrow">Why? (+5 points either way)</span>
              <textarea
                value={rationale}
                onChange={(event) => setRationale(event.target.value)}
                rows={2}
                maxLength={200}
                placeholder="What in the chart makes you say that…"
                className="mt-1 w-full resize-none rounded border border-rule-strong bg-paper px-3 py-2 text-sm text-ink outline-none transition-colors focus:border-accent"
              />
            </label>

            {hint?.available && (
              <p className="rounded border border-play/40 bg-play/5 p-3 text-sm text-ink">
                <Lightbulb size={13} className="mr-1.5 inline text-play" />
                {hint.hint}
              </p>
            )}
            {hint && !hint.available && (
              <p className="text-xs text-ink-faint">No hint available for this one right now.</p>
            )}

            <div className="flex flex-wrap gap-3">
              {!hint && (
                <Button variant="ghost" size="sm" onClick={askForHint} disabled={busy}>
                  <Lightbulb size={13} />
                  Ask for a hint
                </Button>
              )}
              <Button className="ml-auto" disabled={!call || busy} onClick={submit}>
                Submit call
              </Button>
            </div>
          </div>
        )}
      </Panel>
    </div>
  )
}

function Result({ result, onNext }) {
  return (
    <div className="mt-5 border-t border-rule pt-5">
      <div className="flex flex-wrap items-center gap-3">
        <Badge tone={result.correct ? 'up' : 'down'}>
          {result.correct ? 'Correct' : 'Missed'}
        </Badge>
        <span className="num text-sm text-ink">
          +{result.score} points
          {result.rationale_bonus > 0 && (
            <span className="text-ink-faint"> ({result.rationale_bonus} for reasoning)</span>
          )}
        </span>
      </div>

      <p className="mt-3 text-sm text-ink-muted">
        You said <strong className="text-ink">{result.your_call}</strong>; the chart read{' '}
        <strong className="text-ink">{result.actual}</strong>
        {/* Practice charts carry no real percentage, so none is quoted. */}
        {result.move_percent !== null && (
          <>
            {' '}
            at {result.move_percent > 0 ? '+' : ''}
            {result.move_percent}% over ten sessions
          </>
        )}
        .
      </p>

      {result.feedback && (
        <p className="measure mt-4 rounded border border-rule bg-paper-sunken p-3 text-sm leading-relaxed text-ink-muted">
          {result.feedback}
        </p>
      )}

      {result.explanation && (
        <p className="measure mt-3 text-sm leading-relaxed text-ink-muted">{result.explanation}</p>
      )}

      <Button className="mt-5" onClick={onNext}>
        Next chart
      </Button>
    </div>
  )
}
