/**
 * Rank It — order four listings by last year's return, best first.
 *
 * Scored on pairs rather than exact positions: knowing the winner and the loser
 * but flipping the middle two is most of the understanding, and an
 * all-or-nothing score would tell the player nothing about what they got right.
 */
import { useEffect, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

import { api } from '../../lib/api'
import { percent } from '../../lib/format'
import { Badge, Button, Panel, cx } from '../../ui'

export default function RankIt({ onFinish }) {
  const [board, setBoard] = useState(null)
  const [order, setOrder] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let cancelled = false
    api
      .rankBoard()
      .then((data) => {
        if (cancelled) return
        setBoard(data)
        setOrder(data.cards.map((card) => card.symbol))
      })
      .catch(() => !cancelled && setError('Could not load today’s board.'))
    return () => {
      cancelled = true
    }
  }, [])

  function move(index, delta) {
    const target = index + delta
    if (target < 0 || target >= order.length) return

    const next = [...order]
    ;[next[index], next[target]] = [next[target], next[index]]
    setOrder(next)
  }

  async function submit() {
    setBusy(true)
    setError('')

    try {
      const result = await api.rankSubmit(order)
      setBoard(result)
      onFinish?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (!board) return <Panel className="h-72 animate-pulse" />

  const byId = Object.fromEntries(board.cards.map((card) => [card.symbol, card]))
  const result = board.result
  const shown = board.finished ? board.answer.order : order
  const exactMatches = board.finished
    ? shown.filter((symbol, index) => result.order.indexOf(symbol) === index).length
    : 0

  return (
    <Panel className="p-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Puzzle four</p>
          <h2 className="mt-1 text-headline">Rank It</h2>
        </div>
        {board.finished && (
          <Badge tone={board.solved ? 'up' : 'neutral'}>
            {result.pairs}/{result.of} pairs
          </Badge>
        )}
      </header>

      <p className="mt-2 text-sm text-ink-muted">
        {board.finished
          ? 'The real order, with each return over the past year.'
          : `Put these four in order by return over the ${board.window}, best at the top.`}
      </p>

      <ol className="mt-5 grid gap-2">
        {shown.map((symbol, index) => {
          const card = byId[symbol]
          const change = board.finished ? board.answer.changes[symbol] : null
          const yours = board.finished ? result.order.indexOf(symbol) : index

          return (
            <li
              key={symbol}
              className={cx(
                'flex items-center gap-3 rounded border px-3 py-2.5 transition-colors duration-200',
                board.finished && yours === index
                  ? 'border-up/40 bg-up/5'
                  : board.finished
                    ? 'border-rule bg-paper-sunken'
                    : 'border-rule bg-paper',
              )}
            >
              <span className="num w-5 shrink-0 text-sm font-semibold text-ink-faint">
                {index + 1}
              </span>

              <div className="min-w-0 flex-1">
                <p className="truncate text-sm text-ink">{card.name}</p>
                <p className="num text-[11px] text-ink-faint">
                  {symbol} · {card.sector}
                </p>
              </div>

              {board.finished ? (
                <span className={cx('num text-sm', change >= 0 ? 'text-up' : 'text-down')}>
                  {percent(change, 1)}
                </span>
              ) : (
                <span className="flex shrink-0 gap-1">
                  <Nudge label={`Move ${card.name} up`} onClick={() => move(index, -1)} disabled={index === 0}>
                    <ChevronUp size={15} />
                  </Nudge>
                  <Nudge
                    label={`Move ${card.name} down`}
                    onClick={() => move(index, 1)}
                    disabled={index === order.length - 1}
                  >
                    <ChevronDown size={15} />
                  </Nudge>
                </span>
              )}
            </li>
          )
        })}
      </ol>

      {error && <p className="mt-3 text-xs text-down">{error}</p>}

      {board.finished ? (
        <p className="mt-5 border-t border-rule pt-4 text-sm text-ink-muted">
          You placed {result.pairs} of {result.of} pairs in the right order
          {board.score ? ` for ${board.score} XP.` : '.'}{' '}
          {exactMatches > 0
            ? 'Rows highlighted in green are the ones you put in the right place.'
            : 'None landed in exactly the right slot, but the pairs you did get are what the score counts.'}
        </p>
      ) : (
        <Button className="mt-5" onClick={submit} disabled={busy}>
          {busy ? 'Scoring…' : 'Lock in this order'}
        </Button>
      )}
    </Panel>
  )
}

function Nudge({ children, label, onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      className="rounded-sm border border-rule p-1 text-ink-muted transition-colors hover:border-ink-faint hover:text-ink disabled:opacity-30"
    >
      {children}
    </button>
  )
}
