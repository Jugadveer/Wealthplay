/**
 * Ledger — a five-letter financial term in six tries.
 *
 * Wordle's mechanic, but every answer is a term the courses actually use, and
 * the definition is revealed when the board closes. Losing still teaches you a
 * word, which is the whole reason for picking this shape.
 */
import { useEffect, useRef, useState } from 'react'
import { Check, Copy } from 'lucide-react'

import { api } from '../../lib/api'
import { Badge, Button, Panel } from '../../ui'

const KEYS = ['QWERTYUIOP', 'ASDFGHJKL', 'ZXCVBNM']

export default function Ledger({ onFinish }) {
  const [board, setBoard] = useState(null)
  const [draft, setDraft] = useState('')
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const busy = useRef(false)

  useEffect(() => {
    let cancelled = false
    api
      .ledgerBoard()
      .then((data) => !cancelled && setBoard(data))
      .catch(() => !cancelled && setError('Could not load today’s board.'))
    return () => {
      cancelled = true
    }
  }, [])

  async function submit(word) {
    if (busy.current) return
    busy.current = true
    setError('')

    try {
      const result = await api.ledgerGuess(word)
      setBoard(result)
      setDraft('')
      if (result.finished) onFinish?.()
    } catch (err) {
      setError(err.message)
    } finally {
      busy.current = false
    }
  }

  // A physical keyboard should work; the on-screen one exists for phones.
  useEffect(() => {
    if (!board || board.finished) return undefined

    const onKey = (event) => {
      if (event.metaKey || event.ctrlKey || event.altKey) return
      if (event.key === 'Enter') {
        if (draft.length === board.length) submit(draft)
      } else if (event.key === 'Backspace') {
        setDraft((current) => current.slice(0, -1))
      } else if (/^[a-zA-Z]$/.test(event.key)) {
        setDraft((current) => (current.length < board.length ? current + event.key.toUpperCase() : current))
      }
    }

    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [board, draft])

  function copyShare() {
    navigator.clipboard?.writeText(board.share).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  if (!board) return <Panel className="h-96 animate-pulse" />

  const rows = board.rows ?? []
  const remaining = board.max_guesses - rows.length
  const letterState = bestLetterState(rows)

  return (
    <Panel className="p-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="eyebrow">Puzzle two</p>
          <h2 className="mt-1 text-headline">Ledger</h2>
        </div>
        <Badge tone={board.finished ? (board.solved ? 'up' : 'down') : 'neutral'}>
          {board.finished
            ? board.solved
              ? `solved in ${rows.length}`
              : 'not solved'
            : `${remaining} left`}
        </Badge>
      </header>

      <p className="mt-2 text-sm text-ink-muted">
        A five-letter term from the money world. Green is right, amber is in the word elsewhere.
      </p>

      <div className="mx-auto mt-5 grid w-full max-w-xs gap-1.5" role="grid" aria-label="Guesses">
        {Array.from({ length: board.max_guesses }, (_, rowIndex) => (
          <Row
            key={rowIndex}
            length={board.length}
            row={rows[rowIndex]}
            draft={rowIndex === rows.length && !board.finished ? draft : ''}
          />
        ))}
      </div>

      {error && <p className="mt-3 text-xs text-down">{error}</p>}

      {board.finished ? (
        <div className="mt-6 border-t border-rule pt-5">
          <p className="num text-sm font-semibold text-ink">{board.answer.word}</p>
          <p className="measure mt-1.5 text-sm text-ink-muted">{board.answer.meaning}</p>

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
      ) : (
        <Keyboard
          letterState={letterState}
          canSubmit={draft.length === board.length}
          onKey={(key) => {
            if (key === 'ENTER') {
              if (draft.length === board.length) submit(draft)
            } else if (key === 'DEL') {
              setDraft((current) => current.slice(0, -1))
            } else {
              setDraft((current) => (current.length < board.length ? current + key : current))
            }
          }}
        />
      )}
    </Panel>
  )
}

const TILE_STATE = {
  hit: 'border-transparent bg-up text-white',
  near: 'border-transparent bg-play text-white',
  miss: 'border-transparent bg-paper-sunken text-ink-faint',
}

function Row({ length, row, draft }) {
  return (
    <div className="flex gap-1.5" role="row">
      {Array.from({ length }, (_, index) => {
        const mark = row?.marks?.[index]
        const letter = row ? row.word[index] : draft[index] || ''

        return (
          <span
            key={index}
            role="gridcell"
            className={`num grid aspect-square flex-1 place-items-center rounded-sm border text-lg font-semibold uppercase transition-colors duration-200 ${
              mark ? TILE_STATE[mark] : letter ? 'border-ink-faint text-ink' : 'border-rule text-ink'
            }`}
            style={mark ? { animation: `flip-in 300ms var(--ease) ${index * 70}ms backwards` } : undefined}
          >
            {letter}
          </span>
        )
      })}
    </div>
  )
}

/** The strongest verdict seen for each letter, for colouring the keyboard. */
function bestLetterState(rows) {
  const rank = { miss: 0, near: 1, hit: 2 }
  const state = {}

  for (const row of rows) {
    row.word.split('').forEach((letter, index) => {
      const mark = row.marks[index]
      if (!(letter in state) || rank[mark] > rank[state[letter]]) state[letter] = mark
    })
  }

  return state
}

const KEY_STATE = {
  hit: 'bg-up text-white',
  near: 'bg-play text-white',
  miss: 'bg-paper-sunken text-ink-faint',
}

function Keyboard({ letterState, canSubmit, onKey }) {
  return (
    <div className="mx-auto mt-6 grid w-full max-w-md gap-1.5">
      {KEYS.map((row, index) => (
        <div key={row} className="flex justify-center gap-1.5">
          {index === 2 && (
            <KeyCap wide disabled={!canSubmit} onClick={() => onKey('ENTER')}>
              Enter
            </KeyCap>
          )}
          {row.split('').map((letter) => (
            <KeyCap key={letter} state={letterState[letter]} onClick={() => onKey(letter)}>
              {letter}
            </KeyCap>
          ))}
          {index === 2 && (
            <KeyCap wide onClick={() => onKey('DEL')}>
              Del
            </KeyCap>
          )}
        </div>
      ))}
    </div>
  )
}

function KeyCap({ children, state, wide, disabled, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`num h-11 rounded-sm text-xs font-semibold uppercase transition-colors duration-150 active:scale-95 disabled:opacity-40 ${
        wide ? 'px-3' : 'flex-1'
      } ${state ? KEY_STATE[state] : 'bg-paper-sunken text-ink hover:bg-rule'}`}
    >
      {children}
    </button>
  )
}
