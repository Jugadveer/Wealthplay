/**
 * Ticker Tiles — guess the listed company in five tries.
 *
 * Each miss reveals one more clue, running broad to narrow: sector, listing,
 * market-cap band, one-year move, first letter. A normalised price silhouette
 * unlocks after the second guess — the shape is the clue, the level is not.
 *
 * Everyone gets the same puzzle each day, so the emoji grid is worth sharing.
 */
import { useEffect, useRef, useState } from 'react'
import { Check, Copy, Search } from 'lucide-react'

import { api } from '../../lib/api'
import { Badge, Button, Panel } from '../../ui'

export default function TickerTiles({ onFinish }) {
  const [board, setBoard] = useState(null)
  const [query, setQuery] = useState('')
  const [matches, setMatches] = useState([])
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    api
      .tickerBoard()
      .then((data) => !cancelled && setBoard(data))
      .catch(() => !cancelled && setError('Could not load today’s board.'))
    return () => {
      cancelled = true
    }
  }, [])

  // Debounced autocomplete: the guess box searches a fixed universe, so the
  // game tests reading clues rather than spelling company names.
  useEffect(() => {
    if (query.trim().length < 2) {
      setMatches([])
      return undefined
    }

    const timer = setTimeout(() => {
      api
        .tickerSearch(query)
        .then((data) => setMatches(data.results))
        .catch(() => setMatches([]))
    }, 180)

    return () => clearTimeout(timer)
  }, [query])

  async function guess(symbol) {
    setError('')
    setQuery('')
    setMatches([])

    try {
      const result = await api.submitTicker({ symbol })
      setBoard((current) => ({ ...current, ...result }))
      if (result.finished) onFinish?.()
    } catch (err) {
      setError(err.message)
    }
  }

  function copyShare() {
    navigator.clipboard?.writeText(board.share).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  if (!board) return <Panel className="h-64 animate-pulse" />

  const remaining = board.max_guesses - board.guesses.length

  return (
    <Panel className="p-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Puzzle one</p>
          <h2 className="mt-1 text-headline">Ticker Tiles</h2>
        </div>
        <Badge tone={board.finished ? (board.solved ? 'up' : 'down') : 'neutral'}>
          {board.finished ? (board.solved ? `solved in ${board.guesses.length}` : 'not solved') : `${remaining} left`}
        </Badge>
      </header>

      <div className="mt-5 flex gap-1.5" aria-label={`${board.guesses.length} of ${board.max_guesses} guesses used`}>
        {Array.from({ length: board.max_guesses }, (_, index) => {
          const attempt = board.guesses[index]
          return (
            <div
              key={index}
              className="flip-in h-10 flex-1 rounded-sm border"
              style={{
                animationDelay: `${index * 60}ms`,
                background: attempt
                  ? attempt.correct
                    ? 'rgb(var(--up))'
                    : 'rgb(var(--paper-sunken))'
                  : 'transparent',
                borderColor: attempt ? 'transparent' : 'rgb(var(--rule))',
              }}
            >
              {attempt && (
                <span
                  className="num flex h-full items-center justify-center text-xs font-semibold"
                  style={{ color: attempt.correct ? '#fff' : 'rgb(var(--ink-muted))' }}
                >
                  {attempt.symbol}
                </span>
              )}
            </div>
          )
        })}
      </div>

      {board.clues.length > 0 && (
        <dl className="mt-6 divide-y divide-rule border-y border-rule">
          {board.clues.map((clue) => (
            <div key={clue.label} className="flex items-baseline justify-between gap-4 py-2.5">
              <dt className="eyebrow">{clue.label}</dt>
              <dd className="num text-sm text-ink">{clue.value}</dd>
            </div>
          ))}
        </dl>
      )}

      {board.silhouette?.length > 0 && (
        <figure className="mt-5">
          <figcaption className="eyebrow">Price shape, past year</figcaption>
          <Silhouette values={board.silhouette} />
        </figure>
      )}

      {!board.finished ? (
        <div className="relative mt-6">
          <label className="eyebrow" htmlFor="ticker-guess">
            Your guess
          </label>
          <div className="mt-1 flex items-center gap-2 rounded border border-rule-strong bg-paper px-3 transition-colors focus-within:border-accent">
            <Search size={15} className="shrink-0 text-ink-faint" />
            <input
              id="ticker-guess"
              ref={inputRef}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Type a company name…"
              autoComplete="off"
              spellCheck="false"
              className="h-10 flex-1 bg-transparent text-sm text-ink outline-none"
            />
          </div>

          {matches.length > 0 && (
            <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded border border-rule bg-paper-raised shadow-float">
              {matches.map((match) => (
                <li key={match.symbol}>
                  <button
                    type="button"
                    onClick={() => guess(match.symbol)}
                    className="flex w-full items-baseline justify-between gap-3 px-3 py-2 text-left text-sm transition-colors hover:bg-paper-sunken"
                  >
                    <span className="text-ink">{match.name}</span>
                    <span className="num text-xs text-ink-faint">{match.symbol}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}

          {error && <p className="mt-2 text-xs text-down">{error}</p>}
        </div>
      ) : (
        <div className="mt-6 border-t border-rule pt-5">
          <p className="text-sm text-ink-muted">
            It was{' '}
            <strong className="font-semibold text-ink">{board.answer.name}</strong> ({board.answer.symbol}).
          </p>

          {board.share && (
            <div className="mt-4">
              <pre className="whitespace-pre-wrap rounded border border-rule bg-paper-sunken p-3 text-xs leading-relaxed text-ink">
                {board.share}
              </pre>
              <Button size="sm" variant="secondary" className="mt-3" onClick={copyShare}>
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? 'Copied' : 'Copy result'}
              </Button>
            </div>
          )}
        </div>
      )}
    </Panel>
  )
}

/** The normalised price shape, drawn without an axis so only form is readable. */
function Silhouette({ values }) {
  const width = 300
  const height = 56
  const path = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width
      const y = height - value * height
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(' ')

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className="mt-2 w-full"
      style={{ height }}
      aria-hidden="true"
    >
      <path
        d={path}
        fill="none"
        className="stroke-accent"
        strokeWidth="2"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  )
}
