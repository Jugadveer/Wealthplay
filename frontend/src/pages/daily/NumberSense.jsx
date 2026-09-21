/**
 * Number Sense — estimate a real figure, scored by proximity.
 *
 * Banding rather than exactness is the whole idea: knowing gold is "about a
 * lakh per 10g" is a useful instinct, and demanding the precise rupee would
 * teach nothing. The explanation after the guess is where the learning is.
 */
import { useEffect, useState } from 'react'

import { api } from '../../lib/api'
import { Badge, Button, Panel } from '../../ui'

const BAND_TONE = {
  'spot on': 'up',
  'very close': 'up',
  close: 'play',
  'in the region': 'neutral',
  'way off': 'down',
}

export default function NumberSense({ onFinish }) {
  const [round, setRound] = useState(null)
  const [guess, setGuess] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.numberSense().then(setRound).catch(() => setRound(null))
  }, [])

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')

    try {
      setRound(await api.submitEstimate({ guess: Number(guess) }))
      onFinish?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (!round) return <Panel className="h-56 animate-pulse" />

  const result = round.result

  return (
    <Panel className="p-6">
      <p className="eyebrow">Puzzle three</p>
      <h2 className="mt-1 text-headline">Number Sense</h2>

      <p className="measure mt-4 text-base text-ink">{round.question}</p>

      {result ? (
        <div className="mt-6 space-y-4 border-t border-rule pt-5">
          <div className="flex flex-wrap items-baseline gap-x-8 gap-y-3">
            <Figure label="You said" value={format(result.guess, round.unit)} />
            <Figure label="Actual" value={format(result.answer, round.unit)} emphasis />
            <Figure label="Off by" value={`${result.off_by_percent}%`} />
          </div>

          <Badge tone={BAND_TONE[result.band] ?? 'neutral'}>
            {result.band} · +{result.score} XP
          </Badge>

          <p className="measure text-sm leading-relaxed text-ink-muted">{result.context}</p>
        </div>
      ) : (
        <form onSubmit={submit} className="mt-6">
          <label className="eyebrow" htmlFor="estimate">
            Your estimate
          </label>
          <div className="mt-1 flex gap-2">
            <div className="flex flex-1 items-center gap-2 rounded border border-rule-strong bg-paper px-3 transition-colors focus-within:border-accent">
              {round.unit === '₹' && <span className="num text-ink-faint">₹</span>}
              <input
                id="estimate"
                type="number"
                inputMode="decimal"
                step="any"
                value={guess}
                onChange={(event) => setGuess(event.target.value)}
                required
                className="num h-10 flex-1 bg-transparent text-sm text-ink outline-none"
              />
              {round.unit !== '₹' && <span className="text-xs text-ink-faint">{round.unit}</span>}
            </div>
            <Button type="submit" disabled={busy || guess === ''}>
              Submit
            </Button>
          </div>
          {error && <p className="mt-2 text-xs text-down">{error}</p>}
          <p className="mt-2 text-xs text-ink-faint">
            Within 2% is full marks; within 25% still scores. Estimate, do not look it up.
          </p>
        </form>
      )}
    </Panel>
  )
}

function Figure({ label, value, emphasis }) {
  return (
    <div>
      <p className="eyebrow">{label}</p>
      <p className={`num mt-1 font-semibold ${emphasis ? 'text-xl text-ink' : 'text-lg text-ink-muted'}`}>
        {value}
      </p>
    </div>
  )
}

function format(value, unit) {
  if (unit === '₹') return `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
  return `${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 })}${unit === '%' ? '%' : ` ${unit}`}`
}
